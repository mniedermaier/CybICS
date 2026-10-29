#!/usr/bin/env python3
"""Try a Modbus read allowlist against a capture, without touching the plant.

    python3 read_allowlist.py baseline.pcap allowlist.example.json

The allowlist is a JSON list of rules. A request passes if any rule matches
all of the keys that rule sets:

    {"client": "172.18.0.4", "fc": 3, "first": 1124, "last": 1134}

- client: the source IP address of the request
- fc:     the function code (1 coils, 2 inputs, 3 holding, 4 input registers, ...)
- first, last: the lowest and highest address the request may touch; a
          request for 11 registers from 1124 touches 1124-1134

A key a rule leaves out matches anything, so {"client": "172.18.0.4"} lets
that host do whatever it likes.

The script prints, per TCP connection, how many requests passed and how many
the rule set would flag. It does not print addresses or values: deciding
what is normal is your job, and so is decoding.

Stdlib only; reads classic little-endian pcap files with Ethernet frames.
"""
import json
import struct
import sys
from collections import Counter, OrderedDict


def requests(path):
    """Yield (client ip, client port, function code, first address, last address)."""
    with open(path, "rb") as f:
        data = f.read()
    if struct.unpack("<I", data[:4])[0] != 0xA1B2C3D4:
        sys.exit("only classic little-endian pcap files are supported")
    pos = 24
    while pos + 16 <= len(data):
        _, _, incl, _ = struct.unpack("<IIII", data[pos:pos + 16])
        raw = data[pos + 16:pos + 16 + incl]
        pos += 16 + incl
        if len(raw) < 54 or raw[12:14] != b"\x08\x00" or raw[23] != 6:
            continue
        ihl = (raw[14] & 0x0F) * 4
        total = struct.unpack("!H", raw[16:18])[0]
        t = 14 + ihl
        sport, dport = struct.unpack("!HH", raw[t:t + 4])
        payload = raw[t + (raw[t + 12] >> 4) * 4:14 + total]
        if dport != 502 or len(payload) < 8:
            continue
        client = ".".join(str(b) for b in raw[26:30])
        fc = payload[7]
        first = last = None
        if fc in (1, 2, 3, 4, 5, 6, 15, 16) and len(payload) >= 12:
            first, value = struct.unpack("!HH", payload[8:12])
            count = value if fc in (1, 2, 3, 4, 15, 16) else 1
            last = first + max(count, 1) - 1
        yield client, sport, fc, first, last


def allowed(rule, client, fc, first, last):
    if "client" in rule and rule["client"] != client:
        return False
    if "fc" in rule and rule["fc"] != fc:
        return False
    if "first" in rule and (first is None or first < rule["first"]):
        return False
    if "last" in rule and (last is None or last > rule["last"]):
        return False
    return True


def main(argv):
    if len(argv) != 3:
        print(__doc__.split("\n\n")[1])
        return 2
    with open(argv[2], encoding="utf-8") as f:
        rules = json.load(f)
    passed, flagged = Counter(), Counter()
    order = OrderedDict()
    for client, sport, fc, first, last in requests(argv[1]):
        key = f"{client}:{sport}"
        order.setdefault(key, None)
        if any(allowed(rule, client, fc, first, last) for rule in rules):
            passed[key] += 1
        else:
            flagged[key] += 1
    print(f"{'connection':24} {'passed':>8} {'flagged':>8}")
    for key in order:
        print(f"{key:24} {passed[key]:8} {flagged[key]:8}")
    print(f"{'total':24} {sum(passed.values()):8} {sum(flagged.values()):8}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
