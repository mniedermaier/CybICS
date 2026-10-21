"""Unit tests for Sharky's Python-side capture filters (no stack needed).

Scapy attaches the kernel's BPF filter only after it has opened the raw
socket, and on a Pi Zero compiling it takes long enough for packets of the
wrong kind to arrive in between: a Modbus-only capture started with HTTP
packets, and a restarted ARP capture showed the previous capture's Modbus.
network_capture.matches() checks every packet against the chosen preset.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

scapy = pytest.importorskip("scapy")
from scapy.layers.inet import ICMP, IP, TCP, UDP  # noqa: E402
from scapy.layers.l2 import ARP, Ether  # noqa: E402

from modules import network_capture as nc  # noqa: E402

MODBUS = Ether() / IP(src="172.18.0.2", dst="172.18.0.3") / TCP(sport=40000, dport=502)
MODBUS_REPLY = Ether() / IP(src="172.18.0.3", dst="172.18.0.2") / TCP(sport=502, dport=40000)
HTTP_FROM_PROXY = Ether() / IP(src="172.18.0.12", dst="10.0.0.172") / TCP(sport=80, dport=50000)
S7 = Ether() / IP(src="172.18.0.100", dst="172.18.0.3") / TCP(sport=40001, dport=102)
ENIP_UDP = Ether() / IP(src="172.18.0.100", dst="172.18.0.3") / UDP(sport=40002, dport=44818)
PING = Ether() / IP(src="172.18.0.100", dst="172.18.0.3") / ICMP()
LAB_ARP = Ether() / ARP(psrc="172.18.0.4", pdst="172.18.0.3")
OUTSIDE = Ether() / IP(src="10.0.0.172", dst="10.0.0.1") / TCP(sport=50000, dport=502)
OUTSIDE_ARP = Ether() / ARP(psrc="10.0.0.172", pdst="10.0.0.1")


def test_every_capture_filter_has_a_matcher():
    assert set(nc.CAPTURE_MATCHERS) == set(nc.CAPTURE_FILTERS)


@pytest.mark.parametrize("packet", [MODBUS, MODBUS_REPLY])
def test_modbus_capture_takes_modbus(packet):
    assert nc.matches(packet, "modbus")


@pytest.mark.parametrize("packet", [HTTP_FROM_PROXY, S7, ENIP_UDP, PING, LAB_ARP])
def test_modbus_capture_drops_everything_else(packet):
    assert not nc.matches(packet, "modbus")


def test_arp_capture_drops_modbus_from_a_previous_capture():
    assert nc.matches(LAB_ARP, "arp")
    assert not nc.matches(MODBUS, "arp")


@pytest.mark.parametrize("name, packet", [
    ("s7comm", S7), ("enip", ENIP_UDP), ("icmp", PING), ("tcp", HTTP_FROM_PROXY),
    ("udp", ENIP_UDP), ("", LAB_ARP), ("", HTTP_FROM_PROXY),
])
def test_presets_take_their_traffic(name, packet):
    assert nc.matches(packet, name)


@pytest.mark.parametrize("packet", [OUTSIDE, OUTSIDE_ARP])
def test_nothing_outside_the_lab_network(packet):
    for name in nc.CAPTURE_FILTERS:
        assert not nc.matches(packet, name)
