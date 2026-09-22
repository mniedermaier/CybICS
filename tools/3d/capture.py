#!/usr/bin/env python3
"""Load the CybICS 3D view, stage it, photograph it, and report what it cost.

Nothing about this scene can be judged from the source.  This is the tool that
turns "it should look right now" into a picture and a number.

    tools/3d/capture.py --out docs/3d/shots/overview.png
    tools/3d/capture.py --gst 200 --hpt 40 --camera close --out /tmp/a.png
    tools/3d/capture.py --hardware-gl --soak 60      # does the page survive?

Writes the PNG and a sidecar .json with console errors, draw calls, triangles,
frame rate, build time and any page navigation -- a navigation means NiceGUI
reloaded the page under us, which is a build failure, not a flake.

Two deliberate orderings, both learned the hard way:

  * Everything cheap is read the moment the scene exists, and the screenshot is
    taken before the frame-rate window.  On a software renderer the page has
    only a few seconds before NiceGUI's client gives up and reloads it, and a
    run that comes back with a traceback instead of a picture has told us
    nothing.
  * No probe is allowed to abort the run.  A lost page sets "reloaded" and the
    report keeps whatever it had, because half a measurement plus the reason
    for the other half is still a result.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser  # noqa: E402


class ContextLost(Exception):
    """The page went away under us -- almost always a NiceGUI reload."""


def guard(page, expression, await_promise=False):
    """Evaluate, and turn a vanished scene into a diagnosis rather than a stack.

    The scene stalls software renderers badly enough that NiceGUI gives up on
    its own client and reloads the page.  When that happens every later probe
    fails with a confusing TypeError on window.CybICS3D, so catch it once, here,
    and say what actually happened.
    """
    try:
        return page.eval(expression, await_promise=await_promise)
    except RuntimeError as exc:
        try:
            alive = page.eval("typeof window.CybICS3D") == "object"
        except RuntimeError:
            alive = False
        if not alive:
            raise ContextLost("the page reloaded while being measured") from exc
        raise


def safe(page, report, expression, await_promise=False, label=None):
    """guard(), but a failed probe is recorded in the report instead of raised.

    Once the page is gone every further probe would fail the same way, so the
    first loss short-circuits the rest of the run.

    A probe that yields nothing says so under "skipped" rather than leaving a
    bare null in the report.  A null that could mean "measured as nothing",
    "the page died" or "the expression was wrong" is worse than no number at
    all, and this tool exists to be believed.
    """
    label = label or expression.strip().split("\n")[0][:40]
    if report.get("reloaded"):
        report.setdefault("skipped", {})[label] = "page already lost"
        return None
    try:
        value = guard(page, expression, await_promise)
    except ContextLost as exc:
        report["reloaded"] = True
        report.setdefault("error", str(exc))
        report.setdefault("skipped", {})[label] = str(exc)
        return None
    except RuntimeError as exc:
        report.setdefault("skipped", {})[label] = str(exc)[:200]
        return None
    if value is None:
        report.setdefault("skipped", {})[label] = "returned undefined"
    return value


CAMERAS = {
    "overview": None,                       # leave the scene's own default
    "close":    {"pos": [6, 5, 14],  "look": [0, 3, 0]},
    "gst":      {"pos": [-4, 5, 12], "look": [-7, 4, 0]},
    "hpt":      {"pos": [10, 5, 12], "look": [7, 4, 0]},
    "top":      {"pos": [0, 26, 10], "look": [0, 0, 0]},
}


def stage(page, report, args):
    """Pin whatever the caller wants fixed, so shots are comparable."""
    notes = {}
    if args.gst is not None or args.hpt is not None:
        gst = (args.gst if args.gst is not None else 128) / 255.0
        hpt = (args.hpt if args.hpt is not None else 128) / 255.0
        notes["levels"] = safe(page, report,
            "(() => {"
            "  const t = []; window.CybICS3D.scene.traverse(n => {"
            "    if (n.userData && n.userData.setLevel) t.push(n); });"
            "  if (t.length < 2) return 'found ' + t.length;"
            f"  t[0].userData.setLevel({gst}); t[1].userData.setLevel({hpt});"
            "  return 'pinned';"
            "})()"
        )
    cam = CAMERAS.get(args.camera)
    if cam:
        safe(page, report,
            "(() => { const c = window.CybICS3D.camera;"
            f" c.position.set({cam['pos'][0]}, {cam['pos'][1]}, {cam['pos'][2]});"
            f" c.lookAt({cam['look'][0]}, {cam['look'][1]}, {cam['look'][2]});"
            " c.updateProjectionMatrix(); })()"
        )
        notes["camera"] = args.camera
    if args.exposure is not None:
        safe(page, report, f"window.CybICS3D.exposure({args.exposure})")
        notes["exposure"] = args.exposure
    return notes


# Read in one round trip, immediately after the scene exists.  Anything that
# needs the page alive belongs here rather than after the screenshot.
SNAPSHOT_JS = """
(() => {
  const r = window.CybICS3D.renderer, s = window.CybICS3D.scene;
  const gl = r.getContext();
  const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  let meshes = 0, lights = 0, shadowCasters = 0, materials = new Set();
  s.traverse(n => {
    if (n.isMesh) { meshes++; if (n.castShadow) shadowCasters++;
                    if (n.material) materials.add(n.material.uuid); }
    if (n.isLight) lights++;
  });
  return {
    gpu: dbg ? String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) : 'unknown',
    frame: r.info.render.frame,
    draw_calls: r.info.render.calls,
    triangles: r.info.render.triangles,
    geometries: r.info.memory.geometries,
    textures: r.info.memory.textures,
    programs: r.info.programs ? r.info.programs.length : null,
    meshes, lights, shadow_casters: shadowCasters, materials: materials.size,
    pixel_ratio: r.getPixelRatio(), environment: !!s.environment,
    exposure: r.toneMappingExposure,
    shadow_auto_update: r.shadowMap.autoUpdate,
    drawing_buffer: [gl.drawingBufferWidth, gl.drawingBufferHeight]
  };
})()
"""


# Two different questions, two different numbers.
#
# submit_ms drives render() in a tight loop and times it.  Through ANGLE that
# measures how long the main thread spends building and handing over the
# command stream -- gl.finish() does not reach across the process boundary, so
# this is emphatically NOT the cost of drawing.  It is still the number that
# matters for whether the scene starves NiceGUI's websocket, which is how this
# page took itself down before.
#
# frame_ms drives render() from requestAnimationFrame instead, so each frame
# waits for the one before it to be presented.  That is the real end-to-end
# cost, floored at the display interval when there is headroom to spare.
BENCH_JS = """
(() => {
  const r = window.CybICS3D.renderer, s = window.CybICS3D.scene,
        c = window.CybICS3D.camera, gl = r.getContext();
  r.render(s, c); gl.finish();                 // warm the pipeline
  const N = %d, t0 = performance.now();
  for (let i = 0; i < N; i++) { r.render(s, c); }
  gl.finish();
  return Math.round((performance.now() - t0) / N * 100) / 100;
})()
"""

RAF_BENCH_JS = """
new Promise(resolve => {
  const r = window.CybICS3D.renderer, s = window.CybICS3D.scene,
        c = window.CybICS3D.camera;
  let n = 0; const N = %d; let t0 = 0;
  const tick = () => {
    r.render(s, c);
    if (n === 0) t0 = performance.now();
    if (++n > N) { resolve(Math.round((performance.now() - t0) / N * 100) / 100); }
    else requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8090/?force3d=1")
    p.add_argument("--out", default="docs/3d/shots/scene.png")
    p.add_argument("--camera", default="overview", choices=sorted(CAMERAS))
    p.add_argument("--gst", type=int, help="pin GST pressure, 0-255")
    p.add_argument("--hpt", type=int, help="pin HPT pressure, 0-255")
    p.add_argument("--exposure", type=float)
    p.add_argument("--settle", type=float, default=1.5, help="seconds before the shutter")
    p.add_argument("--window", type=float, default=3.0, help="seconds to average the frame rate over")
    p.add_argument("--bench", type=int, default=20,
                   help="time this many forced renders; 0 to skip")
    p.add_argument("--soak", type=float, default=0.0, help="watch this long for a self-reload")
    p.add_argument("--hardware-gl", action="store_true", help="use the real GPU if there is one")
    p.add_argument("--width", type=int, default=1400)
    p.add_argument("--height", type=int, default=900)
    args = p.parse_args()

    report = {"url": args.url, "camera": args.camera,
              "gl": "hardware" if args.hardware_gl else "swiftshader"}
    browser = Browser(width=args.width, height=args.height, software_gl=not args.hardware_gl)
    page = None
    try:
        page = browser.page()
        page.navigate(args.url)
        time.sleep(8)

        page.eval(
            "(() => { const t = [...document.querySelectorAll('.q-tab')]"
            ".find(e => /3D/i.test(e.innerText)); t && t.click(); })()"
        )
        t0 = time.monotonic()
        ready = False
        for _ in range(90):
            time.sleep(1)
            try:
                if page.eval("typeof window.CybICS3D") == "object":
                    ready = True
                    break
            except RuntimeError:
                pass
        report["build_seconds"] = round(time.monotonic() - t0, 2) if ready else None
        report["ready"] = ready
        if not ready:
            report["error"] = "the scene never finished building"
            _write(args, report, page)
            return 1

        # Cheap and first: on a software renderer this may be the only window
        # we get.
        snap = safe(page, report, SNAPSHOT_JS, label="snapshot")
        if snap:
            frame0, t_frame0 = snap.pop("frame"), time.monotonic()
            report.update(snap)
        else:
            frame0 = t_frame0 = None

        report["staged"] = stage(page, report, args)
        time.sleep(args.settle)
        report["bytes"] = page.screenshot(args.out)

        if frame0 is not None:
            time.sleep(max(0.0, args.window - (time.monotonic() - t_frame0)))
            after = safe(page, report,
                "(() => { const r = window.CybICS3D.renderer; return {"
                " frame: r.info.render.frame, draw_calls: r.info.render.calls,"
                " triangles: r.info.render.triangles}; })()")
            if after:
                elapsed = time.monotonic() - t_frame0
                report["fps"] = round((after["frame"] - frame0) / elapsed, 1)
                report["frames"] = after["frame"] - frame0
                report["draw_calls"] = after["draw_calls"]
                report["triangles"] = after["triangles"]

        if args.bench:
            report["submit_ms"] = safe(page, report, BENCH_JS % args.bench,
                                       label="submit_ms")
            report["frame_ms"] = safe(page, report, RAF_BENCH_JS % args.bench,
                                      await_promise=True, label="frame_ms")

        if args.soak:
            before = len(page.navigations())
            time.sleep(args.soak)
            page.pump()
            report["soak_seconds"] = args.soak
            report["reloaded"] = len(page.navigations()) > before

        try:
            page.pump()
            report["console_errors"] = page.console_errors()
            report["navigations"] = len(page.navigations())
        except Exception:
            pass
        _write(args, report, page)
        return 1 if (report.get("console_errors") or report.get("reloaded")) else 0
    finally:
        if page is not None:
            try:
                page.pump()
                report.setdefault("console_errors", page.console_errors())
                report.setdefault("navigations", len(page.navigations()))
            except Exception:
                pass
        browser.close()


def _write(args, report, page):
    side = os.path.splitext(args.out)[0] + ".json"
    os.makedirs(os.path.dirname(os.path.abspath(side)) or ".", exist_ok=True)
    with open(side, "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    sys.exit(main())
