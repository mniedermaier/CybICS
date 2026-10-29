#!/usr/bin/env python3
"""Generate training/incident_pcap/incident.pcap, the "Incident PCAP" capture.

The capture is the mirror (SPAN) port of OpenPLC's switch port on the night
of an incident: everything sent to or from the PLC, plus broadcasts. A small
rogue computer (a Raspberry Pi, MAC b8:27:eb:...) joins the plant network,
discovers it, poisons the PLC's ARP cache for the HMI (FUXA) and the
engineering workstation, and stops the plant three times over three
protocols: a Modbus write from FUXA's address, an S7comm Write Var from the
workstation's address and a DNP3 Direct Operate from its own address. The
operator restarts the plant from the HMI after each stop.

Everything is fixed: MACs, addresses, timestamps, sequence numbers and IP IDs
come from constants and a seeded PRNG, so running this script again gives the
same bytes. tests/test_incident_pcap.py checks that, and checks that the
answers the challenge grades can be read out of the capture itself.

The S7comm and DNP3 application bytes are the ones the stack's own clients
send (python-snap7 db_write and training/dnp3_sidedoor/dnp3_stop.py, captured
from the attack shell against virtual-openplc on 2026-10-28), so Wireshark
and OpenPLC parse them the same way as live traffic.

    python3 software/scripts/generate_incident_pcap.py           # rewrite the pcap
    python3 software/scripts/generate_incident_pcap.py --key     # print the answer key
    python3 software/scripts/generate_incident_pcap.py --check   # compare with the committed file

The hwio I/O service (172.18.0.2) talks to the PLC about 50 times a second;
the capture was "taken with the filter `not host 172.18.0.2`", which keeps
the file small. The README says so.
"""
import argparse
import calendar
import os
import random
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT = os.path.join(ROOT, "training", "incident_pcap", "incident.pcap")

# 2026-03-14 02:58:00 UTC, a Saturday night.
START = calendar.timegm((2026, 3, 14, 2, 58, 0, 0, 0, 0))
DURATION = 120.0
SEED = 0x1CC5

BROADCAST = "ff:ff:ff:ff:ff:ff"
ZERO_MAC = "00:00:00:00:00:00"

PLC = ("172.18.0.3", "02:42:ac:12:00:03")
FUXA = ("172.18.0.4", "02:42:ac:12:00:04")
EWS = ("172.18.0.10", "02:42:ac:12:00:0a")
ROGUE_MAC = "b8:27:eb:3c:9a:71"          # Raspberry Pi Foundation OUI
ROGUE_IP = "172.18.0.77"

# Times (seconds from START) of the story's events.
T_EWS_READ = 6.5
T_PROBE = 20.5
T_SWEEP = 21.0
T_SCAN = 25.0
T_POISON = 34.0
POISON_EVERY = 4.0
T_MODBUS = 40.0
T_RUN1 = 58.3
T_S7 = 70.0
T_RUN2 = 86.3
T_DNP3 = 96.0
T_RUN3 = 110.3

SCAN_PORTS = [21, 22, 23, 80, 102, 443, 502, 1881, 2404, 4840, 8080, 8443, 20000, 44818]
OPEN_PORTS = {102, 502, 8080, 8443, 20000, 44818}   # what nmap finds on virtual-openplc

STOP_REGISTER = 1128      # %MW104, holding register 1024 + 104

# --- S7comm (python-snap7 3.3.0 against OpenPLC's Snap7 server) ------------
S7_COTP_CR = bytes.fromhex("0300001611e00000000100c1020100c2020101c0010a")
S7_COTP_CC = bytes.fromhex("0300001611d00001000100c1020100c2020101c0010a")
S7_SETUP_JOB = bytes.fromhex("0300001902f08032010000000100080000f0000001000101e0")
S7_SETUP_ACK = bytes.fromhex("0300001b02f080320300000001000800000000f0000001000101e0")
# Write Var DB1002.DBB208, 2 bytes = 0x0001: %MW104 (stop) = 1
S7_WRITE_STOP = bytes.fromhex("0300002502f080320100000003000e00060501120a1002000203ea84000680000400100001")
S7_WRITE_ACK = bytes.fromhex("0300001602f0803203000000030002000100000501ff")
S7_COTP_DR = bytes.fromhex("0300000c0680000100010000")
S7_COTP_DC = bytes.fromhex("0300000c06c0000100010000")

