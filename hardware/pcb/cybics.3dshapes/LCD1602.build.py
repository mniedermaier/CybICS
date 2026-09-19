"""Build the 1602 LCD module (DS1) for the CybICS board.

Regenerate with:   python3 -m venv .venv && .venv/bin/pip install cadquery
                   .venv/bin/python LCD1602.build.py

KiCad ships Display.3dshapes/WC1602A.step, but it is a single fused solid, so
the whole module takes one colour: the stock render shows a pale green board,
a grey frame and a blank white screen.  The real part in doc/pics/cybics.png is
dark green with a black bezel and a vivid blue screen carrying pale characters.

The envelope is taken from the stock model, sliced in Z to recover how it is
built up, so this drops in at the same place:
    spacer   z  0.0.. 5.2   68.85 x 25.15   (header and standoff below)
    PCB      z  5.2.. 6.8   80.00 x 36.00
    bezel    z  6.8..15.0   72.00 x 25.13
Pin and mounting-hole positions come from DS1's own footprint.

The screen reads "CybICS" and nothing else.  The firmware also prints a version
and an uptime there, but both would go stale in a file nobody thinks to
regenerate, so only the constant part is modelled.
"""
import pathlib

import cadquery as cq

# ---- envelope, from slicing the stock model ------------------------------
PCB_X0, PCB_X1, PCB_Y0, PCB_Y1 = -8.0, 72.0, -33.5, 2.5
SPC_X0, SPC_X1, SPC_Y0, SPC_Y1 = -2.85, 66.0, -28.15, -3.0
BZL_X0, BZL_X1, BZL_Y0, BZL_Y1 = -4.0, 68.0, -28.0, -2.87
Z_SPC, Z_PCB, Z_BZL, Z_TOP = 0.0, 5.2, 6.8, 15.0

# ---- from DS1's footprint (model Y is the negated footprint Y) ------------
PINS = [(i * 2.54, 0.0) for i in range(16)]
MOUNT = [(-5.4991, 0.0), (-5.4991, -31.0007), (69.4995, -31.0007), (69.5, 0.0)]

# ---- 1602 optical layout (standard for this module) ----------------------
BZL_CX, BZL_CY = (BZL_X0 + BZL_X1) / 2, (BZL_Y0 + BZL_Y1) / 2
VIEW_W, VIEW_H = 64.5, 16.1
CHAR_W, CHAR_H = 2.95, 5.55          # 5 x 8 dots per character
PITCH_X, PITCH_Y = 3.55, 5.95
Z_GLASS = Z_TOP - 0.8


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").workplane(offset=z0)
            .moveTo((x0 + x1) / 2, (y0 + y1) / 2)
            .rect(abs(x1 - x0), abs(y1 - y0)).extrude(z1 - z0))


# ---- body ----------------------------------------------------------------
spacer = box(SPC_X0, SPC_X1, SPC_Y0, SPC_Y1, Z_SPC, Z_PCB)
pcb = box(PCB_X0, PCB_X1, PCB_Y0, PCB_Y1, Z_PCB, Z_BZL)

rings = None
for mx, my in MOUNT:
    pcb = pcb.faces(">Z").workplane(origin=(0, 0, 0)).moveTo(mx, my).hole(2.5)
    r = (cq.Workplane("XY").workplane(offset=Z_BZL)
         .moveTo(mx, my).circle(2.3).circle(1.25).extrude(0.05))
    rings = r if rings is None else rings.union(r)

# Bezel with the viewing window cut through its top face.
win = (BZL_CX - VIEW_W / 2, BZL_CX + VIEW_W / 2,
       BZL_CY - VIEW_H / 2, BZL_CY + VIEW_H / 2)
bezel = box(BZL_X0, BZL_X1, BZL_Y0, BZL_Y1, Z_BZL, Z_TOP)
# Cut the window right through: a recess only in the top face leaves the glass
# buried in solid bezel material, which is what made the first attempt render
# as a black screen.
bezel = bezel.cut(box(win[0], win[1], win[2], win[3], Z_BZL - 0.1, Z_TOP + 0.1))
glass = box(win[0], win[1], win[2], win[3], Z_BZL, Z_GLASS)

# Soldered pin row along the top edge.
pads = None
for px, py in PINS:
    p = (cq.Workplane("XY").workplane(offset=Z_BZL)
         .moveTo(px, py).circle(0.85).extrude(0.9))
    pads = p if pads is None else pads.union(p)

