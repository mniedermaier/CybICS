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
import argparse, base64, functools, http.server, json, os, socketserver, subprocess, sys, threading, time
from pathlib import Path

from playwright.sync_api import sync_playwright

WIDTH, HEIGHT, FPS = 1920, 1080, 30
DISPLAY = ":98"
HERE = Path(__file__).resolve().parent
HELP = HERE.parent / "helper-scripts"          # compose_cue.py lives here
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

# The attack VM runs an XFCE desktop on display :1, exposed over noVNC on 6081.
# For "run" beats we embed that live desktop and type the real command into a
# real terminal on it, so the footage shows the genuine attack machine at work.
VM_VNC_URL = "http://localhost:6081/vnc.html?autoconnect=true&resize=remote&reconnect=true&show_dot=false"
# Inherit the running XFCE session (D-Bus, runtime dir) so apps we launch from
# `docker exec` join the real desktop session instead of a headless orphan.
VM_ENV = ('P=$(pgrep -x xfce4-panel | head -1); export DISPLAY=:1; '
          'export DBUS_SESSION_BUS_ADDRESS=$(tr "\\0" "\\n" </proc/$P/environ | sed -n "s/^DBUS_SESSION_BUS_ADDRESS=//p"); '
          'export XDG_RUNTIME_DIR=$(tr "\\0" "\\n" </proc/$P/environ | sed -n "s/^XDG_RUNTIME_DIR=//p"); ')


def vm_sh(vm, script, timeout=240):
    """Run a bash script inside the VM (stdin heredoc; -i so stdin is attached)."""
    return subprocess.run(["docker", "exec", "-i", vm, "bash"], input=script,
                          capture_output=True, text=True, timeout=timeout)


def vm_term_open(vm, font="Monospace 15", geom="200x50"):
    """Open one maximized, large-font terminal on the VM desktop and focus it."""
    vm_sh(vm, VM_ENV + (
        'pkill -f xfce4-terminal 2>/dev/null; sleep 1; '
        f'setsid xfce4-terminal --geometry={geom} --font="{font}" --hide-menubar '
        '--title=CybICS-AttackVM </dev/null >/tmp/cyterm.log 2>&1 & '
        'sleep 4; W=$(xdotool search --class xfce4-terminal | tail -1); '
        'wmctrl -i -r $W -b add,maximized_vert,maximized_horz 2>/dev/null; '
        'xdotool windowactivate --sync $W; xdotool mousemove 1912 1070'))


def vm_term_maximize(vm):
    vm_sh(vm, VM_ENV + ('W=$(xdotool search --class xfce4-terminal | tail -1); '
                        'wmctrl -i -r $W -b add,maximized_vert,maximized_horz 2>/dev/null; '
                        'xdotool windowactivate --sync $W; xdotool mousemove 1912 1070'), timeout=30)


def vm_term_run(vm, cmd, clear=True):
    """Type cmd into the focused VM terminal (visibly) and press Enter; run for real.

    The command is passed base64-encoded to avoid any shell/xdotool quoting issues.
    """
    b64 = base64.b64encode(cmd.encode()).decode()
    vm_sh(vm, VM_ENV + (
        'W=$(xdotool search --class xfce4-terminal | tail -1); xdotool windowactivate --sync $W; '
        + ('xdotool type --clearmodifiers "clear"; xdotool key Return; sleep 0.35; ' if clear else '')
        + f'C=$(echo {b64} | base64 -d); '
        'xdotool type --clearmodifiers --delay 42 -- "$C"; xdotool key Return; xdotool mousemove 1912 1070'), timeout=60)


def vm_wait_done(vm, cmd, cap=60):
    """Block until the real command's process leaves the VM process table (or cap)."""
    b64 = base64.b64encode(cmd.encode()).decode()
    t0 = time.time()
    while time.time() - t0 < cap:
        r = vm_sh(vm, VM_ENV + f'C=$(echo {b64} | base64 -d); ps -eo args | grep -F -- "$C" | grep -vq grep && echo RUN || echo IDLE',
                  timeout=20)
        if "IDLE" in (r.stdout or ""):
            return time.time() - t0
        time.sleep(0.5)
    return time.time() - t0


