#!/usr/bin/env python3
"""Generate training/physics_forensics/historian.csv, the "Physics Never Lies" export.

The file is a historian export of the CybICS gas plant for one night: one row
per process cycle with the values the PLC held at that moment (the two tank
pressures, the system and blow-out sensors, the stop flag and the four
coils). Near its end an adversary in the middle between the I/O service and
the PLC rewrites the HPT pressure on its way to the PLC: the PLC, the HMI and
the historian see a calm, slowly rising HPT while the compressor runs without
a break and the real tank climbs far above its working range. The export ends
while the forgery is still running.

Nothing in the file says "attack". The forgery is only visible because the
recorded HPT disobeys the plant's physics: the compressor takes 2 bar out of
the GST for every bar it puts into the HPT, and the system sensor is computed
from the real HPT.

The plant is simulated with a copy of the tick in physical_process_thread()
(software/hwio-virtual/hardwareAbstraction.py, which mirrors the firmware) and
the automatic mode of software/OpenPLC/cybICS.st. tests/test_physics_forensics.py
executes the real hwio code against plant_tick() below with the same random
numbers, checks the PLC thresholds against cybICS.st, regenerates this file
and compares it byte for byte, and derives the answers from the CSV alone.

    python3 software/scripts/generate_physics_historian.py           # rewrite the CSV
    python3 software/scripts/generate_physics_historian.py --key     # print the answer key
    python3 software/scripts/generate_physics_historian.py --check   # compare with the committed file

It sits outside training/ so the landing page and the attack shell, which
both carry a copy of training/, do not ship the scenario or its key.
"""
import argparse
import calendar
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT = os.path.join(ROOT, "training", "physics_forensics", "historian.csv")

# 2026-03-21 01:30:00, the start of the export (plant local time).
START = calendar.timegm((2026, 3, 21, 1, 30, 0, 0, 0, 0))
PLANT_SEED = 0x50F1      # random draws of the plant model (consumption, refill, vent)
STORY_SEED = 0x7C3       # cycle jitter and the forger's rounding

WARMUP = 400             # cycles simulated before the export starts
CYCLE = 1.09             # seconds per process cycle, measured on the virtual stack
JITTER = 0.025

STOP_AT, STOP_CYCLES = 1150, 260     # planned stop (a valve inspection), a decoy
EARLIEST_ATTACK = 2700               # the forgery starts at the first suitable cycle after this
FAKE_CEILING = 88                    # the forger keeps the HPT below the compressor's cut-out (90)
FAKE_RISE = 0.22                     # chance per cycle that the forged value creeps up by 1
GST_FLOOR = 62                       # the export ends before the GST refill (below 60) restarts

COLUMNS = ["time", "gst", "hpt", "sysSen", "boSen", "stop",
           "compressor", "systemValve", "gstSig"]


def plant_tick(state, coils, rng):
    """One cycle of physical_process_thread() in hardwareAbstraction.py.

    state: dict with gst, hpt, boSen; coils: dict with compressor, systemValve,
    gstSig. Returns the new state. The random draws happen in the same order and
    under the same conditions as in the hwio code, so the same seed gives the
    same plant (tests/test_physics_forensics.py runs both side by side).
    """
    gst, hpt, bo = state["gst"], state["hpt"], state["boSen"]
    if coils["compressor"] > 0:
        if hpt < 255 and gst >= 50:
            gst = gst - 2
            hpt = hpt + 1
    else:
        use = rng.randint(0, 2)
        if coils["systemValve"] > 0 and (hpt - use) >= 0:
            hpt = hpt - use
    if coils["gstSig"] > 0 and gst < 251:
        gst = gst + rng.randint(0, 3)
    if hpt > 220 or (bo > 0 and hpt > 200):
        bo = 1
        vent = rng.randint(0, 1)
        if (hpt - vent) >= 0:
            hpt = hpt - vent
    else:
        bo = 0
    # The checks after the tick in the same loop iteration.
    bo = 1 if (hpt > 220 or (bo == 1 and hpt > 200)) else 0
    gst = min(max(gst, 0), 255)
    hpt = min(max(hpt, 0), 255)
    return {"gst": gst, "hpt": hpt, "boSen": bo}


