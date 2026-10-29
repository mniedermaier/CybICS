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
import time  # noqa: E402

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


# ---- The outstation's reply (no rule; filed under the request) ----
#
# The alert records what was sent.  Whether the outstation carried it out is
# only in its reply: a response (0x81) with the request's sequence number that
# echoes each point with its control status.  The DNP3 Side Door verify check
# credits a stop only on status 0, so the pairing must not attach a reply to
# the wrong request.


def _dnp3_reply(points, seq=1, iin=0, control=0x44, app=None, func=0x81, dest=1, source=10):
    """An outstation response echoing (index, value, status) analog-output points."""
    body = bytes([41, 2, 0x28]) + len(points).to_bytes(2, "little")
    for index, value, status in points:
        body += index.to_bytes(2, "little") + struct.pack("<h", value) + bytes([status])
    app = 0xC0 | seq if app is None else app
    return _dnp3_frame(bytes([0xC0, app, func]) + iin.to_bytes(2, "little") + body,
                       control=control, dest=dest, source=source)


def _confirmed(request):
    """True if the IDS filed a reply under the request (as opposed to none or unattributed)."""
    return isinstance(request["reply"], dict) and "objects" in request["reply"]


def _from_outstation(payload, dport=51000, dst=ATTACK_MACHINE):
    return (OPENPLC, dst, 20000, dport, "PA", 6, payload, None)


