#!/usr/bin/env python3
"""
Rebuild a PLC's register map from the outside, with reads only.

Samples a block of holding registers and coils for a while, classifies every
word by how it behaves (always 0, constant, flag, analog value) and, for each
flag, prints the analog values at the moment it switched. Then it translates
every word that is not always 0 into the other address spaces of an OpenPLC
controller: the %MW variable, the 1-based number an HMI shows and the S7comm
data block and byte offset.

Nothing is written. Works with pymodbus 3.5 and later.

    python3 map_registers.py                       # 172.18.0.3, 600 s
    python3 map_registers.py --seconds 60 --csv /tmp/hr.csv
"""
import argparse
import csv
import sys
import time

from pymodbus.client import ModbusTcpClient

OPENPLC_MW_BASE = 1024     # OpenPLC: holding registers 1024-2047 are %MW0-%MW1023
S7_MW_DB = 1002            # OpenPLC's S7comm server shows %MW as DB1002, 2 bytes a word
BLOCK = 125                # most registers one Modbus read may ask for
MAX_SWITCHES = 24          # switches printed per flag; the rest are counted


def read_words(client, start, count):
    words = []
    for offset in range(0, count, BLOCK):
        n = min(BLOCK, count - offset)
        reply = client.read_holding_registers(start + offset, count=n)
        if reply.isError():
            raise RuntimeError(f"read of {n} registers at {start + offset} failed: {reply}")
        words.extend(reply.registers[:n])
    return words


def read_coils(client, count):
    reply = client.read_coils(0, count=count)
    if reply.isError():
        raise RuntimeError(f"read of coils failed: {reply}")
    return [int(bit) for bit in reply.bits[:count]]


def classify(values):
    seen = set(values)
    if seen == {0}:
        return "zero"
    if len(seen) == 1:
        return "constant"
    if seen <= {0, 1}:
        return "flag"
    return "analog"


def translate(address):
    """Other names for holding register `address` on an OpenPLC controller."""
    if address < OPENPLC_MW_BASE or address >= 2 * OPENPLC_MW_BASE:
        return "", ""
    word = address - OPENPLC_MW_BASE
    return f"%MW{word}", f"DB{S7_MW_DB}.DBW{2 * word}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--host", default="172.18.0.3")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--start", type=int, default=1024, help="first holding register (wire address)")
    parser.add_argument("--count", type=int, default=256, help="number of holding registers")
    parser.add_argument("--coils", type=int, default=8, help="number of coils from 0")
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--csv", help="also write every sample to this file")
    args = parser.parse_args()

    client = ModbusTcpClient(args.host, port=args.port, timeout=3)
    if not client.connect():
        sys.exit(f"cannot connect to {args.host}:{args.port}")

    hr_names = [f"hr{args.start + i}" for i in range(args.count)]
    coil_names = [f"coil{i}" for i in range(args.coils)]
    samples = []
    print(f"Sampling {args.count} holding registers from {args.start} and coils 0-{args.coils - 1} "
          f"every {args.interval} s for {args.seconds:.0f} s (reads only) ...", flush=True)
    end = time.time() + args.seconds
    try:
        while time.time() < end:
            t = time.time()
            samples.append([round(t, 2)] + read_words(client, args.start, args.count)
                           + read_coils(client, args.coils))
            time.sleep(max(0.0, args.interval - (time.time() - t)))
    except KeyboardInterrupt:
        print("stopped early", file=sys.stderr)
    finally:
        client.close()
    if len(samples) < 2:
        sys.exit("not enough samples")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time"] + hr_names + coil_names)
            writer.writerows(samples)
        print(f"wrote {len(samples)} samples to {args.csv}")

    columns = list(zip(*samples))[1:]
    names = hr_names + coil_names
    kinds = {name: classify(col) for name, col in zip(names, columns)}
    series = dict(zip(names, columns))
    analog = [n for n in hr_names if kinds[n] == "analog"]

    print(f"\n{len(samples)} samples. Holding registers that are not always 0:")
    print(f"{'wire':>6} {'class':9} {'min':>6} {'max':>6} {'last':>6}  {'1-based':>7}  {'variable':9} S7comm")
    for i, name in enumerate(hr_names):
        if kinds[name] == "zero":
            continue
        address = args.start + i
        col = series[name]
        variable, s7 = translate(address)
        print(f"{address:>6} {kinds[name]:9} {min(col):>6} {max(col):>6} {col[-1]:>6}  "
              f"{address + 1:>7}  {variable:9} {s7}")
    zeros = sum(1 for n in hr_names if kinds[n] == "zero")
    print(f"({zeros} holding registers stayed 0 the whole time)")

    print("\nCoils:")
    for i, name in enumerate(coil_names):
        col = series[name]
        print(f"{i:>6} {kinds[name]:9} on in {100 * sum(col) / len(col):5.1f} % of samples")

    print("\nFlags: the analog registers at every switch")
    header = "  ".join(f"{n[2:] if n.startswith('hr') else n:>6}" for n in analog)
    for name in hr_names + coil_names:
        if kinds[name] != "flag":
            continue
        col = series[name]
        print(f"\n{name}  (analog columns: {header})")
        switches = [k for k in range(1, len(col)) if col[k] != col[k - 1]]
        for k in switches[:MAX_SWITCHES]:
            row = "  ".join(f"{series[a][k]:>6}" for a in analog)
            print(f"  t={samples[k][0] - samples[0][0]:7.1f} s  {col[k - 1]} -> {col[k]}   {row}")
        if len(switches) > MAX_SWITCHES:
            span = samples[-1][0] - samples[0][0]
            print(f"  ... {len(switches)} switches in {span:.0f} s, about one every "
                  f"{span / len(switches):.1f} s")


if __name__ == "__main__":
    main()