def vm_firefox_open(vm, url, cap=28):
    """Open Firefox in the VM in kiosk mode on `url` with a clean, quiet profile.

    Kiosk hides the tab/URL bar and the first-run clutter, so the recording shows
    just the real dashboard fullscreen — driven for real on the attack machine.
    """
    b64u = base64.b64encode(url.encode()).decode()
    script = VM_ENV.replace("; ", "\n") + f"""
pkill -f firefox 2>/dev/null; sleep 1.5
PROF=/tmp/cyff; rm -rf "$PROF"; mkdir -p "$PROF"
cat > "$PROF/user.js" <<'JS'
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("datareporting.policy.firstRunURL", "");
user_pref("browser.aboutwelcome.enabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.messaging-system.whatsNewPanel.enabled", false);
JS
U=$(echo {b64u} | base64 -d)
setsid firefox --profile "$PROF" --kiosk "$U" </dev/null >/tmp/ff.log 2>&1 &
"""
    vm_sh(vm, script, timeout=30)
    t0 = time.time()
    while time.time() - t0 < cap:
        r = vm_sh(vm, VM_ENV + 'xdotool search --class Navigator >/dev/null 2>&1 && echo Y || echo N', timeout=15)
        if "Y" in (r.stdout or ""):
            break
        time.sleep(0.7)
    time.sleep(6)                                  # let the page paint and settle


def vm_action(vm, a):
    """One scripted desktop action for a vm_web beat: click [x,y], type, or key."""
    if "click" in a:
        x, y = a["click"]
        vm_sh(vm, VM_ENV + f'xdotool mousemove {x} {y}; sleep 0.25; xdotool click 1; sleep 0.15; xdotool mousemove 1912 1070', timeout=20)
    elif "type" in a:
        b64 = base64.b64encode(a["type"].encode()).decode()
        vm_sh(vm, VM_ENV + f'T=$(echo {b64} | base64 -d); xdotool type --clearmodifiers --delay 55 -- "$T"', timeout=30)
    elif "key" in a:
        vm_sh(vm, VM_ENV + f'xdotool key {a["key"]}', timeout=15)


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


