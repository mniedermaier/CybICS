"""Build a Raspberry Pi Zero 2 W 3D model for the CybICS carrier board.

Regenerate with:   python3 -m venv .venv && .venv/bin/pip install cadquery
                   .venv/bin/python Raspberry_Pi_Zero.build.py

Outline, mounting holes and the three edge-connector centres come from the
official mechanical drawing (65 x 30 mm, four 2.75 mm holes 3.5 mm in from each
edge, connector centres 12.4 / 41.4 / 54 mm).  Everything else is measured off
doc/pics/cybics.png, the photograph of the assembled board -- the connector
centres read off that photograph land within 0.4 mm of the drawing, which is
what fixes the scale and origin.

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
PAD_OD = 5.4                                  # gold ring around each hole
SILK_T = 0.04                                 # silkscreen / plating thickness

# u,v -> KiCad 3D model space for J1's footprint (origin at pin 1, Y negated).
MX, MY = -4.77, -8.37
x = lambda v: v + MX
y = lambda u: u + MY

HOLES = [(u, v) for u in (EDGE, LEN - EDGE) for v in (EDGE, WID - EDGE)]


def blk(u0, u1, v0, v1, w0, w1):
    """An axis-aligned block given in Pi coordinates."""
    return (cq.Workplane("XY").workplane(offset=THK + w0)
            .moveTo((x(v0) + x(v1)) / 2, (y(u0) + y(u1)) / 2)
            .rect(abs(v1 - v0), abs(u1 - u0))
            .extrude(w1 - w0))


def soften(shape, r, sel="|Z"):
    """Fillet if OCCT can; a block is better than a failed build."""
    try:
        return shape.edges(sel).fillet(r)
    except Exception:
        return shape


def label(txt, u, v, size, along_u=True):
    """Silkscreen text lying on the PCB's top face."""
    t = (cq.Workplane("XY").workplane(offset=THK)
         .text(txt, size, SILK_T, halign="center", valign="center"))
    if along_u:
        t = t.rotate((0, 0, 0), (0, 0, 1), 90)
    return t.translate((x(v), y(u), 0))


# ---------------------------------------------------------------- the PCB
pcb = (cq.Workplane("XY")
       .moveTo(x(WID / 2), y(LEN / 2)).rect(WID, LEN).extrude(THK)
       .edges("|Z").fillet(CORNER_R))
for u, v in HOLES:
    pcb = pcb.faces(">Z").workplane(origin=(0, 0, 0)).moveTo(x(v), y(u)).hole(HOLE_D)

# Plated ring around each mounting hole -- clearly visible in the photograph.
rings = None
for u, v in HOLES:
    r = (cq.Workplane("XY").workplane(offset=THK)
         .moveTo(x(v), y(u)).circle(PAD_OD / 2).circle(HOLE_D / 2).extrude(SILK_T))
    rings = r if rings is None else rings.union(r)

# ------------------------------------------------- GPIO pins, from the pads
# Footprint pads are at local x 0 / -2.54 and local y 0 .. -48.26, which is
# u 8.37 .. 56.63 and v 2.23 / 4.77.  Soldered socket tails, seen from above.
pins = None
for col in range(20):
    for v in (2.23, 4.77):
        p = (cq.Workplane("XY").workplane(offset=THK)
             .moveTo(x(v), y(8.37 + col * 2.54)).circle(0.36).extrude(0.85))
        pins = p if pins is None else pins.union(p)

# ------------------------------------------------------- top-side components
soc = soften(blk(19.5, 35.5, 8.0, 23.0, 0, 1.15), 0.4)

# The raspberry on the SiP. Seven berries over two leaves, 0.03 mm proud --
# enough for the renderer to pick it out, not enough to matter mechanically.
def dot(u, v, r, h=0.03):
    return (cq.Workplane("XY").workplane(offset=THK + 1.15)
            .moveTo(x(v), y(u)).circle(r).extrude(h))

LOGO_U, LOGO_V = 27.5, 15.5
logo = None
for du, dv in ((0, 0.75), (-0.75, 0.30), (0.75, 0.30), (-1.15, -0.45),
               (1.15, -0.45), (-0.45, -0.60), (0.45, -0.60)):
    d = dot(LOGO_U + du, LOGO_V + dv, 0.42)
    logo = d if logo is None else logo.union(d)
for du, dv in ((-0.85, 1.75), (0.85, 1.75)):
    logo = logo.union(dot(LOGO_U + du, LOGO_V + dv, 0.55))

