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
import os
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


def frame_of(page, iframe_id, timeout=20000):
    page.wait_for_selector(f"#{iframe_id}", timeout=timeout)
    frame = page.query_selector(f"#{iframe_id}").content_frame()
    try:
        frame.wait_for_load_state("networkidle", timeout=timeout)
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

def walkthrough(page):
    # 1. Home: the orientation sections, then the physical process and the
    #    network topology overlays. The page is already loaded when the
    #    capture starts.
    page.wait_for_timeout(3000)
    scroll(page, 4, dy=450, pause=1800)
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    page.wait_for_timeout(1500)
    for toggle in ("togglePhysicalProcess", "toggleNetworkTopology"):
        page.evaluate(f"{toggle}()")
        page.wait_for_timeout(4500)
        page.evaluate(f"{toggle}()")
        page.wait_for_timeout(800)

    # 2. CTF training: the challenge overview, then one challenge with its flag.
    view(page, "ctf", 3000)
    ctf = frame_of(page, "ctf-iframe")
    scroll(ctf, 5, dy=400, pause=1600)
    time.sleep(1)
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
    view(page, "vhardware", 5000)
    hw = frame_of(page, "vhardware-iframe")
    if click_text(hw, "3D Visualization", 5000):
        box = page.query_selector("#vhardware-iframe").bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx, cy)
        page.mouse.down()
        for i in range(40):
            page.mouse.move(cx + i * 8, cy + i * 2)
            page.wait_for_timeout(60)
        page.mouse.up()
        page.wait_for_timeout(2500)
        click_text(hw, "Classic View", 2500)

    # 4. OpenPLC: log in, dashboard, programs, live monitoring.
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
    click_text(plc, "Monitoring", 4000)

    # 5. FUXA: log in, pressure overview, system view.
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
    view(page, "attackmachine", 6000)
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


# ---------------------------------------------------------------------------
# Display, browser, recorder
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    default = Path.home() / "Videos" / "cybics-demo" / f"cybics-demo-{datetime.date.today()}.mp4"
    ap.add_argument("--out", type=Path, default=default)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
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
            try:
                walkthrough(page)
            finally:
                time.sleep(1)
                ffmpeg.terminate()
                ffmpeg.wait(timeout=30)
                print(f"Recorded {time.time() - started:.0f} s")
            browser.close()
        add_intro(recording, args.out)
        print(f"Wrote {args.out}")
    finally:
        if ffmpeg and ffmpeg.poll() is None:
            ffmpeg.kill()
        xvfb.terminate()


if __name__ == "__main__":
    main()
