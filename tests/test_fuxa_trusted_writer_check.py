"""The Trusted Writer challenge's verify logic, without a stack.

software/landing/modules/defense_checks/check_fuxa_trusted_writer.py grants
the flag when the newest write of the PLC's stop flag the IDS journaled came
from FUXA, the IDS stayed silent around it and the plant is stopped. These
tests feed it made-up journal entries and alerts, and tie its constants to the
files they mirror: the stop tag in software/FUXA/fuxa-project.json, FUXA's
address in the compose file and in the IDS's KNOWN_SERVICES.

tests/test_training.py::TestFuxaTrustedWriter runs the challenge on a live stack.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))
sys.path.insert(0, os.path.join(ROOT, "software", "ids"))

from modules.defense_checks import check_fuxa_trusted_writer as check  # noqa: E402
import rules  # noqa: E402

NOW = datetime(2026, 10, 28, 12, 0, 0)
STATUS = {"active": True, "now": NOW.isoformat(),
          "stats": {"started_at": (NOW - timedelta(hours=1)).isoformat()}}


def write(src, value, ago=10, wid=1, function=6, address=1128, dst="172.18.0.3"):
    values = value if isinstance(value, list) else [value]
    return {"id": wid, "timestamp": (NOW - timedelta(seconds=ago)).isoformat(), "src": src,
            "dst": dst, "function": function, "address": address, "count": len(values),
            "values": values}


def alert(rule, ago, src="172.18.0.100"):
    return {"rule": rule, "src": src, "timestamp": (NOW - timedelta(seconds=ago)).isoformat()}


# --- constants against the files they mirror ------------------------------------

def test_stop_register_is_the_fuxa_stop_tag_on_the_wire():
    with open(os.path.join(ROOT, "software", "FUXA", "fuxa-project.json"), encoding="utf-8") as f:
        project = json.load(f)
    stops = [t for d in project["devices"].values() for t in (d.get("tags") or {}).values()
             if t.get("name") == "stop"]
    assert len(stops) == 1 and stops[0]["memaddress"] == "400000"
    assert int(stops[0]["address"]) - 1 == check.STOP_REGISTER   # FUXA counts from 1


def test_fuxa_address_matches_compose_and_ids():
    assert rules.KNOWN_SERVICES[check.FUXA_IP] == "fuxa"
    assert "fuxa" in rules._MODBUS_AUTH_WRITERS, "the challenge assumes FUXA is a trusted writer"
    with open(os.path.join(ROOT, ".devcontainer", "virtual", "docker-compose.yml"),
              encoding="utf-8") as f:
        compose = f.read()
    service = re.search(r"\n  fuxa:\n(.*?)\n  \w", compose, re.S).group(1)
    assert re.search(r"ipv4_address:\s*" + re.escape(check.FUXA_IP) + r"\s", service)


def test_ctf_entry_points_to_this_module():
    with open(os.path.join(ROOT, "software", "landing", "ctf_config.json"), encoding="utf-8") as f:
        config = json.load(f)
    entry = [c for cat in config["categories"].values() for c in cat["challenges"]
             if c["id"] == "fuxa_trusted_writer"]
    assert len(entry) == 1
    assert entry[0]["verify_module"] == "check_fuxa_trusted_writer"
    assert entry[0]["type"] == "verify" and "answers" not in entry[0]
    assert re.fullmatch(r"CybICS\([a-z0-9_]+\)", entry[0]["flag"])


# --- which write counts ------------------------------------------------------------

def test_fuxa_stop_passes():
    row, when = check._write_check(STATUS, [write("172.18.0.4", 1)])
    assert row["passed"] and when == NOW - timedelta(seconds=10)


def test_a_direct_write_after_fuxa_wins():
    writes = [write("172.18.0.4", 1, ago=30, wid=1), write("172.18.0.100", 1, ago=5, wid=2)]
    row, when = check._write_check(STATUS, writes)
    assert not row["passed"] and when is None and "172.18.0.100" in row["detail"]


def test_a_direct_stop_alone_fails():
    row, _ = check._write_check(STATUS, [write("172.18.0.100", 1)])
    assert not row["passed"]


def test_fuxa_restoring_zero_fails():
    writes = [write("172.18.0.4", 1, ago=30, wid=1), write("172.18.0.4", 0, ago=5, wid=2)]
    assert not check._write_check(STATUS, writes)[0]["passed"]


def test_an_old_fuxa_stop_fails():
    row, _ = check._write_check(STATUS, [write("172.18.0.4", 1, ago=check.WRITE_WINDOW + 5)])
    assert not row["passed"]


def test_writes_elsewhere_do_not_count():
    writes = [write("172.18.0.4", 1, wid=1),
              write("172.18.0.100", 1, wid=2, address=1130),            # manual, not stop
              write("172.18.0.100", 1, wid=3, function=5, address=1128),  # a coil
              write("172.18.0.100", 1, wid=4, dst="172.18.0.9")]          # another device
    assert check._write_check(STATUS, writes)[0]["passed"]


def test_a_multi_register_write_covering_the_flag_counts():
    writes = [write("172.18.0.4", 1, wid=1),
              write("172.18.0.100", [7, 0, 9], wid=2, function=16, address=1127)]
    row, _ = check._write_check(STATUS, writes)
    assert not row["passed"] and "172.18.0.100" in row["detail"]
    assert check._newest_stop_write(writes)[1] == 0


def test_garbage_entries_are_ignored():
    writes = [write("172.18.0.4", 1, wid=1), None, "x", {"id": 9, "values": "1"},
              {"id": 10, "dst": "172.18.0.3", "function": 6, "address": "1128", "values": [1]}]
    assert check._write_check(STATUS, writes)[0]["passed"]


# --- the quiet window --------------------------------------------------------------

def test_no_alerts_is_quiet():
    when = NOW - timedelta(seconds=10)
    assert check._quiet_check(STATUS, [alert("arp_spoof", 5), alert("port_scan", 200)],
                              when)["passed"]


def test_an_alert_inside_the_window_fails():
    when = NOW - timedelta(seconds=10)
    for ago in (5, 10 + check.QUIET_BEFORE - 1):
        row = check._quiet_check(STATUS, [alert("http_brute_force", ago)], when)
        assert not row["passed"] and "http_brute_force" in row["detail"]


def test_an_ids_started_after_the_window_opened_fails():
    status = dict(STATUS, stats={"started_at": (NOW - timedelta(seconds=30)).isoformat()})
    assert not check._quiet_check(status, [], NOW - timedelta(seconds=10))["passed"]
