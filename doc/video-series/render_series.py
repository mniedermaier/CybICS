#!/usr/bin/env python3
"""
CybICS training video series renderer.

Renders one lesson video from a JSON spec (see specs/*.json and
doc/video-series-plan.md). CLI steps run for real in the named VM via
`docker exec` and their real output is shown in an on-screen terminal; GUI/show
steps embed the real service. Narration is Piper (public-domain LJ Speech), with
an optional music bed. Pacing is driven by each beat's narration length.

Usage (needs Playwright+Chromium, piper-tts, ffmpeg, Xvfb; fluidsynth for music):

    python3 render_series.py --spec specs/scanning.json \
        --voice ~/.local/share/piper-voices/en_US-ljspeech-high.onnx --music

Output goes to ~/videos/series-<date>/<id>.mp4 unless --out is given.
"""
import argparse, functools, http.server, json, os, socketserver, subprocess, sys, threading, time
from pathlib import Path

from playwright.sync_api import sync_playwright

WIDTH, HEIGHT, FPS = 1920, 1080, 30
DISPLAY = ":98"
HERE = Path(__file__).resolve().parent
HELP = HERE.parent / "helper-scripts"          # compose_cue.py lives here
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"


def dur(p):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def synth(model, text, wav):
    subprocess.run([sys.executable, "-m", "piper", "--model", str(model), "--output_file", str(wav)],
                   input=text.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def vm_exec(vm, cmd, max_lines=18):
    """Run cmd in the VM, return trimmed combined output (real execution)."""
    try:
        r = subprocess.run(["docker", "exec", vm, "bash", "-lc", cmd],
                           capture_output=True, text=True, timeout=240)
        lines = (r.stdout + r.stderr).rstrip("\n").split("\n")
    except subprocess.TimeoutExpired:
        lines = ["(command timed out)"]
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + [f"... ({len(lines) - max_lines + 1} more lines)"]
    return "\n".join(lines)


def serve(directory, port):
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", port), h)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--voice", type=Path,
                    default=Path.home() / ".local/share/piper-voices/en_US-ljspeech-high.onnx")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--music", action="store_true", help="add a quiet music bed (needs fluidsynth)")
    args = ap.parse_args()
    if not args.voice.exists():
        ap.error(f"Piper voice not found: {args.voice} (see doc/video-series/README.md)")

    spec = json.loads(args.spec.read_text())
    outdir = args.out.parent if args.out else Path.home() / "videos" / ("series-" + time.strftime("%Y-%m-%d"))
    outdir.mkdir(parents=True, exist_ok=True)
    out = args.out or outdir / (spec["id"] + ".mp4")
    work = outdir / (spec["id"] + "_work"); work.mkdir(exist_ok=True)
    beats, vm = spec["beats"], spec.get("vm")

    # 1) real command output + narration per beat
    for i, b in enumerate(beats):
        if b["type"] == "run":
            print("exec:", b["cmd"])
            b["_out"] = vm_exec(vm, b["cmd"], b.get("max_lines", 18))
        wav = work / f"n{i:02d}.wav"
        synth(args.voice, b["say"], wav)
        b["_wav"], b["_nd"] = str(wav), dur(wav)

    # 2) drive the stage and capture the screen
    port = 8099
    httpd = serve(HERE, port)
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{WIDTH}x{HEIGHT + 160}x24", "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    env = {k: v for k, v in os.environ.items() if k not in ("WAYLAND_DISPLAY", "XDG_SESSION_TYPE")}
    env["DISPLAY"] = DISPLAY
    raw = work / "raw.mp4"; ff = None; marks = []
    try:
        with sync_playwright() as p:
            br = p.chromium.launch(headless=False, env=env,
                                   args=["--ozone-platform=x11", "--window-position=0,0",
                                         f"--window-size={WIDTH},{HEIGHT + 160}", "--no-first-run"])
            page = br.new_context(viewport={"width": WIDTH, "height": HEIGHT},
                                  ignore_https_errors=True).new_page()
            page.goto(f"http://127.0.0.1:{port}/stage.html", wait_until="load"); time.sleep(1)
            chrome = page.evaluate("window.outerHeight - window.innerHeight")
            page.evaluate("(t)=>cyHeader(t[0],t[1])", [spec["title"], spec.get("badge", "")])
            ff = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "x11grab", "-draw_mouse", "0",
                 "-framerate", str(FPS), "-video_size", f"{WIDTH}x{HEIGHT}", "-i", f"{DISPLAY}+0,{chrome}",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart", str(raw)])
            t0 = time.time()
            hold = lambda s: time.sleep(max(0.1, s))
            host = spec.get("term_host", "root@attack-vm")
            for b in beats:
                marks.append(time.time() - t0)
                page.evaluate("(c)=>cyCaption(c)", b.get("caption", ""))
                nd, pad = b["_nd"], 0.8
                if b["type"] == "card":
                    page.evaluate("(t)=>cyCard(t[0],t[1])", [b["title"], b.get("sub", "")])
                    page.evaluate("()=>cyCaption('')"); hold(nd + pad)
                elif b["type"] == "say":
                    page.evaluate("(t)=>cySlide(t[0],t[1])", [b.get("head", ""), b.get("body", "")]); hold(nd + pad)
                elif b["type"] == "run":
                    page.evaluate("(h)=>cyTerminal(h)", host); page.evaluate("()=>cyClearTerm()")
                    tt = min(2.5, max(0.6, len(b["cmd"]) * 0.045))
                    page.evaluate("(a)=>cyType(a[0],a[1])", [b["cmd"], int(tt * 1000)]); hold(tt + 0.5)
                    stream = max(1.5, nd - tt - 0.6)
                    page.evaluate("(a)=>cyStream(a[0],a[1],a[2])", [b["_out"], int(stream * 1000), b.get("hl", "")])
                    hold(stream + 1.0)
                elif b["type"] == "show":
                    page.evaluate("(u)=>cyIframe(u)", b["url"]); hold(b.get("seconds", nd) + pad)
            hold(0.8)
        ff.terminate(); ff.wait(timeout=30); ff = None
    finally:
        if ff and ff.poll() is None:
            ff.kill()
        xvfb.terminate(); httpd.shutdown()

    # 3) audio: narration at the marks (+ optional music bed), then mux
    vlen = dur(raw)
    inputs = ["-i", str(raw)]; fc = []; labels = []
    for i, b in enumerate(beats):
        inputs += ["-i", b["_wav"]]
        ms = int((marks[i] + 0.15) * 1000)
        fc.append(f"[{i + 1}:a]adelay={ms}|{ms},apad=whole_dur={vlen}[n{i + 1}]")
        labels.append(f"[n{i + 1}]")
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest[voiceraw]")
    fc.append("[voiceraw]dynaudnorm=f=200:g=6,volume=2.0[voice]")
    if args.music:
        cue_mid = work / "cue.mid"
        subprocess.run([sys.executable, str(HELP / "compose_cue.py"), str(cue_mid), "--length", str(int(vlen) + 2)],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["fluidsynth", "-ni", "-q", "-r", "44100", "-g", "0.6", "-F", str(work / "cue_raw.wav"),
                        SF2, str(cue_mid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(work / "cue_raw.wav"),
                        "-af", "loudnorm=I=-21:TP=-2:LRA=11", "-t", str(vlen), "-ar", "44100", str(work / "cue.wav")],
                       check=True)
        inputs += ["-i", str(work / "cue.wav")]
        fc.append(f"[{len(beats) + 1}:a]volume=0.5,aformat=channel_layouts=stereo[mus]")
        fc.append("[voice]aformat=channel_layouts=stereo[voc]")
        fc.append(f"[mus][voc]amix=inputs=2:normalize=0:duration=first,"
                  f"afade=t=out:st={vlen - 3:.3f}:d=3,alimiter=limit=0.95,aresample=44100[mix]")
        amap = "[mix]"
    else:
        fc.append(f"[voice]afade=t=out:st={vlen - 3:.3f}:d=3,aresample=44100[mix]"); amap = "[mix]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs
                   + ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", amap,
                      "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], check=True)
    print(f"Wrote {out} ({dur(out):.0f}s)")


if __name__ == "__main__":
    main()
