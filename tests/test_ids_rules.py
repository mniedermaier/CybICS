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


# ---- Rule 11: DNP3 control requests (dnp3_operate) ----
#
# OpenPLC runs a DNP3 outstation on TCP 20000 (link address 10, master 1)
# mapped onto the same memory as Modbus: an Analog Output Int16 (g41v2) at
# index 1128 is %MW104, the plant's stop flag.  DNP3_STOP is the TCP payload
# captured with tcpdump in the attack shell while
# training/dnp3_sidedoor/dnp3_stop.py stopped the plant on the virtual stack;
# the outstation answered it with control status 0 (success).  The builder
# below is an independent implementation used for the variations.
import struct  # noqa: E402

DNP3_STOP = bytes.fromhex(
    "056412c40a000100" "5686" "c0c105290228010068040100" "00" "0e1e")


def _dnp3_crc(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA6BC if crc & 1 else crc >> 1
    return struct.pack("<H", ~crc & 0xFFFF)


def _dnp3_frame(user, control=0xC4, dest=10, source=1):
    header = bytes([0x05, 0x64, 5 + len(user), control]) + struct.pack("<HH", dest, source)
    frame = header + _dnp3_crc(header)
    for i in range(0, len(user), 16):
        block = user[i:i + 16]
        frame += block + _dnp3_crc(block)
    return frame


def _ao_points(*points, variation=2, qualifier=0x28):
    """Object header g41v<variation> plus (index, value) points, prefix/count per qualifier."""
    width = 2 if qualifier == 0x28 else 1
    fmt = {1: "<i", 2: "<h", 3: "<f", 4: "<d"}[variation]
    body = bytes([41, variation, qualifier]) + len(points).to_bytes(width, "little")
    for index, value in points:
        body += index.to_bytes(width, "little") + struct.pack(fmt, value) + b"\x00"
    return body


def _dnp3_request(objects, func=0x05):
    # transport FIR|FIN seq 0, application FIR|FIN seq 1, function code
    return _dnp3_frame(bytes([0xC0, 0xC1, func]) + objects)


def _dnp3_packet(payload, src=ATTACK_MACHINE):
    return (src, OPENPLC, 51000, 20000, "PA", 6, payload, None)


def _dnp3_alerts(alerts):
    return [a for a in alerts if a["rule"] == "dnp3_operate"]


def test_dnp3_crc_matches_the_reference_vector():
    """CRC-16/DNP check value: crc("123456789") = 0xEA82."""
    assert rules.dnp3_crc(b"123456789") == 0xEA82


def test_builder_reproduces_the_captured_stop_frame():
    """The test builder and the solution script agree byte for byte."""
    assert _dnp3_request(_ao_points((1128, 1))) == DNP3_STOP


def test_dnp3_captured_direct_operate_decodes_index_and_value():
    assert rules.parse_dnp3_requests(DNP3_STOP) == [{
        "function": 0x05, "function_name": "DIRECT_OPERATE",
        "link_dst": 10, "link_src": 1, "seq": 1,
        "objects_crc": rules.dnp3_crc(DNP3_STOP[13:23]),
        "objects": [{"group": 41, "variation": 2, "index": 1128, "value": 1}],
    }]


def test_dnp3_sequence_number_and_object_crc_pair_select_with_operate():
    """The verify check pairs SELECT and OPERATE as the outstation does.

    opendnp3 runs an OPERATE only after a SELECT with the previous application
    sequence number and the same object bytes, so the parser reports both.
    """
    objects = _ao_points((1128, 1))
    select = _dnp3_frame(bytes([0xC0, 0xC4, 0x03]) + objects)
    operate = _dnp3_frame(bytes([0xC0, 0xC5, 0x04]) + objects)
    other = _dnp3_frame(bytes([0xC0, 0xC5, 0x04]) + _ao_points((1128, 2)))
    (s,), (o,), (x,) = map(rules.parse_dnp3_requests, (select, operate, other))
    assert (s["seq"], o["seq"]) == (4, 5)
    assert s["objects_crc"] == o["objects_crc"] == rules.dnp3_crc(objects)
    assert x["objects_crc"] != o["objects_crc"]


def test_a_select_resent_with_a_new_sequence_number_is_logged_again():
    engine = rules.RuleEngine()
    objects = _ao_points((1128, 1))
    first = engine.check_packet(_dnp3_packet(_dnp3_frame(bytes([0xC0, 0xC4, 0x03]) + objects)))
    retry = engine.check_packet(_dnp3_packet(_dnp3_frame(bytes([0xC0, 0xC4, 0x03]) + objects)))
    fresh = engine.check_packet(_dnp3_packet(_dnp3_frame(bytes([0xC0, 0xC6, 0x03]) + objects)))
    assert len(_dnp3_alerts(first)) == 1 and not _dnp3_alerts(retry)
    assert _dnp3_alerts(fresh)[0]["dnp3"][0]["seq"] == 6


def test_dnp3_operate_alerts_with_the_point_and_value():
    alerts = _dnp3_alerts(rules.RuleEngine().check_packet(_dnp3_packet(DNP3_STOP)))
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["severity"] == "high"
    assert alert["mitre"] == rules.MITRE_COMMAND_MESSAGE == "T1692.001"
    assert (alert["src"], alert["dst"], alert["dport"]) == (ATTACK_MACHINE, OPENPLC, 20000)
    assert alert["dnp3"][0]["objects"][0] == {
        "group": 41, "variation": 2, "index": 1128, "value": 1}
    assert "index 1128 = 1" in alert["message"] and "link 1 -> 10" in alert["message"]


def test_dnp3_object_header_past_the_first_crc_block():
    """Two points push the data across a 16-byte block boundary."""
    reqs = rules.parse_dnp3_requests(_dnp3_request(_ao_points((1128, 1), (1130, -5))))
    assert [(o["index"], o["value"]) for o in reqs[0]["objects"]] == [(1128, 1), (1130, -5)]


@pytest.mark.parametrize("variation,value", [(1, 70000), (3, 1.5), (4, -2.25)])
def test_dnp3_other_analog_output_variations(variation, value):
    reqs = rules.parse_dnp3_requests(_dnp3_request(_ao_points((2050, value), variation=variation)))
    assert reqs[0]["objects"] == [
        {"group": 41, "variation": variation, "index": 2050, "value": value}]


def test_dnp3_one_octet_qualifier_and_crob():
    crob = bytes([12, 1, 0x17, 1, 3, 0x03, 1]) + (100).to_bytes(4, "little") * 2 + b"\x00"
    reqs = rules.parse_dnp3_requests(_dnp3_request(_ao_points((7, 9), qualifier=0x17) + crob))
    assert reqs[0]["objects"] == [
        {"group": 41, "variation": 2, "index": 7, "value": 9},
        {"group": 12, "variation": 1, "index": 3, "code": 0x03}]


def test_dnp3_one_octet_count_with_qualifier_0x28_is_not_a_write():
    """The mistake an earlier README taught: 0x28 with a 1-octet count.

    OpenPLC answers it with 'Not enough data for specified objects' and
    writes nothing, so the IDS must not decode a point out of it either.
    """
    wrong = bytes([41, 2, 0x28, 1]) + struct.pack("<Hh", 1128, 1) + b"\x00"
    reqs = rules.parse_dnp3_requests(_dnp3_request(wrong))
    assert reqs and reqs[0]["objects"] == []


@pytest.mark.parametrize("func", [0x02, 0x03, 0x04, 0x05, 0x06])
def test_dnp3_every_control_function_alerts(func):
    alerts = rules.RuleEngine().check_packet(
        _dnp3_packet(_dnp3_request(_ao_points((1128, 1)), func=func)))
    assert _dnp3_alerts(alerts)[0]["dnp3"][0]["function"] == func


def test_dnp3_read_link_status_and_responses_are_silent():
    integrity_poll = _dnp3_request(bytes([60, 1, 0x06]), func=0x01)
    link_status = _dnp3_frame(b"", control=0xC9)
    # An outstation response (PRM clear) echoing the operate.
    response = _dnp3_frame(bytes([0xC0, 0xC1, 0x81, 0, 0]) + _ao_points((1128, 1)),
                           control=0x44, dest=1, source=10)
    for payload in (integrity_poll, link_status, response):
        assert not _dnp3_alerts(rules.RuleEngine().check_packet(_dnp3_packet(payload)))


def test_dnp3_bad_crc_is_not_a_command():
    """The outstation drops a frame with a wrong CRC, so the IDS ignores it too."""
    for pos in (8, 20, len(DNP3_STOP) - 1):
        broken = bytearray(DNP3_STOP)
        broken[pos] ^= 0x01
        assert rules.parse_dnp3_requests(bytes(broken)) == []


@pytest.mark.parametrize("cut", range(1, len(DNP3_STOP)))
def test_truncated_dnp3_never_raises(cut):
    payload = DNP3_STOP[:cut]
    assert rules.parse_dnp3_requests(payload) == []
    rules.RuleEngine().check_packet(_dnp3_packet(payload))


@pytest.mark.parametrize("payload", [
    b"\x05\x64\x00\xc4" + b"\x00" * 20,                  # length below 5
    b"\x05\x64\xff\xc4\x0a\x00\x01\x00" + b"\xff" * 40,  # length beyond payload
    _dnp3_request(bytes([41, 2, 0x28, 0xff, 0xff])),   # 65535 points announced
    _dnp3_request(bytes([99, 9, 0x28, 1, 0])),         # unknown object
    bytes(range(256)),
], ids=["short-length", "long-length", "count", "unknown-object", "noise"])
def test_malformed_dnp3_never_raises(payload):
    assert isinstance(rules.parse_dnp3_requests(payload), list)
    rules.RuleEngine().check_packet(_dnp3_packet(payload))


def test_two_dnp3_frames_in_one_segment_are_both_parsed():
    restore = _dnp3_request(_ao_points((1128, 0)))
    reqs = rules.parse_dnp3_requests(DNP3_STOP + restore)
    assert [r["objects"][0]["value"] for r in reqs] == [1, 0]


def test_dnp3_cooldown_suppresses_only_an_exact_repeat():
    """Set, restore and set again are three alerts; a repeat is folded.

    The DNP3 Side Door verify check lets the newest alert for the stop flag
    decide, exactly as the S7 one does.
    """
    engine = rules.RuleEngine()
    restore = _dnp3_request(_ao_points((1128, 0)))
    first = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    repeat = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    back = _dnp3_alerts(engine.check_packet(_dnp3_packet(restore)))
    again = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    other_host = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP, src=OUTSIDE)))
    assert len(first) == 1 and not repeat
    assert len(back) == 1 and back[0]["dnp3"][0]["objects"][0]["value"] == 0
    assert len(again) == 1 and again[0]["dnp3"][0]["objects"][0]["value"] == 1
    assert len(other_host) == 1


