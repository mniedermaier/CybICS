"""
The IDS-backed attack checks (Flood & Overwrite, Fuzzing Modbus, MitM) only
count an alert the IDS raised in the last ATTACK_WINDOW seconds.

The IDS keeps its alert buffer across CTF resets, so an attack run once -- by
the test suite, an instructor's demo or another student -- used to pass these
checks for everyone afterwards. The IDS API is replaced by a fake; the live
solves of all three are in TestAdvancedSecurity in tests/test_training.py.
"""
import os
import sys
from datetime import datetime, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

# No skip when requests is missing: tests/requirements.txt pins it, and a
# module that silently skips on a bare host is how a check goes untested.
from modules.defense_checks import _ids_rule  # noqa: E402
from modules.defense_checks import (  # noqa: E402
    check_flood_attack, check_fuzzing_attack, check_mitm_attack)

NOW = datetime(2026, 10, 29, 12, 0, 0)

CHECKS = [
    (check_flood_attack, "modbus_flood"),
    (check_fuzzing_attack, "modbus_diagnostic"),
    (check_mitm_attack, "arp_spoof"),
]


class _Response:
    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


@pytest.fixture
def ids(monkeypatch):
    state = {"stats": {}, "now": NOW.isoformat()}

    def get(url, timeout=None):
        if url.endswith("/api/rules/stats"):
            return _Response(state["stats"])
        if url.endswith("/api/status"):
            return _Response({"active": True, "now": state["now"]})
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(_ids_rule.requests, "get", get)
    return state


def _fired(rule, age):
    return {rule: {"count": 3, "last_seen": (NOW - timedelta(seconds=age)).isoformat()}}


@pytest.mark.parametrize("check,rule", CHECKS, ids=[r for _, r in CHECKS])
def test_a_fresh_alert_passes(ids, check, rule):
    ids["stats"] = _fired(rule, 30)
    assert check.verify()["success"]


@pytest.mark.parametrize("check,rule", CHECKS, ids=[r for _, r in CHECKS])
def test_an_old_alert_does_not(ids, check, rule):
    ids["stats"] = _fired(rule, _ids_rule.ATTACK_WINDOW + 1)
    result = check.verify()
    assert not result["success"]
    assert "10 minutes" in result["checks"][0]["detail"]


@pytest.mark.parametrize("check,rule", CHECKS, ids=[r for _, r in CHECKS])
def test_no_alert_does_not(ids, check, rule):
    ids["stats"] = {rule: {"count": 0, "last_seen": None}}
    assert not check.verify()["success"]


@pytest.mark.parametrize("check,rule", CHECKS, ids=[r for _, r in CHECKS])
def test_another_rule_does_not_count(ids, check, rule):
    ids["stats"] = _fired("port_scan", 10)
    assert not check.verify()["success"]


def test_age_is_measured_on_the_ids_clock(ids):
    # The IDS clock is an hour ahead of NOW (another time zone); only the
    # difference between its "now" and its timestamps matters.
    ids["now"] = (NOW + timedelta(hours=1)).isoformat()
    ids["stats"] = _fired("modbus_flood", -3600 + 20)
    assert _ids_rule.rule_fired("modbus_flood")[0]


def test_unreadable_timestamps_do_not_pass(ids):
    ids["stats"] = {"modbus_flood": {"count": 1, "last_seen": "garbage"}}
    assert not _ids_rule.rule_fired("modbus_flood")[0]


def test_max_age_none_accepts_any_alert(ids):
    ids["stats"] = _fired("modbus_flood", 10 ** 6)
    assert _ids_rule.rule_fired("modbus_flood", max_age=None)[0]