def _stop_with_reply(reply, engine=None, sport=51000):
    engine = engine or rules.RuleEngine()
    (alert,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    assert alert["dnp3"][0]["reply"] is None
    assert engine.check_packet(_from_outstation(reply, dport=sport)) == []
    return alert["dnp3"][0]["reply"]


def test_dnp3_reply_is_filed_under_the_request():
    reply = _stop_with_reply(_dnp3_reply([(1128, 1, 0)]))
    assert reply == {"iin": 0, "objects": [
        {"group": 41, "variation": 2, "index": 1128, "value": 1, "status": 0}]}


def test_dnp3_refusal_keeps_its_status():
    reply = _stop_with_reply(_dnp3_reply([(1128, 1, 2)]))
    assert reply["objects"][0]["status"] == 2


@pytest.mark.parametrize("payload,label", [
    (_dnp3_reply([(1128, 1, 0)], seq=2), "other-sequence"),
    (_dnp3_reply([(1128, 1, 0)], dest=2), "other-master"),
    (_dnp3_reply([(1128, 1, 0)], source=11), "other-outstation"),
    (_dnp3_reply([(1128, 1, 0)], control=0xC4), "dir-set"),
    (_dnp3_reply([(1128, 1, 0)], func=0x82), "unsolicited"),
    (_dnp3_reply([(1128, 1, 0)], app=0x81), "not-fir"),
    (_dnp3_frame(b"", control=0x0B, dest=1, source=10), "link-status"),
    (bytes(range(64)), "noise"),
], ids=lambda v: v if isinstance(v, str) else "")
def test_dnp3_only_the_matching_reply_is_filed(payload, label):
    assert _stop_with_reply(payload) is None, label


def test_dnp3_reply_on_another_connection_is_not_filed():
    assert _stop_with_reply(_dnp3_reply([(1128, 1, 0)]), sport=51001) is None


def test_dnp3_late_reply_is_not_filed(monkeypatch):
    engine = rules.RuleEngine()
    (alert,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    later = time.time() + rules.DNP3_REPLY_TIMEOUT + 1
    monkeypatch.setattr(rules.time, "time", lambda: later)
    engine.check_packet(_from_outstation(_dnp3_reply([(1128, 1, 0)])))
    assert alert["dnp3"][0]["reply"] == {"unattributed": True}


def test_dnp3_connection_state_goes_once_idle(monkeypatch):
    engine = rules.RuleEngine()
    engine.check_packet(_dnp3_packet(DNP3_STOP))
    idle = time.time() + rules.DNP3_CONNECTION_IDLE + 1
    monkeypatch.setattr(rules.time, "time", lambda: idle)
    engine.cleanup()
    assert not engine.dnp3_connections


def test_dnp3_reply_to_a_folded_repeat_goes_to_the_first_alert():
    engine = rules.RuleEngine()
    (alert,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    assert not _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    engine.check_packet(_from_outstation(_dnp3_reply([(1128, 1, 0)])))
    assert alert["dnp3"][0]["reply"]["objects"][0]["status"] == 0


def test_dnp3_request_keys_never_change_after_the_alert():
    """The API may serialise a stored alert while its reply arrives."""
    engine = rules.RuleEngine()
    (alert,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    keys = set(alert["dnp3"][0])
    engine.check_packet(_from_outstation(_dnp3_reply([(1128, 1, 0)])))
    assert set(alert["dnp3"][0]) == keys


def test_dnp3_connections_are_bounded():
    engine = rules.RuleEngine()
    for port in range(rules.DNP3_MAX_CONNECTIONS + 20):
        engine.check_packet((ATTACK_MACHINE, OPENPLC, 40000 + port, 20000, "PA", 6,
                             _dnp3_request(_ao_points((1128, port % 2))), None))
    assert len(engine.dnp3_connections) <= rules.DNP3_MAX_CONNECTIONS


def test_dnp3_reply_echoing_other_points_is_not_filed():
    """Review bypass: a stop split across two TCP segments is never logged.

    The student sends a frame the outstation drops (stop = 1) and, in the
    same burst, a valid restore of 0 with its tail held back to the next
    segment. The IDS logs only the dropped stop; the outstation writes 0 and
    answers status 00 with the same sequence number. That reply echoes 0,
    so it must not be filed under the logged stop.
    """
    engine = rules.RuleEngine()
    dropped = _dnp3_frame(bytes([0xC0, 0xD7, 0x05]) + _ao_points((1128, 1)))
    restore = _dnp3_frame(bytes([0xC0, 0xC7, 0x05]) + _ao_points((1128, 0)))
    (alert,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(dropped + restore[:-3])))
    assert engine.check_packet(_dnp3_packet(restore[-3:])) == []
    engine.check_packet(_from_outstation(_dnp3_reply([(1128, 0, 0)], seq=7)))
    assert alert["dnp3"][0]["reply"] is None


def test_dnp3_a_later_request_does_not_take_an_earlier_ones_reply():
    """Review bypass: restore 0, then a dropped stop of 1 with the same sequence."""
    engine = rules.RuleEngine()
    restore = _dnp3_frame(bytes([0xC0, 0xC7, 0x05]) + _ao_points((1128, 0)))
    dropped = _dnp3_frame(bytes([0xC0, 0xD7, 0x05]) + _ao_points((1128, 1)))
    (first,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(restore)))
    (second,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(dropped)))
    engine.check_packet(_from_outstation(_dnp3_reply([(1128, 0, 0)], seq=7)))
    assert first["dnp3"][0]["reply"]["objects"][0]["value"] == 0
    assert second["dnp3"][0]["reply"] is None


# Review round 2: a response does not name the function it answers.  A
# SELECT the outstation accepts is answered with status 00 and writes
# nothing; its reply must not confirm a Direct Operate the outstation dropped
# (UNS set) that carries the same sequence number and points.
_DROPPED_DO = _dnp3_frame(bytes([0xC0, 0xD9, 0x05]) + _ao_points((1128, 1)))
_SELECT_9 = _dnp3_frame(bytes([0xC0, 0xC9, 0x03]) + _ao_points((1128, 1)))
_SELECT_9_REPLY = _dnp3_reply([(1128, 1, 0)], seq=9)


def _requests_after(segments):
    engine = rules.RuleEngine()
    alerts = []
    for segment in segments:
        alerts += _dnp3_alerts(engine.check_packet(_dnp3_packet(segment)))
    engine.check_packet(_from_outstation(_SELECT_9_REPLY))
    return [r for a in alerts for r in a["dnp3"]]


@pytest.mark.parametrize("segments,label", [
    ([_DROPPED_DO, _SELECT_9], "two-segments"),
    ([_DROPPED_DO + _SELECT_9], "one-segment"),
    ([_DROPPED_DO + _SELECT_9[:-4], _SELECT_9[-4:]], "select-split"),
    ([_DROPPED_DO, _SELECT_9[:7], _SELECT_9[7:]], "select-in-pieces"),
])
def test_dnp3_a_selects_reply_never_confirms_an_operate(segments, label):
    operates = [r for r in _requests_after(segments) if r["function"] == 0x05]
    assert operates and not any(_confirmed(r) for r in operates), label


def test_dnp3_a_folded_answered_select_still_counts_as_a_match():
    """Review round 3: a dropped DO on port P, a SELECT on Q, the same SELECT on P.

    The repeat folds into the SELECT's alert, which already has its reply,
    and waits on P next to the dropped DO; the second 00 must not go to it.
    """
    engine = rules.RuleEngine()

    def send(payload, port):
        return _dnp3_alerts(engine.check_packet(
            (ATTACK_MACHINE, OPENPLC, port, 20000, "PA", 6, payload, None)))

    (operate,) = send(_DROPPED_DO, 51000)
    (select,) = send(_SELECT_9, 51001)
    engine.check_packet(_from_outstation(_SELECT_9_REPLY, dport=51001))
    assert select["dnp3"][0]["reply"] is not None
    assert send(_SELECT_9, 51000) == []   # folded
    engine.check_packet(_from_outstation(_SELECT_9_REPLY, dport=51000))
    assert not _confirmed(operate["dnp3"][0])


def test_dnp3_a_corrected_retry_is_credited():
    """A dropped attempt, then the same request fixed: folds, and is confirmed."""
    engine = rules.RuleEngine()
    (alert,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(DNP3_STOP)))
    engine.check_packet(_dnp3_packet(DNP3_STOP, src=ATTACK_MACHINE))
    engine.check_packet(_from_outstation(_dnp3_reply([(1128, 1, 0)])))
    assert alert["dnp3"][0]["reply"]["objects"][0]["status"] == 0


