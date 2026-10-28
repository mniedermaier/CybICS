"""The DNP3 Side Door verify module, without a stack.

software/landing/modules/defense_checks/check_dnp3_sidedoor.py passes only when
the newest DNP3 operate on the stop flag (analog output 1128) that the IDS
logged went to OpenPLC's outstation on port 20000 with the right link
addresses, wrote a non-zero value within the last few minutes, and the flag is
still set. These tests pin that it fails closed: a Modbus write or the HMI's
button sets the same flag, a DNP3 read or an operate on another point shows up
in the IDS too, and an old DNP3 stop -- restored or stale -- must not vouch for
a later stop by another route. The IDS API and the PLC read are replaced by
fakes.

tests/test_training.py::TestDnp3SideDoor runs the real thing on a live stack.
"""
import os
import sys
from datetime import datetime, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

try:
    from modules.defense_checks import check_dnp3_sidedoor as check
except ImportError as error:  # requests or pymodbus missing on this host
    pytest.skip(f"check_dnp3_sidedoor not importable here ({error})", allow_module_level=True)

PLC = "172.18.0.3"
NOW = datetime(2026, 10, 28, 15, 0, 0)


def _operate_alert(value=1, index=1128, group=41, variation=2, func=0x05,
                   link_dst=10, link_src=1, dst=PLC, dport=20000, age=10, alert_id=1,
                   seq=1, objects_crc=None):
    objects = [{"group": group, "variation": variation, "index": index, "value": value}]
    if objects_crc is None:   # stands in for the CRC of the raw object bytes
        objects_crc = hash((group, variation, index, value)) & 0xFFFF
    return {"id": alert_id, "rule": "dnp3_operate", "src": "172.18.0.100", "dst": dst,
            "dport": dport, "timestamp": (NOW - timedelta(seconds=age)).isoformat(),
            "dnp3": [{"function": func, "link_dst": link_dst, "link_src": link_src,
                      "seq": seq, "objects_crc": objects_crc, "objects": objects}]}


def _select_then_operate(value=1, age=10, first_id=1, gap=1, seq=4, operate=None):
    """A SELECT and the OPERATE that follows it, as the outstation expects them."""
    select = _operate_alert(value=value, func=0x03, age=age + gap, alert_id=first_id,
                            seq=seq)
    kwargs = {"value": value, "func": 0x04, "age": age, "alert_id": first_id + 1,
              "seq": (seq + 1) & 0x0F}
    kwargs.update(operate or {})
    return [select, _operate_alert(**kwargs)]


class _Response:
    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


@pytest.fixture
def plant(monkeypatch):
    state = {"alerts": [], "active": True, "stop": 1}

    def get(url, timeout=None):
        if url.endswith("/api/alerts"):
            return _Response({"alerts": state["alerts"]})
        return _Response({"active": state["active"], "now": NOW.isoformat()})

    monkeypatch.setattr(check.requests, "get", get)
    monkeypatch.setattr(check, "_read_stop_flag", lambda: (state["stop"], "Modbus"))
    return state


def test_dnp3_operate_on_the_stop_flag_passes(plant):
    plant["alerts"] = [_operate_alert()]
    result = check.verify()
    assert result["success"], result
    assert all(c["passed"] for c in result["checks"])


@pytest.mark.parametrize("alert,label", [
    ({"rule": "modbus_unauth_write", "src": "172.18.0.100", "dst": PLC}, "modbus"),
    ({"rule": "s7_write", "src": "172.18.0.100", "dst": PLC, "dport": 102,
      "s7_items": [{"area": "DB", "db": 1002, "start": 208, "data": "0001"}]}, "s7"),
    (_operate_alert(value=0), "zero"),
    (_operate_alert(index=1130), "manual-ish"),
    (_operate_alert(group=12, variation=1), "relay-output"),
    (_operate_alert(func=0x01), "read-function"),
    (_operate_alert(func=0x03), "select-alone"),
    (_operate_alert(func=0x04), "operate-without-select"),
    (_operate_alert(link_dst=11), "wrong-outstation"),
    (_operate_alert(link_src=2), "wrong-master"),
    (_operate_alert(dport=20001), "wrong-port"),
    (_operate_alert(dst="172.18.0.6"), "wrong-host"),
])
def test_only_a_dnp3_operate_of_the_stop_flag_counts(plant, alert, label):
    """The plant is stopped in every case; the route or point is what fails."""
    plant["alerts"] = [alert]
    result = check.verify()
    assert not result["success"], label
    assert [c["passed"] for c in result["checks"]] == [False, True], label


