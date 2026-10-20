#!/usr/bin/env python3
"""Calculate the PWM shares that give every LED on a v1.1 board the same brightness.

Each LED sinks into an STM32 pin through its own series resistor from 3V3.
For every colour this solves the operating point

    VCC = Vf(I) + I * (R_series + R_pin)

against the forward-voltage curve from the LED's datasheet, converts the
current to luminous intensity with the datasheet's relative-intensity curve,
and scales the result so the colour matches the status greens D11-D13, which
run undimmed on 20k. The printed shares go into led_brightness_v1_1 in
software/stm32/src/main.c.

Datasheets (LCSC):
  green  C2297  KENTO KT-0805G    175-430 mcd at 5 mA
  red    C84256 NATIONSTAR NCD0805R1  50-230 mcd at 20 mA, typ 115
  yellow C2296  KENTO KT-0805Y     70-175 mcd at 20 mA
  white  C34499 KENTO KT-0805W    145-360 mcd at 5 mA

Assumptions:
  - Curves are read off the datasheet plots; relative intensity is 1 at 20 mA.
  - The red datasheet has no curves. It is an AlGaInP chip like the yellow,
    with the same typical Vf of 2.0 V at 20 mA, so it uses the yellow curves.
  - Below the plotted range, Vf follows the diode law through the first two
    points, and intensity a power law through the 5 and 10 mA points.
  - Intensity is the geometric middle of each datasheet's min-max bin range.
  - The pin's output resistance is the STM32G070 limit, VOL <= 0.4 V at 8 mA.

Corrections by eye are kept separate from the calculation in CORRECTION, so
the datasheet result stays visible next to what the board actually needed.
"""

import math

VCC = 3.3
R_PIN = 0.4 / 8e-3

# (current mA, forward voltage V)
FORWARD_VOLTAGE = {
    "green": [(1, 2.40), (4.5, 2.60), (9, 2.80), (12, 2.90), (17, 3.00), (25, 3.10), (35, 3.20)],
    "yellow": [(1, 1.90), (4, 1.93), (10, 1.97), (20, 2.00), (35, 2.02)],
    "white": [(1, 2.65), (5, 2.80), (12, 3.00), (25, 3.20), (35, 3.30)],
}
FORWARD_VOLTAGE["red"] = FORWARD_VOLTAGE["yellow"]

# (current mA, intensity relative to 20 mA)
RELATIVE_INTENSITY = {
    "green": [(0, 0.0), (5, 0.40), (10, 0.63), (15, 0.84), (20, 1.00)],
    "yellow": [(0, 0.0), (5, 0.30), (10, 0.57), (15, 0.80), (20, 1.00)],
    "white": [(0, 0.0), (5, 0.33), (10, 0.60), (15, 0.82), (20, 1.00)],
}
RELATIVE_INTENSITY["red"] = RELATIVE_INTENSITY["yellow"]

# (luminous intensity mcd, at test current mA)
DATASHEET_INTENSITY = {
    "green": (math.sqrt(175 * 430), 5),
    "yellow": (math.sqrt(70 * 175), 20),
    "white": (math.sqrt(145 * 360), 5),
    "red": (115, 20),
}

# (colour, series resistor ohm, LEDs)
PROCESS_LEDS = [
    ("green", 1000, "D2 D4 D8 D15 D17 D19"),
    ("red", 330, "D1 D5 D6 D14 D16 D18"),
    ("yellow", 330, "D7 D9"),
    ("white", 100, "D3 D10"),
]
REFERENCE = ("green", 20000, "D11 D12 D13")

# Factor on the calculated share, judged by eye on a v1.1 board. Perceived
# brightness goes roughly with the cube root of intensity, so 0.7 is about
# 10 % dimmer to the eye.
CORRECTION = {
    # The calculated 61 % looked slightly too bright. Red is the least certain
    # colour: its datasheet has no curves (the yellow's are used) and bins
    # intensity from 50 to 230 mcd, against the typical 115 used here.
    "red": 0.7,
}


def interpolate(points, x):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def forward_voltage(colour, current):
    points = FORWARD_VOLTAGE[colour]
    if current >= points[0][0]:
        return interpolate(points, current)
    (i0, v0), (i1, v1) = points[0], points[1]
    per_decade = (v1 - v0) / math.log10(i1 / i0)
    return v0 - per_decade * math.log10(i0 / current)


def relative_intensity(colour, current):
    points = RELATIVE_INTENSITY[colour]
    if current >= 5:
        return interpolate(points, current)
    at_5, at_10 = interpolate(points, 5), interpolate(points, 10)
    exponent = math.log(at_10 / at_5) / math.log(2)
    return at_5 * (current / 5) ** exponent


def operating_current(colour, resistor):
    low, high = 1e-4, 30.0
    for _ in range(100):
        current = (low + high) / 2
        if forward_voltage(colour, current) + current * 1e-3 * (resistor + R_PIN) > VCC:
            high = current
        else:
            low = current
    return current


def intensity(colour, current):
    mcd, at = DATASHEET_INTENSITY[colour]
    return mcd * relative_intensity(colour, current) / relative_intensity(colour, at)


def main():
    reference_current = operating_current(*REFERENCE[:2])
    target = intensity(REFERENCE[0], reference_current)
    print(f"{'colour':7}{'R':>7}{'I':>9}{'Vf':>7}{'Iv':>10}{'calc':>10}{'share':>7}  LEDs")
    for colour, resistor, leds in PROCESS_LEDS:
        current = operating_current(colour, resistor)
        mcd = intensity(colour, current)
        calculated = 100 * target / mcd
        share = min(100, round(calculated * CORRECTION.get(colour, 1.0)))
        print(f"{colour:7}{resistor:>7}{current:>7.2f}mA{forward_voltage(colour, current):>6.2f}V"
              f"{mcd:>7.1f}mcd{calculated:>9.0f}%{share:>7}%  {leds}")
    print(f"{'status':7}{REFERENCE[1]:>7}{reference_current:>7.2f}mA"
          f"{forward_voltage(REFERENCE[0], reference_current):>6.2f}V{target:>7.1f}mcd"
          f"{'ref':>10}{'ref':>7}  {REFERENCE[2]}")


if __name__ == "__main__":
    main()