# --- DNP3 (training/dnp3_sidedoor/dnp3_stop.py, outstation 10, master 1) ---
# Direct Operate, g41v2 (Analog Output Int16) index 1128 = 1
DNP3_STOP = bytes.fromhex("056412c40a0001005686c0c105290228010068040100000e1e")
DNP3_STOP_RESPONSE = bytes.fromhex("0564144401000a00aaacc9c1818208290228010068040100000d20")


def mac_bytes(mac):
    return bytes(int(part, 16) for part in mac.split(":"))


def ip_bytes(ip):
    return bytes(int(part) for part in ip.split("."))


def checksum(data):
    if len(data) % 2:
        data += b"\0"
    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF


def ethernet(dst, src, ethertype, payload):
    frame = mac_bytes(dst) + mac_bytes(src) + struct.pack("!H", ethertype) + payload
    return frame + b"\0" * max(0, 60 - len(frame))      # minimum frame size, FCS not captured


def arp(op, sender_mac, sender_ip, target_mac, target_ip):
    return struct.pack("!HHBBH", 1, 0x0800, 6, 4, op) + mac_bytes(sender_mac) + \
        ip_bytes(sender_ip) + mac_bytes(target_mac) + ip_bytes(target_ip)


def ipv4(src, dst, proto, payload, ident, ttl=64):
    header = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(payload), ident, 0x4000,
                         ttl, proto, 0, ip_bytes(src), ip_bytes(dst))
    header = header[:10] + struct.pack("!H", checksum(header)) + header[12:]
    return header + payload


FIN, SYN, RST, PSH, ACK = 0x01, 0x02, 0x04, 0x08, 0x10


def tcp(src, dst, sport, dport, seq, ack, flags, payload=b"", window=502, options=b""):
    offset = (20 + len(options)) // 4
    header = struct.pack("!HHIIBBHHH", sport, dport, seq & 0xFFFFFFFF, ack & 0xFFFFFFFF,
                         offset << 4, flags, window, 0, 0) + options
    pseudo = ip_bytes(src) + ip_bytes(dst) + struct.pack("!BBH", 0, 6, len(header) + len(payload))
    csum = checksum(pseudo + header + payload)
    return header[:16] + struct.pack("!H", csum) + header[18:] + payload


MSS_1460 = struct.pack("!BBH", 2, 4, 1460)


class Capture:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.frames = []            # (time, order, bytes, tag)
        self.ip_ids = {}

    def add(self, t, frame, tag=None):
        self.frames.append((t, len(self.frames), frame, tag))

    def ip_id(self, sender):
        """Linux-like IP ID counter per sending stack (a spoofer keeps its own)."""
        if sender not in self.ip_ids:
            self.ip_ids[sender] = self.rng.randrange(1, 0xFFFF)
        self.ip_ids[sender] = (self.ip_ids[sender] + 1) & 0xFFFF
        return self.ip_ids[sender]

    def arp(self, t, eth_dst, op, sender_mac, sender_ip, target_mac, target_ip, tag=None):
        self.add(t, ethernet(eth_dst, sender_mac, 0x0806,
                             arp(op, sender_mac, sender_ip, target_mac, target_ip)), tag)

    def ip(self, t, src_mac, dst_mac, src, dst, segment, stack, tag=None):
        self.add(t, ethernet(dst_mac, src_mac, 0x0800,
                             ipv4(src, dst, 6, segment, self.ip_id(stack))), tag)

    def ordered(self):
        return sorted(self.frames, key=lambda f: (f[0], f[1]))


class PlcArpCache:
    """Which MAC the PLC sends to for an address, as the poisoning changes it."""

    def __init__(self):
        self.entries = {FUXA[0]: FUXA[1], EWS[0]: EWS[1]}
        self.poisoned = {}          # ip -> time from which the rogue MAC is used

    def __call__(self, ip, t):
        if ip in self.poisoned and t >= self.poisoned[ip]:
            return ROGUE_MAC
        return self.entries.get(ip, ROGUE_MAC if ip == ROGUE_IP else None)


