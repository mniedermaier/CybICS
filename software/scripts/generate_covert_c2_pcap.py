#!/usr/bin/env python3
"""Generate training/modbus_covert_c2/baseline.pcap, the "Whispering PLC" capture.

The plant team wants a read allowlist for the PLC, so it recorded four
minutes of Modbus/TCP at the PLC's mirror (SPAN) port to learn who reads
what. The recording holds the HMI (FUXA, 172.18.0.4) polling HR 1124-1134 and
coils 0-3 about once a second, the OPC-UA gateway (172.18.0.5) reading six
holding registers one at a time about every two seconds, and one thing that
does not belong: an implant on the OPC-UA gateway, on a second TCP connection
of its own, that sends one FC3 read of quantity 1 every 5.000 s. Its start
address is 0x0500 plus one ASCII character, so the stream of addresses spells
a status message ("gw ready for stage 2|", repeated). OpenPLC answers those
reads with zeros (%MW288-%MW382 hold nothing), so nothing fails and the
CybICS IDS, which never inspects reads, stays silent.

The timings and request shapes of FUXA and the OPC-UA gateway were measured
on the virtual stack (tcpdump on the docker bridge, 2026-10-29): FUXA FC3
1124 x 11 then FC1 0 x 4 ten milliseconds later, cycle 0.999-1.006 s; the
gateway FC3 x 1 at 1124, 1126, 1132, 1134, 1128, 1130, cycle 2.002-2.004 s;
OpenPLC answers a read of 0x05xx with zeros (checked with a raw read).
The I/O service (172.18.0.2) writes to the PLC about 40 times a second and
never reads holding registers; the capture filter
`tcp port 502 and not host 172.18.0.2` keeps it out, as in Incident PCAP,
so the file stays small.

Everything is fixed: MACs, timestamps, ports, sequence numbers and IP IDs
come from constants and a seeded PRNG, so running this script again gives
the same bytes. tests/test_modbus_covert_c2.py checks that and reads the
answers back out of the capture.

    python3 software/scripts/generate_covert_c2_pcap.py          # rewrite the pcap
    python3 software/scripts/generate_covert_c2_pcap.py --key    # print the answer key
    python3 software/scripts/generate_covert_c2_pcap.py --check  # compare with the committed file

It sits outside training/ so landing and the attack shell do not ship the key.
"""
import argparse
import calendar
import os
import random
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT = os.path.join(ROOT, "training", "modbus_covert_c2", "baseline.pcap")

# 2026-10-06 14:20:00 UTC, an ordinary Tuesday afternoon.
START = calendar.timegm((2026, 10, 6, 14, 20, 0, 0, 0, 0))
DURATION = 240.0
SEED = 0xC2C2

PLC = ("172.18.0.3", "02:42:ac:12:00:03")
FUXA = ("172.18.0.4", "02:42:ac:12:00:04")
OPCUA = ("172.18.0.5", "02:42:ac:12:00:05")

FUXA_PORT = 49628
OPCUA_PORT = 41772
IMPLANT_PORT = 50918

# What the implant whispers, one character per read, in a loop.
MESSAGE = "gw ready for stage 2|"
BASE_ADDRESS = 0x0500
BEACON_EVERY = 5.000
BEACON_JITTER = 0.0002          # a timer thread, not a scan cycle: well under a millisecond
FIRST_BEACON = 3.2187
FIRST_CHAR = 17                 # the implant started long before the recording

OPCUA_ORDER = [1124, 1126, 1132, 1134, 1128, 1130]
FUXA_FIRST, FUXA_COUNT = 1124, 11


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


def ethernet(dst, src, payload):
    frame = mac_bytes(dst) + mac_bytes(src) + b"\x08\x00" + payload
    return frame + b"\0" * max(0, 60 - len(frame))


def ipv4(src, dst, payload, ident):
    header = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(payload), ident, 0x4000,
                         64, 6, 0, ip_bytes(src), ip_bytes(dst))
    header = header[:10] + struct.pack("!H", checksum(header)) + header[12:]
    return header + payload


PSH, ACK = 0x08, 0x10


def tcp(src, dst, sport, dport, seq, ack, flags, payload, window):
    header = struct.pack("!HHIIBBHHH", sport, dport, seq & 0xFFFFFFFF, ack & 0xFFFFFFFF,
                         5 << 4, flags, window, 0, 0)
    pseudo = ip_bytes(src) + ip_bytes(dst) + struct.pack("!BBH", 0, 6, len(header) + len(payload))
    csum = checksum(pseudo + header + payload)
    return header[:16] + struct.pack("!H", csum) + header[18:] + payload


