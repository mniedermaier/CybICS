#!/usr/bin/env python3
"""
CybICS demo recorder.

Drives the landing page of a running virtual stack through every view and
records a walkthrough of roughly two minutes as an H.264 MP4.

Nothing on the desktop is involved: the script starts its own Xvfb display,
opens Chromium on it in kiosk mode, and captures the display with ffmpeg at
30 fps. It needs the stack from './cybics.sh start' in full mode, plus Xvfb,
ffmpeg and Playwright with its Chromium (pip install playwright && playwright
install chromium).

    python3 record_demo.py [--out ~/Videos/cybics-demo/cybics-demo.mp4]
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

LANDING_URL = "http://localhost:80"
WIDTH, HEIGHT = 1920, 1080
FPS = 30
ENGWS_CONTAINER = "virtual-engineeringws-1"
DISPLAY = ":99"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def view(page, name, wait=3000):
    """Switch the landing page to a view, the same way the sidebar does."""
    page.evaluate(f"updateView('{name}')")
    page.wait_for_timeout(wait)
    skip = page.query_selector(".tour-btn-skip")
    if skip and skip.is_visible():
        skip.click()


def frame_of(page, iframe_id, timeout=8000):
    """The iframe's frame once its document is in. Not 'networkidle': the
    virtual hardware page keeps a websocket open and would only time out."""
    page.wait_for_selector(f"#{iframe_id}", timeout=timeout)
    frame = page.query_selector(f"#{iframe_id}").content_frame()
    try:
        frame.wait_for_load_state("domcontentloaded", timeout=timeout)
    except Exception:
        pass
    return frame


def scroll(frame_or_page, steps, dy=350, pause=1400):
    for _ in range(steps):
        frame_or_page.evaluate(f"window.scrollBy({{top: {dy}, behavior: 'smooth'}})")
        time.sleep(pause / 1000)


def click_text(frame, text, wait=2500):
    el = frame.query_selector(f"text={text}")
    if el and el.is_visible():
        el.click()
        time.sleep(wait / 1000)
        return True
    return False


# ---------------------------------------------------------------------------
# The walkthrough
# ---------------------------------------------------------------------------

def walkthrough(page, mark):
    # 1. Home: the orientation sections, then the physical process and the
    #    network topology overlays. The page is already loaded when the
    #    capture starts.
    mark("Landing page", "One hub for every service of the lab, virtual or on the real hardware")
    page.wait_for_timeout(3000)
    scroll(page, 4, dy=450, pause=1800)
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    page.wait_for_timeout(1500)
    for toggle, title, text in (
            ("togglePhysicalProcess", "Physical process", "Gas storage tank, compressor and high-pressure tank, controlled by the PLC"),
            ("toggleNetworkTopology", "Network topology", "Every system of the lab with its address and role")):
        mark(title, text)
        page.evaluate(f"{toggle}()")
        page.wait_for_timeout(4500)
        page.evaluate(f"{toggle}()")
        page.wait_for_timeout(800)

    # 2. CTF training: the challenge overview, then one challenge with its flag.
    mark("CTF training", "Challenges from reconnaissance to attack and defense, each with a flag")
    view(page, "ctf", 3000)
    ctf = frame_of(page, "ctf-iframe")
    scroll(ctf, 5, dy=400, pause=1600)
    time.sleep(1)
    mark("IDS evasion challenge", "Read the task, do it on the lab, submit the flag")
    page.evaluate("document.getElementById('ctf-iframe').src = '/ctf/challenge/ids_evasion'")
    page.wait_for_timeout(3000)
    ctf = frame_of(page, "ctf-iframe")
    scroll(ctf, 3, dy=400, pause=1800)
    flag_input = ctf.query_selector('input[type="text"]')
    if flag_input:
        flag_input.click()
        page.keyboard.type("CybICS(st34lth_0p3r4t0r)", delay=40)
        page.wait_for_timeout(500)
        submit = ctf.query_selector('button:has-text("Submit")')
        if submit:
            submit.click()
            page.wait_for_timeout(4000)

    # 3. Virtual hardware: the board, then the 3D view with a slow rotation.
    mark("Virtual hardware", "The CybICS board simulated in software, same process model as the STM32")
    view(page, "vhardware", 5000)
    hw = frame_of(page, "vhardware-iframe")
    mark("3D view", "The physical process as a scene, live values from the PLC")
    if click_text(hw, "3D Visualization", 5000):
        box = page.query_selector("#vhardware-iframe").bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        # WebGL renders in software on the virtual display, so every mouse
        # move costs about a second there; few, large steps keep this short.
        page.mouse.move(cx, cy)
        page.mouse.down()
        for i in range(1, 13):
            page.mouse.move(cx + i * 28, cy + i * 6)
            page.wait_for_timeout(80)
        page.mouse.up()
        page.wait_for_timeout(2500)
        click_text(hw, "Classic View", 2500)

    # 4. OpenPLC: log in, dashboard, programs, live monitoring.
    mark("OpenPLC", "The controller, running the IEC 61131-3 program of the plant")
    view(page, "openplc", 3000)
    plc = frame_of(page, "openplc-iframe")
    if plc.query_selector('input[name="username"]'):
        plc.click('input[name="username"]')
        page.keyboard.type("openplc", delay=50)
        plc.click('input[name="password"]')
        page.keyboard.type("openplc", delay=50)
        plc.click('button:has-text("LOGIN"), button:has-text("Login"), input[type=submit]')
        page.wait_for_timeout(3500)
        plc = frame_of(page, "openplc-iframe")
    click_text(plc, "Programs", 2500)
    plc = frame_of(page, "openplc-iframe")
    mark("Live monitoring", "Inputs, outputs and variables of the running program")
    click_text(plc, "Monitoring", 4000)

    # 5. FUXA: log in, pressure overview, system view.
    mark("FUXA HMI", "The operator view: pressures, valves, compressor state, trends")
    view(page, "fuxa", 5000)
    fuxa = frame_of(page, "fuxa-iframe")
    for _ in range(20):
        inputs = [i for i in fuxa.query_selector_all("input") if i.is_visible()]
        text = [i for i in inputs if i.get_attribute("type") in ("text", None)]
        pw = [i for i in inputs if i.get_attribute("type") == "password"]
        if text and pw:
            text[-1].click()
            page.keyboard.type("admin", delay=40)
            pw[-1].click()
            page.keyboard.type("123456", delay=40)
            ok = fuxa.query_selector('button:has-text("OK")')
            if ok:
                ok.click()
            for _ in range(16):
                page.wait_for_timeout(500)
                if not any(i.is_visible() for i in fuxa.query_selector_all('input[type="password"]')):
                    break
            page.wait_for_timeout(2500)
            break
        page.wait_for_timeout(500)
    click_text(fuxa, "Pressure", 4000)
    click_text(fuxa, "System", 3500)

    # 6. IDS: overview, alerts, rules, challenges.
    mark("Intrusion detection", "Alerts, detection rules mapped to MITRE ATT&CK for ICS, defense challenges")
    view(page, "ids", 3500)
    ids = frame_of(page, "ids-iframe")
    for tab in ("alerts", "rules", "challenges"):
        btn = ids.query_selector(f'button[data-tab="{tab}"]')
        if btn:
            btn.click()
            page.wait_for_timeout(3000)

    # 7. Engineering workstation with the OpenPLC Editor opened.
    subprocess.run(["docker", "exec", ENGWS_CONTAINER, "pkill", "-f", "Beremiz.py"],
                   capture_output=True, timeout=10)
    subprocess.Popen(["docker", "exec", "-d", ENGWS_CONTAINER, "sh", "-c",
                      "DISPLAY=:1 /usr/local/bin/openplc-editor /root/Desktop/CybICS >/dev/null 2>&1"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    mark("Engineering workstation", "OpenPLC Editor with the Structured Text program of the plant")
    view(page, "engineeringws", 12000)
    # The desktop arrives through noVNC, and the canvas forwards mouse events
    # to the X display in the container. Double-click the ST program in the
    # editor's project tree; its position is in framebuffer coordinates of the
    # 1920x1080 desktop, mapped onto the scaled canvas.
    ews = frame_of(page, "engineeringws-iframe")
    canvas = ews.query_selector("canvas")
    box = canvas.bounding_box() if canvas else None
    if box:
        def fb(x, y):
            return box["x"] + x * box["width"] / 1920, box["y"] + y * box["height"] / 1080
        page.mouse.move(*fb(110, 171))
        page.wait_for_timeout(600)
        page.mouse.dblclick(*fb(110, 171), delay=60)
        page.wait_for_timeout(5000)
        page.mouse.move(*fb(900, 550))
        for _ in range(6):
            page.mouse.wheel(0, 120)
            page.wait_for_timeout(900)
        page.wait_for_timeout(2000)

    # 8. Attack machine, then back home.
    mark("Attack machine", "Kali Linux with ICS tooling, the place to run the training modules from")
    view(page, "attackmachine", 6000)
    mark("", "")
    view(page, "all", 3000)


# ---------------------------------------------------------------------------
# Title card
# ---------------------------------------------------------------------------

LOGO = Path(__file__).resolve().parent.parent / "pics" / "CybICS_logo.png"
INTRO_SECONDS = 3.5
CROSSFADE = 0.8


def add_intro(recording, out):
    """Put the logo on the landing page's background for a few seconds, then
    cross-fade into the recording. Re-encodes once with the same settings."""
    intro = out.with_suffix(".intro.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-loop", "1", "-t", str(INTRO_SECONDS), "-i", str(LOGO),
         "-f", "lavfi", "-t", str(INTRO_SECONDS), "-i", f"color=c=0x1a1a1a:s={WIDTH}x{HEIGHT}:r={FPS}",
         "-filter_complex",
         "[0]scale=900:-1:flags=lanczos[logo];[1][logo]overlay=(W-w)/2:(H-h)/2,"
         "fade=t=in:st=0:d=0.7,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(intro)], check=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(intro), "-i", str(recording),
         "-filter_complex",
         f"[0:v][1:v]xfade=transition=fade:duration={CROSSFADE}:offset={INTRO_SECONDS - CROSSFADE},format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", str(out)],
        check=True)
    intro.unlink()
    recording.unlink()


FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
ACCENT = "#ff6b00"
CAPTION_MAX = 9.0
OUTRO_SECONDS = 4.0
REPO_URL = "github.com/mniedermaier/CybICS"


def _esc(text):
    return text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")


def add_captions(video, marks, offset):
    """Burn a lower-third per section: orange title, one line of text, fading
    in and out. marks are (seconds since capture start, title, text); offset is
    what the title card adds in front."""
    chains = []
    for i, (t, title, text) in enumerate(marks):
        if not title:
            continue
        start = t + offset + 1.0          # the view needs a moment to switch
        nxt = marks[i + 1][0] + offset if i + 1 < len(marks) else start + CAPTION_MAX
        end = min(nxt - 0.4, start + CAPTION_MAX)
        if end - start < 1.5:
            continue
        alpha = f"if(lt(t,{start:.2f}+0.4),(t-{start:.2f})/0.4,if(gt(t,{end:.2f}-0.4),({end:.2f}-t)/0.4,1))"
        enable = f"between(t,{start:.2f},{end:.2f})"
        common = f"x=300:y=h-210:enable='{enable}':alpha='{alpha}'"
        # An invisible two-line drawtext provides the box, sized by the longer
        # line; the title and the text are drawn on top of it separately so
        # they can differ in font and colour while sharing one fade.
        chains.append(f"drawtext=fontfile={FONT}:text='{_esc(title)}\n{_esc(text)}':fontsize=30:fontcolor=white@0"
                      f":box=1:boxcolor=black@0.62:boxborderw=24:line_spacing=34:{common}")
        chains.append(f"drawtext=fontfile={FONT_BOLD}:text='{_esc(title)}':fontsize=40:fontcolor={ACCENT}"
                      f":{common.replace('y=h-210', 'y=h-214')}")
        chains.append(f"drawtext=fontfile={FONT}:text='{_esc(text)}':fontsize=30:fontcolor=white"
                      f":{common.replace('y=h-210', 'y=h-210+64')}")
    if not chains:
        return
    script = video.with_suffix(".captions.txt")
    script.write_text(",\n".join(chains))
    plain = video.with_suffix(".plain.mp4")
    video.rename(plain)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(plain), "-filter_script:v", str(script),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", str(video)],
                   check=True)
    plain.unlink(); script.unlink()


def add_outro(video):
    """Logo and repository address on the same background, cross-faded in."""
    outro = video.with_suffix(".outro.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-loop", "1", "-t", str(OUTRO_SECONDS), "-i", str(LOGO),
         "-f", "lavfi", "-t", str(OUTRO_SECONDS), "-i", f"color=c=0x1a1a1a:s={WIDTH}x{HEIGHT}:r={FPS}",
         "-filter_complex",
         f"[0]scale=900:-1:flags=lanczos[logo];[1][logo]overlay=(W-w)/2:(H-h)/2-60,"
         f"drawtext=fontfile={FONT}:text='{_esc(REPO_URL)}':fontsize=40:fontcolor=white@0.85:x=(w-tw)/2:y=h/2+110,"
         f"fade=t=out:st={OUTRO_SECONDS - 0.8}:d=0.8,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(outro)], check=True)
    body = video.with_suffix(".body.mp4")
    video.rename(body)
    length = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                            "-of", "csv=p=0", str(body)]))
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(body), "-i", str(outro), "-filter_complex",
         f"[0:v][1:v]xfade=transition=fade:duration={CROSSFADE}:offset={length - CROSSFADE:.3f},format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", str(video)], check=True)
    body.unlink(); outro.unlink()


def add_music(out, music):
    """Mux an audio track under the finished video; the picture is not re-encoded."""
    silent = out.with_suffix(".silent.mp4")
    out.rename(silent)
    length = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                            "-of", "csv=p=0", str(silent)]))
    # The picture decides the length: pad the audio if it is shorter, and fade
    # it out over the last four seconds either way.
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(music),
         "-filter_complex", f"[1:a]apad,atrim=0:{length:.3f},afade=t=out:st={length - 4:.3f}:d=4[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
         str(out)], check=True)
    silent.unlink()


# ---------------------------------------------------------------------------
# Display, browser, recorder
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    default = Path.home() / "Videos" / "cybics-demo" / f"cybics-demo-{datetime.date.today()}.mp4"
    ap.add_argument("--out", type=Path, default=default)
    ap.add_argument("--music", type=Path, default=None,
                    help="audio file to put under the video, see compose_cue.py")
    ap.add_argument("--keep-raw", action="store_true",
                    help="keep the raw capture and the section marks next to the output")
    ap.add_argument("--remux", action="store_true",
                    help="do not record; put --music under the existing --out video")
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.remux:
        add_music(args.out, args.music)
        print(f"Wrote {args.out}")
        return
    recording = args.out.with_suffix(".raw.mp4")

    # Kiosk and fullscreen flags do nothing without a window manager, so the
    # tab strip and address bar stay. The display is made taller than the page
    # and ffmpeg grabs only the page area below them.
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{WIDTH}x{HEIGHT + 200}x24", "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    # Chromium picks Wayland over X11 whenever WAYLAND_DISPLAY is set, and would
    # then open on the real desktop instead of the virtual display.
    env = {k: v for k, v in os.environ.items() if k not in ("WAYLAND_DISPLAY", "XDG_SESSION_TYPE")}
    env["DISPLAY"] = DISPLAY
    ffmpeg = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False, env=env,
                args=["--ozone-platform=x11", "--window-position=0,0", f"--window-size={WIDTH},{HEIGHT + 200}",
                      "--no-first-run", "--password-store=basic",
                      "--disable-features=PasswordLeakDetection,PasswordManagerOnboarding"])
            context = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT},
                                          ignore_https_errors=True)
            page = context.new_page()
            page.goto(LANDING_URL, wait_until="networkidle")
            time.sleep(1)
            chrome = page.evaluate("window.outerHeight - window.innerHeight")

            ffmpeg = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "x11grab", "-draw_mouse", "0",
                 "-framerate", str(FPS), "-video_size", f"{WIDTH}x{HEIGHT}", "-i", f"{DISPLAY}+0,{chrome}",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart", str(recording)])
            started = time.time()
            marks = []

            def mark(title, text):
                marks.append((time.time() - started, title, text))

            try:
                walkthrough(page, mark)
            finally:
                time.sleep(1)
                ffmpeg.terminate()
                ffmpeg.wait(timeout=30)
                print(f"Recorded {time.time() - started:.0f} s")
            browser.close()
        args.out.with_suffix(".marks.json").write_text(json.dumps(marks, indent=1))
        if args.keep_raw:
            shutil.copy(recording, args.out.with_suffix(".raw.mp4.keep"))
        add_intro(recording, args.out)
        add_captions(args.out, marks, INTRO_SECONDS - CROSSFADE)
        add_outro(args.out)
        if args.music:
            add_music(args.out, args.music)
        print(f"Wrote {args.out}")
    finally:
        if ffmpeg and ffmpeg.poll() is None:
            ffmpeg.kill()
        xvfb.terminate()


if __name__ == "__main__":
    main()
