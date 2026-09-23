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