class Conn:
    """An established Modbus/TCP connection between a client and the PLC."""

    def __init__(self, frames, rng, client, sport):
        self.frames, self.rng = frames, rng
        (self.cip, self.cmac), self.sport = client, sport
        self.cseq, self.sseq = rng.randrange(1 << 32), rng.randrange(1 << 32)
        self.cid, self.sid = rng.randrange(1, 0xFFFF), rng.randrange(1, 0xFFFF)
        self.tid = rng.randrange(1, 0x8000)

    def _send(self, t, from_client, data, tag=None):
        if from_client:
            self.cid = (self.cid + 1) & 0xFFFF
            seg = tcp(self.cip, PLC[0], self.sport, 502, self.cseq, self.sseq, PSH | ACK if data else ACK,
                      data, 502)
            frame = ethernet(PLC[1], self.cmac, ipv4(self.cip, PLC[0], seg, self.cid))
            self.cseq += len(data)
        else:
            self.sid = (self.sid + 1) & 0xFFFF
            seg = tcp(PLC[0], self.cip, 502, self.sport, self.sseq, self.cseq, PSH | ACK, data, 509)
            frame = ethernet(self.cmac, PLC[1], ipv4(PLC[0], self.cip, seg, self.sid))
            self.sseq += len(data)
        self.frames.append((t, len(self.frames), frame, tag))

    def read(self, t, fc, start, count, reply_data, tag=None):
        """One request and the PLC's answer 0.1 ms later; returns the time after the answer."""
        self.tid = (self.tid + 1) & 0xFFFF
        pdu = struct.pack("!BHH", fc, start, count)
        self._send(t, True, struct.pack("!HHHB", self.tid, 0, len(pdu) + 1, 1) + pdu, tag)
        rpdu = struct.pack("!BB", fc, len(reply_data)) + reply_data
        self._send(t + 0.0001, False, struct.pack("!HHHB", self.tid, 0, len(rpdu) + 1, 1) + rpdu)
        return t + 0.0001

    def ack(self, t):
        self._send(t, True, b"")


class Plant:
    """Plausible, slowly changing values for HR 1124-1134 and coils 0-3."""

    def registers(self, t):
        sec = int(t)
        gst = 105 - (sec // 45) % 3
        phase = sec % 64
        hpt = 60 + (phase if phase < 32 else 64 - phase)        # compressor cycles 60..92
        return [gst, 0, hpt, 0, 0, 0, 0, 0, 1, 0, 0]

    def register(self, t, address):
        return self.registers(t)[address - FUXA_FIRST]

    def coils(self, t):
        sec = int(t)
        compressor = int((sec % 64) < 32)
        return (sec % 2) | compressor << 1 | 1 << 2 | 1 << 3


def build():
    """Return (pcap bytes, answer key)."""
    rng = random.Random(SEED)
    frames = []
    plant = Plant()
    fuxa = Conn(frames, rng, FUXA, FUXA_PORT)
    opcua = Conn(frames, rng, OPCUA, OPCUA_PORT)
    implant = Conn(frames, rng, OPCUA, IMPLANT_PORT)

    # FUXA: FC3 1124 x 11, ACK at once; FC1 0 x 4 10 ms later, delayed ACK.
    t = 0.0412
    while t < DURATION:
        regs = plant.registers(t)
        end = fuxa.read(t, 3, FUXA_FIRST, FUXA_COUNT, struct.pack(f"!{FUXA_COUNT}H", *regs))
        fuxa.ack(end + 0.0001)
        end = fuxa.read(t + 0.0105, 1, 0, 4, bytes([plant.coils(t)]))
        fuxa.ack(end + 0.0405)
        t += rng.uniform(0.999, 1.006)

    # OPC-UA gateway: six single-register reads back to back, then a delayed ACK.
    t = 0.5383
    while t < DURATION:
        when = t
        for i, address in enumerate(OPCUA_ORDER):
            end = opcua.read(when, 3, address, 1, struct.pack("!H", plant.register(when, address)))
            if i == 0:
                opcua.ack(end + 0.0001)
            when = end + rng.uniform(0.0001, 0.0003)
        opcua.ack(end + 0.041)
        t += rng.uniform(2.002, 2.004)

    # The implant: one character every 5.000 s, quantity 1, answered with zeros.
    beacons = []
    k = 0
    while True:
        t = FIRST_BEACON + k * BEACON_EVERY + rng.uniform(-BEACON_JITTER, BEACON_JITTER)
        if t >= DURATION:
            break
        char = MESSAGE[(FIRST_CHAR + k) % len(MESSAGE)]
        end = implant.read(t, 3, BASE_ADDRESS + ord(char), 1, b"\0\0", tag="beacon")
        implant.ack(end + 0.0403)
        beacons.append(char)
        k += 1

    out = [struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)]
    numbers = []
    for number, (when, _, frame, tag) in enumerate(sorted(frames, key=lambda f: (f[0], f[1])), 1):
        ts = round((START + when) * 1_000_000)
        out.append(struct.pack("<IIII", ts // 1_000_000, ts % 1_000_000, len(frame), len(frame)))
        out.append(frame)
        if tag == "beacon":
            numbers.append(number)
    key = {
        "implant": f"{OPCUA[0]}:{IMPLANT_PORT}",
        "interval_s": BEACON_EVERY,
        "message": MESSAGE.rstrip("|"),
        "decoded_in_capture": "".join(beacons),
        "read_range": f"{FUXA_FIRST}-{FUXA_FIRST + FUXA_COUNT - 1}",
        "beacon_frames": numbers,
        "frames": number,
    }
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
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "wb") as f:
        f.write(data)
    print(f"wrote {args.output}: {key['frames']} frames, {len(data)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
