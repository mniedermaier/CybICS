"""The landing page's side of the optional central CTF server.

modules/central_ctf.py is the CybICS-CTF reference client, vendored unchanged
and tested in that repository. What is CybICS' own is the glue in
utils/central.py: the strict progress read the enrolment baseline depends on,
the instance description, the heartbeat status and the file exchange with
hwio-raspberry. That is tested here, plus one round trip of the vendored
client against a minimal in-process server, wired the way app.py wires it.

None of this needs Flask or a running stack.
"""
import json
import os
import stat
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")
sys.path.insert(0, LANDING)

from modules.central_ctf import CTFClient, CTFClientError  # noqa: E402
from utils import central  # noqa: E402

VERSION_H = os.path.join(ROOT, "software", "stm32", "src", "version.h")


# ---------- progress ----------

def test_no_progress_file_means_no_solves(tmp_path):
    assert central.read_progress_strict(str(tmp_path / "missing.json")) == []


def test_progress_is_read(tmp_path):
    path = tmp_path / "ctf_progress.json"
    path.write_text(json.dumps({"solved_challenges": ["scanning", "opcua"], "total_points": 300}))
    assert central.read_progress_strict(str(path)) == ["scanning", "opcua"]


@pytest.mark.parametrize("content", ['{"solved_chall', '[]', '{}'])
def test_unreadable_progress_raises(tmp_path, content):
    """An empty list here would become the enrolment baseline, and every old
    solve on a reused board would be reported as new."""
    path = tmp_path / "ctf_progress.json"
    path.write_text(content)
    with pytest.raises(Exception):
        central.read_progress_strict(str(path))


def test_enrolment_refuses_unreadable_progress(tmp_path):
    progress = tmp_path / "ctf_progress.json"
    progress.write_text('{"half')
    client = CTFClient(str(tmp_path / "central.json"),
                       local_solves=lambda: central.read_progress_strict(str(progress)))
    with pytest.raises(CTFClientError) as error:
        client.enroll("http://127.0.0.1:9", "CODE", "Team", "password1", {"kind": "virtual"})
    assert error.value.code == "progress_unreadable"


# ---------- instance description ----------

def test_version_comes_from_the_firmware_header(monkeypatch):
    monkeypatch.delenv("CYBICS_RELEASE", raising=False)
    with open(VERSION_H, encoding="utf-8") as fh:
        header = fh.read()
    import re
    expected = ".".join(re.search(rf"FIRMWARE_VERSION_{p}\s+(\d+)", header).group(1)
                        for p in ("MAJOR", "MINOR", "PATCH"))
    assert central.read_version(VERSION_H) == expected


def test_version_without_a_header_is_unknown(tmp_path, monkeypatch):
    monkeypatch.delenv("CYBICS_RELEASE", raising=False)
    assert central.read_version(str(tmp_path / "version.h")) is None


@pytest.mark.parametrize("content, expected", [
    ('{"device_uid": "0042001a3133"}', "0042001a3133"),
    ('{"device_uid": "0042001A3133"}', None),       # the server wants lower case
    ('{"device_uid": "abc"}', None),                # too short
    ('{"device_uid": 42}', None),
    ('[]', None),
    ('{half', None),
])
def test_device_uid(tmp_path, content, expected):
    path = tmp_path / "device.json"
    path.write_text(content)
    assert central.read_device_uid(str(path)) == expected


def test_no_device_file_on_a_virtual_stack(tmp_path):
    assert central.read_device_uid(str(tmp_path / "device.json")) is None


def test_status_is_small_and_names_no_network():
    containers = [{"name": "openplc", "status": "running"}, {"name": "fuxa", "status": "exited"},
                  {"status": "running"}]
    status = central.collect_status(containers, ["scanning"])
    assert status["services"] == {"openplc": True, "fuxa": False}
    assert status["local_solved"] == ["scanning"]
    assert len(json.dumps(status)) < 16 * 1024
    assert not any(key in json.dumps(status) for key in ("172.18.", "10.0.0.", "wlan"))


# ---------- uplink hand-over to hwio-raspberry ----------