def test_dnp3_a_select_in_two_transport_segments_never_confirms_an_operate():
    """Each frame is whole, but the SELECT's message spans two of them.

    The IDS reads frame by frame and sees a SELECT with no decodable points;
    the outstation reassembles the transport segments and answers 00. The
    dropped DO must not take that reply.
    """
    message = bytes([0xC9, 0x03]) + _ao_points((1128, 1))
    first = _dnp3_frame(bytes([0x40]) + message[:4])      # FIR, seq 0
    second = _dnp3_frame(bytes([0x81]) + message[4:])     # FIN, seq 1
    operates = [r for r in _requests_after([_DROPPED_DO, first, second])
                if r["function"] == 0x05]
    assert operates and not _confirmed(operates[0])


@pytest.mark.parametrize("payload,opaque", [
    (DNP3_STOP, False),
    (DNP3_STOP + DNP3_STOP, False),
    (_dnp3_frame(bytes([0xC0, 0x01, 0x05]) + _ao_points((1128, 1))), True),
    (_dnp3_frame(bytes([0x40, 0xC1, 0x05]) + _ao_points((1128, 1))), True),
    (_dnp3_frame(bytes([0x80, 0xC1, 0x05]) + _ao_points((1128, 1))), True),
    (_dnp3_request(_ao_points((1128, 1)) + b"\x00"), True),
    (_dnp3_request(bytes([41, 2, 0x28, 1]) + struct.pack("<Hh", 1128, 1) + b"\x00"), True),
    (_dnp3_request(_ao_points(*[(1100 + i, 0) for i in range(rules.DNP3_MAX_POINTS + 1)])), True),
    (_dnp3_request(bytes([60, 1, 0x06]), func=0x01), False),
    (_dnp3_frame(b"", control=0xC9), False),
    (DNP3_STOP[:-2], True),
], ids=["stop", "two-stops", "app-not-fir-fin", "transport-fir-only",
        "transport-fin-only", "trailing-byte", "short-count", "too-many-points",
        "read", "link-status", "partial"])
def test_dnp3_opaque(payload, opaque):
    assert rules.dnp3_opaque(payload) is opaque


def test_dnp3_a_select_past_the_frames_the_rules_read_never_confirms_an_operate():
    """Review round 4: 15 link-status fillers, then the SELECT as frame 17."""
    filler = _dnp3_frame(b"", control=0xC9) * (rules.DNP3_MAX_FRAMES - 1)
    segment = _DROPPED_DO + filler + _SELECT_9
    assert rules.dnp3_opaque(segment)
    operates = [r for r in _requests_after([segment]) if r["function"] == 0x05]
    assert operates and not _confirmed(operates[0])


