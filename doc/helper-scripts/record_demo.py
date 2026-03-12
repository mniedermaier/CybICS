#!/usr/bin/env python3
"""
CybICS Demo Video Recorder (~2 minutes, smooth 30fps)
Navigates entirely through the landing page's built-in views.
Captures screenshots inline at ~30fps, then stitches with ffmpeg.
"""

import os
import time
from playwright.sync_api import sync_playwright

LANDING_URL = "http://localhost:80"
OUTPUT_DIR = os.path.expanduser("~/Videos/cybics-demo")
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH = 1920
HEIGHT = 1080
CAPTURE_FPS = 3   # actual screenshot capture rate (~330ms per frame)
OUTPUT_FPS = 30   # output video framerate (frames are duplicated for smoothness)
FRAME_DIR = os.path.join(OUTPUT_DIR, "frames")
FRAME_INTERVAL = 1.0 / CAPTURE_FPS

# Global frame counter
frame_num = 0


def capture_frame(page):
    """Capture a single screenshot frame."""
    global frame_num
    path = os.path.join(FRAME_DIR, f"frame_{frame_num:06d}.jpg")
    page.screenshot(path=path, type="jpeg", quality=85)
    frame_num += 1


def wait_recording(page, ms):
    """Wait while continuously capturing frames at FPS rate."""
    end = time.time() + ms / 1000.0
    while time.time() < end:
        t0 = time.time()
        capture_frame(page)
        elapsed = time.time() - t0
        remaining = FRAME_INTERVAL - elapsed
        if remaining > 0:
            time.sleep(remaining)


def nav_click(page, view_name, wait=3000):
    btn = page.query_selector(f"#{view_name}-btn")
    if btn:
        box = btn.bounding_box()
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            wait_recording(page, 300)
            btn.click()
            wait_recording(page, wait)


def hover_el(page, selector, pause=600):
    el = page.query_selector(selector)
    if el:
        box = el.bounding_box()
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            wait_recording(page, pause)


def iframe_page(page, iframe_id):
    el = page.query_selector(f"#{iframe_id}")
    if el:
        return el.content_frame()
    return None