class Conn:
    """A TCP connection between a client and the PLC as the mirror port sees it.

    client_mac is the source MAC of the client's frames (the rogue's MAC when
    it spoofs an address); stack names whose IP ID counter the client uses.
    The PLC's frames go to whatever its ARP cache says at that moment.
    """

    def __init__(self, cap, cache, client_ip, client_mac, sport, dport, stack,
                 established=False):
        self.cap, self.cache = cap, cache
        self.cip, self.cmac, self.sport, self.dport, self.stack = \
            client_ip, client_mac, sport, dport, stack
        self.cseq = cap.rng.randrange(1 << 32)
        self.sseq = cap.rng.randrange(1 << 32)
        self.established = established

    def _c(self, t, flags, data=b"", options=b"", window=502, tag=None):
        seg = tcp(self.cip, PLC[0], self.sport, self.dport, self.cseq, self.sseq, flags,
                  data, window, options)
        self.cap.ip(t, self.cmac, PLC[1], self.cip, PLC[0], seg, self.stack, tag)
        self.cseq += len(data) + (1 if flags & (SYN | FIN) else 0)

    def _s(self, t, flags, data=b"", options=b"", window=509, tag=None):
        seg = tcp(PLC[0], self.cip, self.dport, self.sport, self.sseq, self.cseq, flags,
                  data, window, options)
        self.cap.ip(t, PLC[1], self.cache(self.cip, t), PLC[0], self.cip, seg, "plc", tag)
        self.sseq += len(data) + (1 if flags & (SYN | FIN) else 0)

    def open(self, t):
        seg = tcp(self.cip, PLC[0], self.sport, self.dport, self.cseq, 0, SYN, b"", 64240, MSS_1460)
        self.cap.ip(t, self.cmac, PLC[1], self.cip, PLC[0], seg, self.stack)
        self.cseq += 1
        self._s(t + 0.00003, SYN | ACK, options=MSS_1460, window=65160)
        self._c(t + 0.00005, ACK)
        self.established = True
        return t + 0.0002

    def request(self, t, data, reply, tag=None, reply_tag=None, ack_after=0.04):
        """Client sends data, the PLC answers, the client ACKs a little later."""
        self._c(t, PSH | ACK, data, tag=tag)
        self._s(t + 0.0001, PSH | ACK, reply, tag=reply_tag)
        self._c(t + ack_after, ACK)
        return t + ack_after

    def close(self, t):
        self._c(t, FIN | ACK)
        self._s(t + 0.0001, FIN | ACK)
        self._c(t + 0.0002, ACK)
        return t + 0.0002


# --- Modbus ----------------------------------------------------------------

def mbap(tid, pdu, unit=1):
    return struct.pack("!HHHB", tid, 0, len(pdu) + 1, unit) + pdu


def read_holding(start, count):
    return struct.pack("!BHH", 3, start, count)


def read_holding_reply(values):
    return struct.pack("!BB", 3, 2 * len(values)) + struct.pack(f"!{len(values)}H", *values)


def write_single(register, value):
    return struct.pack("!BHH", 6, register, value)


