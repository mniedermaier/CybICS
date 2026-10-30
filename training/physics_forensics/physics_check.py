#!/usr/bin/env python3
"""Check a CybICS historian export against the plant's physics.

Reads a CSV with the columns time, gst, hpt, sysSen, boSen, stop, compressor,
systemValve, gstSig (one row per process cycle, the coils as the PLC set them
from that row's values) and reports every row the plant cannot have produced.

The rules come from the plant model (physical_process_thread in
software/hwio-virtual/hardwareAbstraction.py, thread_physical in the
firmware). Between one row and the next, driven by the coils of the first:

  compressor on   the compressor moves gas: GST -2 bar, HPT +1 bar
                  (the GST refill may add 0..3 bar on top while gstSig is on)
  compressor off  the HPT can only fall, by 0..2 bar, and only while the
                  system valve is open; with the valve closed it stays put
  gstSig off      nothing adds gas to the GST
  blow-out valve  vents 0..1 bar from the HPT while boSen is on

and within one row: the system sensor (sysSen) is computed by the I/O
service from the real HPT and the valve, so in automatic mode it must equal
systemValve whenever the HPT is in the valve's band.

    python3 physics_check.py historian.csv
    python3 physics_check.py historian.csv --all     # list every violation

Only the Python standard library is needed.
"""
import argparse
import csv
import sys

INT_COLUMNS = ("gst", "hpt", "sysSen", "boSen", "stop", "compressor", "systemValve", "gstSig")


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in INT_COLUMNS:
            r[c] = int(r[c])
    return rows


def hpt_range(prev):
    """The HPT values the plant can reach from row prev in one cycle."""
    hpt = prev["hpt"]
    if prev["compressor"]:
        low = high = hpt + 1 if (hpt < 255 and prev["gst"] >= 50) else hpt
    elif prev["systemValve"]:
        low, high = max(hpt - 2, 0), hpt
    else:
        low = high = hpt
    if prev["boSen"] or high > 220:
        low = max(low - 1, 0)
    return low, high


def gst_range(prev):
    """The GST values the plant can reach from row prev in one cycle."""
    gst = prev["gst"]
    if prev["compressor"] and prev["hpt"] < 255 and gst >= 50:
        gst -= 2
    if prev["gstSig"] and gst < 251:
        return gst, min(gst + 3, 255)
    return gst, gst


def violations(rows):
    """Yield (row index, rule, detail) for every row the physics forbids."""
    for i in range(1, len(rows)):
        prev, row = rows[i - 1], rows[i]
        low, high = hpt_range(prev)
        if not low <= row["hpt"] <= high:
            yield i, "hpt-step", (f"hpt {prev['hpt']} -> {row['hpt']}, physics allows "
                                  f"{low}..{high} (compressor {prev['compressor']}, "
                                  f"valve {prev['systemValve']})")
        low, high = gst_range(prev)
        if not low <= row["gst"] <= high:
            yield i, "gst-step", f"gst {prev['gst']} -> {row['gst']}, physics allows {low}..{high}"
    for i, row in enumerate(rows):
        if row["stop"] == 0 and 50 < row["hpt"] < 100 and row["sysSen"] != row["systemValve"]:
            yield i, "sysSen", (f"hpt {row['hpt']} with the valve open, but sysSen is "
                                f"{row['sysSen']}: the real HPT is outside 51..99")


def main():
    parser = argparse.ArgumentParser(description="Check a historian export against the plant's physics.")
    parser.add_argument("csv", help="the historian export (historian.csv)")
    parser.add_argument("--all", action="store_true", help="list every violation, not only the first per rule")
    args = parser.parse_args()
    rows = load(args.csv)

    found = sorted(violations(rows))
    if not found:
        print(f"{len(rows)} rows, no violation: every row is something the plant can do.")
        return 0

    print(f"{len(rows)} rows, {len(found)} violations\n")
    seen = set()
    for i, rule, detail in found:
        if args.all or rule not in seen:
            print(f"  line {i + 2:5}  {rows[i]['time']}  {rule:9} {detail}")
        seen.add(rule)
    if not args.all:
        print("\n  (first violation per rule; --all lists them all)")

    first = found[0][0]
    honest = rows[first - 1]
    print(f"\nFirst row the plant cannot have produced: {rows[first]['time']} "
          f"(file line {first + 2}). Rows before it are consistent.")

    # Mass balance from the last trustworthy row to the end of the file: while
    # the GST refill is off, every 2 bar that left the GST are 1 bar in the HPT.
    tail = rows[first - 1:]
    if all(r["gstSig"] == 0 and r["boSen"] == 0 for r in tail) and \
            all(r["compressor"] == 1 or r["systemValve"] == 0 for r in tail[:-1]):
        moved = honest["gst"] - rows[-1]["gst"]
        cycles = sum(1 for r in tail[:-1] if r["compressor"] == 1)
        print(f"\nMass balance from the last consistent row ({honest['time']}, "
              f"HPT {honest['hpt']}, GST {honest['gst']}) to the last row:")
        print(f"  GST fell by {moved} bar, the compressor ran {cycles} cycles")
        print(f"  real HPT in the last row = {honest['hpt']} + {moved} / 2 = "
              f"{honest['hpt'] + moved // 2} bar (the file shows {rows[-1]['hpt']})")
    else:
        print("\nThe refill, the blow-out valve or consumption overlaps the tail of the file;"
              " reconstruct the HPT cycle by cycle instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
