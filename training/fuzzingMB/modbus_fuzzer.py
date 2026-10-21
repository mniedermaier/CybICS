#!/usr/bin/env python3
"""
A small, non-interactive Modbus/TCP fuzzer for the CybICS fuzzing challenge.

It sends Modbus/TCP requests built from random and boundary values to a
Modbus server and reports how the server answers: a normal response, a Modbus
exception, a dropped connection or no answer at all.  Three kinds of test cases
are mixed:

  valid-shaped   a known function code with random addresses, counts, values
  malformed      a known function code with a truncated or overlong body
  header         a broken MBAP header (wrong length, protocol id, unit id)

Function codes 0x08 (Diagnostics) and 0x2B (Read Device Identification) are
part of the default set; the IDS treats both as diagnostic traffic.

Examples:
  python3 modbus_fuzzer.py 172.18.0.3
  python3 modbus_fuzzer.py 172.18.0.3 --count 500 --rate 20 --fc 3,6,8
"""
import argparse
import random
import socket
import struct
import sys
import time
from collections import Counter

DEFAULT_FCS = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x0F, 0x10,
               0x11, 0x16, 0x17, 0x2B]
BOUNDARY = [0x0000, 0x0001, 0x007D, 0x007E, 0x07D0, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF]


def word(rng):
    return rng.choice(BOUNDARY) if rng.random() < 0.4 else rng.randrange(0x10000)


def pdu_for(fc, rng):
    """A request PDU for fc whose fields are random or boundary values."""
    if fc in (0x01, 0x02, 0x03, 0x04, 0x05, 0x06):
        body = struct.pack(">HH", word(rng), word(rng))
    elif fc == 0x07 or fc == 0x11:
        body = b""
    elif fc == 0x08:
        # Diagnostics: sub-function, then data.
        sub = rng.choice([0x0000, 0x0001, 0x0002, 0x0004, 0x000A, 0x000B, word(rng)])
        body = struct.pack(">HH", sub, word(rng))
    elif fc in (0x0F, 0x10):
        count = rng.choice([0, 1, 2, 10, 123, word(rng)])
        data = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 40)))
        body = struct.pack(">HHB", word(rng), count & 0xFFFF, len(data) & 0xFF) + data
    elif fc == 0x16:
        body = struct.pack(">HHH", word(rng), word(rng), word(rng))
    elif fc == 0x17:
        data = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 20)))
        body = struct.pack(">HHHHB", word(rng), word(rng), word(rng), word(rng),
                           len(data)) + data
    elif fc == 0x2B:
        # Encapsulated interface: MEI type 0x0E (device id), read code, object id.
        body = bytes([rng.choice([0x0E, 0x0D, rng.randrange(256)]),
                      rng.choice([1, 2, 3, 4, rng.randrange(256)]),
                      rng.randrange(256)])
    else:
        body = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 12)))
    return bytes([fc]) + body


def build_case(fcs, rng, tid):
    """Return (kind, fc, adu) for one test case."""
    fc = rng.choice(fcs)
    pdu = pdu_for(fc, rng)
    unit = 1
    proto = 0
    kind = rng.choices(["valid-shaped", "malformed", "header"], [6, 3, 1])[0]
    length = len(pdu) + 1
    if kind == "malformed":
        if rng.random() < 0.5 and len(pdu) > 1:
            pdu = pdu[:rng.randrange(1, len(pdu))]
        else:
            pdu += bytes(rng.randrange(256) for _ in range(rng.randrange(1, 64)))
        length = len(pdu) + 1
    elif kind == "header":
        choice = rng.randrange(3)
        if choice == 0:
            length = rng.choice([0, 1, 2, 255, 260, 0xFFFF])
        elif choice == 1:
            proto = rng.randrange(1, 0x10000)
        else:
            unit = rng.randrange(256)
    adu = struct.pack(">HHHB", tid, proto, length, unit) + pdu
    return kind, fc, adu


def classify(reply, fc):
    if not reply:
        return "closed"
    if len(reply) < 8:
        return "short reply"
    rfc = reply[7]
    if rfc == fc | 0x80:
        code = reply[8] if len(reply) > 8 else None
        return f"exception {code:#04x}" if code is not None else "exception"
    if rfc == fc:
        return "response"
    return f"reply fc {rfc:#04x}"


def main():
    parser = argparse.ArgumentParser(description="Non-interactive Modbus/TCP fuzzer")
    parser.add_argument("host", help="Modbus server, e.g. 172.18.0.3 (OpenPLC)")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--count", type=int, default=300, help="test cases to send (default 300)")
    parser.add_argument("--rate", type=float, default=20.0,
                        help="test cases per second (default 20)")
    parser.add_argument("--fc", help="comma-separated function codes, decimal or 0x.. "
                                     "(default: the common ones plus 0x08 and 0x2B)")
    parser.add_argument("--seed", type=int, help="random seed, to repeat a run")
    parser.add_argument("--timeout", type=float, default=1.0, help="reply timeout in seconds")
    parser.add_argument("-v", "--verbose", action="store_true", help="print every test case")
    args = parser.parse_args()

    fcs = [int(x, 0) for x in args.fc.split(",")] if args.fc else DEFAULT_FCS
    seed = args.seed if args.seed is not None else random.randrange(1 << 32)
    rng = random.Random(seed)
    print(f"Fuzzing {args.host}:{args.port} with {args.count} cases, seed {seed}")
    print(f"Function codes: {', '.join(f'{fc:#04x}' for fc in fcs)}")

    results = Counter()
    sock = None
    delay = 1.0 / args.rate if args.rate > 0 else 0
    try:
        for i in range(args.count):
            kind, fc, adu = build_case(fcs, rng, i & 0xFFFF)
            if sock is None:
                try:
                    sock = socket.create_connection((args.host, args.port), timeout=args.timeout)
                except OSError as e:
                    print(f"[!] case {i}: cannot connect: {e}")
                    results["connect failed"] += 1
                    time.sleep(1)
                    continue
            try:
                sock.sendall(adu)
                reply = sock.recv(512)
                outcome = classify(reply, fc)
            except socket.timeout:
                outcome = "no answer"
            except OSError:
                outcome = "closed"
            if outcome in ("closed", "no answer"):
                # The server dropped or ignored the frame; start fresh.
                sock.close()
                sock = None
            results[outcome] += 1
            if args.verbose or outcome == "closed":
                print(f"  #{i:<5} {kind:12} fc {fc:#04x} {adu.hex()[:48]:48} -> {outcome}")
            if delay:
                time.sleep(delay)
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        if sock:
            sock.close()

    print("\nOutcomes:")
    for outcome, n in results.most_common():
        print(f"  {outcome:16} {n}")
    # Is the server still answering a plain read?
    try:
        with socket.create_connection((args.host, args.port), timeout=2) as s:
            s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, 0x03, 0, 1))
            alive = classify(s.recv(512), 0x03) == "response"
    except OSError:
        alive = False
    print(f"\nServer still answers a normal read: {'yes' if alive else 'NO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