def test_port_20000_is_captured():
    with open(os.path.join(IDS_DIR, "detector.py"), encoding="utf-8") as fh:
        ports = re.search(r"_IDS_PORTS = \(([^)]*)\)", fh.read()).group(1)
    assert "20000" in ports, "DNP3 traffic would be dropped before any rule runs"


# ---- Rule 12: S7comm CPU operating mode (s7_cpu_control) ----
#
# TCP payloads captured with tcpdump on the plant bridge while python-snap7
# 3.3.0 in the attack shell called plc_stop(), plc_hot_start() and
# plc_cold_start() against OpenPLC's Snap7 server (172.18.0.3:102).

# PLC Stop (function 0x29), PI service "P_PROGRAM".
S7_PLC_STOP = bytes.fromhex(
    "0300002102f0803201000000030010000029000000000009505f50524f4752414d")
# PLC Control (0x28), no argument, "P_PROGRAM": warm (hot) restart.
S7_PLC_HOT_START = bytes.fromhex(
    "0300002502f0803201000000060014000028000000000000fd000009505f50524f4752414d")
# PLC Control (0x28), argument "C ", "P_PROGRAM": cold restart.
S7_PLC_COLD_START = bytes.fromhex(
    "0300002702f0803201000000080016000028000000000000fd0002432009505f50524f4752414d")
