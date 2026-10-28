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


# ---- Rule 10: S7comm WriteVar (s7_write) ----
#
# The frames below are TCP payloads captured with tcpdump in the attack shell
# while python-snap7 3.3.0 ran training/s7_sidedoor/s7_sidedoor.py against
# OpenPLC's Snap7 server (172.18.0.3:102) on the virtual stack.

OPENPLC = "172.18.0.3"
# db_write(1002, 208, b"\x00\x01"): WriteVar, one item, DB1002 byte 208,
# transport size 0x04 (bits), 16 bits of data.
S7_WRITE_STOP = bytes.fromhex(
    "0300002502f080320100000003000e00060501120a1002000203ea84000680000400100001")
# db_read(1002, 208, 2): ReadVar (function 0x04) of the same word.
S7_READ_STOP = bytes.fromhex(
    "0300001f02f080320100000006000e00000401120a1002000203ea84000680")
# The connection set-up a client sends first: COTP connect, Setup Communication.
S7_COTP_CONNECT = bytes.fromhex("0300001611e00000000100c1020100c2020101c0010a")
S7_SETUP = bytes.fromhex("0300001902f08032010000000100080000f0000001000101e0")
# write_area(PA, 0, 0, b"\x04"): the process image of outputs, %QX0.0-0.7.
S7_WRITE_OUTPUTS = bytes.fromhex(
    "0300002402f080320100000007000e00050501120a100200010000820000000004000804")


def _s7_packet(payload, src=ATTACK_MACHINE, dport=102):
    return (src, OPENPLC, 51000, dport, "PA", 6, payload, None)


def _s7_writes(alerts):
    return [a for a in alerts if a["rule"] == "s7_write"]


def test_parse_s7_write_decodes_a_captured_db_write():
    assert rules.parse_s7_write(S7_WRITE_STOP) == [{
        "area": "DB", "db": 1002, "start": 208, "bit": 0, "length": 2, "data": "0001"}]


@pytest.mark.parametrize("payload", [S7_READ_STOP, S7_COTP_CONNECT, S7_SETUP],
                         ids=["readvar", "cotp-connect", "setup"])
def test_parse_s7_write_ignores_everything_but_writes(payload):
    assert rules.parse_s7_write(payload) == []


def test_s7_write_alerts_with_the_address_and_value():
    alerts = rules.RuleEngine().check_packet(_s7_packet(S7_WRITE_STOP))
    writes = _s7_writes(alerts)
    assert len(writes) == 1
    alert = writes[0]
    assert alert["severity"] == "high"
    assert alert["mitre"] == "T1692.001"
    assert (alert["src"], alert["dst"], alert["dport"]) == (ATTACK_MACHINE, OPENPLC, 102)
    assert "DB1002.DBB208" in alert["message"] and "0001" in alert["message"]
    # Every S7comm payload is still also an s7_enumeration alert.
    assert any(a["rule"] == "s7_enumeration" for a in alerts)


def test_s7_read_raises_no_write_alert():
    alerts = rules.RuleEngine().check_packet(_s7_packet(S7_READ_STOP))
    assert not _s7_writes(alerts)
    assert any(a["rule"] == "s7_enumeration" for a in alerts)


def test_s7_write_to_the_outputs_is_named_as_such():
    writes = _s7_writes(rules.RuleEngine().check_packet(_s7_packet(S7_WRITE_OUTPUTS)))
    assert writes and writes[0]["s7_items"][0]["area"] == "PA"
    assert "process outputs" in writes[0]["message"]


def test_s7_write_on_the_gateway_port_alerts_too():
    assert _s7_writes(rules.RuleEngine().check_packet(_s7_packet(S7_WRITE_STOP, dport=1102)))


@pytest.mark.parametrize("cut", range(1, len(S7_WRITE_STOP)))
def test_truncated_s7_write_never_raises(cut):
    """The sniffer's snap length or a split segment can cut any frame short."""
    payload = S7_WRITE_STOP[:cut]
    items = rules.parse_s7_write(payload)
    assert isinstance(items, list)
    rules.RuleEngine().check_packet(_s7_packet(payload))


@pytest.mark.parametrize("payload", [
    b"\x03\x00\x00\x00" + b"\x00" * 20,              # TPKT length 0
    b"\x03\x00\xff\xff\x02\xf0\x80\x32\x01",          # length beyond the payload
    b"\x03\x00\x00\x25\x02\xf0\x80\x32\x01" + b"\xff" * 28,  # garbage lengths
    b"\x03\x00\x00\x25\x7f\xf0" + b"\x00" * 31,       # COTP length past the frame
    S7_WRITE_STOP[:24] + b"\x05\xff" + S7_WRITE_STOP[26:],   # 255 items announced
    bytes(range(256)),
], ids=["zero-length", "long-length", "garbage", "cotp", "item-count", "noise"])
def test_malformed_s7_payload_never_raises(payload):
    assert isinstance(rules.parse_s7_write(payload), list)
    rules.RuleEngine().check_packet(_s7_packet(payload))


def test_two_frames_in_one_segment_are_both_parsed():
    items = rules.parse_s7_write(S7_READ_STOP + S7_WRITE_STOP)
    assert [i["start"] for i in items] == [208]


def test_s7_write_cooldown_suppresses_only_an_exact_repeat():
    """Repeating one write is one alert; every change of value is another.

    The S7 Side Door verify check lets the newest alert covering the stop flag
    decide, so set, restore and set again must be three alerts even inside
    the cooldown, or the second set would hide behind the restore.
    """
    engine = rules.RuleEngine()
    restore = S7_WRITE_STOP[:-1] + b"\x00"
    first = _s7_writes(engine.check_packet(_s7_packet(S7_WRITE_STOP)))
    repeat = _s7_writes(engine.check_packet(_s7_packet(S7_WRITE_STOP)))
    back = _s7_writes(engine.check_packet(_s7_packet(restore)))
    again = _s7_writes(engine.check_packet(_s7_packet(S7_WRITE_STOP)))
    other_host = _s7_writes(engine.check_packet(_s7_packet(S7_WRITE_STOP, src=OUTSIDE)))
    assert len(first) == 1 and not repeat
    assert len(back) == 1 and back[0]["s7_items"][0]["data"] == "0000"
    assert len(again) == 1 and again[0]["s7_items"][0]["data"] == "0001"
    assert len(other_host) == 1


def test_every_rule_is_listed_by_the_server_and_the_dashboard():
    """ALL_RULE_IDS (stats API) and the dashboard's rule table name every rule."""
    with open(os.path.join(IDS_DIR, "rules.py"), encoding="utf-8") as fh:
        emitted = set(re.findall(r'"rule": "(\w+)"', fh.read()))
    with open(os.path.join(IDS_DIR, "ids_server.py"), encoding="utf-8") as fh:
        block = re.search(r"ALL_RULE_IDS = \[(.*?)\]", fh.read(), re.S).group(1)
    listed = set(re.findall(r'"(\w+)"', block))
    with open(os.path.join(IDS_DIR, "templates", "index.html"), encoding="utf-8") as fh:
        page = set(re.findall(r"\{ id: '(\w+)', name: '[^']*', severity:", fh.read()))
    assert emitted == listed, f"ALL_RULE_IDS differs from rules.py: {emitted ^ listed}"
    assert emitted <= page, f"rules missing on the dashboard: {emitted - page}"
