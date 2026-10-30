#!/usr/bin/env python3
"""
Packet Anatomy: build Modbus/TCP frames by hand and read the PLC's answers.

Standard library only. Builds every frame with struct.pack, so each field
is visible, and prints it as hex. It sends the two *read* frames (the GST/HPT
read and a read of a register the PLC does not have) to the PLC and prints
the raw answers. It never sends the write frame: the plant is shared.

    python3 frames.py                 # PLC at 172.18.0.3:502
    python3 frames.py --host 172.18.0.3 --tid 0x2a2a --unit 1
"""
import argparse
import socket
import struct


def mbap(tid, unit, pdu):
    """MBAP header (transaction, protocol 0, length = unit + PDU) + unit + PDU."""
    return struct.pack(">HHHB", tid & 0xFFFF, 0, len(pdu) + 1, unit) + pdu


def read_holding(tid, unit, start, quantity):
    return mbap(tid, unit, struct.pack(">BHH", 0x03, start, quantity))


def write_multiple(tid, unit, start, values):
    data = b"".join(struct.pack(">H", v) for v in values)
    return mbap(tid, unit, struct.pack(">BHHB", 0x10, start, len(values), len(data)) + data)


def explain(frame):
    """One line per field of a Modbus/TCP frame (request or response)."""
    tid, proto, length, unit = struct.unpack(">HHHB", frame[:7])
    fc = frame[7]
    lines = [f"  transaction {tid:#06x}  protocol {proto}  length {length}  unit {unit}",
             f"  function    {fc:#04x}" + ("  (exception: top bit set)" if fc & 0x80 else "")]
    if fc & 0x80:
        lines.append(f"  exception code {frame[8]:#04x}")
    return "\n".join(lines)


def ask(host, port, frame):
    with socket.create_connection((host, port), timeout=3) as sock:
        sock.sendall(frame)
        return sock.recv(260)


def hexs(data):
    return data.hex(" ")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="172.18.0.3", help="PLC address (default: 172.18.0.3)")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--tid", type=lambda s: int(s, 0), default=0x2A2A, help="transaction ID")
    parser.add_argument("--unit", type=lambda s: int(s, 0), default=1, help="unit ID")
    args = parser.parse_args()

    # %MWn sits at holding register 1024 + n on OpenPLC.
    gst, stop = 1024 + 100, 1024 + 104      # GST %MW100, HPT %MW102, STOP %MW104, MANUAL %MW106

    read = read_holding(args.tid, args.unit, gst, 3)            # 1124, 1125, 1126
    print("read_request :", hexs(read))
    answer = ask(args.host, args.port, read)
    print("read_response:", hexs(answer))
    print(explain(answer))
    if len(answer) >= 15 and answer[7] == 0x03:
        g, _, h = struct.unpack(">HHH", answer[9:15])
        print(f"  GST {g}  HPT {h}")

    write = write_multiple(args.tid + 1, args.unit, stop, [0, 0, 0])  # 1128, 1129, 1130
    print("write_request:", hexs(write), "(not sent)")

    missing = read_holding(args.tid + 2, args.unit, 9000, 1)
    print("probe        :", hexs(missing))
    answer = ask(args.host, args.port, missing)
    print("exception    :", hexs(answer))
    print(explain(answer))


if __name__ == "__main__":
    main()
