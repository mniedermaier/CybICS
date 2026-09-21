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
female 2x20 socket on its underside that plugs onto the male header on the
CybICS board.  That socket is modelled, with a hole at each pin position, so
it mates with the carrier's header instead of intersecting it.

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
soc = soften(blk(19.4, 35.6, 8.0, 23.6, 0, 1.15), 0.4)

# The raspberry on the SiP. Seven berries over two leaves, 0.03 mm proud --
# enough for the renderer to pick it out, not enough to matter mechanically.
def dot(u, v, r, h=0.03):
    return (cq.Workplane("XY").workplane(offset=THK + 1.15)
            .moveTo(x(v), y(u)).circle(r).extrude(h))

LOGO_U, LOGO_V = 26.4, 13.1
logo = None
for du, dv in ((0.0, 0.95), (-1.00, 0.42), (1.00, 0.42), (-1.55, -0.60),
               (1.55, -0.60), (-0.60, -0.80), (0.60, -0.80), (0.0, -1.55)):
    d = dot(LOGO_U + du, LOGO_V + dv, 0.55)
    logo = d if logo is None else logo.union(d)
for du, dv in ((-1.15, 2.25), (1.15, 2.25)):
    logo = logo.union(dot(LOGO_U + du, LOGO_V + dv, 0.72))

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
sd_slot = sd_slot.cut(blk(12.6, 14.1, 18.2, 19.7, 0.9, 1.5))   # corner notch
# The grooves need their own dark solids: cut alone is invisible when the lid
# and the body underneath are the same colour.
sd_grooves = None
for gu in (4.6, 10.2):
    g = blk(gu, gu + 0.5, 8.4, 18.6, 1.30, 1.44)
    sd_grooves = g if sd_grooves is None else sd_grooves.union(g)
sd_grooves = sd_grooves.union(blk(1.9, 13.1, 18.55, 18.9, 1.30, 1.44))

# Column of dark contact pads down the holder's right side, and the small
# orange part at its lower corner -- both clearly visible in the photograph.
sd_pads = None
for k in range(5):
    q = blk(9.0, 9.9, 12.3 + k * 1.15, 12.3 + k * 1.15 + 0.7, 1.30, 1.46)
    sd_pads = q if sd_pads is None else sd_pads.union(q)
sd_latch = blk(10.7, 12.4, 17.1, 18.6, 1.30, 1.48)
sd_card = blk(-2.2, 1.4, 7.9, 19.4, 0.2, 1.2)
sd_label = blk(-2.2, 0.2, 7.9, 11.4, 1.2, 1.26)                # white corner only

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
hdmi_top = blk(12.4 - 5.6, 12.4 + 5.6, 26.0, 27.4, 3.05, 3.22)

# Two pale bars stand in for the part marking on the SiP; STEP carries no
# textures, so this is as close to printed text as the format allows.
soc_mark = (blk(24.0, 31.0, 17.4, 18.3, 1.15, 1.18)
            .union(blk(25.0, 30.0, 19.1, 20.0, 1.15, 1.18)))

# Small ICs: dark body with silver leads down each long side.
ics = leads = None
for uc, vc, du, dv in ((50.5, 14.0, 1.9, 1.5), (55.85, 15.85, 1.25, 1.15),
                       (44.5, 25.4, 1.7, 1.4), (53.2, 22.45, 1.9, 1.55)):
    b = blk(uc - du, uc + du, vc - dv, vc + dv, 0, 0.85)
    ics = b if ics is None else ics.union(b)
    for s in (-1, 1):
        l = blk(uc - du, uc + du, vc + s * dv, vc + s * (dv + 0.35), 0, 0.25)
        leads = l if leads is None else leads.union(l)

