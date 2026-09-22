#!/usr/bin/env python3
"""Measure and photograph what moves in the CybICS 3D scene.

A still frame says nothing about animation, and neither does the source. The
question "does the fan turn at the same rate on a fast machine and a slow one"
is a question about two numbers taken a known time apart, and this is the tool
that takes them.

    tools/3d/motion.py --strip 8 --interval 0.4 --out docs/3d/shots/flow.png
    tools/3d/motion.py --rates                 # per-second rates at two caps
    tools/3d/motion.py --rates --caps 33,83    # 30 fps against 12 fps

--strip tiles N screenshots into one image so a motion can be looked at as a
sequence. --rates samples window.CybICS3D.motion() across a wall-clock window,
once per frame cap, and reports each quantity's rate per *second*. Anything
whose rate changes when the cap changes is animated per frame rather than per
second, which means it runs slower on a slower machine.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser  # noqa: E402
from capture import CAMERAS  # noqa: E402

# Quantities that only ever increase, so a wrap or a reset is not a rate.
CUMULATIVE = ("fan", "frame")


def open_scene(page, url, timeout=90):
    page.navigate(url)
    time.sleep(8)
    page.eval(
        "(() => { const t = [...document.querySelectorAll('.q-tab')]"
        ".find(e => /3D/i.test(e.innerText)); t && t.click(); })()"
    )
    for _ in range(timeout):
        time.sleep(1)
        try:
            if page.eval("typeof window.CybICS3D") == "object":
                return True
        except RuntimeError:
            pass
    return False


def pin(page, gst, hpt, blowout=False):
    """Freeze the plant data, so motion is the only thing changing."""
    state = {"gst": gst, "hpt": hpt, "sysSen": 1, "boSen": 1 if blowout else 0, "heartbeat": True,
             "compressor": True, "systemValve": True, "gstSig": True}
    page.eval(
        "(() => { const fixed = %s; const orig = window.fetch.bind(window);"
        "  window.fetch = (u, o) => /api\\/state/.test(String(u))"
        "    ? Promise.resolve(new Response(JSON.stringify(fixed),"
        "        {headers: {'Content-Type': 'application/json'}}))"
        "    : orig(u, o); })()" % json.dumps(state))
    time.sleep(1)


def sample_rates(page, window_s, cap_ms):
    """Per-second rate of every quantity motion() reports, at one frame cap."""
    page.eval("window.CybICS3D.frameCap(%f)" % cap_ms)
    time.sleep(1.0)                       # let the new cap take effect
    a = page.eval("window.CybICS3D.motion()")
    time.sleep(window_s)
    b = page.eval("window.CybICS3D.motion()")
    dt = (b["t"] - a["t"]) / 1000.0
    rates = {"cap_ms": cap_ms, "seconds": round(dt, 2),
             "fps": round((b["frame"] - a["frame"]) / dt, 1)}
    for key in CUMULATIVE:
        if key in a and key != "frame":
            rates[key + "_per_s"] = round((b[key] - a[key]) / dt, 4)
    rates["fan_per_frame"] = (round((b["fan"] - a["fan"]) / (b["frame"] - a["frame"]), 5)
                              if b["frame"] > a["frame"] else None)
    return rates


def filmstrip(page, out, count, interval, columns, crop=None):
    from PIL import Image
    frames = []
    base = os.path.splitext(os.path.abspath(out))[0]
    for i in range(count):
        path = "%s-frame%02d.png" % (base, i)
        page.screenshot(path)
        frames.append(path)
        time.sleep(interval)

    images = [Image.open(f) for f in frames]
    if crop:
        # A whole 1400-pixel frame tiled six times leaves each copy too small
        # to see a chevron move. The crop is what makes a filmstrip legible.
        images = [img.crop(crop) for img in images]
    w, h = images[0].size
    rows = (count + columns - 1) // columns
    sheet = Image.new("RGB", (w * columns, h * rows), (10, 14, 20))
    for i, img in enumerate(images):
        sheet.paste(img, ((i % columns) * w, (i // columns) * h))
    sheet.save(out)
    for f in frames:
        os.remove(f)
    return sheet.size


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8090/?force3d=1")
    p.add_argument("--out", default="docs/3d/shots/motion.png")
    p.add_argument("--strip", type=int, default=0, help="tile this many frames")
    p.add_argument("--interval", type=float, default=0.4, help="seconds between frames")
    p.add_argument("--columns", type=int, default=4)
    p.add_argument("--rates", action="store_true", help="measure per-second rates")
    p.add_argument("--caps", default="33,83", help="frame caps in ms to compare")
    p.add_argument("--window", type=float, default=4.0, help="seconds per rate sample")
    p.add_argument("--gst", type=int, default=200)
    p.add_argument("--hpt", type=int, default=60)
    p.add_argument("--blowout", action="store_true",
                   help="pin the blowout sensor active, to see the alarm state")
    p.add_argument("--camera", default="overview", choices=sorted(CAMERAS))
    p.add_argument("--crop", default="", help="left,top,right,bottom for the strip")
    p.add_argument("--hardware-gl", action="store_true")
    p.add_argument("--width", type=int, default=1400)
    p.add_argument("--height", type=int, default=900)
    args = p.parse_args()

    report = {"url": args.url}
    browser = Browser(width=args.width, height=args.height,
                      software_gl=not args.hardware_gl)
    try:
        page = browser.page()
        if not open_scene(page, args.url):
            report["error"] = "the scene never finished building"
            print(json.dumps(report, indent=2))
            return 1
        pin(page, args.gst, args.hpt, args.blowout)
        cam = CAMERAS.get(args.camera)
        if cam:
            page.eval(
                "(() => { const c = window.CybICS3D.camera;"
                " c.position.set(%s, %s, %s); c.lookAt(%s, %s, %s);"
                " c.updateProjectionMatrix(); })()"
                % (cam["pos"][0], cam["pos"][1], cam["pos"][2],
                   cam["look"][0], cam["look"][1], cam["look"][2]))
            report["camera"] = args.camera
        report["motion_keys"] = sorted(page.eval("window.CybICS3D.motion()").keys())

        if args.rates:
            report["rates"] = [sample_rates(page, args.window, float(c))
                               for c in args.caps.split(",")]
            # The point of the whole exercise: a quantity animated per second
            # keeps its rate when the frame cap changes, one animated per frame
            # does not.
            if len(report["rates"]) == 2:
                a, b = report["rates"]
                report["fan_rate_ratio"] = (
                    round(b["fan_per_s"] / a["fan_per_s"], 3)
                    if a.get("fan_per_s") else None)
                report["verdict"] = (
                    "frame-rate dependent" if report["fan_rate_ratio"] is not None
                    and abs(report["fan_rate_ratio"] - 1.0) > 0.15
                    else "time-based")

        if args.strip:
            page.eval("window.CybICS3D.frameCap(33)")
            crop = None
            if args.crop:
                crop = tuple(int(v) for v in args.crop.split(","))
                report["crop"] = crop
            report["strip"] = filmstrip(page, args.out, args.strip,
                                        args.interval, args.columns, crop)
        page.pump()
        report["console_errors"] = page.console_errors()
    finally:
        browser.close()
    side = os.path.splitext(args.out)[0] + ".json"
    os.makedirs(os.path.dirname(os.path.abspath(side)) or ".", exist_ok=True)
    with open(side, "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
