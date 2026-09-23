#!/usr/bin/env python3
"""Render one section of the CybICS scene on its own, at several parameter values.

This is the tool that ends arguments.  The scene is 1800 lines of JavaScript in
a Python string, and reasoning about a single material from that is how three
wrong diagnoses of an invisible tank fill happened in a row.  Rendering the
subject alone, side by side at several values, answered it in one screenshot --
and a two-by-two matrix then narrowed it to one material property.

The section is lifted *verbatim* out of hardwareAbstraction.py by matching the
comments already in the file, never copied.  A harness that holds its own copy
of the code under test drifts from it, and then it lies.

    tools/3d/harness.py liquid --out docs/3d/shots/liquid.png
    tools/3d/harness.py liquid --values 0,0.25,0.5,0.75,1.0
    tools/3d/harness.py --list
    tools/3d/harness.py --from 'GST dished end caps' --to 'Add access ladder' \\
        --returns 'gstCapTop' --out /tmp/caps.png

Writes the standalone HTML next to the PNG, so it can be opened in a real
browser and poked at by hand.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOURCE = os.path.join(ROOT, "software/hwio-virtual/hardwareAbstraction.py")
THREE_JS = os.path.join(ROOT, "software/hwio-virtual/static/js/three.min.js")

sys.path.insert(0, HERE)
from cdp import Browser  # noqa: E402


# A preset is: where the section starts, where it ends, what the lifted code
# leaves behind that the harness should use, and how to build one variant from
# it.  Start and end are matched against the section comments already in the
# source, so renaming a comment breaks the preset loudly rather than lifting
# the wrong lines.
PRESETS = {
    "level-band": {
        # The one subject the whole visualisation hangs on: a viewer has to be
        # able to tell two vessels apart by their level at a glance. Rendered
        # alone at five fractions, that claim is either obvious or it is false.
        "start": r"// Level, shown on the vessel rather than inside it",
        "end": r"// GST Tank \(left\)",
        "returns": ["makeLevelBand", "BAND_R", "BAND_H"],
        "variant": """
          // A stand-in for the vessel, so the band is judged where it lives
          // rather than floating on its own.
          const shell = new THREE.Mesh(
            new THREE.CylinderGeometry(2, 2, 8, 32),
            new THREE.MeshStandardMaterial({
              color: 0x8f9bab, metalness: 0.15, roughness: 0.6 }));
          shell.position.y = 4;
          scene.add(shell);

          const band = api.makeLevelBand(0x2196f3, 0x0d47a1);
          band.userData.setLevel(value);
          scene.add(band);

          camera.position.set(0, 5, 15); camera.lookAt(0, 4, 0);
          return (value * 100).toFixed(0) + '%';
        """,
        "values": "0,0.25,0.5,0.75,1.0",
    },
}


def lift(start, end):
    """Pull the lines between two section comments out of the source."""
    lines = open(SOURCE).read().splitlines()
    s = e = None
    for i, line in enumerate(lines):
        if s is None and re.search(start, line):
            s = i
        elif s is not None and re.search(end, line):
            e = i
            break
    if s is None:
        raise SystemExit("harness: no line matches %r in %s" % (start, SOURCE))
    if e is None:
        raise SystemExit("harness: %r matched at line %d but %r never did"
                         % (start, s + 1, end))
    return "\n".join(lines[s:e]), (s + 1, e)


PAGE = """<!doctype html>
<meta charset="utf-8">
<title>CybICS 3D harness &mdash; %(title)s</title>
<style>
  body { margin: 0; background: #14181d; color: #cfd8e3;
         font: 13px/1.4 ui-monospace, monospace; }
  h1 { font-size: 13px; font-weight: 600; padding: 8px 12px; margin: 0;
       color: #ff8c42; border-bottom: 1px solid #262c34; }
  h1 span { color: #6b7686; font-weight: 400; }
  #grid { display: grid; grid-template-columns: repeat(%(cols)d, max-content); }
  .cell { position: relative; }
  .cell div { position: absolute; left: 6px; bottom: 6px; padding: 1px 6px;
              background: rgba(0,0,0,.6); border-radius: 3px; }
  .err { color: #ff6b6b; padding: 12px; white-space: pre-wrap; }
</style>
<h1>%(title)s <span>&mdash; lifted verbatim from hardwareAbstraction.py lines %(lines)s</span></h1>
<div id="grid"></div>
<script src="three.min.js"></script>
<script>
const CELL_W = %(w)d, CELL_H = %(h)d;
const VALUES = %(values)s;

// The lifted code, untouched.  Whatever it declares is in scope below.
function buildSection(THREE, scene, renderer, camera) {
%(section)s
  return { %(returns)s };
}

function cell(value) {
  const wrap = document.createElement('div');
  wrap.className = 'cell';
  document.getElementById('grid').appendChild(wrap);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(CELL_W, CELL_H);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate = false;
  renderer.outputEncoding = THREE.sRGBEncoding;   // r128 spelling
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = %(exposure)s;
  renderer.localClippingEnabled = true;           // the liquid needs it
  wrap.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1b2027);
  const camera = new THREE.PerspectiveCamera(60, CELL_W / CELL_H, 0.1, 1000);

  // The same environment the real scene builds, so metals are not flat grey.
  const c = document.createElement('canvas');
  c.width = 64; c.height = 32;
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, 32);
  grad.addColorStop(0.00, '#dfe9f5'); grad.addColorStop(0.45, '#8fa4bb');
  grad.addColorStop(0.55, '#6b5a4a'); grad.addColorStop(1.00, '#20242a');
  g.fillStyle = grad; g.fillRect(0, 0, 64, 32);
  const tex = new THREE.CanvasTexture(c);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileEquirectangularShader();
  scene.environment = pmrem.fromEquirectangular(tex).texture;
  tex.dispose(); pmrem.dispose();

  scene.add(new THREE.AmbientLight(0x5a6a7a, 0.22));
  const key = new THREE.DirectionalLight(0xfff8f0, 1.0);
  key.position.set(12, 20, 8); key.castShadow = true;
  key.shadow.mapSize.width = 1024; key.shadow.mapSize.height = 1024;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x88aaff, 0.22);
  fill.position.set(-15, 8, -10); scene.add(fill);

  const api = buildSection(THREE, scene, renderer, camera);
  const label = (function (value) { %(variant)s })(value);

  const tag = document.createElement('div');
  tag.textContent = label === undefined ? String(value) : label;
  wrap.appendChild(tag);

  renderer.shadowMap.needsUpdate = true;
  renderer.render(scene, camera);
  return renderer;
}

