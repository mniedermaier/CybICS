"""What Sharky tells the browser when a capture is refused or cannot start
(no stack needed).

CodeQL alert 101 (py/stack-trace-exposure): /api/network/start answered a
failed start with str(CaptureError), whose message carried Scapy's or the
kernel's own words, and /api/network/stats showed the same text as the
capture's error. The browser now only gets the fixed texts of
network_capture.PUBLIC_MESSAGES; the detail goes to the landing log.
"""
import os
import sys
import threading

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

pytest.importorskip("scapy")
from modules import network_capture as nc  # noqa: E402

INTERNAL = "/proc/net/secret-path: Operation not permitted (errno 1)"


class DyingSniffer:
    """An AsyncSniffer whose thread ends at once with an internal error."""

    def __init__(self, **kwargs):
        self.exception = PermissionError(INTERNAL)
        self.thread = threading.Thread(target=lambda: None)
        self.running = False

    def start(self):
        self.thread.start()
        self.thread.join()

    def stop(self, join=True):
        pass


@pytest.fixture
def capture(monkeypatch):
    import scapy.sendrecv
    monkeypatch.setattr(scapy.sendrecv, "AsyncSniffer", DyingSniffer)
    monkeypatch.setattr(nc, "all_interfaces", lambda: ["br-lab"])
    capture = nc.NetworkCapture()
    yield capture
    if capture.pcap is not None:
        capture.pcap.close()


def test_a_failed_start_tells_the_browser_a_fixed_text_only(capture):
    with pytest.raises(nc.CaptureError) as caught:
        capture.start("all", "")
    assert INTERNAL in str(caught.value), "the log should keep the detail"
    assert nc.public_message(caught.value) == nc.PUBLIC_MESSAGES["start_failed"]
    assert capture.get_stats()["error"] == nc.PUBLIC_MESSAGES["start_failed"]


@pytest.mark.parametrize("interface, filter_name, reason", [
    (["ctfwlan0"], "", "bad_request"),
    ("all", "tcp) or (not net 172.18.0.0/24", "unknown_filter"),
])
def test_a_refused_request_does_not_echo_the_input(capture, interface, filter_name, reason):
    with pytest.raises(nc.CaptureError) as caught:
        capture.start(interface, filter_name)
    assert caught.value.reason == reason
    text = nc.public_message(caught.value)
    assert text == nc.PUBLIC_MESSAGES[reason]
    assert "172.18" not in text and "ctfwlan0" not in text


def test_an_unknown_reason_falls_back_to_the_generic_text():
    assert nc.public_message(ValueError("anything")) == nc.PUBLIC_MESSAGES["start_failed"]