def test_a_dnp3_restore_cancels_an_earlier_dnp3_stop(plant):
    plant["alerts"] = [_operate_alert(value=1, age=60, alert_id=1),
                       _operate_alert(value=0, age=50, alert_id=2)]
    plant["stop"] = 1   # set afterwards over Modbus or the HMI
    result = check.verify()
    assert not result["success"]
    assert "put 0 back" in result["checks"][0]["detail"]


def test_stop_again_after_a_restore_passes(plant):
    plant["alerts"] = [_operate_alert(value=1, age=90, alert_id=1),
                       _operate_alert(value=0, age=80, alert_id=2),
                       _operate_alert(value=1, age=5, alert_id=3)]
    assert check.verify()["success"]


def test_the_newest_alert_decides_whatever_the_buffer_order(plant):
    plant["alerts"] = [_operate_alert(value=0, age=50, alert_id=2),
                       _operate_alert(value=1, age=60, alert_id=1)]
    assert not check.verify()["success"]


def test_a_later_operate_on_another_point_does_not_cancel_the_stop(plant):
    plant["alerts"] = [_operate_alert(value=1, age=20, alert_id=1),
                       _operate_alert(value=0, index=1130, age=5, alert_id=2)]
    assert check.verify()["success"]


def test_a_stale_stop_does_not_count(plant):
    plant["alerts"] = [_operate_alert(value=1, age=check.WRITE_WINDOW + 30)]
    result = check.verify()
    assert not result["success"]
    assert "older than" in result["checks"][0]["detail"]


def test_a_stop_just_inside_the_window_counts(plant):
    plant["alerts"] = [_operate_alert(value=1, age=check.WRITE_WINDOW - 5)]
    assert check.verify()["success"]


def test_an_alert_without_a_timestamp_fails_closed(plant):
    alert = _operate_alert()
    del alert["timestamp"]
    plant["alerts"] = [alert]
    assert not check.verify()["success"]


def test_the_plant_must_still_be_stopped(plant):
    plant["alerts"] = [_operate_alert()]
    plant["stop"] = 0
    result = check.verify()
    assert not result["success"]
    assert [c["passed"] for c in result["checks"]] == [True, False]


def test_a_stopped_ids_is_reported(plant):
    plant["active"] = False
    result = check.verify()
    assert not result["success"]
    assert any(c["name"] == "IDS capturing" for c in result["checks"])


def test_malformed_dnp3_payload_fails_closed(plant):
    plant["alerts"] = [{"rule": "dnp3_operate", "dst": PLC, "dport": 20000,
                        "dnp3": [{"function": 0x05, "link_dst": 10, "link_src": 1,
                                  "objects": [{"group": 41, "variation": 2}]},
                                 {"function": None, "objects": None}]}]
    assert not check.verify()["success"]


def test_an_unreachable_ids_is_reported(plant, monkeypatch):
    import requests as requests_mod

    def boom(url, timeout=None):
        raise requests_mod.exceptions.ConnectionError("down")

    monkeypatch.setattr(check.requests, "get", boom)
    result = check.verify()
    assert not result["success"]
    assert any("IDS" in c["name"] for c in result["checks"])


def test_an_unreadable_flag_fails(plant, monkeypatch):
    plant["alerts"] = [_operate_alert()]

    def unreadable():
        raise ConnectionError("both ports closed")

    monkeypatch.setattr(check, "_read_stop_flag", unreadable)
    assert not check.verify()["success"]