# The wireless can reads as a rim around a slightly sunken lid, not a slab.
can_rim = blk(38.0, 48.5, 11.0, 23.5, 0, 1.05)
can_lid = blk(38.4, 48.1, 11.4, 23.1, 0, 0.92)
can_rim = can_rim.cut(blk(38.4, 48.1, 11.4, 23.1, 0.92, 1.2))

sd_slot = soften(blk(1.0, 14.0, 7.5, 19.5, 0, 1.35), 0.25)
# The holder's lid is stamped, not flat; two grooves and the latch cut-out are
# what stop it reading as a blank silver tile.
sd_lid = blk(1.6, 13.4, 8.1, 18.9, 1.35, 1.45)
for gu in (4.6, 10.2):
    sd_lid = sd_lid.cut(blk(gu, gu + 0.45, 8.4, 18.6, 1.38, 1.5))
sd_lid = sd_lid.cut(blk(11.6, 13.2, 9.0, 12.0, 1.38, 1.5))
sd_card = blk(-2.1, 1.0, 9.0, 20.0, 0.2, 1.2)

# Camera FFC: ivory body, dark contact comb, silver latch ears.
csi_body = blk(62.0, 66.2, 8.0, 23.0, 0, 2.8)
csi_comb = blk(62.9, 63.5, 8.6, 22.4, 1.5, 2.85)
csi_body = csi_body.cut(blk(62.9, 63.5, 8.6, 22.4, 1.5, 3.0))
csi_ears = blk(64.6, 66.2, 7.2, 8.6, 0, 1.2).union(blk(64.6, 66.2, 22.4, 23.8, 0, 1.2))


def shell(uc, half_u, v0, h, mouth_u, mouth_h):
    """A connector shell with a recess in its outward face."""
    body = soften(blk(uc - half_u, uc + half_u, v0, 32.3, 0, h), 0.25)
    cutter = blk(uc - mouth_u, uc + mouth_u, 32.3 - 1.8, 32.4,
                 (h - mouth_h) / 2, (h + mouth_h) / 2)
    shown = blk(uc - mouth_u, uc + mouth_u, 32.3 - 1.8, 32.3,
                (h - mouth_h) / 2, (h + mouth_h) / 2)
    return body.cut(cutter), shown


hdmi, hdmi_m = shell(12.4, 5.6, 26.0, 3.2, 4.5, 1.7)
usb, usb_m = shell(41.4, 3.8, 26.6, 2.6, 3.0, 1.3)
pwr, pwr_m = shell(54.0, 3.8, 26.6, 2.6, 3.0, 1.3)
mouths = hdmi_m.union(usb_m).union(pwr_m)

# Small ICs: dark body with silver leads down each long side.
ics = leads = None
for uc, vc, du, dv in ((50.5, 14.0, 1.9, 1.5), (56.8, 16.5, 1.6, 1.3),
                       (44.5, 25.4, 1.7, 1.4)):
    b = blk(uc - du, uc + du, vc - dv, vc + dv, 0, 0.85)
    ics = b if ics is None else ics.union(b)
    for s in (-1, 1):
        l = blk(uc - du, uc + du, vc + s * dv, vc + s * (dv + 0.35), 0, 0.25)
        leads = l if leads is None else leads.union(l)

# Passives.  The photograph shows a mix of black chip resistors and pale beige
# MLCCs, not a uniform field of black, so they are split into two colours.
RES = [(17.0, 24.5), (36.0, 6.5), (44.0, 6.5), (59.0, 8.0), (23.0, 25.5),
       (30.0, 25.0), (16.5, 20.5), (18.5, 4.5), (33.0, 25.5), (37.5, 24.0),
       (47.0, 7.0), (26.0, 6.5), (60.5, 12.5), (38.6, 8.6), (57.5, 24.5)]
CAP = [(52.5, 8.5), (56.5, 9.5), (57.0, 21.5), (60.5, 17.0), (45.5, 25.0),
       (53.5, 19.5), (55.0, 11.5), (48.5, 9.2), (15.5, 6.0), (36.5, 9.5)]
res = cap = None
for u0, v0 in RES:
    b = blk(u0, u0 + 1.9, v0, v0 + 1.1, 0, 0.5)
    res = b if res is None else res.union(b)
for u0, v0 in CAP:
    b = blk(u0, u0 + 1.7, v0, v0 + 1.0, 0, 0.6)
    cap = b if cap is None else cap.union(b)