def test_dnp3_many_link_status_frames_are_not_opaque():
    """The solution's address sweep sends one burst of link-status requests."""
    assert not rules.dnp3_opaque(_dnp3_frame(b"", control=0xC9) * 100)


def test_dnp3_a_held_back_select_reply_never_confirms_an_operate(monkeypatch):
    """Review round 4: the master closes its TCP window to delay the SELECT's reply."""
    engine = rules.RuleEngine()
    start = time.time()
    monkeypatch.setattr(rules.time, "time", lambda: start)
    engine.check_packet(_dnp3_packet(_SELECT_9))
    monkeypatch.setattr(rules.time, "time", lambda: start + rules.DNP3_REPLY_TIMEOUT - 1)
    (operate,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(_DROPPED_DO)))
    monkeypatch.setattr(rules.time, "time", lambda: start + 10 * rules.DNP3_REPLY_TIMEOUT)
    engine.check_packet(_from_outstation(_SELECT_9_REPLY))
    assert not _confirmed(operate["dnp3"][0])


def test_dnp3_pushing_a_select_off_the_list_blocks_replies():
    """Review round 4: enough other requests to push the SELECT off the list."""
    engine = rules.RuleEngine()
    engine.check_packet(_dnp3_packet(_SELECT_9))
    (operate,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(_DROPPED_DO)))
    for value in range(rules.DNP3_MAX_WAITING):
        engine.check_packet(_dnp3_packet(_dnp3_request(_ao_points((1200, value)))))
    engine.check_packet(_from_outstation(_SELECT_9_REPLY))
    assert not _confirmed(operate["dnp3"][0])


# Review round 5: state a connection gets from TCP itself.  These tests use
# the detector's full tuple with sequence and acknowledgement numbers.

class _Session:
    """A master's TCP connection to the outstation, as the IDS sees it."""

    def __init__(self, engine, port=52000, isn=1000, syn=True):
        self.engine, self.port, self.next = engine, port, isn + 1
        if syn:
            engine.check_packet((ATTACK_MACHINE, OPENPLC, port, 20000, "S", 6, b"", None,
                                 None, None, isn, 0, 0))

    def send(self, payload, seen=True, length=None):
        length = len(payload) if length is None else length
        pkt = (ATTACK_MACHINE, OPENPLC, self.port, 20000, "PA", 6, payload, None,
               None, None, self.next, 1, length)
        self.next = (self.next + length) & 0xFFFFFFFF
        return _dnp3_alerts(self.engine.check_packet(pkt)) if seen else []

    def reply(self, payload, ack=None):
        self.engine.check_packet((OPENPLC, ATTACK_MACHINE, 20000, self.port, "PA", 6,
                                  payload, None, None, None, 1,
                                  self.next if ack is None else ack, len(payload)))


def test_dnp3_a_followed_connection_is_confirmed():
    session = _Session(rules.RuleEngine())
    (alert,) = session.send(DNP3_STOP)
    session.reply(_dnp3_reply([(1128, 1, 0)]))
    assert _confirmed(alert["dnp3"][0])


def test_dnp3_a_syn_flood_cannot_make_the_ids_forget_a_select():
    engine = rules.RuleEngine()
    session = _Session(engine)
    session.send(_SELECT_9)                 # its reply is held back
    for port in range(rules.DNP3_MAX_CONNECTIONS + 10):
        _Session(engine, port=30000 + port)
    (operate,) = session.send(_DROPPED_DO)
    session.reply(_SELECT_9_REPLY)
    assert not _confirmed(operate["dnp3"][0])


def test_dnp3_a_forgotten_connection_comes_back_opaque():
    """Real connections, each with a request, push the target out after all."""
    engine = rules.RuleEngine()
    session = _Session(engine)
    session.send(_SELECT_9)
    for port in range(rules.DNP3_MAX_CONNECTIONS):
        _Session(engine, port=30000 + port).send(_dnp3_request(_ao_points((1200, port))))
    assert (ATTACK_MACHINE, session.port, OPENPLC) not in engine.dnp3_connections
    (operate,) = session.send(_DROPPED_DO)
    session.reply(_SELECT_9_REPLY)
    assert not _confirmed(operate["dnp3"][0])


