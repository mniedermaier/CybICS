"""Build a Raspberry Pi Zero 2 W 3D model for the CybICS carrier board.

Regenerate with:   python3 -m venv .venv && .venv/bin/pip install cadquery
                   .venv/bin/python Raspberry_Pi_Zero.build.py

Outline, mounting holes and the three edge-connector positions come from the
official mechanical drawing (65 x 30 mm, four 2.75 mm holes 3.5 mm in from each
edge, connector centres 12.4 / 41.4 / 54 mm).  Everything else is measured off
doc/pics/cybics.png, the photograph of the assembled board -- component
positions there agree with the drawing's connector centres to about 0.4 mm,
which is what fixes the scale and origin.

Components sit on the TOP face: the Pi is mounted component side up, with a
2x20 socket on its underside that plugs onto the carrier's male header.  That
socket is deliberately not modelled -- the carrier's own header model already
occupies the same volume, so a second solid there would only produce a
spurious clash.

Local coordinates are the intuitive ones and converted at the end:
    u  0..65  along the long axis, 0 at the microSD end
    v  0..30  across, 0 at the GPIO header edge
    w  height above the PCB's top face
The PCB thickness of 1.4 mm is an assumption; the drawing does not give one.
"""
import pathlib

import cadquery as cq

LEN, WID, THK = 65.0, 30.0, 1.4
CORNER_R, HOLE_D, EDGE = 3.0, 2.75, 3.5

# u,v -> KiCad 3D model space for J1's footprint (origin at pin 1, Y negated).
MX, MY = -4.77, -8.37
x = lambda v: v + MX
y = lambda u: u + MY


def blk(u0, u1, v0, v1, w0, w1):
    """An axis-aligned block given in Pi coordinates."""
    return (cq.Workplane("XY").workplane(offset=THK + w0)
            .moveTo((x(v0) + x(v1)) / 2, (y(u0) + y(u1)) / 2)
            .rect(abs(v1 - v0), abs(u1 - u0))
            .extrude(w1 - w0))


# ---------------------------------------------------------------- the PCB
pcb = (cq.Workplane("XY")
       .moveTo(x(WID / 2), y(LEN / 2)).rect(WID, LEN).extrude(THK)
       .edges("|Z").fillet(CORNER_R))
for u in (EDGE, LEN - EDGE):
    for v in (EDGE, WID - EDGE):
        pcb = pcb.faces(">Z").workplane(origin=(0, 0, 0)).moveTo(x(v), y(u)).hole(HOLE_D)

# ------------------------------------------------- GPIO pins, from the pads
# Footprint pads are at local x 0 / -2.54 and local y 0 .. -48.26, which is
# u 8.37 .. 56.63 and v 2.23 / 4.77.  Soldered socket tails, seen from above.
pins = None
for col in range(20):
    for v in (2.23, 4.77):
        p = blk(8.37 + col * 2.54 - 0.45, 8.37 + col * 2.54 + 0.45, v - 0.45, v + 0.45, 0, 0.9)
        pins = p if pins is None else pins.union(p)

# ------------------------------------------------------- top-side components
soc     = blk(19.5, 35.5, 8.0, 23.0, 0, 1.1)      # RP3A0 SiP, raspberry logo
shield  = blk(38.0, 48.5, 11.0, 23.5, 0, 1.0)     # wireless module can
pmic    = blk(50.5, 54.0, 12.0, 16.0, 0, 0.9)
ic2     = blk(55.5, 58.5, 14.5, 18.5, 0, 0.9)
sd_slot = blk(1.0, 14.0, 7.5, 19.5, 0, 1.4)       # microSD holder
sd_card = blk(-2.1, 1.0, 9.0, 20.0, 0.2, 1.2)     # card, protrudes past the edge
csi     = blk(62.0, 66.2, 8.0, 23.0, 0, 2.8)      # camera FFC, over the edge

