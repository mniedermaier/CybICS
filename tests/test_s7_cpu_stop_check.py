"""The Stop Means Stop? verify module, without a stack.

software/landing/modules/defense_checks/check_s7_cpu_stop.py passes only when
the newest S7comm CPU control request the IDS logged for OpenPLC (rule
s7_cpu_control, 172.18.0.3:102) is a PLC STOP from the last few minutes, the
PLC's status list (SZL 0x0424) reports STOP, and the PLC's heartbeat output
still toggles. These tests pin that it fails closed: a restart after the
STOP, a stale STOP somebody left behind, a STOP to another S7 server, a
stop-flag write and an unreadable PLC must not pass. The IDS API and the PLC
reads are replaced by fakes; the reply parsers are fed frames captured from
OpenPLC's Snap7 server.

tests/test_training.py::TestS7CpuStop runs the real thing on a live stack.
"""
import os
import sys
from datetime import datetime, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

try:
    from modules.defense_checks import check_s7_cpu_stop as check
except ImportError as error:  # requests or pymodbus missing on this host
    pytest.skip(f"check_s7_cpu_stop not importable here ({error})", allow_module_level=True)

PLC = "172.18.0.3"
NOW = datetime(2026, 10, 28, 19, 0, 0)   # the IDS clock in the fake status

# Replies of OpenPLC's Snap7 server to the module's own requests, captured on
# the virtual stack: SZL 0x0424 in RUN, and a read of process outputs byte 0.
SZL_RUN = bytes.fromhex(
    "0300003d02f080320700000002000c0020000112081284010000000000ff09001c0424"
    "0000001400015144ff0800000000000000002610281905010003")
SZL_STOP = SZL_RUN[:44] + b"\x04" + SZL_RUN[45:]
PA_HEARTBEAT_ON = bytes.fromhex("0300001a02f0803203000000030002000500000401ff04000805")
PA_HEARTBEAT_OFF = bytes.fromhex("0300001a02f0803203000000030002000500000401ff04000804")


def _control(action="stop", src="172.18.0.100", dst=PLC, dport=102, age=10, alert_id=1):
    return {"id": alert_id, "rule": "s7_cpu_control", "src": src, "dst": dst,
            "dport": dport, "timestamp": (NOW - timedelta(seconds=age)).isoformat(),
            "s7_control": action, "s7_pi_service": "P_PROGRAM"}


class _Response:
    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


@pytest.fixture
def plc(monkeypatch):
    """Fake IDS alerts, CPU mode and heartbeat; returns a dict the test fills in."""
    state = {"alerts": [], "active": True, "mode": check.CPU_STOP, "running": True}

    def get(url, timeout=None):
        if url.endswith("/api/alerts"):
            return _Response({"alerts": state["alerts"]})
        return _Response({"active": state["active"], "now": NOW.isoformat()})

    monkeypatch.setattr(check.requests, "get", get)
    monkeypatch.setattr(check, "read_cpu_mode", lambda: state["mode"])
    monkeypatch.setattr(check, "scan_cycle_running", lambda: (state["running"], "Modbus"))
    return state


def _passed(result):
    return [c["passed"] for c in result["checks"]]


def test_a_stop_the_plant_ignores_passes(plc):
    plc["alerts"] = [_control()]
    result = check.verify()
    assert result["success"], result
    assert _passed(result) == [True, True, True]
    assert "restart" in result["message"]


@pytest.mark.parametrize("alert", [
    {"rule": "s7_write", "src": "172.18.0.100", "dst": PLC, "dport": 102},   # stop flag
    {"rule": "s7_enumeration", "src": "172.18.0.100", "dst": PLC},          # a read
    _control(dst="172.18.0.6", dport=1102),       # the s7com gateway, not the PLC
    _control(dport=1102),
    _control(action="pi_service"),                # e.g. compress memory
], ids=["stop-flag", "s7-read", "gateway", "port", "other-pi-service"])
def test_only_a_plc_stop_to_openplc_counts(plc, alert):
    plc["alerts"] = [alert]
    result = check.verify()
    assert not result["success"]
    assert _passed(result) == [False, True, True]


@pytest.mark.parametrize("restart", ["warm_start", "cold_start"])
def test_a_restart_after_the_stop_cancels_it(plc, restart):
    plc["alerts"] = [_control(age=60, alert_id=1), _control(restart, age=50, alert_id=2)]
    result = check.verify()
    assert not result["success"]
    assert "restarted" in result["checks"][0]["detail"]