def test_dnp3_a_select_the_capture_lost_is_noticed_by_the_reply():
    session = _Session(rules.RuleEngine())
    (operate,) = session.send(_DROPPED_DO)
    session.send(_SELECT_9, seen=False)     # dropped by the capture
    session.reply(_SELECT_9_REPLY)          # acknowledges it nonetheless
    assert not _confirmed(operate["dnp3"][0])


def test_dnp3_a_gap_in_the_stream_makes_the_connection_opaque():
    engine = rules.RuleEngine()
    session = _Session(engine)
    session.send(_SELECT_9, seen=False)
    (operate,) = session.send(_DROPPED_DO)
    assert engine.dnp3_connections[(ATTACK_MACHINE, session.port, OPENPLC)]["opaque"]
    session.reply(_SELECT_9_REPLY)
    assert not _confirmed(operate["dnp3"][0])


def test_dnp3_a_connection_joined_midway_is_opaque():
    session = _Session(rules.RuleEngine(), syn=False)
    (alert,) = session.send(DNP3_STOP)
    session.reply(_dnp3_reply([(1128, 1, 0)]))
    assert not _confirmed(alert["dnp3"][0])


def test_dnp3_a_segment_cut_off_by_the_capture_is_opaque():
    session = _Session(rules.RuleEngine())
    (alert,) = session.send(DNP3_STOP, length=len(DNP3_STOP) + 40)
    session.reply(_dnp3_reply([(1128, 1, 0)]))
    assert not _confirmed(alert["dnp3"][0])


def test_dnp3_a_segment_captured_twice_is_not_a_gap():
    engine = rules.RuleEngine()
    session = _Session(engine)
    pkt = (ATTACK_MACHINE, OPENPLC, session.port, 20000, "PA", 6, DNP3_STOP, None,
           None, None, session.next, 1, len(DNP3_STOP))
    (alert,) = _dnp3_alerts(engine.check_packet(pkt))
    engine.check_packet(pkt)
    session.next += len(DNP3_STOP)
    session.reply(_dnp3_reply([(1128, 1, 0)]))
    assert _confirmed(alert["dnp3"][0])


def test_dnp3_a_retransmission_with_other_bytes_is_opaque():
    """TCP keeps the bytes it got first; the IDS may have seen only the second copy."""
    engine = rules.RuleEngine()
    session = _Session(engine)
    start = session.next
    session.send(_SELECT_9)
    session.next = start
    (operate,) = session.send(_DROPPED_DO[:len(_SELECT_9)])
    assert engine.dnp3_connections[(ATTACK_MACHINE, session.port, OPENPLC)]["opaque"]


# Review round 6: a station resyncs on 05 64 after a header that fails its
# CRC, so a frame inside the bytes the IDS would skip by the declared length
# reaches the outstation.