# ---- characters ----------------------------------------------------------
# A 5 x 8 bitmap per glyph, the way an HD44780 actually draws them; a smooth
# outline font would not read as a dot-matrix display.
FONT = {
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110", "00000"),
    "y": ("00000", "00000", "10001", "10001", "10001", "01111", "00001", "01110"),
    "b": ("10000", "10000", "10110", "11001", "10001", "10001", "11110", "00000"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110", "00000"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110", "00000"),
}
TEXT = "CybICS"
TEXT_X0 = BZL_CX - (16 * PITCH_X - (PITCH_X - CHAR_W)) / 2
TEXT_Y0 = BZL_CY + (2 * PITCH_Y - (PITCH_Y - CHAR_H)) / 2
DOT_W, DOT_H = CHAR_W / 5, CHAR_H / 8

chars = None
for n, ch in enumerate(TEXT):
    bitmap = FONT.get(ch)
    if bitmap is None:
        continue
    cx0 = TEXT_X0 + n * PITCH_X
    for row, bits in enumerate(bitmap):
        for col, bit in enumerate(bits):
            if bit != "1":
                continue
            x0 = cx0 + col * DOT_W
            y1 = TEXT_Y0 - row * DOT_H
            d = box(x0 + 0.04, x0 + DOT_W - 0.04, y1 - DOT_H + 0.04, y1 - 0.04,
                    Z_GLASS, Z_GLASS + 0.06)
            chars = d if chars is None else chars.union(d)

# ---- silkscreen ----------------------------------------------------------
# Pin names under the header and the 1 / 16 end markers, as printed on the part.
NAMES = ["VSS", "VDD", "V0", "RS", "RW", "E", "D0", "D1", "D2", "D3",
         "D4", "D5", "D6", "D7", "A", "K"]


def label(txt, cx, cy, size):
    return (cq.Workplane("XY").workplane(offset=Z_BZL)
            .center(cx, cy).text(txt, size, 0.04, halign="center", valign="center"))


silk = None
for n, nm in enumerate(NAMES):
    t = label(nm, n * 2.54, -1.9, 0.95)
    silk = t if silk is None else silk.union(t)
for txt, cx in (("1", -2.2), ("16", 40.3)):
    silk = silk.union(label(txt, cx, 0.0, 1.2))

# The bezel carries a shallow inner lip around the window, clearly visible in
# the photograph as a step between the frame and the glass.
lip = (box(win[0] - 1.2, win[1] + 1.2, win[2] - 1.2, win[3] + 1.2, Z_TOP - 0.35, Z_TOP)
       .cut(box(win[0], win[1], win[2], win[3], Z_TOP - 0.45, Z_TOP + 0.1)))

asm = (cq.Assembly()
       .add(spacer, name="standoff",  color=cq.Color(0.10, 0.10, 0.11))
       .add(pcb,    name="pcb",       color=cq.Color(0.045, 0.215, 0.105))
       .add(rings,  name="hole_pads", color=cq.Color(0.72, 0.57, 0.21))
       .add(pads,   name="pin_pads",  color=cq.Color(0.76, 0.63, 0.26))
       .add(bezel,  name="bezel",     color=cq.Color(0.085, 0.085, 0.095))
       .add(glass,  name="lcd",       color=cq.Color(0.055, 0.30, 0.90))
       .add(chars,  name="characters", color=cq.Color(0.80, 0.93, 1.00))
       .add(silk,   name="silkscreen", color=cq.Color(0.86, 0.86, 0.84))
       .add(lip,    name="bezel_lip",  color=cq.Color(0.135, 0.135, 0.145)))

out = str(pathlib.Path(__file__).with_name("LCD1602.step"))
asm.export(out)

whole = spacer
for p in (pcb, rings, pads, bezel, glass, chars, silk, lip):
    whole = whole.union(p)
b = whole.val().BoundingBox()
print(f"  wrote {out}")
print(f"  bbox X {b.xmin:7.2f}..{b.xmax:7.2f}  Y {b.ymin:7.2f}..{b.ymax:7.2f}  Z {b.zmin:6.2f}..{b.zmax:6.2f}")
print(f"  stock model envelope was X   -8.00..  72.00  Y  -33.50..   2.50  Z   0.00.. 15.00")