def test_stop_again_after_a_restart_passes(plc):
    plc["alerts"] = [_control(age=90, alert_id=1), _control("warm_start", age=80, alert_id=2),
                     _control(age=5, alert_id=3)]
    assert check.verify()["success"]


def test_the_newest_alert_decides_whatever_the_buffer_order(plc):
    plc["alerts"] = [_control("warm_start", age=50, alert_id=2), _control(age=60, alert_id=1)]
    assert not check.verify()["success"]


def test_another_pi_service_after_the_stop_does_not_cancel_it(plc):
    plc["alerts"] = [_control(age=20, alert_id=1), _control("pi_service", age=10, alert_id=2)]
    assert check.verify()["success"]


def test_a_stale_stop_left_behind_does_not_count(plc):
    """Someone stopped the CPU and never restarted it; a later player must not inherit it."""
    plc["alerts"] = [_control(age=check.STOP_WINDOW + 30)]
    result = check.verify()
    assert not result["success"]
    assert _passed(result) == [False, True, True]
    assert "older than" in result["checks"][0]["detail"]


def test_a_stop_just_inside_the_window_counts(plc):
    plc["alerts"] = [_control(age=check.STOP_WINDOW - 5)]
    assert check.verify()["success"]


def test_an_alert_without_a_timestamp_fails_closed(plc):
    alert = _control()
    del alert["timestamp"]
    plc["alerts"] = [alert]
    assert not check.verify()["success"]


def test_the_plc_must_still_report_stop(plc):
    plc["alerts"] = [_control()]
    plc["mode"] = check.CPU_RUN
    result = check.verify()
    assert not result["success"]
    assert _passed(result) == [True, False, True]
    assert "0x08" in result["checks"][1]["detail"]


def test_a_halted_scan_cycle_fails(plc):
    """If the program really stopped, the lesson's premise is gone: no flag."""
    plc["alerts"] = [_control()]
    plc["running"] = False
    result = check.verify()
    assert not result["success"]
    assert _passed(result) == [True, True, False]


def test_unreadable_plc_fails(plc, monkeypatch):
    plc["alerts"] = [_control()]

    def unreachable():
        raise ConnectionError("port closed")

    monkeypatch.setattr(check, "read_cpu_mode", unreachable)
    monkeypatch.setattr(check, "scan_cycle_running", unreachable)
    result = check.verify()
    assert not result["success"]
    assert _passed(result) == [True, False, False]


def test_unreachable_ids_fails(plc, monkeypatch):
    def down(url, timeout=None):
        raise check.requests.exceptions.ConnectionError("refused")

    monkeypatch.setattr(check.requests, "get", down)
    result = check.verify()
    assert not result["success"]
    assert result["checks"][0]["name"] == "IDS reachable"


def test_a_stopped_ids_is_reported(plc):
    plc["active"] = False
    result = check.verify()
    assert not result["success"]
    assert any(c["name"] == "IDS capturing" for c in result["checks"])


# ---- the raw S7comm replies ----

def test_mode_is_read_from_the_captured_status_list():
    assert check.mode_from_reply(SZL_RUN) == check.CPU_RUN
    assert check.mode_from_reply(SZL_STOP) == check.CPU_STOP


@pytest.mark.parametrize("reply", [
    SZL_RUN[:30],                                   # truncated
    SZL_RUN[:29] + b"\x0a" + SZL_RUN[30:],          # return code: object does not exist
    SZL_RUN[:33] + b"\x00\x11" + SZL_RUN[35:],      # another SZL (identity)
    PA_HEARTBEAT_ON,                                # a job reply, not userdata
], ids=["short", "refused", "other-szl", "not-userdata"])
def test_unexpected_status_replies_raise(reply):
    with pytest.raises(ConnectionError):
        check.mode_from_reply(reply)


def test_heartbeat_is_read_from_the_captured_output_byte():
    assert check.heartbeat_from_reply(PA_HEARTBEAT_ON) is True
    assert check.heartbeat_from_reply(PA_HEARTBEAT_OFF) is False
    with pytest.raises(ConnectionError):
        check.heartbeat_from_reply(PA_HEARTBEAT_ON[:21] + b"\x0a\x00\x00\x00")


def test_sampling_stops_at_the_first_change(monkeypatch):
    values = iter([True, True, False])
    monkeypatch.setattr(check.time, "sleep", lambda s: None)
    assert check._sample(lambda: next(values)) is True


def test_a_frozen_heartbeat_is_not_running(monkeypatch):
    monkeypatch.setattr(check, "HEARTBEAT_SAMPLE", 0.05)
    monkeypatch.setattr(check.time, "sleep", lambda s: None)
    assert check._sample(lambda: True) is False
