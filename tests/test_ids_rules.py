"""Unit tests for the IDS rule engine (software/ids/rules.py).

These exercise the rule logic directly against parsed packet tuples, so they
need no running stack and no captured traffic.

The OPC-UA cases exist because the rule used to exempt every host in
KNOWN_SERVICES, which includes the bundled attack machine -- so the one host
an exercise expects to be detected was the one host that never alerted.
"""
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS_DIR = os.path.join(ROOT, "software", "ids")

if not os.path.exists(os.path.join(IDS_DIR, "rules.py")):
    pytest.skip("software/ids/rules.py not present", allow_module_level=True)

sys.path.insert(0, IDS_DIR)
import rules  # noqa: E402


ATTACK_MACHINE = "172.18.0.100"
OPCUA_SERVER = "172.18.0.5"
HWIO = "172.18.0.2"
OUTSIDE = "172.18.0.1"


def _opcua_packet(src_ip):
    """A TCP packet to the OPC-UA port with a payload long enough to be checked.

    Tuple layout matches _parse_raw_packet: src, dst, sport, dport, flags,
    proto, payload, arp_op.
    """
    return (src_ip, OPCUA_SERVER, 51000, 4840, "PA", 6, b"HELF\x00\x00\x00\x00", None)


def _rules_for(src_ip):
    engine = rules.RuleEngine()
    return engine.check_packet(_opcua_packet(src_ip))


def _opcua_alerts(alerts):
    return [a for a in alerts if a["rule"] == "opcua_access"]


def test_opcua_access_from_attack_machine_alerts():
    """The regression this fix is about: the attack box must be detected."""
    assert _opcua_alerts(_rules_for(ATTACK_MACHINE)), (
        "OPC-UA access from the bundled attack machine raised no alert"
    )


def test_opcua_access_from_unknown_host_alerts():
    assert _opcua_alerts(_rules_for(OUTSIDE))


def test_opcua_access_from_ot_client_is_silent():
    """hwio legitimately speaks OPC-UA and must not be flagged."""
    assert not _opcua_alerts(_rules_for(HWIO))


def test_attack_machine_is_still_a_known_service():
    """The fix must not work by removing the attack machine from the map --
    other rules rely on resolving its name."""
    assert rules.KNOWN_SERVICES.get(ATTACK_MACHINE) == "attack-machine"


def test_opcua_clients_are_a_subset_of_known_services():
    assert set(rules._OPCUA_CLIENTS) <= set(rules.KNOWN_SERVICES.values())


def test_short_payload_is_ignored():
    pkt = (ATTACK_MACHINE, OPCUA_SERVER, 51000, 4840, "PA", 6, b"HEL", None)
    assert not _opcua_alerts(rules.RuleEngine().check_packet(pkt))


def _compose_static_ips():
    """Service name -> static IP, read from the virtual stack's compose file."""
    compose = os.path.join(ROOT, ".devcontainer", "virtual", "docker-compose.yml")
    if not os.path.exists(compose):
        pytest.skip("virtual docker-compose.yml not present")
    found, service = {}, None
    with open(compose, encoding="utf-8") as fh:
        for line in fh:
            name = re.match(r"^  ([a-z0-9_-]+):\s*$", line)
            if name:
                service = name.group(1)
            addr = re.search(r"ipv4_address:\s*(\d+\.\d+\.\d+\.\d+)", line)
            if addr and service:
                found[service] = addr.group(1)
    assert found, "no static addresses found in the compose file"
    return found


def test_every_container_is_a_known_service():
    """Each container with a fixed address must be named in KNOWN_SERVICES.

    A container the IDS cannot name shows up in the dashboard as an unknown
    host, and the rules that exempt known services never apply to it. This
    caught nginx-proxy on 172.18.0.12, which had been added to the compose
    file and to pushDockerRepos.yml but not here.

    The converse is deliberately not asserted: 172.18.0.7 is the STM32, which
    is a container only in the Raspberry Pi deployment, not in this stack.
    """
    missing = {
        name: ip
        for name, ip in _compose_static_ips().items()
        if ip not in rules.KNOWN_SERVICES
    }
    assert not missing, (
        "containers with a fixed address but no KNOWN_SERVICES entry in "
        "software/ids/rules.py: " + ", ".join(f"{n} ({i})" for n, i in sorted(missing.items()))
    )


def test_dashboard_service_table_matches_the_rules_table():
    """The IDS page carries its own copy of KNOWN_SERVICES in JavaScript.

    Two hand-maintained copies of the same table drift, and they had: the
    dashboard knew a 'gateway' the rule engine did not, and neither knew the
    reverse proxy. Until the page is served the table from the backend, this
    test is what keeps them together.
    """
    page = os.path.join(ROOT, "software", "ids", "templates", "index.html")
    if not os.path.exists(page):
        pytest.skip("IDS dashboard template not present")
    with open(page, encoding="utf-8") as fh:
        text = fh.read()
    block = re.search(r"const KNOWN_SERVICES = \{(.*?)\}", text, re.S)
    assert block, "KNOWN_SERVICES not found in the dashboard template"
    page_table = dict(re.findall(r"'([\d.]+)':\s*'([^']+)'", block.group(1)))

    # The gateway is an address on the bridge, not a container of ours.
    page_table.pop("172.18.0.1", None)

    assert page_table == rules.KNOWN_SERVICES, (
        "the dashboard's table and software/ids/rules.py disagree; "
        f"only in the page: {sorted(set(page_table) - set(rules.KNOWN_SERVICES))}, "
        f"only in rules.py: {sorted(set(rules.KNOWN_SERVICES) - set(page_table))}"
    )


