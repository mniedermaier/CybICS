"""Build a Raspberry Pi Zero 3D model for the CybICS carrier board.

Regenerate with:   python3 -m venv .venv && .venv/bin/pip install cadquery
                   .venv/bin/python Raspberry_Pi_Zero.build.py


Dimensions come from the official mechanical drawing
(datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-mechanical-drawing.pdf):
65 x 30 mm, four 2.75 mm holes 3.5 mm in from each edge (58 x 23 mm apart),
connector centres 12.4, 41.4 and 54 mm along the long axis.  The drawing does
not give a PCB thickness; 1.4 mm is an assumption.

Coordinates are KiCad 3D model space for J1's footprint: origin at pin 1,
X as in the footprint, Y negated, Z up from the carrier's top surface.
"""
import pathlib

import cadquery as cq

# --- from the mechanical drawing -------------------------------------------
LEN, WID, THK = 65.0, 30.0, 1.4          # THK assumed, not in the drawing
CORNER_R, HOLE_D, EDGE = 3.0, 2.75, 3.5

# --- from J1's footprint, in model space (footprint Y negated) --------------
HOLES = [(-1.27, -4.87), (-1.27, 53.13), (21.73, -4.87), (21.73, 53.13)]
X0, X1 = -4.77, 25.23                     # 30 mm across, header edge at X0
Y0, Y1 = -8.37, 56.63                     # 65 mm long, microSD end at Y1
assert abs((X1 - X0) - WID) < 1e-9 and abs((Y1 - Y0) - LEN) < 1e-9

# --- origin ----------------------------------------------------------------
# z = 0 is the Pi's PCB lower face, which is its component side: the footprint
# is "FaceDown", so the Pi is mounted upside down and its parts point at the
# carrier.  The mounting height lives in the footprint's model offset, not
# here, so it can be adjusted without rebuilding this file.
Z_PCB = 0.0

pcb = (cq.Workplane("XY").workplane(offset=Z_PCB)
       .moveTo((X0 + X1) / 2, (Y0 + Y1) / 2)
       .rect(WID, LEN).extrude(THK)
       .edges("|Z").fillet(CORNER_R))
for hx, hy in HOLES:
    pcb = (pcb.faces(">Z").workplane(origin=(0, 0, 0))
           .moveTo(hx, hy).hole(HOLE_D))

# Components sit on the carrier-facing side: the footprint is "FaceDown", so
# the Pi is mounted upside down and its parts hang into the 11 mm gap.
# These are representative envelopes, not exact part geometry.
def below(x, y, w, l, h):
    return (cq.Workplane("XY").workplane(offset=Z_PCB - h)
            .moveTo(x, y).rect(w, l).extrude(h))

soc = below((X0 + X1) / 2 + 2.0, (Y0 + Y1) / 2 - 4.0, 12.0, 12.0, 1.2)

# Edge connectors, centres 12.4 / 41.4 / 54 mm from the microSD end, standing
# proud of the long edge opposite the GPIO header (matches the footprint's
# F.Fab overhang on that side).
conns = None
for dist, w, h in ((12.4, 11.2, 3.0), (41.4, 7.6, 2.6), (54.0, 7.6, 2.6)):
    c = below(X1 - 0.45, Y1 - dist, 5.5, w, h)   # protrudes to the F.Fab edge, 27.53
    conns = c if conns is None else conns.union(c)

# microSD holder at the short edge, plus the card protruding past it.
sd = below(X0 + 9.0, Y1 - 4.3, 12.0, 11.0, 1.4)   # protrudes to the F.Fab edge, 57.83

# Export as an assembly so each part carries its own STEP AP214 colour;
# a plain solid export would render as an untextured white slab.
asm = (cq.Assembly()
       .add(pcb,   name="pcb",        color=cq.Color(0.05, 0.35, 0.15))
       .add(soc,   name="soc",        color=cq.Color(0.12, 0.12, 0.12))
       .add(conns, name="connectors", color=cq.Color(0.75, 0.75, 0.78))
       .add(sd,    name="microsd",    color=cq.Color(0.75, 0.75, 0.78)))

out = str(pathlib.Path(__file__).with_suffix("").with_name("Raspberry_Pi_Zero.step"))
asm.save(out)
model = pcb.union(soc).union(conns).union(sd)
b = model.val().BoundingBox()
print(f"  wrote {out}")
print(f"  bbox X {b.xmin:7.2f}..{b.xmax:7.2f}  Y {b.ymin:7.2f}..{b.ymax:7.2f}  Z {b.zmin:6.2f}..{b.zmax:6.2f}")
print(f"  PCB plane z {Z_PCB:.2f}..{Z_PCB + THK:.2f}   overall height {b.zmax - b.zmin:.2f} mm")
