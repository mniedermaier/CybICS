"""The S7 Side Door verify module, without a stack.

software/landing/modules/defense_checks/check_s7_sidedoor.py passes only when
the newest S7comm WriteVar to OpenPLC's stop flag (DB1002 bytes 208-209 on
port 102) that the IDS logged put a non-zero value there within the last few
minutes, and the flag is still set. These tests pin that it fails closed: the
HMI's stop button or a Modbus write sets the same flag, an S7 read or an
unrelated S7 write shows up in the IDS too, and an old S7 stop -- restored
over S7 or simply stale -- may not vouch for a later stop by another route.
The IDS API and the PLC read are replaced by fakes.

tests/test_training.py::TestS7SideDoor runs the real thing on a live stack.
"""
import os
import sys
from datetime import datetime, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

try:
    from modules.defense_checks import check_s7_sidedoor as check
except ImportError as error:  # requests or pymodbus missing on this host
    pytest.skip(f"check_s7_sidedoor not importable here ({error})", allow_module_level=True)

PLC = "172.18.0.3"
NOW = datetime(2026, 10, 28, 15, 0, 0)   # the IDS clock in the fake status


def _write_alert(data="0001", start=208, db=1002, area="DB", dst=PLC, dport=102,
                 age=10, alert_id=1):
    return {"id": alert_id, "rule": "s7_write", "src": "172.18.0.100", "dst": dst,
            "dport": dport, "timestamp": (NOW - timedelta(seconds=age)).isoformat(),
            "s7_items": [{"area": area, "db": db, "start": start, "bit": 0,
                          "length": len(data) // 2, "data": data}]}


class _Response:
    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


@pytest.fixture
def plant(monkeypatch):
    """Fake IDS alerts and stop flag; returns a dict the test fills in."""
    state = {"alerts": [], "active": True, "stop": 1}

    def get(url, timeout=None):
        if url.endswith("/api/alerts"):
            return _Response({"alerts": state["alerts"]})
        return _Response({"active": state["active"], "now": NOW.isoformat()})

    monkeypatch.setattr(check.requests, "get", get)
    monkeypatch.setattr(check, "_read_stop_flag", lambda: (state["stop"], "Modbus"))
    return state


def test_s7_write_of_the_stop_flag_passes(plant):
    plant["alerts"] = [_write_alert()]
    result = check.verify()
    assert result["success"], result
    assert all(c["passed"] for c in result["checks"])


def test_a_wider_write_that_covers_the_flag_passes(plant):
    # DB1002 bytes 200-211: gst (%MW100), %MW101, hpt (%MW102), %MW103, stop = 1, %MW105
    plant["alerts"] = [_write_alert(data="0064" "0000" "0032" "0000" "0001" "0000", start=200)]
    assert check.verify()["success"]


@pytest.mark.parametrize("alert", [
    {"rule": "modbus_unauth_write", "src": "172.18.0.100", "dst": PLC},   # Modbus route
    {"rule": "s7_enumeration", "src": "172.18.0.100", "dst": PLC},        # a read
    _write_alert(data="0000"),                  # writing 0 does not stop the plant
    _write_alert(start=212),                    # manual, not stop
    _write_alert(db=1),                         # another data block
    _write_alert(area="PA", db=0, start=0),     # the outputs
    _write_alert(dst="172.18.0.6", dport=1102),  # the s7com gateway, not the PLC
    _write_alert(dport=1102),
], ids=["modbus", "s7-read", "zero", "manual", "other-db", "outputs", "gateway", "port"])
def test_only_an_s7_write_of_the_stop_flag_counts(plant, alert):
    """The plant is stopped in every case; the route it took is what fails."""
    plant["alerts"] = [alert]
    result = check.verify()
    assert not result["success"]
    assert [c["passed"] for c in result["checks"]] == [False, True]


def test_an_s7_restore_cancels_an_earlier_s7_stop(plant):
    """Write 1, write 0, then stop by another route: the critic's live repro."""
    plant["alerts"] = [_write_alert("0001", age=60, alert_id=1),
                       _write_alert("0000", age=50, alert_id=2)]
    plant["stop"] = 1      # set afterwards over Modbus or the HMI
    result = check.verify()
    assert not result["success"]
    assert [c["passed"] for c in result["checks"]] == [False, True]
    assert "put 0 back" in result["checks"][0]["detail"]


def test_a_wider_restore_cancels_a_narrow_stop(plant):
    plant["alerts"] = [_write_alert("0001", age=60, alert_id=1),
                       _write_alert("0000" * 6, start=200, age=50, alert_id=2)]
    assert not check.verify()["success"]


def test_stop_again_after_a_restore_passes(plant):
    plant["alerts"] = [_write_alert("0001", age=90, alert_id=1),
                       _write_alert("0000", age=80, alert_id=2),
                       _write_alert("0001", age=5, alert_id=3)]
    assert check.verify()["success"]


def test_the_newest_alert_decides_whatever_the_buffer_order(plant):
    plant["alerts"] = [_write_alert("0000", age=50, alert_id=2),
                       _write_alert("0001", age=60, alert_id=1)]
    assert not check.verify()["success"]


def test_unrelated_writes_after_the_stop_do_not_cancel_it(plant):
    plant["alerts"] = [_write_alert("0001", age=20, alert_id=1),
                       _write_alert("0000", start=212, age=10, alert_id=2),   # manual
                       _write_alert("04", area="PA", db=0, start=0, age=5, alert_id=3)]
    assert check.verify()["success"]


def test_a_stale_stop_write_does_not_count(plant):
    """An S7 stop older than the window, never restored, then a stop by another route."""
    plant["alerts"] = [_write_alert("0001", age=check.WRITE_WINDOW + 30)]
    result = check.verify()
    assert not result["success"]
    assert [c["passed"] for c in result["checks"]] == [False, True]
    assert "older than" in result["checks"][0]["detail"]


def test_a_stop_write_just_inside_the_window_counts(plant):
    plant["alerts"] = [_write_alert("0001", age=check.WRITE_WINDOW - 5)]
    assert check.verify()["success"]


def test_an_alert_without_a_timestamp_fails_closed(plant):
    alert = _write_alert()
    del alert["timestamp"]
    plant["alerts"] = [alert]
    assert not check.verify()["success"]


def test_the_plant_must_still_be_stopped(plant):
    plant["alerts"] = [_write_alert()]
    plant["stop"] = 0
    result = check.verify()
    assert not result["success"]
    assert [c["passed"] for c in result["checks"]] == [True, False]


def test_a_stopped_ids_is_reported(plant):
    plant["active"] = False
    result = check.verify()
    assert not result["success"]
    assert any(c["name"] == "IDS capturing" for c in result["checks"])


def test_malformed_alert_items_fail_closed(plant):
    plant["alerts"] = [{"rule": "s7_write", "dst": PLC, "dport": 102,
                        "s7_items": [{"area": "DB", "db": 1002, "start": "x", "data": "zz"},
                                     {"area": "DB", "db": 1002, "start": 208, "data": None}]}]
    assert not check.verify()["success"]


def test_an_unreadable_flag_fails(plant, monkeypatch):
    plant["alerts"] = [_write_alert()]

    def unreadable():
        raise ConnectionError("both ports closed")

    monkeypatch.setattr(check, "_read_stop_flag", unreadable)
    assert not check.verify()["success"]


def test_modbus_closed_falls_back_to_s7(monkeypatch):
    """The Modbus Firewall challenge closes 502 to the landing host."""
    def closed():
        raise ConnectionError("Modbus port closed")

    monkeypatch.setattr(check, "_read_stop_modbus", closed)
    monkeypatch.setattr(check, "_read_stop_s7", lambda: 1)
    assert check._read_stop_flag() == (1, "S7comm")
