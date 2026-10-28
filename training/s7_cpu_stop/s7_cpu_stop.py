#!/usr/bin/env python3
"""
Stop Means Stop? -- send OpenPLC an S7comm CPU STOP and check what it does.

    python3 s7_cpu_stop.py            mode from SZL 0x0424 and get_cpu_state()
    python3 s7_cpu_stop.py stop       PLC STOP (S7 function 0x29), then the mode
    python3 s7_cpu_stop.py watch      heartbeat, GST and HPT over Modbus, 5 s
    python3 s7_cpu_stop.py start      warm restart (PLC Control, P_PROGRAM)

Environment: PLC_IP (default 172.18.0.3).
"""
import os
import sys
import time

import snap7
from pymodbus.client import ModbusTcpClient

PLC_IP = os.environ.get("PLC_IP", "172.18.0.3")
MODES = {0x08: "RUN", 0x04: "STOP", 0x00: "unknown"}


def cpu_mode(plc):
    """The mode byte of SZL 0x0424, read from the PLC."""
    szl = plc.read_szl(0x0424, 0)
    raw = bytes(szl.Data[:szl.Header.LengthDR])
    # python-snap7 3.3.0 leaves the list header (record length, record count)
    # in front of the record; other releases strip it.
    if len(raw) >= 8 and int.from_bytes(raw[0:2], "big") == len(raw) - 4:
        raw = raw[4:]
    return raw[3]


def library_state(plc):
    """What python-snap7's get_cpu_state() claims (3.3.0 never asks the PLC)."""
    for _ in range(2):
        try:
            return plc.get_cpu_state()
        except Exception as e:     # 3.3.0 sends a malformed read; see the README
            error = e
    return f"failed ({error})"


def show(plc):
    print(f"get_cpu_state()      : {library_state(plc)}")
    mode = cpu_mode(plc)
    print(f"SZL 0x0424 mode byte : 0x{mode:02X} ({MODES.get(mode, '?')})")


def watch(seconds=5.0):
    mb = ModbusTcpClient(PLC_IP, port=502, timeout=2)
    if not mb.connect():
        sys.exit(f"cannot reach Modbus on {PLC_IP}:502")
    try:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            heartbeat = mb.read_coils(0, count=1).bits[0]
            gst, _, hpt = mb.read_holding_registers(1124, count=3).registers
            print(f"heartbeat={int(heartbeat)}  gst={gst:3d}  hpt={hpt:3d}")
            time.sleep(0.5)
    finally:
        mb.close()


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "show"
    if action == "watch":
        watch()
        return
    plc = snap7.client.Client()
    plc.connect(PLC_IP, 0, 1)
    try:
        if action == "stop":
            print(f"plc_stop()           : {plc.plc_stop()}")
        elif action == "start":
            print(f"plc_hot_start()      : {plc.plc_hot_start()}")
        elif action != "show":
            sys.exit(__doc__)
        show(plc)
    finally:
        plc.disconnect()


if __name__ == "__main__":
    main()