# Read SZL 0x0424 (CPU operating mode): a userdata request, not a job.
S7_READ_SZL_0424 = bytes.fromhex(
    "0300002102f080320700000002000800080001120411440100ff09000404240000")


def _controls(alerts):
    return [a for a in alerts if a["rule"] == "s7_cpu_control"]


@pytest.mark.parametrize("payload, action, argument", [
    (S7_PLC_STOP, "stop", ""),
    (S7_PLC_HOT_START, "warm_start", ""),
    (S7_PLC_COLD_START, "cold_start", "C "),
])
def test_parse_s7_control_decodes_captured_requests(payload, action, argument):
    assert rules.parse_s7_control(payload) == [
        {"action": action, "pi_service": "P_PROGRAM", "argument": argument}]


@pytest.mark.parametrize("payload", [S7_READ_SZL_0424, S7_READ_STOP, S7_WRITE_STOP,
                                     S7_COTP_CONNECT, S7_SETUP],
                         ids=["szl-read", "read", "write", "cotp", "setup"])
def test_parse_s7_control_ignores_everything_else(payload):
    assert rules.parse_s7_control(payload) == []
    assert not _controls(rules.RuleEngine().check_packet(_s7_packet(payload)))


def test_plc_stop_is_a_critical_alert_with_the_mode_change():
    alerts = rules.RuleEngine().check_packet(_s7_packet(S7_PLC_STOP))
    controls = _controls(alerts)
    assert len(controls) == 1
    alert = controls[0]
    assert alert["severity"] == rules.SEVERITY_CRITICAL
    assert alert["mitre"] == "T0858"
    assert (alert["src"], alert["dst"], alert["dport"]) == (ATTACK_MACHINE, OPENPLC, 102)
    assert alert["s7_control"] == "stop" and "STOP" in alert["message"]
    assert any(a["rule"] == "s7_enumeration" for a in alerts)
    assert not _s7_writes(alerts)