# ---- OPERATE (0x04) acts only after a matching SELECT ----
#
# opendnp3's ControlState::ValidateSelection runs an OPERATE only when the last
# SELECT carried the previous application sequence number, byte-identical
# objects, and came less than selectTimeout (10 s) earlier; otherwise the
# outstation answers control status 02 (NO_SELECT) or 01 (TIMEOUT) and writes
# nothing.  The IDS logs the refused OPERATE all the same, so the check has to
# replay those rules, or a refused OPERATE plus a Modbus stop earns the flag.


def test_a_lone_operate_followed_by_a_modbus_stop_is_refused(plant):
    """The bypass found in review: FC 04 without SELECT, then HR1128 = 1 over Modbus."""
    plant["alerts"] = [_operate_alert(func=0x04, alert_id=1),
                       {"id": 2, "rule": "modbus_unauth_write", "src": "172.18.0.100",
                        "dst": PLC}]
    plant["stop"] = 1
    result = check.verify()
    assert not result["success"]
    assert [c["passed"] for c in result["checks"]] == [False, True]
    assert "NO_SELECT" in result["checks"][0]["detail"]


def test_select_then_operate_passes(plant):
    plant["alerts"] = _select_then_operate()
    assert check.verify()["success"]


def test_select_then_operate_wraps_the_sequence_number(plant):
    plant["alerts"] = _select_then_operate(seq=15)   # the OPERATE carries 0
    assert plant["alerts"][1]["dnp3"][0]["seq"] == 0
    assert check.verify()["success"]


@pytest.mark.parametrize("operate,gap,label", [
    ({"seq": 9}, 1, "wrong-sequence"),
    ({"seq": 4}, 1, "same-sequence"),
    ({"objects_crc": 0x1234}, 1, "other-objects"),
    ({}, check.SELECT_TIMEOUT, "select-timed-out"),
    ({}, -1, "operate-before-select"),
    ({"link_src": 2}, 1, "operate-wrong-master"),
])
def test_an_operate_the_outstation_refuses_does_not_count(plant, operate, gap, label):
    alerts = _select_then_operate(gap=gap, operate=operate)
    if gap < 0:   # the IDS logged the OPERATE first
        alerts[0]["id"], alerts[1]["id"] = 2, 1
    plant["alerts"] = alerts
    result = check.verify()
    assert not result["success"], label
    assert [c["passed"] for c in result["checks"]] == [False, True], label


def test_a_select_to_the_wrong_outstation_arms_nothing(plant):
    alerts = _select_then_operate()
    alerts[0]["dnp3"][0]["link_dst"] = 11
    plant["alerts"] = alerts
    assert not check.verify()["success"]


def test_a_later_select_replaces_the_earlier_one(plant):
    """The outstation keeps only the last selection, so the OPERATE must match it."""
    alerts = _select_then_operate(seq=4)
    other = _operate_alert(value=1, index=1130, func=0x03, age=10.5, alert_id=5, seq=6)
    alerts[1]["id"] = 6
    plant["alerts"] = [alerts[0], other, alerts[1]]
    assert not check.verify()["success"]


def test_a_refused_restore_does_not_cancel_a_direct_stop(plant):
    """An OPERATE of 0 without SELECT wrote nothing, so the stop still stands."""
    plant["alerts"] = [_operate_alert(value=1, age=20, alert_id=1),
                       _operate_alert(value=0, func=0x04, age=5, alert_id=2)]
    assert check.verify()["success"]


def test_a_select_before_operate_restore_cancels_the_stop(plant):
    plant["alerts"] = ([_operate_alert(value=1, age=30, alert_id=1)]
                       + _select_then_operate(value=0, age=5, first_id=2))
    result = check.verify()
    assert not result["success"]
    assert "put 0 back" in result["checks"][0]["detail"]
