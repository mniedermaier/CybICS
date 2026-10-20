// CybICS simple stand
//
// Print two of these. They hold the CybICS PCB at 45 degrees, one at each
// short edge.
// Two pins go through the board's corner holes: H1 and H3 on the left,
// H2 and the LCD's mounting hole on the right, all 3 mm from the edges.
// A lip below the lower edge catches the board while it is put on and
// keeps it from sliding off if it is lifted off the pins. The lower edge is
// lifted off the desk so the Raspberry Pi's micro-USB and mini-HDMI
// ports, which point down past that edge, stay reachable.
//
// The stand is symmetric about the pin, so the same part serves both
// sides. Its frame is as wide as twice the hole inset, which keeps it
// flush with the board edge; a wider flange at the bottom keeps it from
// tipping over.
//
// Print upright, standing on the flange, no supports needed.

/* [Board] */
pcb_length    = 100;  // board edge to board edge along the slope
pcb_thickness = 1.6;
hole_inset    = 3;    // mounting hole centre to board edge (both axes)
hole_d        = 3.2;  // H1, H2, H3: M3 mounting holes
lcd_hole_d    = 2.5;  // the LCD's lower right hole, where the right stand's lower pin goes

/* [Stand] */
lift       = 30;   // height of the board's lower edge above the desk
angle      = 45;   // board inclination
frame      = 8;    // wall thickness of the profile
foot_width = 18;   // flange width, centred on the frame
foot_thick = 3;
lip_height = 2.5;  // how far the lip rises above the board's top face
lip_thick  = 3;
pad_length = 12;   // length of each contact pad along the slope
relief     = 1.5;  // recess between the pads, clears THT pins (SW1, SW2, J4)
pin_play   = 0.4;  // pin diameter below the hole; adjust to your printer
pin_height = 2;    // above the board's top face
clearance  = 0.2;  // play between the board edges and the stand
label      = "CybICS";

$fn = 48;

width = 2 * hole_inset;  // frame flush with the board edge, pin centred

c = cos(angle);
s = sin(angle);
lip_h = pcb_thickness + lip_height;

// Point on the slope: `t` along the board from its lower edge,
// `h` perpendicular to it (positive above the board's underside).
// The frame is offset so the lip's front edge lands on y = 0.
y0 = (lip_thick + clearance) * c + lip_h * s;
function q(t, h = 0) = [y0 + t * c - h * s, lift + t * s + h * c];

top   = pcb_length + clearance;
back  = q(top)[0];
// [position along the slope, diameter]. The lower pin has to fit the
// smaller LCD hole, the same part serves both sides.
pins  = [[hole_inset, min(hole_d, lcd_hole_d) - pin_play],
         [pcb_length - hole_inset, hole_d - pin_play]];

function outline() = [
  [0, 0],
  [back, 0],
  q(top),
  q(top - pad_length),
  q(top - pad_length, -relief),
  q(pad_length, -relief),
  q(pad_length),
  q(-clearance),
  q(-clearance, lip_h),
  q(-clearance - lip_thick, lip_h),
];

module rounded(r) { offset(r = r) offset(delta = -r) children(); }

module profile() {
  difference() {
    rounded(1) polygon(outline());
    // Lightening cut-out, leaves a frame of constant thickness
    rounded(4) offset(delta = -frame) polygon(outline());
  }
}

// Places children on the slope at (t, h), z-axis along the slope normal.
// x = 0 is the stand's plane of symmetry, through the pins.
module on_slope(t, h = 0) {
  p = q(t, h);
  translate([0, p[0], p[1]]) rotate([angle, 0, 0]) children();
}

module flange() {
  translate([0, back / 2, 0]) linear_extrude(foot_thick)
    offset(r = 2) square([foot_width - 4, back - 2], center = true);
}

module body() {
  translate([-width / 2, 0, 0]) rotate([90, 0, 90]) linear_extrude(width) profile();
  flange();
  // Pins through the corner holes, chamfered tips
  for (pin = pins) on_slope(pin[0]) {
    tip = pcb_thickness + pin_height;
    r = pin[1] / 2;
    rotate_extrude() polygon([[0, -1], [r, -1], [r, tip - 0.5], [r - 0.5, tip], [0, tip]]);
  }
}

// Engraved into the flange on both sides of the frame, so the label faces
// outward whichever side the stand goes on, reading from that side.
module engraving(depth = 0.6) {
  for (side = [-1, 1])
    translate([side * (width + foot_width) / 4, back / 2, foot_thick - depth])
      rotate([0, 0, side * 90])
        linear_extrude(depth + 1)
          text(label, font = "Liberation Sans:style=Bold", size = 3.5,
               halign = "center", valign = "center");
}

difference() { body(); engraving(); }