# Edge connectors, centres from the drawing, protruding 2.3 mm past v = 30.
# Each is a shell with a recess in the outward face, which is what makes them
# read as sockets rather than as blank blocks.
def shell(uc, half_u, v0, h, mouth_u, mouth_h):
    body = blk(uc - half_u, uc + half_u, v0, 32.3, 0, h)
    # cut slightly proud so the boolean is clean, but show a body that stops
    # exactly at the F.Fab edge so the model's envelope stays truthful
    cutter = blk(uc - mouth_u, uc + mouth_u, 32.3 - 1.6, 32.4,
                 (h - mouth_h) / 2, (h + mouth_h) / 2)
    shown = blk(uc - mouth_u, uc + mouth_u, 32.3 - 1.6, 32.3,
                (h - mouth_h) / 2, (h + mouth_h) / 2)
    return body.cut(cutter), shown

hdmi, hdmi_m = shell(12.4, 5.6, 26.0, 3.2, 4.5, 1.7)     # mini-HDMI
usb,  usb_m  = shell(41.4, 3.8, 26.6, 2.6, 3.0, 1.3)     # micro-USB, data
pwr,  pwr_m  = shell(54.0, 3.8, 26.6, 2.6, 3.0, 1.3)     # micro-USB, power
mouths = hdmi_m.union(usb_m).union(pwr_m)

# The camera FFC slot reads as a dark line along the connector.
csi_slot = blk(63.2, 63.8, 8.4, 22.6, 1.4, 2.9)
csi = csi.cut(csi_slot)

small = None
for u0, v0 in ((17.0, 24.5), (36.0, 6.5), (44.0, 6.5), (50.0, 7.0),
               (59.0, 8.0), (59.0, 21.0), (23.0, 25.5), (30.0, 25.0),
               (16.5, 20.5), (18.5, 4.5), (33.0, 25.5), (37.5, 24.0),
               (47.0, 7.0), (52.5, 8.5), (56.5, 9.5), (57.0, 21.5),
               (26.0, 6.5), (60.5, 12.5), (60.5, 17.0), (45.5, 25.0)):
    s = blk(u0, u0 + 2.0, v0, v0 + 1.2, 0, 0.6)
    small = s if small is None else small.union(s)

GREEN, BLACK, SILVER = (0.04, 0.29, 0.12), (0.09, 0.09, 0.09), (0.52, 0.53, 0.56)
asm = (cq.Assembly()
       .add(pcb,     name="pcb",       color=cq.Color(*GREEN))
       .add(pins,    name="gpio",      color=cq.Color(0.83, 0.69, 0.22))
       .add(soc,     name="soc",       color=cq.Color(*BLACK))
       .add(shield,  name="wifi_can",  color=cq.Color(*SILVER))
       .add(pmic,    name="pmic",      color=cq.Color(*BLACK))
       .add(ic2,     name="ic2",       color=cq.Color(*BLACK))
       .add(sd_slot, name="microsd",   color=cq.Color(*SILVER))
       .add(sd_card, name="sd_card",   color=cq.Color(0.55, 0.08, 0.08))
       .add(csi,     name="csi",       color=cq.Color(0.80, 0.76, 0.64))
       .add(hdmi,    name="mini_hdmi", color=cq.Color(*SILVER))
       .add(usb,     name="usb_otg",   color=cq.Color(*SILVER))
       .add(pwr,     name="usb_pwr",   color=cq.Color(*SILVER))
       .add(small,   name="passives",  color=cq.Color(*BLACK))
       .add(mouths,  name="openings",  color=cq.Color(0.06, 0.06, 0.07))
       .add(csi_slot, name="csi_slot", color=cq.Color(0.10, 0.10, 0.11)))

out = str(pathlib.Path(__file__).with_name("Raspberry_Pi_Zero.step"))
asm.export(out)

parts = [pcb, pins, soc, shield, pmic, ic2, sd_slot, sd_card, csi, hdmi, usb, pwr,
         small, mouths, csi_slot]
whole = parts[0]
for p in parts[1:]:
    whole = whole.union(p)
b = whole.val().BoundingBox()
print(f"  wrote {out}")
print(f"  bbox X {b.xmin:7.2f}..{b.xmax:7.2f}  Y {b.ymin:7.2f}..{b.ymax:7.2f}  Z {b.zmin:6.2f}..{b.zmax:6.2f}")
print(f"  PCB 0..{THK}, tallest feature {b.zmax:.2f} mm above the PCB underside")
