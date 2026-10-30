"""The DNP3 Side Door verify module, without a stack.

software/landing/modules/defense_checks/check_dnp3_sidedoor.py passes only when
the newest DNP3 operate on the stop flag (analog output 1128) that the IDS
logged went to OpenPLC's outstation on port 20000, wrote a non-zero value
within the last few minutes, the outstation confirmed it (the IDS filed its
reply with control status 00 under the request), and the flag is still set.
These tests pin that it fails closed: a Modbus write or the HMI's button sets
the same flag, a frame the outstation dropped or refused shows up in the IDS
too, and an old DNP3 stop -- restored or stale -- must not vouch for a later
stop by another route. The IDS API and the PLC read are replaced by fakes;
tests/test_ids_rules.py covers how the IDS pairs requests with replies.

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
                   dst=PLC, dport=20000, age=10, alert_id=1, status=0):
    """An IDS dnp3_operate alert; status is the outstation's reply, None for none."""
    objects = [{"group": group, "variation": variation, "index": index, "value": value}]
    reply = None if status is None else {
        "iin": 0, "objects": [dict(objects[0], status=status)]}
    return {"id": alert_id, "rule": "dnp3_operate", "src": "172.18.0.100", "dst": dst,
            "dport": dport, "timestamp": (NOW - timedelta(seconds=age)).isoformat(),
            "dnp3": [{"function": func, "link_dst": 10, "link_src": 1, "seq": 1,
                      "objects_crc": 0, "objects": objects, "reply": reply}]}


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


def test_a_confirmed_dnp3_operate_on_the_stop_flag_passes(plant):
    plant["alerts"] = [_operate_alert()]
    result = check.verify()
    assert result["success"], result
    assert all(c["passed"] for c in result["checks"])


@pytest.mark.parametrize("func", [0x04, 0x05], ids=["select-before-operate", "direct"])
def test_either_operate_counts_once_confirmed(plant, func):
    plant["alerts"] = [_operate_alert(func=func)]
    assert check.verify()["success"]


@pytest.mark.parametrize("alert,label", [
    ({"rule": "modbus_unauth_write", "src": "172.18.0.100", "dst": PLC}, "modbus"),
    ({"rule": "s7_write", "src": "172.18.0.100", "dst": PLC, "dport": 102,
      "s7_items": [{"area": "DB", "db": 1002, "start": 208, "data": "0001"}]}, "s7"),
    (_operate_alert(value=0), "zero"),
    (_operate_alert(index=1130), "other-point"),
    (_operate_alert(group=12, variation=1), "relay-output"),
    (_operate_alert(func=0x01), "read-function"),
    (_operate_alert(func=0x03), "select-alone"),
    (_operate_alert(dport=20001), "wrong-port"),
    (_operate_alert(dst="172.18.0.6"), "wrong-host"),
])
def test_only_a_dnp3_operate_of_the_stop_flag_counts(plant, alert, label):
    """The plant is stopped in every case; the route or point is what fails."""
    plant["alerts"] = [alert]
    result = check.verify()
    assert not result["success"], label
    assert [c["passed"] for c in result["checks"]] == [False, True], label


# ---- The outstation's reply decides ----
#
# Review found frames the outstation drops or refuses -- a lone OPERATE, then
# transport and application headers without FIR/FIN, UNS or CON set, a
# confirmed-data link control, a cleared DIR bit -- each logged as an operate,
# so a following Modbus stop earned the flag.  Replaying opendnp3's acceptance
# rules in the check kept missing cases; its reply does not.


@pytest.mark.parametrize("status,label", [
    (None, "dropped"),
    (2, "no-select"),
    (1, "select-timeout"),
    (12, "out-of-range"),
    (0xFF, "no-echo"),
])
def test_an_unconfirmed_stop_followed_by_a_modbus_stop_is_refused(plant, status, label):
    plant["alerts"] = [_operate_alert(status=status, alert_id=1),
                       {"id": 2, "rule": "modbus_unauth_write", "src": "172.18.0.100",
                        "dst": PLC}]
    plant["stop"] = 1
    result = check.verify()
    assert not result["success"], label
    assert [c["passed"] for c in result["checks"]] == [False, True], label


def test_a_reply_without_the_point_is_not_a_confirmation(plant):
    alert = _operate_alert()
    alert["dnp3"][0]["reply"] = {"iin": 0x0400, "objects": []}
    plant["alerts"] = [alert]
    assert not check.verify()["success"]


