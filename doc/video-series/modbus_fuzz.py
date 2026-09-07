#!/usr/bin/env python3
"""A small Modbus/TCP fuzzer for the training videos.

It walks the Modbus function-code space and sends each function with random
data, probing how the PLC handles unexpected input. It is a demonstration, not
an exhaustive fuzzer, and it deliberately includes the diagnostic functions
(0x08 / 0x2B) that legacy devices rarely validate.

Usage: modbus_fuzz.py [ip] [port]
"""
import random
import socket
import struct
import sys
import time

ip = sys.argv[1] if len(sys.argv) > 1 else "172.18.0.3"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 502
funcs = list(range(0x01, 0x2C))          # reads, writes, diagnostics, encap.

print(f"Fuzzing Modbus/TCP on {ip}:{port} - {len(funcs)} function codes, random payloads")
sent = 0
for tid, fc in enumerate(funcs, 1):
    try:
        s = socket.socket()
        s.settimeout(1.5)
        s.connect((ip, port))
        data = bytes(random.randint(0, 255) for _ in range(4))
        pdu = struct.pack(">B", fc) + data
        mbap = struct.pack(">HHHB", tid, 0, len(pdu) + 1, 1)
        s.send(mbap + pdu)
        try:
            resp = s.recv(256)
        except socket.timeout:
            resp = b""
        s.close()
        tag = "   <-- diagnostic function" if fc in (0x08, 0x2B) else ""
        print(f"  FC 0x{fc:02X}  sent {len(pdu)} bytes, {len(resp)} back{tag}")
        sent += 1
    except Exception as e:
        print(f"  FC 0x{fc:02X}  no response ({type(e).__name__})")
    time.sleep(0.08)
print(f"Done - {sent} malformed frames sent, including diagnostic function 0x08.")