def record_demo():
    global frame_num
    frame_num = 0

    # Clean up old frames
    os.makedirs(FRAME_DIR, exist_ok=True)
    for f in os.listdir(FRAME_DIR):
        os.remove(os.path.join(FRAME_DIR, f))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
        )
        page = context.new_page()

        # ===== 1. LANDING PAGE - Home screen =====
        print("[1/10] Landing page - Home...")
        page.goto(LANDING_URL, wait_until="networkidle")
        wait_recording(page, 2500)

        # Hover over service boxes
        for name in ["openplc", "fuxa", "ids", "vhardware", "engineeringws", "attackmachine"]:
            sel = f".service-box[onclick=\"updateView('{name}')\"]"
            hover_el(page, sel, 400)

        wait_recording(page, 1000)

        # ===== 2. CTF Training =====
        print("[2/10] CTF Training...")
        nav_click(page, "ctf", 3000)
        wait_recording(page, 1500)

        page.mouse.move(WIDTH // 2, HEIGHT // 2)
        wait_recording(page, 500)
        ctf_frame = iframe_page(page, "ctf-iframe")
        if ctf_frame:
            for _ in range(3):
                ctf_frame.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
                wait_recording(page, 2000)
            for _ in range(4):
                ctf_frame.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
                wait_recording(page, 2500)
            wait_recording(page, 3000)

        # ===== 3. OpenPLC =====
        print("[3/10] OpenPLC...")
        nav_click(page, "openplc", 2000)

        frame = iframe_page(page, "openplc-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            wait_recording(page, 1000)

            user_el = frame.query_selector('input[name="username"]')
            if user_el:
                user_el.click()
                wait_recording(page, 150)
                page.keyboard.type("openplc", delay=50)
                wait_recording(page, 200)

            pass_el = frame.query_selector('input[name="password"]')
            if pass_el:
                pass_el.click()
                wait_recording(page, 150)
                page.keyboard.type("openplc", delay=50)
                wait_recording(page, 200)

            login_btn = frame.query_selector('button:has-text("LOGIN"), button:has-text("Login")')
            if login_btn:
                login_btn.click()
                wait_recording(page, 3000)

            wait_recording(page, 2000)

            programs = frame.query_selector("text=Programs") or frame.query_selector("a[href*='program']")
            if programs:
                programs.click()
                wait_recording(page, 2500)

            monitoring = frame.query_selector("text=Monitoring") or frame.query_selector("a[href*='monitor']")
            if monitoring:
                monitoring.click()
                wait_recording(page, 2500)

            dashboard = frame.query_selector("text=Dashboard") or frame.query_selector("a[href*='dashboard'], a[href='/']")
            if dashboard:
                dashboard.click()
                wait_recording(page, 2000)

        # ===== 4. FUXA HMI =====
        print("[4/10] FUXA HMI...")
        nav_click(page, "fuxa", 2000)

        frame = iframe_page(page, "fuxa-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            wait_recording(page, 1000)

            try:
                all_inputs = frame.query_selector_all('input')
                visible_text = [i for i in all_inputs if i.is_visible() and i.get_attribute("type") == "text"]
                visible_pass = [i for i in all_inputs if i.is_visible() and i.get_attribute("type") == "password"]

                if visible_text and visible_pass:
                    visible_text[-1].click()
                    wait_recording(page, 150)
                    page.keyboard.type("admin", delay=50)
                    wait_recording(page, 200)

                    visible_pass[-1].click()
                    wait_recording(page, 150)
                    page.keyboard.type("123456", delay=50)
                    wait_recording(page, 200)

                    ok_btn = frame.query_selector('button:has-text("OK")')
                    if ok_btn and ok_btn.is_visible():
                        ok_btn.click()
                        wait_recording(page, 3000)
            except Exception as e:
                print(f"    FUXA login error: {e}")

            wait_recording(page, 3000)

            try:
                pressure = frame.query_selector('button:has-text("Pressure")')
                if pressure and pressure.is_visible():
                    pressure.click()
                    wait_recording(page, 2500)

                system = frame.query_selector('button:has-text("System")')
                if system and system.is_visible():
                    system.click()
                    wait_recording(page, 2500)

                overview = frame.query_selector('button:has-text("Overview")')
                if overview and overview.is_visible():
                    overview.click()
                    wait_recording(page, 2000)
            except Exception as e:
                print(f"    FUXA nav error: {e}")

        # ===== 5. Virtual Hardware - 2D =====
        print("[5/10] Virtual Hardware - 2D...")
        nav_click(page, "vhardware", 4000)

        frame = iframe_page(page, "vhardware-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            wait_recording(page, 4000)
            wait_recording(page, 3000)

            # ===== 6. 3D =====
            print("[6/10] Virtual Hardware - 3D...")
            tab_3d = frame.query_selector("text=3D Visualization")
            if tab_3d:
                tab_3d.click()
                wait_recording(page, 5000)

                page.mouse.move(WIDTH // 2, HEIGHT // 2)
                wait_recording(page, 500)
                page.mouse.down()
                for i in range(20):
                    page.mouse.move(WIDTH // 2 + i * 15, HEIGHT // 2 + i * 5)
                    capture_frame(page)
                    time.sleep(0.03)
                page.mouse.up()
                wait_recording(page, 2000)

            tab_2d = frame.query_selector("text=Classic View")
            if tab_2d:
                tab_2d.click()
                wait_recording(page, 2000)

        # ===== 7. IDS Dashboard =====
        print("[7/10] IDS Dashboard - Overview...")
        nav_click(page, "ids", 3000)

        frame = iframe_page(page, "ids-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            wait_recording(page, 2500)

            for sel in ["#s-packets", "#s-total", "#s-critical"]:
                el = frame.query_selector(sel)
                if el:
                    box = el.bounding_box()
                    if box:
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        wait_recording(page, 400)

            wait_recording(page, 1500)

            print("[8/10] IDS - Alerts tab...")
            alerts_btn = frame.query_selector('button[data-tab="alerts"]')
            if alerts_btn:
                alerts_btn.click()
                wait_recording(page, 2500)

            print("[9/10] IDS - Rules tab...")
            rules_btn = frame.query_selector('button[data-tab="rules"]')
            if rules_btn:
                rules_btn.click()
                wait_recording(page, 2500)

            challenges_btn = frame.query_selector('button[data-tab="challenges"]')
            if challenges_btn:
                challenges_btn.click()
                wait_recording(page, 2500)

            overview_btn = frame.query_selector('button[data-tab="overview"]')
            if overview_btn:
                overview_btn.click()
                wait_recording(page, 1500)

        # ===== 10. Engineering WS & Attack Box =====
        print("[10/10] Engineering WS & Attack Box...")
        nav_click(page, "engineeringws", 4000)
        wait_recording(page, 3000)

        nav_click(page, "attackmachine", 4000)
        wait_recording(page, 3000)

        # ===== BACK TO HOME =====
        print("[End] Back to home...")
        nav_click(page, "all", 3000)
        wait_recording(page, 2000)

        context.close()
        browser.close()

    print(f"    Captured {frame_num} frames")

    # Stitch frames into video with ffmpeg
    output_path = os.path.join(OUTPUT_DIR, "cybics-demo.mp4")
    if os.path.exists(output_path):
        os.remove(output_path)

    print("Encoding video with ffmpeg...")
    ffmpeg_cmd = (
        f"ffmpeg -y -framerate {CAPTURE_FPS} "
        f"-i {FRAME_DIR}/frame_%06d.jpg "
        f"-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p "
        f"-r {OUTPUT_FPS} "
        f"-movflags +faststart "
        f"{output_path}"
    )
    ret = os.system(ffmpeg_cmd + " 2>/dev/null")

    if ret == 0 and os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        duration = frame_num / CAPTURE_FPS
        print(f"\nVideo saved: {output_path}")
        print(f"Duration: {int(duration // 60)}:{int(duration % 60):02d}")
        print(f"Size: {size_mb:.1f} MB")
        print(f"Resolution: {WIDTH}x{HEIGHT} @ {OUTPUT_FPS}fps (captured {frame_num} frames @ ~{CAPTURE_FPS}fps)")
    else:
        print("ffmpeg encoding failed!")

    # Clean up frames
    print("Cleaning up frames...")
    for f in os.listdir(FRAME_DIR):
        os.remove(os.path.join(FRAME_DIR, f))
    os.rmdir(FRAME_DIR)


if __name__ == "__main__":
    record_demo()