def test_the_echoed_value_decides_not_the_requested_one(plant):
    """Defence in depth: a reply that echoes 0 under a request for 1 is no stop."""
    alert = _operate_alert(value=1)
    alert["dnp3"][0]["reply"]["objects"][0]["value"] = 0
    plant["alerts"] = [alert]
    assert not check.verify()["success"]


@pytest.mark.parametrize("variation", [1, 3, 4])
def test_an_echo_of_another_variation_is_not_a_confirmation(plant, variation):
    alert = _operate_alert()
    alert["dnp3"][0]["reply"]["objects"][0]["variation"] = variation
    plant["alerts"] = [alert]
    assert not check.verify()["success"]


def test_an_unattributed_reply_is_not_a_confirmation(plant):
    alert = _operate_alert()
    alert["dnp3"][0]["reply"] = {"unattributed": True}
    plant["alerts"] = [alert]
    result = check.verify()
    assert not result["success"]
    assert "new connection" in result["checks"][0]["detail"]


def test_an_unattributed_restore_cancels_the_stop(plant):
    restore = _operate_alert(value=0, age=5, alert_id=2)
    restore["dnp3"][0]["reply"] = {"unattributed": True}
    plant["alerts"] = [_operate_alert(value=1, age=20, alert_id=1), restore]
    assert not check.verify()["success"]


def test_a_dropped_frame_is_explained(plant):
    plant["alerts"] = [_operate_alert(status=None)]
    assert "never answered" in check.verify()["checks"][0]["detail"]


def test_a_refused_operate_names_the_status(plant):
    plant["alerts"] = [_operate_alert(func=0x04, status=2)]
    detail = check.verify()["checks"][0]["detail"]
    assert "02 (NO_SELECT)" in detail and "SELECT" in detail


def test_a_direct_operate_no_ack_cannot_be_confirmed(plant):
    plant["alerts"] = [_operate_alert(func=0x06, status=None)]
    result = check.verify()
    assert not result["success"]
    assert "(06)" in result["checks"][0]["detail"]


def test_a_confirmed_stop_survives_a_later_dropped_one(plant):
    plant["alerts"] = [_operate_alert(value=1, age=20, alert_id=1),
                       _operate_alert(value=1, age=5, alert_id=2, status=None)]
    assert check.verify()["success"]


# ---- Newest write and window ----


def test_a_dnp3_restore_cancels_an_earlier_dnp3_stop(plant):
    plant["alerts"] = [_operate_alert(value=1, age=60, alert_id=1),
                       _operate_alert(value=0, age=50, alert_id=2)]
    plant["stop"] = 1   # set afterwards over Modbus or the HMI
    result = check.verify()
    assert not result["success"]
    assert "put 0 back" in result["checks"][0]["detail"]


def test_an_unanswered_restore_cancels_the_stop(plant):
    """An 06 restore writes 0 without a reply, so it must cancel too."""
    plant["alerts"] = [_operate_alert(value=1, age=60, alert_id=1),
                       _operate_alert(value=0, func=0x06, age=50, alert_id=2, status=None)]
    assert not check.verify()["success"]


def test_a_refused_restore_does_not_cancel_the_stop(plant):
    plant["alerts"] = [_operate_alert(value=1, age=20, alert_id=1),
                       _operate_alert(value=0, func=0x04, age=5, alert_id=2, status=2)]
    assert check.verify()["success"]


def test_a_refused_stop_after_a_restore_is_not_enough(plant):
    plant["alerts"] = [_operate_alert(value=1, age=90, alert_id=1),
                       _operate_alert(value=0, age=80, alert_id=2),
                       _operate_alert(value=1, age=5, alert_id=3, status=2)]
    assert not check.verify()["success"]


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


# ---- Plant, IDS and malformed input ----


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


@pytest.mark.parametrize("dnp3", [
    [{"function": 0x05, "objects": [{"group": 41, "variation": 2}], "reply": None},
     {"function": None, "objects": None}],
    [{"function": 0x05, "objects": [{"group": 41, "variation": 2, "index": 1128,
                                     "value": 1}],
      "reply": {"objects": [{"group": 41, "index": 1128, "status": "0"}]}}],
    [{"function": 0x05, "objects": [{"group": 41, "variation": 2, "index": 1128,
                                     "value": 1}], "reply": "yes"}],
    ["junk"],
], ids=["no-point", "string-status", "string-reply", "junk"])
def test_malformed_dnp3_payload_fails_closed(plant, dnp3):
    plant["alerts"] = [{"rule": "dnp3_operate", "dst": PLC, "dport": 20000,
                        "timestamp": NOW.isoformat(), "dnp3": dnp3}]
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
