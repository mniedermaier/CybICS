"""Sharky, the landing page's packet capture, against the running stack.

The lab network always carries traffic -- hwio and the HMI poll OpenPLC
over Modbus every few hundred milliseconds -- so a capture of a few seconds
that comes back empty means the capture is broken, not that the lab is quiet.
"""
import time

import pytest
import requests

from conftest import NGINX_PROXY_PORT, READ_TIMEOUT, SERVER_IP

pytestmark = pytest.mark.usefixtures("stack_ready")

BASE = f"http://{SERVER_IP}:{NGINX_PROXY_PORT}"
CAPTURE_SECONDS = 5


def capture(interface):
    response = requests.post(BASE + "/api/network/start", json={"interface": interface},
                             timeout=READ_TIMEOUT)
    assert response.status_code == 200, response.text
    try:
        time.sleep(CAPTURE_SECONDS)
        return requests.get(BASE + "/api/network/stats", timeout=READ_TIMEOUT).json()["total_packets"]
    finally:
        requests.post(BASE + "/api/network/stop", timeout=READ_TIMEOUT)


def lab_bridge():
    interfaces = requests.get(BASE + "/api/network/interfaces", timeout=READ_TIMEOUT).json()
    bridges = [i["name"] for i in interfaces if i["type"] == "ics_bridge"]
    assert bridges, f"no interface on the lab network among {interfaces}"
    return bridges[0]


def test_the_lab_bridge_shows_traffic():
    assert capture(lab_bridge()) > 0


def test_all_interfaces_shows_traffic():
    # "All" once meant Scapy's single default interface, which carries no
    # lab traffic, and captured nothing.
    assert capture("all") > 0


def start(body):
    return requests.post(BASE + "/api/network/start", json=body, timeout=READ_TIMEOUT + 5)


@pytest.mark.parametrize("body", [
    {"interface": ["ctfwlan0"]},                      # a list slipped past the uplink check
    {"interface": "all", "filter": "tcp) or (not net 172.18.0.0/24"},  # closed the lab filter
    {"interface": "all", "filter": "tcp port 502"},   # free-form BPF is not accepted at all
    {"interface": "no-such-interface0"},
])
def test_a_capture_request_cannot_leave_the_lab(body):
    response = start(body)
    assert response.status_code == 400, response.text
    assert "error" in response.json()


def test_the_capture_filter_presets_are_offered():
    names = requests.get(BASE + "/api/network/filters", timeout=READ_TIMEOUT).json()
    assert "modbus" in names and "arp" in names


def test_a_modbus_capture_holds_decoded_modbus_only():
    response = start({"interface": lab_bridge(), "filter": "modbus"})
    assert response.status_code == 200, response.text
    try:
        time.sleep(3)
        packets = requests.get(BASE + "/api/network/packets", timeout=READ_TIMEOUT).json()["packets"]
    finally:
        requests.post(BASE + "/api/network/stop", timeout=READ_TIMEOUT)
    assert packets, "the lab polls OpenPLC over Modbus constantly"
    assert all(502 in (p.get("source_port"), p.get("dest_port")) for p in packets)
    decoded = [p for p in packets if p["protocol"] == "MODBUS"]
    assert decoded, "Modbus payloads should be decoded"
    assert "function_code" in decoded[0]["layers"]["modbus"]
    assert "tcp" in decoded[0]["layers"]


def test_restarting_ends_the_previous_capture():
    # The first sniffer used to keep running after a restart and keep adding
    # its packets: here, Modbus into an ARP-only capture.
    assert start({"interface": lab_bridge(), "filter": "modbus"}).status_code == 200
    time.sleep(1)
    assert start({"interface": lab_bridge(), "filter": "arp"}).status_code == 200
    try:
        time.sleep(3)
        packets = requests.get(BASE + "/api/network/packets", timeout=READ_TIMEOUT).json()["packets"]
    finally:
        requests.post(BASE + "/api/network/stop", timeout=READ_TIMEOUT)
    assert all(p["protocol"] == "ARP" for p in packets), {p["protocol"] for p in packets}


def test_polling_returns_only_newer_packets_and_the_raw_bytes_on_request():
    assert start({"interface": lab_bridge()}).status_code == 200
    try:
        time.sleep(2)
        first = requests.get(BASE + "/api/network/packets", timeout=READ_TIMEOUT).json()
        newest = first["packets"][-1]["id"]
        time.sleep(1)
        later = requests.get(BASE + f"/api/network/packets?since={newest}", timeout=READ_TIMEOUT).json()
        raw = requests.get(BASE + f"/api/network/packet/{newest}/raw", timeout=READ_TIMEOUT)
    finally:
        requests.post(BASE + "/api/network/stop", timeout=READ_TIMEOUT)
    assert first["stats"]["active"] is True
    assert all(p["id"] > newest for p in later["packets"])
    assert raw.status_code == 200
    assert len(bytes.fromhex(raw.json()["raw_hex"])) == first["packets"][-1]["length"]


def test_the_export_holds_more_than_the_page_shows():
    assert start({"interface": lab_bridge()}).status_code == 200
    try:
        time.sleep(CAPTURE_SECONDS)
        stats = requests.get(BASE + "/api/network/stats", timeout=READ_TIMEOUT).json()
    finally:
        requests.post(BASE + "/api/network/stop", timeout=READ_TIMEOUT)
    export = requests.get(BASE + "/api/network/export", timeout=READ_TIMEOUT + 10)
    assert export.status_code == 200
    pcap = export.content
    # Little-endian pcap 2.4, Ethernet.
    assert pcap[:4] == bytes.fromhex("d4c3b2a1")
    assert int.from_bytes(pcap[20:24], "little") == 1
    records, offset = 0, 24
    while offset + 16 <= len(pcap):
        records += 1
        offset += 16 + int.from_bytes(pcap[offset + 8:offset + 12], "little")
    assert offset == len(pcap), "the file should end on a record boundary"
    assert records >= min(stats["total_packets"], stats["max_packets"])


def test_a_capture_nobody_polls_stops_by_itself():
    # A closed tab used to leave Scapy dissecting the lab bridge for good.
    # Stats do not count as a poll; the page polls /packets.
    assert start({"interface": lab_bridge()}).status_code == 200
    try:
        deadline = time.time() + 50
        stats = {}
        while time.time() < deadline:
            time.sleep(5)
            stats = requests.get(BASE + "/api/network/stats", timeout=READ_TIMEOUT).json()
            if not stats["active"]:
                break
    finally:
        requests.post(BASE + "/api/network/stop", timeout=READ_TIMEOUT)
    assert stats["active"] is False
    assert stats["stopped_reason"] == "idle"