class Plc:
    """The automatic mode of software/OpenPLC/cybICS.st.

    The PLC runs every 50 ms, twenty times per process cycle, on the values it
    holds; its hysteresis settles after one scan, so one scan per cycle gives
    the same outputs.
    """

    def __init__(self):
        self.compressor_state = 0
        self.gst_state = 0
        self.coils = {"compressor": 0, "systemValve": 0, "gstSig": 0}

    def scan(self, gst, hpt, stop):
        if stop < 1:
            if gst < 60 and self.gst_state == 0:
                self.gst_state = 1
            elif gst < 240 and self.gst_state == 1:
                self.gst_state = 1
            else:
                self.gst_state = 0
            if hpt < 60 and self.compressor_state == 0 and gst > 50:
                self.compressor_state = 1
            elif hpt < 90 and self.compressor_state == 1 and gst > 50:
                self.compressor_state = 1
            else:
                self.compressor_state = 0
            valve = 1 if 50 < hpt < 100 else 0
        else:
            self.compressor_state = 0
            self.gst_state = 0
            valve = 0
        self.coils = {"compressor": self.compressor_state, "systemValve": valve,
                      "gstSig": self.gst_state}
        return self.coils


def stamp(seconds):
    whole = int(seconds)
    tenth = int(round((seconds - whole) * 10))
    if tenth == 10:
        whole, tenth = whole + 1, 0
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(whole)) + f".{tenth}"


def build():
    """Return (csv text, answer key)."""
    plant_rng = random.Random(PLANT_SEED)
    story_rng = random.Random(STORY_SEED)
    plc = Plc()
    true = {"gst": 180, "hpt": 75, "boSen": 0}
    shown_hpt = true["hpt"]
    stop = 0
    plc.scan(true["gst"], shown_hpt, stop)

    rows, key = [], {}
    attack_at = end_at = None
    fake = None
    clock = START - WARMUP * CYCLE
    cycle = -WARMUP
    while end_at is None or cycle <= end_at:
        # One process cycle, driven by the coils the PLC set after the last one.
        true = plant_tick(true, plc.coils, plant_rng)
        clock += CYCLE + story_rng.uniform(-JITTER, JITTER)

        stop = 1 if STOP_AT <= cycle < STOP_AT + STOP_CYCLES else 0

        if attack_at is None and cycle >= EARLIEST_ATTACK and rows:
            last = rows[-1]
            if (last["compressor"] == 1 and last["gstSig"] == 0 and last["stop"] == 0
                    and last["gst"] >= 226 and 62 <= last["hpt"] <= 70):
                attack_at = cycle
                end_at = cycle + (last["gst"] - GST_FLOOR) // 2 - 1
                fake = last["hpt"]           # the forger starts by holding the last value
                key["last_honest"] = dict(last)
        elif attack_at is not None:
            if fake < FAKE_CEILING and story_rng.random() < FAKE_RISE:
                fake += 1

        shown_hpt = fake if attack_at is not None else true["hpt"]
        coils = plc.scan(true["gst"], shown_hpt, stop)
        # hwio recomputes the system sensor every 20 ms from the real HPT and
        # the valve the PLC has just set.
        sys_sen = 1 if (50 < true["hpt"] < 100 and coils["systemValve"] > 0) else 0

        if cycle >= 0:
            rows.append({"time": stamp(clock), "gst": true["gst"], "hpt": shown_hpt,
                         "sysSen": sys_sen, "boSen": true["boSen"], "stop": stop,
                         **coils, "true_hpt": true["hpt"]})
        cycle += 1

    first = rows[attack_at]
    sensor_lie = next(r for r in rows[attack_at:] if r["sysSen"] != r["systemValve"])
    key.update({
        "register": "hpt (holding register 1126, %MW102)",
        "first_forged": first["time"],
        "true_hpt_last_row": rows[-1]["true_hpt"],
        "shown_hpt_last_row": rows[-1]["hpt"],
        "first_sysSen_contradiction": sensor_lie["time"],
        "forged_rows": len(rows) - attack_at,
        "rows": len(rows),
        "stop_decoy": f"{rows[STOP_AT]['time']} .. {rows[STOP_AT + STOP_CYCLES - 1]['time']}",
    })
    lines = [",".join(COLUMNS)]
    for r in rows:
        lines.append(",".join(str(r[c]) for c in COLUMNS))
    return "\n".join(lines) + "\n", key


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--key", action="store_true", help="print the answer key")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the committed CSV differs from a fresh build")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()
    text, key = build()
    if args.key:
        for name, value in key.items():
            print(f"{name}: {value}")
        return 0
    if args.check:
        with open(args.output, encoding="utf-8") as f:
            same = f.read() == text
        print("up to date" if same else "differs: regenerate it")
        return 0 if same else 1
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {args.output}: {key['rows']} rows, {len(text)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