def _iframe(page):
    """The stage iframe's content frame, once its document is in."""
    el = page.query_selector("#frame-if")
    fr = el.content_frame() if el else None
    if fr:
        try:
            fr.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception:
            pass
    return fr


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
    outdir = args.out.parent if args.out else Path.home() / "Videos" / ("cybics-training-" + time.strftime("%Y-%m-%d"))
    outdir.mkdir(parents=True, exist_ok=True)
    # Series naming: cybics-NN-slug.mp4 (see doc/video-series/naming.md); falls
    # back to the challenge id for specs without seq/slug.
    base = f"cybics-{int(spec['seq']):02d}-{spec['slug']}" if spec.get("seq") and spec.get("slug") else spec["id"]
    out = args.out or outdir / (base + ".mp4")
    work = outdir / (base + "_work"); work.mkdir(exist_ok=True)
    beats, vm = spec["beats"], spec.get("vm")
    vm_desktop = spec.get("vm_desktop")            # run beats execute in the real VM desktop

    # 1) narration per beat (+ real output only for the legacy synthetic terminal)
    for i, b in enumerate(beats):
        if b["type"] == "run" and not vm_desktop:
            print("exec:", b["cmd"])
            b["_out"] = vm_exec(vm, b["cmd"], b.get("max_lines", 18))
        wav = work / f"n{i:02d}.wav"
        synth(args.voice, b["say"], wav)
        b["_wav"], b["_nd"] = str(wav), dur(wav)

    if vm_desktop:
        print("preparing attack-VM desktop terminal ...")
        vm_term_open(vm)

    # Start each recording from a clean CTF state so the flag submission shown in
    # the video is a genuine fresh solve, not "already solved".
    if any(b["type"] == "vm_web" for b in beats):
        try:
            import urllib.request
            reset = spec.get("ctf_reset", "http://localhost:80/ctf/reset")
            urllib.request.urlopen(urllib.request.Request(reset, method="POST"), timeout=10).read()
            print("CTF progress reset")
        except Exception as e:
            print("CTF reset failed (continuing):", e)

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
            vm_live = False                        # noVNC desktop already embedded?
            for b in beats:
                marks.append(time.time() - t0)
                page.evaluate("(c)=>cyCaption(c)", b.get("caption", ""))
                nd, pad = b["_nd"], 0.8
                if b["type"] == "card":
                    page.evaluate("(t)=>cyCard(t[0],t[1])", [b["title"], b.get("sub", "")])
                    page.evaluate("()=>cyCaption('')"); hold(nd + pad)
                elif b["type"] == "say":
                    page.evaluate("(t)=>cySlide(t[0],t[1])", [b.get("head", ""), b.get("body", "")]); hold(nd + pad)
                elif b["type"] == "run" and vm_desktop:
                    # Show the real attack VM and type the command into its terminal.
                    page.evaluate("()=>cyCaption('')")
                    if not vm_live:
                        page.evaluate("(u)=>cyVM(u)", VM_VNC_URL)
                        hold(5.0)                  # let noVNC connect and the desktop repaint
                        vm_term_maximize(vm)       # refit the terminal to the (resized) desktop
                        hold(1.0); vm_live = True
                    else:
                        page.evaluate("()=>cyVM()")   # re-show the already-connected desktop
                        hold(0.4)
                    page.evaluate("(c)=>cyVCap(c)", b.get("caption", ""))
                    vm_term_run(vm, b["cmd"], clear=b.get("clear", True))
                    ran = vm_wait_done(vm, b["cmd"], cap=b.get("run_seconds", 45))
                    # keep the finished output on screen for at least the narration
                    hold(max(1.2, nd + pad - ran))
                    page.evaluate("()=>cyVCap('')")
                elif b["type"] == "vm_web":
                    # Submit the flag for real in the attack VM's own browser.
                    page.evaluate("()=>cyCaption('')")
                    if not vm_live:
                        page.evaluate("(u)=>cyVM(u)", VM_VNC_URL); hold(4.0); vm_live = True
                    else:
                        page.evaluate("()=>cyVM()"); hold(0.4)
                    page.evaluate("(c)=>cyVCap(c)", b.get("caption", ""))
                    start = time.time()
                    vm_firefox_open(vm, b["url"])         # terminal -> real dashboard, on screen
                    for a in b.get("actions", []):
                        vm_action(vm, a); hold(a.get("wait", 1.0))
                    hold(max(1.5, nd + pad - (time.time() - start)))
                    page.evaluate("()=>cyVCap('')")
                elif b["type"] == "run":
                    page.evaluate("(h)=>cyTerminal(h)", host); page.evaluate("()=>cyClearTerm()")
                    tt = min(2.5, max(0.6, len(b["cmd"]) * 0.045))
                    page.evaluate("(a)=>cyType(a[0],a[1])", [b["cmd"], int(tt * 1000)]); hold(tt + 0.5)
                    stream = max(1.5, nd - tt - 0.6)
                    page.evaluate("(a)=>cyStream(a[0],a[1],a[2])", [b["_out"], int(stream * 1000), b.get("hl", "")])
                    hold(stream + 1.0)
                elif b["type"] == "show":
                    page.evaluate("(u)=>cyIframe(u)", b["url"]); hold(b.get("seconds", nd) + pad)
                elif b["type"] == "web":
                    # Really perform the challenge in the full web frontend.
                    start = time.time()
                    for st in b.get("steps", []):
                        if "goto" in st:
                            page.evaluate("(u)=>cyIframe(u)", st["goto"]); time.sleep(0.4)
                            _iframe(page); time.sleep(st.get("wait", 1500) / 1000)
                        elif "fill" in st:
                            fr = _iframe(page)
                            try: fr.fill(st["fill"], st.get("text", ""), timeout=8000)
                            except Exception as e: print("fill:", e)
                            time.sleep(st.get("wait", 700) / 1000)
                        elif "click" in st:
                            fr = _iframe(page)
                            try: fr.click(st["click"], timeout=8000)
                            except Exception as e: print("click:", e)
                            time.sleep(st.get("wait", 1500) / 1000)
                        elif "wait" in st:
                            time.sleep(st["wait"] / 1000)
                    rem = nd - (time.time() - start)
                    if rem > 0: hold(rem)
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
        fc.append(f"[mus][voc]amix=inputs=2:normalize=0:duration=longest,"
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