class Plant:
    """Just enough of the gas plant to make FUXA's polling answers plausible."""

    def __init__(self):
        self.stop_changes = []          # (time, stop value)

    def stopped(self, t):
        value = 0
        for when, v in self.stop_changes:
            if t >= when:
                value = v
        return value

    def registers(self, t):
        sec = int(t)
        stop = self.stopped(t)
        gst = 125 - (sec // 30) % 3
        if stop:
            since = t - max(w for w, v in self.stop_changes if w <= t and v)
            hpt = max(60, 78 - int(since // 4))     # valve closed, slow leak
        else:
            hpt = 70 + abs((sec % 24) - 12)          # compressor cycling 70..82
        return [gst, 0, hpt, 0, stop, 0, 0, 0, 0 if stop else 1, 0, 0]

    def coils(self, t):
        sec = int(t)
        stop = self.stopped(t)
        heartbeat = sec % 2
        compressor = 0 if stop else int((sec % 24) < 12)
        valve = 0 if stop else 1
        return heartbeat | compressor << 1 | valve << 2


def build():
    """Return (pcap bytes, answer key)."""
    cap = Capture(SEED)
    cache = PlcArpCache()
    plant = Plant()

    # --- before the incident: the PLC refreshes FUXA, the workstation reads --
    cap.arp(3.0, BROADCAST, 1, PLC[1], PLC[0], ZERO_MAC, FUXA[0])
    cap.arp(3.0002, PLC[1], 2, FUXA[1], FUXA[0], PLC[1], PLC[0])
    cap.arp(T_EWS_READ - 0.01, BROADCAST, 1, EWS[1], EWS[0], ZERO_MAC, PLC[0])
    cap.arp(T_EWS_READ - 0.0098, EWS[1], 2, PLC[1], PLC[0], EWS[1], EWS[0])

    ews = Conn(cap, cache, EWS[0], EWS[1], 45012, 102, "ews")
    t = ews.open(T_EWS_READ)
    t = ews.request(t, S7_COTP_CR, S7_COTP_CC, ack_after=0.0003)
    t = ews.request(t, S7_SETUP_JOB, S7_SETUP_ACK, ack_after=0.0003)
    # Read Var DB1002.DBB200, 22 bytes (%MW100..%MW110), the workstation's trend view
    read_job = bytes.fromhex("0300001f02f080320100000002000e00000401120a10020016" "03ea840006" "40")
    values = struct.pack("!11H", 124, 0, 79, 0, 0, 0, 0, 0, 1, 0, 0)
    read_ack = bytes.fromhex("0300002f02f0803203000000020002001a00000401ff0400b0") + values
    t = ews.request(t, read_job, read_ack, ack_after=0.0003)
    t = ews.request(t + 0.1, S7_COTP_DR, S7_COTP_DC, ack_after=0.0001)
    ews.close(t + 0.0002)

    # --- the rogue device arrives ------------------------------------------
    cap.arp(T_PROBE, BROADCAST, 1, ROGUE_MAC, "0.0.0.0", ZERO_MAC, ROGUE_IP)
    for i, host in enumerate(range(1, 31)):
        target = f"172.18.0.{host}"
        if target == ROGUE_IP:
            continue
        when = T_SWEEP + 0.02 * i
        cap.arp(when, BROADCAST, 1, ROGUE_MAC, ROGUE_IP, ZERO_MAC, target)
        if target == PLC[0]:
            cap.arp(when + 0.0001, ROGUE_MAC, 2, PLC[1], PLC[0], ROGUE_MAC, ROGUE_IP)

    # --- half-open port scan of the PLC (nmap -sS) -------------------------
    ports = SCAN_PORTS[:]
    cap.rng.shuffle(ports)
    scan_seq = cap.rng.randrange(1 << 32)
    for i, port in enumerate(ports):
        when = T_SCAN + 0.003 * i
        seg = tcp(ROGUE_IP, PLC[0], 61234, port, scan_seq, 0, SYN, b"", 1024, MSS_1460)
        cap.ip(when, ROGUE_MAC, PLC[1], ROGUE_IP, PLC[0], seg, "rogue")
        if port in OPEN_PORTS:
            plc_seq = cap.rng.randrange(1 << 32)
            seg = tcp(PLC[0], ROGUE_IP, port, 61234, plc_seq, scan_seq + 1, SYN | ACK, b"",
                      64240, MSS_1460)
            cap.ip(when + 0.0001, PLC[1], ROGUE_MAC, PLC[0], ROGUE_IP, seg, "plc")
            seg = tcp(ROGUE_IP, PLC[0], 61234, port, scan_seq + 1, 0, RST, b"", 0)
            cap.ip(when + 0.0002, ROGUE_MAC, PLC[1], ROGUE_IP, PLC[0], seg, "rogue")
        else:
            seg = tcp(PLC[0], ROGUE_IP, port, 61234, 0, scan_seq + 1, RST | ACK, b"", 0)
            cap.ip(when + 0.0001, PLC[1], ROGUE_MAC, PLC[0], ROGUE_IP, seg, "plc")

    # --- ARP poisoning: tell the PLC that FUXA and the workstation are the Pi
    cache.poisoned = {FUXA[0]: T_POISON, EWS[0]: T_POISON}
    when, first = T_POISON, True
    while when < DURATION:
        cap.arp(when, PLC[1], 2, ROGUE_MAC, FUXA[0], PLC[1], PLC[0],
                tag="poison" if first else None)
        cap.arp(when + 0.0004, PLC[1], 2, ROGUE_MAC, EWS[0], PLC[1], PLC[0])
        when += POISON_EVERY
        first = False

    # --- stop 1: Modbus write from FUXA's address --------------------------
    plant.stop_changes.append((T_MODBUS + 1.2, 1))
    forged = Conn(cap, cache, FUXA[0], ROGUE_MAC, 51514, 502, "rogue-as-fuxa")
    t = forged.open(T_MODBUS)
    t = forged.request(t + 0.3, mbap(1, read_holding(1124, 11)),
                       mbap(1, read_holding_reply(plant.registers(T_MODBUS))))
    t = forged.request(T_MODBUS + 1.2, mbap(2, write_single(STOP_REGISTER, 1)),
                       mbap(2, write_single(STOP_REGISTER, 1)), tag="stop_modbus")
    forged.close(t + 0.5)

    # --- stop 2: S7comm Write Var from the workstation's address -----------
    plant.stop_changes.append((T_RUN1, 0))
    plant.stop_changes.append((T_S7 + 0.0009, 1))
    s7 = Conn(cap, cache, EWS[0], ROGUE_MAC, 49233, 102, "rogue-as-ews")
    t = s7.open(T_S7)
    t = s7.request(t, S7_COTP_CR, S7_COTP_CC, ack_after=0.0002)
    t = s7.request(t, S7_SETUP_JOB, S7_SETUP_ACK, ack_after=0.0002)
    t = s7.request(t, S7_WRITE_STOP, S7_WRITE_ACK, tag="stop_s7")
    t = s7.request(t + 0.4, S7_COTP_DR, S7_COTP_DC, ack_after=0.0001)
    s7.close(t + 0.0001)

    # --- stop 3: DNP3 Direct Operate from the Pi's own address -------------
    plant.stop_changes.append((T_RUN2, 0))
    plant.stop_changes.append((T_DNP3 + 0.0003, 1))
    plant.stop_changes.append((T_RUN3, 0))
    dnp = Conn(cap, cache, ROGUE_IP, ROGUE_MAC, 40112, 20000, "rogue")
    t = dnp.open(T_DNP3)
    t = dnp.request(t, DNP3_STOP, DNP3_STOP_RESPONSE, tag="stop_dnp3")
    dnp.close(t + 1.4)

    # --- FUXA polls the PLC once a second; the operator restarts the plant
    fuxa = Conn(cap, cache, FUXA[0], FUXA[1], 42716, 502, "fuxa", established=True)
    tid = 211
    runs = [T_RUN1, T_RUN2, T_RUN3]
    sec = 0.2
    while sec < DURATION:
        fuxa.request(sec, mbap(tid, read_holding(1124, 11)),
                     mbap(tid, read_holding_reply(plant.registers(sec))), ack_after=0.0001)
        tid += 1
        coils = struct.pack("!BBB", 1, 1, plant.coils(sec))
        fuxa.request(sec + 0.0105, mbap(tid, struct.pack("!BHH", 1, 0, 4)), mbap(tid, coils))
        tid += 1
        while runs and runs[0] < sec + 1.0:
            when = runs.pop(0)
            fuxa.request(when, mbap(tid, write_single(STOP_REGISTER, 0)),
                         mbap(tid, write_single(STOP_REGISTER, 0)), tag="run")
            tid += 1
        sec += 1.0

    # --- write the file -----------------------------------------------------
    out = [struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)]
    key = {"stop_frames": [], "run_frames": []}
    for number, (when, _, frame, tag) in enumerate(cap.ordered(), start=1):
        ts = round((START + when) * 1_000_000)
        out.append(struct.pack("<IIII", ts // 1_000_000, ts % 1_000_000, len(frame), len(frame)))
        out.append(frame)
        if tag == "poison":
            key["poison_frame"] = number
        elif tag and tag.startswith("stop_"):
            key["stop_frames"].append(number)
            key[tag + "_frame"] = number
        elif tag == "run":
            key["run_frames"].append(number)
    key.update({
        "attacker_mac": ROGUE_MAC,
        "attacker_ips": sorted([ROGUE_IP, FUXA[0], EWS[0]]),
        "frames": number,
    })
    return b"".join(out), key


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--key", action="store_true", help="print the answer key")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the committed pcap differs from a fresh build")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()
    data, key = build()
    if args.key:
        for name, value in key.items():
            print(f"{name}: {value}")
        return 0
    if args.check:
        with open(args.output, "rb") as f:
            same = f.read() == data
        print("up to date" if same else "differs: regenerate it")
        return 0 if same else 1
    with open(args.output, "wb") as f:
        f.write(data)
    print(f"wrote {args.output}: {key['frames']} frames, {len(data)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