@pytest.mark.parametrize("ssid, psk, ok", [
    ("cybics-ctf", "12345678", True),
    ("", "12345678", False),
    ("x" * 33, "12345678", False),
    ("cybics-ctf", "1234567", False),
    ("cybics-ctf", "p" * 64, False),
    ("cybics-ctf", "pässwörter", False),
])
def test_uplink_validation(ssid, psk, ok):
    assert (central.validate_uplink(ssid, psk) is None) is ok


def test_uplink_request_is_private(tmp_path):
    central.request_uplink(True, "event-wifi", "secret-pass", directory=str(tmp_path))
    path = tmp_path / central.UPLINK_REQUEST
    assert json.loads(path.read_text())["psk"] == "secret-pass"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert central.uplink_status(str(tmp_path))["pending"] is True


def test_disabling_the_uplink_carries_no_credentials(tmp_path):
    central.request_uplink(False, "event-wifi", "secret-pass", directory=str(tmp_path))
    assert "secret-pass" not in (tmp_path / central.UPLINK_REQUEST).read_text()


def test_uplink_needs_the_shared_volume(tmp_path):
    with pytest.raises(OSError):
        central.request_uplink(True, "event-wifi", "secret-pass", directory=str(tmp_path / "missing"))
    assert central.uplink_status(str(tmp_path / "missing"))["available"] is False


# ---------- round trip with the vendored client ----------

class FakeServer(BaseHTTPRequestHandler):
    """The four calls the client makes, answered the way CybICS-CTF does."""
    received = []

    def log_message(self, *args):
        pass

    def _reply(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/v1/info":
            self._reply(200, {"service": "cybics-ctf", "name": "Test", "version": "0", "api_version": 1})
        else:
            self._reply(404, {"error": {"code": "not_found", "message": "nope"}})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeServer.received.append((self.path, body, self.headers.get("Authorization")))
        event = {"name": "Workshop", "slug": "ws", "state": "running", "created_at": 1.0}
        if self.path == "/api/v1/enroll":
            self._reply(201, {"instance_id": "i-1", "token": "tok", "team": {"id": 1, "name": body["team_name"]},
                              "event": event, "heartbeat_interval": 30})
        elif self.path == "/api/v1/heartbeat":
            self._reply(200, {"event": event, "team": {"id": 1, "name": "Team", "score": 0, "rank": 1, "teams": 1},
                              "solved": [], "catalog_version": "v1", "announcements": [], "announcement_ids": []})
        elif self.path == "/api/v1/solves":
            self._reply(200, {"result": "accepted"})


@pytest.fixture
def server():
    FakeServer.received = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), FakeServer)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_round_trip(tmp_path, server):
    """Old progress stays local, new solves are reported with their flag, and
    the token never reaches the landing page."""
    progress = tmp_path / "ctf_progress.json"
    progress.write_text(json.dumps({"solved_challenges": ["physical_process"], "total_points": 100}))
    flags = {"physical_process": "CybICS(Bl0w0ut)", "scanning": "CybICS(scanning_d0ne)"}
    client = CTFClient(str(tmp_path / "central_ctf.json"),
                       local_solves=lambda: central.read_progress_strict(str(progress)),
                       flag_for=flags.get,
                       status=lambda: central.collect_status([], central.read_progress_strict(str(progress))))

    # Disabled: report_solve is a no-op and nothing is sent.
    client.report_solve("scanning", flags["scanning"])
    assert FakeServer.received == [] and client.snapshot()["pending"] == 0

    assert client.test_connection(server)["service"] == "cybics-ctf"
    client.enroll(server, "CODE", "Team", "password1", {"kind": "virtual"})
    assert "token" not in client.snapshot()

    progress.write_text(json.dumps({"solved_challenges": ["physical_process", "scanning"],
                                    "total_points": 200}))
    client.report_solve("scanning", flags["scanning"])
    assert client.sync_once() is True

    solves = [body for path, body, _ in FakeServer.received if path == "/api/v1/solves"]
    assert [s["challenge_id"] for s in solves] == ["scanning"]
    assert solves[0]["flag"] == "CybICS(scanning_d0ne)"
    assert all(auth == "Bearer tok" for path, _, auth in FakeServer.received if path != "/api/v1/enroll")
    assert client.snapshot()["pending"] == 0

    state = tmp_path / "central_ctf.json"
    assert stat.S_IMODE(state.stat().st_mode) == 0o600