def test_restarts_are_high_alerts():
    for payload, action in ((S7_PLC_HOT_START, "warm_start"), (S7_PLC_COLD_START, "cold_start")):
        alert = _controls(rules.RuleEngine().check_packet(_s7_packet(payload)))[0]
        assert alert["severity"] == rules.SEVERITY_HIGH and alert["s7_control"] == action


def test_unknown_pi_service_is_reported_by_name():
    # PLC Control with another PI service (_GARB, compress memory).
    garb = bytes.fromhex("0300002102f08032010000000a0010000028000000000000fd000005") + b"_GARB"
    garb = garb[:2] + len(garb).to_bytes(2, "big") + garb[4:]
    garb = garb[:13] + (len(garb) - 17).to_bytes(2, "big") + garb[15:]
    alert = _controls(rules.RuleEngine().check_packet(_s7_packet(garb)))[0]
    assert alert["s7_control"] == "pi_service" and alert["s7_pi_service"] == "_GARB"
    assert alert["severity"] == rules.SEVERITY_HIGH


def test_s7_control_cooldown_suppresses_only_an_exact_repeat():
    """stop, stop, start, stop, other host: four alerts, newest names the last mode.

    The Stop Means Stop? verify check lets the newest s7_cpu_control alert to
    the PLC decide, so a restart must never be folded into an earlier STOP.
    """
    engine = rules.RuleEngine()
    seen = [_controls(engine.check_packet(_s7_packet(p, src=s)))
            for p, s in ((S7_PLC_STOP, ATTACK_MACHINE), (S7_PLC_STOP, ATTACK_MACHINE),
                         (S7_PLC_HOT_START, ATTACK_MACHINE), (S7_PLC_STOP, ATTACK_MACHINE),
                         (S7_PLC_STOP, OUTSIDE))]
    assert [len(s) for s in seen] == [1, 0, 1, 1, 1]
    assert [s[0]["s7_control"] for s in seen if s] == ["stop", "warm_start", "stop", "stop"]