# ---- Bounded state under spoofed floods ----
#
# Every tracker is keyed by a source address, which an attacker can make up.
# Before MAX_TRACKED_KEYS, one spoofed SYN per address added an entry for
# good and 100,000 of them held about 118 MB; the IDS gets 32 MB on a board.

def _spoofed(i):
    return f"10.{(i >> 16) & 255}.{(i >> 8) & 255}.{i & 255}"


def _syn(src, dst="172.18.0.3", dport=502):
    return (src, dst, 40000, dport, "S", 6, b"", None, None, None)


def _modbus_write(src):
    return (src, "172.18.0.3", 40000, 502, "PA", 6,
            b"\x00\x01\x00\x00\x00\x06\x01\x06\x04\x64\x00\x01", None, None, None)


def _arp(ip, mac):
    return ("", "", 0, 0, "", 0, b"", 2, mac, ip)


def _all_trackers(engine):
    return {
        "port_scan": engine.port_scan_tracker, "syn": engine.syn_tracker,
        "modbus_flood": engine.modbus_flood_tracker, "modbus_write": engine.modbus_write_tracker,
        "http_login": engine.http_login_tracker, "arp": engine.arp_tracker,
        "recent_alerts": engine.recent_alerts,
    }


@pytest.mark.parametrize("make", [
    lambda i: _syn(_spoofed(i)),
    lambda i: _syn(_spoofed(i), dst=_spoofed(i * 7 + 1)),
    lambda i: _modbus_write(_spoofed(i)),
    lambda i: _opcua_packet(_spoofed(i)),
    lambda i: _arp(_spoofed(i), f"02:00:00:00:{(i >> 8) & 255:02x}:{i & 255:02x}"),
], ids=["syn", "syn-src-dst", "modbus-write", "opcua", "arp"])
def test_spoofed_sources_keep_every_tracker_bounded(make):
    engine = rules.RuleEngine()
    for i in range(3 * rules.MAX_TRACKED_KEYS):
        engine.check_packet(make(i))
    for name, tracker in _all_trackers(engine).items():
        assert len(tracker) <= rules.MAX_TRACKED_KEYS, (name, len(tracker))


def test_one_ip_with_endless_macs_stays_bounded_and_still_alerts():
    engine = rules.RuleEngine()
    alerts = []
    for i in range(1000):
        alerts += engine.check_packet(_arp("172.18.0.3", f"02:00:00:00:{i >> 8:02x}:{i & 255:02x}"))
    assert len(engine.arp_tracker["172.18.0.3"]) <= rules.MAX_VALUES_PER_KEY
    assert any(a["rule"] == "arp_spoof" for a in alerts)


def test_a_full_port_sweep_stays_bounded_and_still_alerts():
    engine = rules.RuleEngine()
    alerts = []
    for port in range(1, 2000):
        alerts += engine.check_packet(_syn(ATTACK_MACHINE, dport=port))
    assert len(engine.port_scan_tracker[(ATTACK_MACHINE, "172.18.0.3")]) <= rules.MAX_VALUES_PER_KEY
    assert any(a["rule"] == "port_scan" for a in alerts)


def test_an_active_source_survives_a_spoofed_flood_between_its_packets():
    """Eviction takes the source that has been quiet longest, so an attacker
    who keeps sending stays tracked while fewer than MAX_TRACKED_KEYS made-up
    sources arrive in between, and its SYN flood is still reported."""
    engine = rules.RuleEngine()
    alerts = []
    for i in range(engine.SYN_FLOOD_THRESHOLD):
        alerts += engine.check_packet(_syn(ATTACK_MACHINE, dport=502))
        for j in range(rules.MAX_TRACKED_KEYS // 2):
            engine.check_packet(_syn(_spoofed(i * 1000 + j)))
    assert any(a["rule"] == "syn_flood" and a["src"] == ATTACK_MACHINE for a in alerts)


def test_cleanup_drops_sources_that_went_quiet(monkeypatch):
    engine = rules.RuleEngine()
    now = [1000.0]
    monkeypatch.setattr(rules.time, "time", lambda: now[0])
    engine.check_packet(_syn(ATTACK_MACHINE))
    engine.check_packet(_modbus_write(ATTACK_MACHINE))
    engine.check_packet(_arp("172.18.0.3", "02:00:00:00:00:01"))
    assert engine.syn_tracker and engine.modbus_write_tracker
    now[0] += engine.MODBUS_WRITE_WINDOW + 1
    engine.cleanup()
    assert not engine.syn_tracker and not engine.modbus_flood_tracker and not engine.modbus_write_tracker
    # The ARP table remembers MACs on purpose; cleanup leaves it.
    assert "172.18.0.3" in engine.arp_tracker