window.HARNESS = { ok: false, error: null, cells: 0 };
try {
  VALUES.forEach(cell);
  window.HARNESS.ok = true;
  window.HARNESS.cells = VALUES.length;
} catch (e) {
  window.HARNESS.error = String(e && e.stack || e);
  const p = document.createElement('pre');
  p.className = 'err'; p.textContent = window.HARNESS.error;
  document.body.appendChild(p);
}
</script>
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("preset", nargs="?", help="a named section, or use --from/--to")
    p.add_argument("--list", action="store_true", help="show the named sections")
    p.add_argument("--from", dest="start", help="regex matching the section's first line")
    p.add_argument("--to", dest="end", help="regex matching the line after it")
    p.add_argument("--returns", help="comma-separated names the lifted code leaves behind")
    p.add_argument("--variant", help="JS body building one cell from `value`")
    p.add_argument("--values", help="comma-separated parameter values")
    p.add_argument("--out", default="docs/3d/shots/harness.png")
    p.add_argument("--exposure", default="0.75")
    p.add_argument("--cell-width", type=int, default=440)
    p.add_argument("--cell-height", type=int, default=520)
    p.add_argument("--hardware-gl", action="store_true")
    p.add_argument("--keep-open", action="store_true", help="print the URL and leave it up")
    args = p.parse_args()

    if args.list or (not args.preset and not args.start):
        for name, spec in sorted(PRESETS.items()):
            print("%-16s %s" % (name, spec["start"]))
        return 0

    spec = dict(PRESETS.get(args.preset, {}))
    if args.preset and not spec:
        raise SystemExit("harness: no preset %r; --list shows them" % args.preset)
    for key, value in (("start", args.start), ("end", args.end),
                       ("variant", args.variant), ("values", args.values)):
        if value:
            spec[key] = value
    if args.returns:
        spec["returns"] = args.returns.split(",")
    for key in ("start", "end", "variant", "values"):
        if not spec.get(key):
            raise SystemExit("harness: --%s is required without a preset" % key)

    section, (first, last) = lift(spec["start"], spec["end"])
    values = [float(v) for v in str(spec["values"]).split(",")]

    per_row = min(len(values), 4)
    rows = (len(values) + per_row - 1) // per_row

    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(THREE_JS, os.path.join(out_dir, "three.min.js"))
    html_path = os.path.splitext(os.path.abspath(args.out))[0] + ".html"
    title = args.preset or spec["start"]
    with open(html_path, "w") as fh:
        fh.write(PAGE % {
            "title": title,
            "lines": "%d-%d" % (first, last),
            "section": section,
            "returns": ", ".join(spec.get("returns") or []),
            "variant": spec["variant"],
            "values": json.dumps(values),
            "w": args.cell_width, "h": args.cell_height,
            "cols": per_row,
            "exposure": args.exposure,
        })

    url = "file://" + html_path
    if args.keep_open:
        print(url)
        return 0

    # Lay the cells out in rows of at most four, then size the viewport to the
    # grid.  --window-size alone does not survive headless Chrome's own
    # chrome; the metrics override below is what actually sets the viewport,
    # and without it the bottom row is silently cropped out of the picture.
    width = args.cell_width * per_row
    height = args.cell_height * rows + 30
    browser = Browser(width=width, height=height, software_gl=not args.hardware_gl)
    report = {"section": title, "source_lines": [first, last], "values": values}
    try:
        page = browser.page()
        page.send("Emulation.setDeviceMetricsOverride", width=width, height=height,
                  deviceScaleFactor=1, mobile=False)
        page.navigate(url)
        time.sleep(3)
        state = page.eval("window.HARNESS")
        if state is None:
            # The page never ran our script: a bad URL, a missing three.min.js,
            # or a syntax error in the lifted section, which takes the whole
            # script block with it.  Silence here once cost a screenshot of
            # Chrome's error page reported as a clean run.
            report["error"] = "window.HARNESS was never set -- the page did not run"
            report["title"] = page.eval("document.title")
        else:
            report.update(state)
        report["bytes"] = page.screenshot(args.out)
        page.pump()
        report["console_errors"] = page.console_errors()
    finally:
        browser.close()
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") and not report.get("console_errors") else 1


if __name__ == "__main__":
    sys.exit(main())
