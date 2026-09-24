"""Unit tests for the IDS packet decoder and capture filter.

software/ids/detector.py is 474 lines and had no tests. Most of it drives
tcpdump, but two pieces are pure and carry the consequences:

- `_parse_raw_packet` turns bytes off the wire into the tuple every rule reads.
  A wrong offset here does not crash, it silently mislabels traffic, and the
  rules then decide on the wrong addresses.
- `_build_bpf_filter` decides what is captured at all. Anything it excludes is
  dropped in the kernel and no rule will ever see it.

Neither needs scapy, tcpdump or a running stack.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS_DIR = os.path.join(ROOT, "software", "ids")

if not os.path.exists(os.path.join(IDS_DIR, "detector.py")):
    pytest.skip("software/ids/detector.py not present", allow_module_level=True)

sys.path.insert(0, IDS_DIR)
import detector  # noqa: E402

parse = detector._parse_raw_packet

SRC_MAC = bytes.fromhex("aabbccddeeff")
DST_MAC = bytes.fromhex("112233445566")


def _eth(eth_type, body, vlan=False):
    if vlan:
        return DST_MAC + SRC_MAC + b"\x81\x00" + b"\x00\x64" + eth_type + body
    return DST_MAC + SRC_MAC + eth_type + body


def _ipv4(proto, payload, src="172.18.0.100", dst="172.18.0.3"):
    src_b = bytes(int(x) for x in src.split("."))
    dst_b = bytes(int(x) for x in dst.split("."))
    total = 20 + len(payload)
    return (b"\x45\x00" + total.to_bytes(2, "big") + b"\x00\x00\x40\x00\x40"
            + bytes([proto]) + b"\x00\x00" + src_b + dst_b + payload)


def _tcp(sport, dport, flags=0x02, payload=b""):
    return (sport.to_bytes(2, "big") + dport.to_bytes(2, "big")
            + b"\x00" * 8 + b"\x50" + bytes([flags]) + b"\x00" * 6 + payload)


def _udp(sport, dport, payload=b""):
    length = 8 + len(payload)
    return (sport.to_bytes(2, "big") + dport.to_bytes(2, "big")
            + length.to_bytes(2, "big") + b"\x00\x00" + payload)


# --- addresses and ports -----------------------------------------------------

def test_a_tcp_packet_yields_the_addresses_the_rules_key_on():
    pkt = parse(_eth(b"\x08\x00", _ipv4(6, _tcp(51000, 502))))
    assert pkt is not None
    src, dst, sport, dport, flags, proto = pkt[:6]
    assert (src, dst) == ("172.18.0.100", "172.18.0.3")
    assert (sport, dport) == (51000, 502)
    assert proto == 6


def test_udp_is_decoded_and_labelled_as_protocol_17():
    pkt = parse(_eth(b"\x08\x00", _ipv4(17, _udp(50000, 4840))))
    assert pkt is not None
    assert pkt[2:4] == (50000, 4840)
    assert pkt[5] == 17


def test_the_tcp_payload_reaches_the_rules_intact():
    """The Modbus rules read the function code out of this payload."""
    body = bytes.fromhex("0001000000060103")
    pkt = parse(_eth(b"\x08\x00", _ipv4(6, _tcp(51000, 502, payload=body))))
    assert pkt[6] == body


# --- TCP flags ---------------------------------------------------------------

def test_a_syn_is_distinguishable_from_an_established_connection():
    """Port-scan and SYN-flood detection both hinge on this."""
    syn = parse(_eth(b"\x08\x00", _ipv4(6, _tcp(1, 502, flags=0x02))))
    established = parse(_eth(b"\x08\x00", _ipv4(6, _tcp(1, 502, flags=0x18))))
    assert "S" in syn[4]
    assert "S" not in established[4]


# --- ARP ---------------------------------------------------------------------

def _arp(op=2, sender_mac=SRC_MAC, sender_ip="172.18.0.1", target_ip="172.18.0.3"):
    return (b"\x00\x01\x08\x00\x06\x04" + op.to_bytes(2, "big") + sender_mac
            + bytes(int(x) for x in sender_ip.split("."))
            + DST_MAC + bytes(int(x) for x in target_ip.split(".")))


def test_arp_carries_the_sender_mac_that_spoofing_detection_compares():
    pkt = parse(_eth(b"\x08\x06", _arp()))
    assert pkt is not None
    assert pkt[5] == 0, "ARP must be protocol id 0"
    assert pkt[7] == 2, "ARP operation (2 = reply)"
    assert pkt[8] == "aa:bb:cc:dd:ee:ff"
    assert pkt[9] == "172.18.0.1"


def test_a_truncated_arp_frame_is_dropped_rather_than_half_read():
    assert parse(_eth(b"\x08\x06", _arp()[:20])) is None


# --- VLAN and other frames ---------------------------------------------------

def test_a_vlan_tagged_packet_is_decoded_past_the_tag():
    """A bridge can hand us tagged frames; reading through the tag would
    take four bytes of the tag as the IP header and mislabel every address."""
    pkt = parse(_eth(b"\x08\x00", _ipv4(6, _tcp(51000, 502)), vlan=True))
    assert pkt is not None
    assert pkt[0] == "172.18.0.100"
    assert pkt[3] == 502


def test_ipv6_and_other_ethertypes_are_ignored_rather_than_misparsed():
    assert parse(_eth(b"\x86\xdd", b"\x00" * 40)) is None


@pytest.mark.parametrize("size", [0, 13])
def test_a_frame_too_short_for_an_ethernet_header_is_dropped(size):
    assert parse(b"\x00" * size) is None


def test_the_decoder_never_raises_on_arbitrary_bytes():
    """It runs on whatever a scan or a fuzzer puts on the bridge."""
    for payload in (b"", b"\xff" * 64, bytes(range(256)), os.urandom(300)):
        parse(payload)


# --- capture filter ----------------------------------------------------------

def test_the_filter_keeps_arp_and_syn_so_those_rules_can_ever_fire():
    """Anything this drops is discarded in the kernel; no rule sees it."""
    bpf = detector.Detector._build_bpf_filter("")
    assert "arp" in bpf, "ARP spoofing detection would never see a packet"
    assert "tcp-syn" in bpf, "port scan and SYN flood detection need SYNs"


def test_the_filter_covers_every_service_port_the_rules_mention():
    bpf = detector.Detector._build_bpf_filter("")
    for port in detector._IDS_PORTS:
        assert f"port {port}" in bpf, f"port {port} is filtered out before any rule runs"


def test_a_base_filter_narrows_rather_than_replaces():
    bpf = detector.Detector._build_bpf_filter("net 172.18.0.0/24")
    assert "net 172.18.0.0/24" in bpf
    assert "arp" in bpf, "the base filter must not drop the IDS's own clauses"