# Exposed gold test pads.
pads = None
for u0, v0, du, dv in ((21.0, 25.0, 1.2, 0.8), (24.5, 27.0, 1.2, 0.8),
                       (28.0, 27.0, 1.2, 0.8), (31.5, 25.8, 1.2, 0.8),
                       (46.0, 27.4, 1.0, 0.7), (49.5, 27.4, 1.0, 0.7)):
    p = blk(u0, u0 + du, v0, v0 + dv, 0, SILK_T)
    pads = p if pads is None else pads.union(p)

act_led = blk(59.6, 60.8, 22.8, 23.8, 0, 0.55)      # green activity LED

# ------------------------------------------------------------- silkscreen
frame = (blk(6.35, 58.65, 0.95, 6.25, 0, SILK_T)
         .cut(blk(6.5, 58.5, 1.1, 6.1, -0.1, SILK_T + 0.1)))
silk = (frame
        .union(label("GPIO", 39.4, 7.5, 1.15))
        .union(label("USB", 38.5, 24.4, 1.0))
        .union(label("PWR IN", 49.6, 27.2, 1.0, along_u=False)))

GREEN = (0.035, 0.235, 0.105)
BLACK = (0.08, 0.08, 0.09)
SILVER = (0.38, 0.39, 0.42)
GOLD = (0.72, 0.57, 0.21)
asm = (cq.Assembly()
       .add(pcb,      name="pcb",        color=cq.Color(*GREEN))
       .add(rings,    name="hole_pads",  color=cq.Color(*GOLD))
       .add(pins,     name="gpio_pins",  color=cq.Color(0.76, 0.63, 0.26))
       .add(silk,     name="silkscreen", color=cq.Color(0.84, 0.84, 0.81))
       .add(pads,     name="test_pads",  color=cq.Color(*GOLD))
       .add(soc,      name="soc",        color=cq.Color(*BLACK))
       .add(logo,     name="raspberry",  color=cq.Color(0.20, 0.20, 0.21))
       .add(can_rim,  name="wifi_rim",   color=cq.Color(0.30, 0.31, 0.33))
       .add(can_lid,  name="wifi_lid",   color=cq.Color(0.42, 0.43, 0.45))
       .add(ics,      name="small_ics",  color=cq.Color(*BLACK))
       .add(leads,    name="ic_leads",   color=cq.Color(0.68, 0.69, 0.71))
       .add(res,      name="resistors",  color=cq.Color(*BLACK))
       .add(cap,      name="capacitors", color=cq.Color(0.78, 0.70, 0.55))
       .add(act_led,  name="act_led",    color=cq.Color(0.25, 0.80, 0.25))
       .add(sd_slot,  name="microsd",    color=cq.Color(0.44, 0.44, 0.45))
       .add(sd_lid,   name="microsd_lid", color=cq.Color(0.50, 0.50, 0.51))
       .add(sd_card,  name="sd_card",    color=cq.Color(0.55, 0.08, 0.08))
       .add(csi_body, name="csi",        color=cq.Color(0.74, 0.71, 0.62))
       .add(csi_comb, name="csi_comb",   color=cq.Color(0.22, 0.20, 0.18))
       .add(csi_ears, name="csi_ears",   color=cq.Color(*SILVER))
       .add(hdmi,     name="mini_hdmi",  color=cq.Color(*SILVER))
       .add(usb,      name="usb_otg",    color=cq.Color(*SILVER))
       .add(pwr,      name="usb_pwr",    color=cq.Color(*SILVER))
       .add(mouths,   name="openings",   color=cq.Color(0.05, 0.05, 0.06)))

out = str(pathlib.Path(__file__).with_name("Raspberry_Pi_Zero.step"))
asm.export(out)

whole = pcb
for p in (rings, pins, silk, pads, soc, logo, can_rim, can_lid, ics, leads, res, cap,
          act_led, sd_slot, sd_lid, sd_card, csi_body, csi_comb, csi_ears,
          hdmi, usb, pwr, mouths):
    whole = whole.union(p)
b = whole.val().BoundingBox()
print(f"  wrote {out}")
print(f"  bbox X {b.xmin:7.2f}..{b.xmax:7.2f}  Y {b.ymin:7.2f}..{b.ymax:7.2f}  Z {b.zmin:6.2f}..{b.zmax:6.2f}")
print(f"  PCB 0..{THK}, tallest feature {b.zmax:.2f} mm above the PCB underside")