def _hide(inner, header_crc=b"\x00\x00"):
    """A frame header with a wrong CRC that declares room for `inner` and padding."""
    data_len = 27
    return (bytes([0x05, 0x64, 5 + data_len, 0xC4, 10, 0, 1, 0]) + header_crc + inner
            + bytes(10 + data_len + 2 * ((data_len + 15) // 16) - 10 - len(inner)))


def test_dnp3_a_select_inside_a_frame_with_a_bad_header_crc_is_opaque():
    hidden = _hide(_SELECT_9)
    assert rules.dnp3_opaque(hidden)
    session = _Session(rules.RuleEngine())
    (operate,) = session.send(_DROPPED_DO)
    assert session.send(hidden) == []
    session.reply(_SELECT_9_REPLY)
    assert not _confirmed(operate["dnp3"][0])


def test_dnp3_a_select_inside_a_frame_with_a_bad_block_crc_is_opaque():
    frame = bytearray(_dnp3_frame(bytes([0xC0, 0xC1, 0x05]) + bytes(12) + _SELECT_9[:4]))
    frame[-1] ^= 0xFF
    assert rules.dnp3_opaque(bytes(frame) + _SELECT_9[4:])


def test_dnp3_urgent_data_makes_the_connection_opaque():
    """The outstation's TCP stack takes the urgent byte out of the stream."""
    engine = rules.RuleEngine()
    session = _Session(engine)
    pkt = (ATTACK_MACHINE, OPENPLC, session.port, 20000, "PAU", 6, DNP3_STOP, None,
           None, None, session.next, 1, len(DNP3_STOP))
    engine.check_packet(pkt)
    assert engine.dnp3_connections[(ATTACK_MACHINE, session.port, OPENPLC)]["opaque"]


def test_dnp3_a_syn_in_the_middle_does_not_wipe_the_requests():
    engine = rules.RuleEngine()
    session = _Session(engine)
    session.send(_SELECT_9)
    engine.check_packet((ATTACK_MACHINE, OPENPLC, session.port, 20000, "S", 6, b"", None,
                         None, None, session.next - 1, 0, 0))
    (operate,) = session.send(_DROPPED_DO)
    session.reply(_SELECT_9_REPLY)
    assert not _confirmed(operate["dnp3"][0])


def test_dnp3_a_new_connection_on_a_reused_port_without_requests_is_clean():
    engine = rules.RuleEngine()
    _Session(engine)
    session = _Session(engine, isn=5000)
    (alert,) = session.send(DNP3_STOP)
    session.reply(_dnp3_reply([(1128, 1, 0)]))
    assert _confirmed(alert["dnp3"][0])


def test_dnp3_select_then_operate_on_one_connection_is_confirmed():
    session = _Session(rules.RuleEngine())
    session.send(_dnp3_frame(bytes([0xC0, 0xC2, 0x03]) + _ao_points((1128, 1))))
    session.reply(_dnp3_reply([(1128, 1, 0)], seq=2))
    (operate,) = session.send(_dnp3_frame(bytes([0xC0, 0xC3, 0x04]) + _ao_points((1128, 1))))
    session.reply(_dnp3_reply([(1128, 1, 0)], seq=3))
    assert _confirmed(operate["dnp3"][0])


def test_dnp3_a_lone_select_still_gets_its_reply():
    (select,) = _requests_after([_SELECT_9])
    assert select["reply"]["objects"][0]["status"] == 0


@pytest.mark.parametrize("payload,whole", [
    (DNP3_STOP, True),
    (DNP3_STOP + DNP3_STOP, True),
    (DNP3_STOP[:-1], False),
    (DNP3_STOP[3:], False),
    (DNP3_STOP + b"\x05", False),
    (b"\x05\x64\x02", False),
])
def test_dnp3_intact_frames(payload, whole):
    assert rules.dnp3_intact_frames(payload) is whole


@pytest.mark.parametrize("pos", [8, 9, 12, len(DNP3_STOP) - 1])
def test_dnp3_a_broken_crc_is_not_intact(pos):
    broken = bytearray(DNP3_STOP)
    broken[pos] ^= 0x01
    assert not rules.dnp3_intact_frames(bytes(broken))


def test_dnp3_a_split_segment_blocks_replies_for_the_connection(monkeypatch):
    """However long the reply is held back, the connection stays opaque."""
    engine = rules.RuleEngine()
    engine.check_packet(_dnp3_packet(DNP3_STOP[:5]))
    (alert,) = _dnp3_alerts(engine.check_packet(_dnp3_packet(_dnp3_request(_ao_points((1128, 1))))))
    engine.check_packet(_from_outstation(_dnp3_reply([(1128, 1, 0)])))
    assert alert["dnp3"][0]["reply"] == {"unattributed": True}
    fresh = _dnp3_alerts(engine.check_packet(
        (ATTACK_MACHINE, OPENPLC, 51009, 20000, "PA", 6, _dnp3_request(_ao_points((1128, 0))), None)))
    engine.check_packet(_from_outstation(_dnp3_reply([(1128, 0, 0)]), dport=51009))
    assert _confirmed(fresh[0]["dnp3"][0]), "a new connection starts clean"


def test_dnp3_waiting_requests_per_connection_are_bounded():
    engine = rules.RuleEngine()
    for value in range(rules.DNP3_MAX_WAITING + 5):
        engine.check_packet(_dnp3_packet(_dnp3_request(_ao_points((1128, value)))))
    connection = engine.dnp3_connections[(ATTACK_MACHINE, 51000, OPENPLC)]
    assert len(connection["waiting"]) == rules.DNP3_MAX_WAITING and connection["opaque"]


def test_dnp3_frame_from_an_outstation_is_not_a_command():
    """Review bypass (f): DIR clear claims the frame comes from an outstation."""
    frame = _dnp3_frame(bytes([0xC0, 0xC1, 0x05]) + _ao_points((1128, 1)), control=0x44)
    assert rules.parse_dnp3_requests(frame) == []


@pytest.mark.parametrize("user,control,label", [
    (bytes([0x40, 0xC1, 0x05]), 0xC4, "transport-fir-without-fin"),
    (bytes([0xC0, 0x01, 0x05]), 0xC4, "app-without-fir-fin"),
    (bytes([0xC0, 0xD1, 0x05]), 0xC4, "app-uns"),
    (bytes([0xC0, 0xE1, 0x05]), 0xC4, "app-con"),
    (bytes([0xC0, 0xC1, 0x05]), 0xF3, "confirmed-data-fcv"),
    (bytes([0xC0, 0xC1, 0x05]), 0xD3, "confirmed-data"),
])
def test_dnp3_frames_the_outstation_drops_stay_unconfirmed(user, control, label):
    """Review bypasses (a)-(e): logged as attempts, but nothing confirms them.

    OpenPLC's outstation sends no reply to these, so their requests keep
    reply None and the verify check does not credit them.
    """
    engine = rules.RuleEngine()
    alerts = _dnp3_alerts(engine.check_packet(
        _dnp3_packet(_dnp3_frame(user + _ao_points((1128, 1)), control=control))))
    assert all(r["reply"] is None for a in alerts for r in a["dnp3"]), label


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


# ---- Memory bounds of the per-server repeat folding ----
#
# s7_last_write, s7_last_control and dnp3_last_request are keyed by the
# destination address and port.  A flood that sprays requests at many
# addresses (any destination passes the capture filter while the source is on
# the plant network) grew them by one entry per packet until the next
# cleanup, beyond the 32 MB the IDS container has on the board.

def _sprayed(payload, n, dport):
    return [(ATTACK_MACHINE, f"10.{i >> 16 & 255}.{i >> 8 & 255}.{i & 255}", 51000 + i % 1000,
             dport, "PA", 6, payload, None) for i in range(n)]


@pytest.mark.parametrize("payload, dport, table", [
    (S7_WRITE_STOP, 102, "s7_last_write"),
    (S7_PLC_STOP, 102, "s7_last_control"),
    (DNP3_STOP, 20000, "dnp3_last_request"),
], ids=["s7-write", "s7-control", "dnp3"])
def test_repeat_folding_tracks_a_bounded_number_of_servers(payload, dport, table):
    engine = rules.RuleEngine()
    packets = _sprayed(payload, rules.MAX_TRACKED_SERVERS * 4, dport)
    for pkt in packets:
        engine.check_packet(pkt)
    assert len(getattr(engine, table)) == rules.MAX_TRACKED_SERVERS
    # The newest servers are the ones kept, so a repeat to one of them is still folded.
    newest = packets[-1]
    assert (newest[1], dport) in getattr(engine, table)
    rule = {"s7_last_write": "s7_write", "s7_last_control": "s7_cpu_control",
            "dnp3_last_request": "dnp3_operate"}[table]
    assert not [a for a in engine.check_packet(newest) if a["rule"] == rule]
    # A forgotten server's repeat is alerted again rather than lost.
    assert [a for a in engine.check_packet(packets[0]) if a["rule"] == rule]


def test_s7_control_folding_is_cleaned_up(monkeypatch):
    engine = rules.RuleEngine()
    engine.check_packet(_s7_packet(S7_PLC_STOP))
    assert engine.s7_last_control
    later = time.time() + engine.ALERT_COOLDOWN * 2 + 1
    monkeypatch.setattr(rules.time, "time", lambda: later)
    engine.cleanup()
    assert not engine.s7_last_control