# Passives.  The photograph shows a mix of black chip resistors and pale beige
# MLCCs, not a uniform field of black, so they are split into two colours.
RES = [(17.0, 24.5), (36.0, 6.5), (44.0, 6.5), (59.0, 8.0), (23.0, 25.5),
       (30.0, 25.0), (16.5, 20.5), (18.5, 4.5), (33.0, 25.5), (37.5, 24.0),
       (47.0, 7.0), (26.0, 6.5), (60.5, 12.5), (38.6, 8.6), (57.5, 24.5),
       (47.1, 7.3), (52.0, 7.3), (52.1, 11.1), (51.3, 16.4), (52.6, 18.2),
       (56.9, 21.3), (57.7, 16.7), (58.8, 18.3), (36.8, 10.5), (36.8, 13.0),
       (58.4, 24.8), (60.2, 20.4), (43.2, 26.6), (33.5, 6.4), (20.0, 25.8),
       (36.8, 15.5), (36.8, 18.0), (49.6, 6.8)]
CAP = [(52.5, 8.5), (56.5, 9.5), (57.0, 21.5), (60.5, 17.0), (45.5, 25.0),
       (53.5, 19.5), (55.0, 11.5), (48.5, 9.2), (15.5, 6.0), (36.5, 9.5),
       (54.5, 10.1), (51.8, 9.2), (44.7, 9.3), (58.2, 12.8), (58.2, 14.6),
       (17.5, 8.0), (17.5, 10.2), (30.5, 6.2), (59.4, 10.4), (55.8, 6.6),
       (46.8, 10.6), (39.8, 25.6)]
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
tantalum = soften(blk(14.4, 16.4, 12.4, 15.7, 0, 1.0), 0.2)  # tan bulk cap
soic = blk(3.7, 6.7, 20.3, 22.5, 0, 0.75)
soic_leads = (blk(3.7, 6.7, 19.95, 20.3, 0, 0.22)
              .union(blk(3.7, 6.7, 22.5, 22.85, 0, 0.22)))
shield_sq = blk(6.9, 8.9, 20.6, 22.2, 0, 0.7)

# A field of exposed test pads sits between the holder and the board edge.
tp = None
for row, (v0, v1) in enumerate(((20.4, 21.0), (21.3, 21.9), (22.2, 22.8))):
    for k in range(9):
        u0 = 10.3 + k * 0.82
        q = blk(u0, u0 + 0.52, v0, v1, 0, SILK_T)
        tp = q if tp is None else tp.union(q)
for k in range(16):                                  # fine-pitch row below
    u0 = 10.0 + k * 0.48
    tp = tp.union(blk(u0, u0 + 0.26, 23.0, 23.5, 0, SILK_T))

# The mini-HDMI is held by two stout through-hole legs, very visible head-on.
hdmi_legs = (blk(8.2, 9.4, 30.6, 32.3, -0.2, 1.1)
             .union(blk(15.4, 16.6, 30.6, 32.3, -0.2, 1.1)))

# ------------------------------------ female 2x20 socket on the underside
# Nominally 8.50 mm tall, resting on the 2.50 mm body of the carrier's male
# header, which is what puts the Pi's PCB 11.0 mm up.  Each pin gets a hole so
# the mated pair does not read as a collision.
#
# Drawn 0.05 mm short on purpose.  The stock header model's body measures
# 2.53 mm rather than the nominal 2.50, so a socket drawn to size overlaps its
# mating face by a hair and every clash check reports a sliver.  The clearance
# is far below any real tolerance and keeps the check meaningful.
SOCK_H = 8.45
socket = blk(7.10, 57.90, 0.96, 6.04, -1.4 - SOCK_H, -1.4)
for col in range(20):
    for v in (2.23, 4.77):
        socket = socket.cut(
            cq.Workplane("XY").workplane(offset=THK - 1.4 - SOCK_H - 0.1)
            .moveTo(x(v), y(8.37 + col * 2.54)).circle(0.85).extrude(SOCK_H + 0.2))

# ------------------------------------------------------------- silkscreen
frame = (blk(6.35, 58.65, 0.95, 6.25, 0, SILK_T)
         .cut(blk(6.5, 58.5, 1.1, 6.1, -0.1, SILK_T + 0.1)))
silk = (frame
        .union(label("GPIO", 39.4, 7.5, 1.15))
        .union(label("USB", 38.5, 24.4, 1.0))
        .union(label("PWR IN", 49.6, 27.2, 1.0, along_u=False)))