def test_s7_control_on_the_gateway_port_alerts_too():
    assert _controls(rules.RuleEngine().check_packet(_s7_packet(S7_PLC_STOP, dport=1102)))


@pytest.mark.parametrize("cut", range(1, len(S7_PLC_COLD_START)))
def test_truncated_s7_control_never_raises(cut):
    payload = S7_PLC_COLD_START[:cut]
    assert isinstance(rules.parse_s7_control(payload), list)
    rules.RuleEngine().check_packet(_s7_packet(payload))


@pytest.mark.parametrize("payload", [
    S7_PLC_STOP[:2] + b"\x00\x05" + S7_PLC_STOP[4:],             # TPKT length too short
    S7_PLC_STOP[:13] + b"\xff\xff" + S7_PLC_STOP[15:],           # parameter length too long
    S7_PLC_COLD_START[:25] + b"\xff\xff" + S7_PLC_COLD_START[27:],  # argument length too long
    S7_PLC_STOP[:-10] + b"\xff",                                  # PI name length too long
    S7_PLC_STOP + S7_PLC_HOT_START + b"\x03\x00",                # trailing garbage
])
def test_malformed_s7_control_never_raises(payload):
    assert isinstance(rules.parse_s7_control(payload), list)
    rules.RuleEngine().check_packet(_s7_packet(payload))


def test_two_controls_in_one_segment_are_both_seen():
    actions = [c["action"] for c in rules.parse_s7_control(S7_PLC_STOP + S7_PLC_HOT_START)]
    assert actions == ["stop", "warm_start"]


# ---- Modbus write journal parser (no rule) ----

def test_parse_modbus_writes_decodes_fuxas_captured_stop():
    # FUXA 1.2.6 setting its "stop" tag, captured on the plant bridge.
    assert rules.parse_modbus_writes(bytes.fromhex("003300000006010604680001")) == [
        {"unit": 1, "function": 6, "address": 1128, "count": 1, "values": [1]}]


def test_parse_modbus_writes_multiple_registers_and_coils():
    fc16 = bytes.fromhex("00010000000b01100467000204" "00000005")
    fc5 = bytes.fromhex("0002000000060105000" "1ff00")
    fc15 = bytes.fromhex("000300000009010f0000000a020503")
    out = rules.parse_modbus_writes(fc16 + fc5)
    assert out[0]["function"] == 16 and out[0]["address"] == 1127 and out[0]["values"] == [0, 5]
    assert out[1] == {"unit": 1, "function": 5, "address": 1, "count": 1, "values": [1]}
    coils = rules.parse_modbus_writes(fc15)[0]
    assert coils["count"] == 10 and coils["values"] == [1, 0, 1, 0, 0, 0, 0, 0, 1, 1]


def test_parse_modbus_writes_ignores_reads_and_responses():
    assert rules.parse_modbus_writes(bytes.fromhex("000100000006010304680001")) == []
    assert rules.parse_modbus_writes(bytes.fromhex("000100000006018604680001")) == []


@pytest.mark.parametrize("cut", range(0, 12))
def test_truncated_modbus_write_never_raises(cut):
    assert rules.parse_modbus_writes(bytes.fromhex("003300000006010604680001")[:cut]) == []


@pytest.mark.parametrize("payload", [b"\xff" * 40, b"\x00" * 40, bytes(range(64)), b"GET / HTTP/1.1"])
def test_malformed_modbus_payload_never_raises(payload):
    rules.parse_modbus_writes(payload)