GREEN = (0.062, 0.265, 0.125)
BLACK = (0.08, 0.08, 0.09)
SILVER = (0.40, 0.39, 0.355)
GOLD = (0.72, 0.57, 0.21)
asm = (cq.Assembly()
       .add(pcb,      name="pcb",        color=cq.Color(*GREEN))
       .add(socket,   name="gpio_socket", color=cq.Color(0.10, 0.10, 0.11))
       .add(rings,    name="hole_pads",  color=cq.Color(*GOLD))
       .add(pins,     name="gpio_pins",  color=cq.Color(0.76, 0.63, 0.26))
       .add(silk,     name="silkscreen", color=cq.Color(0.84, 0.84, 0.81))
       .add(pads,     name="test_pads",  color=cq.Color(*GOLD))
       .add(soc,      name="soc",        color=cq.Color(*BLACK))
       .add(logo,     name="raspberry",  color=cq.Color(0.20, 0.20, 0.21))
       .add(can_rim,  name="wifi_rim",   color=cq.Color(0.255, 0.245, 0.215))
       .add(can_lid,  name="wifi_lid",   color=cq.Color(0.355, 0.345, 0.305))
       .add(ics,      name="small_ics",  color=cq.Color(*BLACK))
       .add(leads,    name="ic_leads",   color=cq.Color(0.68, 0.69, 0.71))
       .add(res,      name="resistors",  color=cq.Color(*BLACK))
       .add(cap,      name="capacitors", color=cq.Color(0.78, 0.70, 0.55))
       .add(act_led,  name="act_led",    color=cq.Color(0.25, 0.80, 0.25))
       .add(tantalum, name="bulk_cap",   color=cq.Color(0.74, 0.66, 0.50))
       .add(soic,     name="soic",       color=cq.Color(*BLACK))
       .add(soic_leads, name="soic_leads", color=cq.Color(0.66, 0.67, 0.69))
       .add(shield_sq, name="small_can", color=cq.Color(0.46, 0.47, 0.49))
       .add(tp,       name="test_field", color=cq.Color(*GOLD))
       .add(hdmi_legs, name="hdmi_legs", color=cq.Color(0.40, 0.39, 0.355))
       .add(hdmi_top, name="hdmi_top",   color=cq.Color(0.19, 0.19, 0.18))
       .add(soc_mark, name="soc_marking", color=cq.Color(0.30, 0.30, 0.30))
       .add(sd_slot,  name="microsd",    color=cq.Color(0.50, 0.455, 0.355))
       .add(sd_lid,   name="microsd_lid", color=cq.Color(0.545, 0.50, 0.39))
       .add(sd_pads,  name="sd_contacts", color=cq.Color(0.42, 0.14, 0.10))
       .add(sd_latch, name="sd_latch",  color=cq.Color(0.62, 0.35, 0.12))
       .add(sd_grooves, name="sd_stamping", color=cq.Color(0.34, 0.31, 0.25))
       .add(sd_card,  name="sd_card",    color=cq.Color(0.58, 0.09, 0.09))
       .add(sd_label, name="sd_label",   color=cq.Color(0.80, 0.79, 0.76))
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
for p in (socket, rings, pins, silk, pads, soc, logo, can_rim, can_lid, ics, leads, res, cap,
          act_led, tantalum, soic, soic_leads, shield_sq, tp, hdmi_legs,
          hdmi_top, soc_mark,
          sd_slot, sd_lid, sd_pads, sd_latch, sd_grooves, sd_card, sd_label,
          csi_body, csi_comb, csi_ears, hdmi, usb, pwr, mouths):
    whole = whole.union(p)
b = whole.val().BoundingBox()
print(f"  wrote {out}")
print(f"  bbox X {b.xmin:7.2f}..{b.xmax:7.2f}  Y {b.ymin:7.2f}..{b.ymax:7.2f}  Z {b.zmin:6.2f}..{b.zmax:6.2f}")
print(f"  PCB 0..{THK}, tallest feature {b.zmax:.2f} mm above the PCB underside")
