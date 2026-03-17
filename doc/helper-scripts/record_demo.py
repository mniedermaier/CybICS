#!/usr/bin/env python3
"""
CybICS Demo Recorder
Launches OBS + Chrome, records the demo automatically, then saves the video.

Requires a .env file in the same directory with:
    OBS_PASSWORD=your_obs_websocket_password
    OBS_PORT=4455
"""

import os
import subprocess
import socket
import struct
import time
import json
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import obsws_python as obs

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

LANDING_URL = "http://localhost:80"
OUTPUT_DIR = os.path.expanduser("~/Videos/cybics-demo")
os.makedirs(OUTPUT_DIR, exist_ok=True)
WIDTH = 1920
HEIGHT = 1080

OBS_PASSWORD = os.environ["OBS_PASSWORD"]
OBS_PORT = int(os.environ.get("OBS_PORT", "4455"))

ENGWS_CONTAINER = "virtual-engineeringws-1"


def nav_click(page, view_name, wait=3000):
    btn = page.query_selector(f"#{view_name}-btn")
    if btn:
        box = btn.bounding_box()
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.wait_for_timeout(300)
            btn.click()
            page.wait_for_timeout(wait)


def hover_el(page, selector, pause=600):
    el = page.query_selector(selector)
    if el:
        box = el.bounding_box()
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.wait_for_timeout(pause)


def iframe_page(page, iframe_id):
    el = page.query_selector(f"#{iframe_id}")
    if el:
        return el.content_frame()
    return None


def engws_dblclick(screen_x, screen_y):
    """Double-click inside the Engineering WS via XTEST fake_input."""
    result = subprocess.run(
        ["docker", "exec", ENGWS_CONTAINER, "python3", "-c", f"""
import time
from Xlib import X, display
from Xlib.ext import xtest

d = display.Display(':1')
xtest.fake_input(d, X.MotionNotify, x={screen_x}, y={screen_y})
d.sync()
time.sleep(0.1)
for _ in range(2):
    xtest.fake_input(d, X.ButtonPress, detail=1)
    d.sync()
    time.sleep(0.03)
    xtest.fake_input(d, X.ButtonRelease, detail=1)
    d.sync()
    time.sleep(0.08)
d.sync()
print('Double-clicked at', {screen_x}, {screen_y})
"""],
        capture_output=True, text=True, timeout=10,
    )
    print(f"    engws_dblclick: {result.stdout.strip()}")
    if result.stderr.strip():
        print(f"    engws_dblclick stderr: {result.stderr.strip()[:200]}")


def generate_ids_data():
    """Trigger IDS alerts so the dashboard has real data."""
    import requests
    PLC_IP = "172.18.0.3"
    IDS_URL = "http://localhost:8443"

    try:
        r = requests.get(f"{IDS_URL}/api/status", timeout=3)
        data = r.json()
        if data["stats"]["alerts_total"] > 0:
            print(f"    IDS already has {data['stats']['alerts_total']} alerts")
            return
    except Exception:
        print("    Warning: cannot reach IDS")
        return

    print("    Triggering port scan...")
    for port in [22, 80, 102, 443, 502, 1881, 8080, 8443]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((PLC_IP, port))
            s.close()
        except Exception:
            pass

    time.sleep(1)
    print("    Triggering Modbus writes...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((PLC_IP, 502))
        for i in range(12):
            pkt = struct.pack(">HHHBBHH", 1, 0, 6, 1, 0x06, 1124, 100 + i)
            s.send(pkt)
            s.recv(256)
            time.sleep(0.1)
        s.close()
    except Exception:
        pass

    time.sleep(1)
    print("    Triggering S7 access...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((PLC_IP, 102))
        cotp_cr = bytes([
            0x03, 0x00, 0x00, 0x16, 0x11, 0xE0, 0x00, 0x00,
            0x00, 0x01, 0x00, 0xC0, 0x01, 0x0A, 0xC1, 0x02,
            0x01, 0x00, 0xC2, 0x02, 0x01, 0x02,
        ])
        s.send(cotp_cr)
        try:
            s.recv(256)
        except Exception:
            pass
        s.close()
    except Exception:
        pass

    time.sleep(2)
    try:
        r = requests.get(f"{IDS_URL}/api/status", timeout=3)
        data = r.json()
        print(f"    IDS now has {data['stats']['alerts_total']} alerts")
    except Exception:
        pass


def run_demo():
    # Generate IDS data before starting
    print("[0] Generating IDS test data...")
    generate_ids_data()

    # Launch Chrome with remote debugging (separate profile to avoid conflicts)
    print("\nLaunching Chrome with remote debugging...")
    import tempfile
    import json
    chrome_profile = tempfile.mkdtemp(prefix="cybics-chrome-")

    # Write preferences to disable password manager entirely
    default_dir = os.path.join(chrome_profile, "Default")
    os.makedirs(default_dir, exist_ok=True)
    prefs = {
        "credentials_enable_service": False,
        "credentials_enable_autosignin": False,
        "password_manager_enabled": False,
        "profile": {
            "password_manager_leak_detection": False,
            "default_content_setting_values": {
                "notifications": 2,
            },
        },
        "safebrowsing": {
            "enabled": False,
        },
    }
    with open(os.path.join(default_dir, "Preferences"), "w") as f:
        json.dump(prefs, f)

    chrome = subprocess.Popen(
        ["google-chrome", "--remote-debugging-port=9222",
         f"--user-data-dir={chrome_profile}",
         "--start-fullscreen", f"--window-size={WIDTH},{HEIGHT}",
         "--no-first-run", "--no-default-browser-check",
         "--disable-features=PasswordLeakDetection,PasswordCheck,PasswordManagerOnboarding,SafeBrowsing",
         "--password-store=basic",
         "--disable-notifications",
         "--disable-component-update",
         "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(4)

    # Launch OBS minimized
    print("Launching OBS...")
    obs_proc = subprocess.Popen(
        ["obs", "--minimize-to-tray", "--disable-shutdown-check"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(5)

    # Connect to OBS websocket and start recording
    print("Connecting to OBS WebSocket...")
    ws = obs.ReqClient(host="localhost", port=OBS_PORT, password=OBS_PASSWORD)
    ws.set_record_directory(OUTPUT_DIR)
    print("Starting OBS recording...")
    ws.start_record()
    time.sleep(2)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        # Hide the mouse cursor via CSS
        page.add_style_tag(content="* { cursor: none !important; }")

        # ===== 1. LANDING PAGE =====
        print("[1] Landing page...")
        page.goto(LANDING_URL, wait_until="networkidle")
        page.add_style_tag(content="* { cursor: none !important; }")
        page.wait_for_timeout(3000)

        for name in ["openplc", "fuxa", "ids", "vhardware", "engineeringws", "attackmachine"]:
            sel = f".service-box[onclick=\"updateView('{name}')\"]"
            hover_el(page, sel, 400)
        page.wait_for_timeout(1000)

        # ===== 2. CTF Training =====
        print("[2] CTF Training...")
        nav_click(page, "ctf", 3000)
        page.wait_for_timeout(1500)

        page.mouse.move(WIDTH // 2, HEIGHT // 2)
        page.wait_for_timeout(500)
        ctf_frame = iframe_page(page, "ctf-iframe")
        if ctf_frame:
            # Scroll through challenge overview to show all categories
            for _ in range(5):
                ctf_frame.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
                page.wait_for_timeout(1500)
            page.wait_for_timeout(1000)

            # Click on the last challenge card (IDS Evasion)
            # The onclick navigates window.top, so we navigate the iframe src directly
            print("    Opening 'IDS Evasion' challenge (last card)...")
            cards = ctf_frame.query_selector_all(".challenge-card")
            if cards:
                last_card = cards[-1]
                # Scroll it into view first
                last_card.scroll_into_view_if_needed()
                page.wait_for_timeout(1000)

                # Navigate iframe to the challenge page directly
                page.evaluate("""() => {
                    document.getElementById('ctf-iframe').src = '/ctf/challenge/ids_evasion';
                }""")
                page.wait_for_timeout(3000)

                ctf_frame = iframe_page(page, "ctf-iframe")
                if ctf_frame:
                    try:
                        ctf_frame.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass
                    page.wait_for_timeout(1000)

                    # Scroll down to see the challenge content
                    ctf_frame.evaluate("window.scrollBy({top: 300, behavior: 'smooth'})")
                    page.wait_for_timeout(2000)
                    ctf_frame.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
                    page.wait_for_timeout(2000)

                    # Scroll down to flag submission area
                    ctf_frame.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
                    page.wait_for_timeout(2000)

                    # Type the flag and submit
                    print("    Submitting flag...")
                    flag_input = ctf_frame.query_selector('input[type="text"]')
                    if flag_input:
                        flag_input.click()
                        page.wait_for_timeout(300)
                        page.keyboard.type("CybICS(st34lth_0p3r4t0r)", delay=40)
                        page.wait_for_timeout(500)

                        submit_btn = ctf_frame.query_selector('button:has-text("Submit")')
                        if submit_btn:
                            submit_btn.click()
                            page.wait_for_timeout(5000)

        # ===== 3. Virtual Hardware - 2D =====
        print("[3] Virtual Hardware - 2D...")
        nav_click(page, "vhardware", 4000)

        frame = iframe_page(page, "vhardware-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            try:
                frame.wait_for_function(
                    "() => document.querySelectorAll('img').length >= 2 && "
                    "[...document.querySelectorAll('img')].every(i => i.complete && i.naturalWidth > 0)",
                    timeout=15000,
                )
            except Exception:
                pass
            page.wait_for_timeout(3000)

            # ===== 3D View =====
            print("[4] Virtual Hardware - 3D...")
            tab_3d = frame.query_selector("text=3D Visualization")
            if tab_3d:
                tab_3d.click()
                page.wait_for_timeout(5000)

                # Slow rotation
                page.mouse.move(WIDTH // 2, HEIGHT // 2)
                page.wait_for_timeout(500)
                page.mouse.down()
                for i in range(40):
                    page.mouse.move(WIDTH // 2 + i * 8, HEIGHT // 2 + i * 2)
                    page.wait_for_timeout(80)
                page.mouse.up()
                page.wait_for_timeout(2000)

        # ===== 5. OpenPLC =====
        print("[5] OpenPLC...")
        nav_click(page, "openplc", 2000)

        frame = iframe_page(page, "openplc-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(1000)

            user_el = frame.query_selector('input[name="username"]')
            if user_el:
                user_el.click()
                page.wait_for_timeout(150)
                page.keyboard.type("openplc", delay=50)
                page.wait_for_timeout(200)

            pass_el = frame.query_selector('input[name="password"]')
            if pass_el:
                pass_el.click()
                page.wait_for_timeout(150)
                page.keyboard.type("openplc", delay=50)
                page.wait_for_timeout(200)

            login_btn = frame.query_selector('button:has-text("LOGIN"), button:has-text("Login")')
            if login_btn:
                login_btn.click()
                page.wait_for_timeout(3000)
            page.wait_for_timeout(2000)

            programs = frame.query_selector("text=Programs") or frame.query_selector("a[href*='program']")
            if programs:
                programs.click()
                page.wait_for_timeout(2500)

            monitoring = frame.query_selector("text=Monitoring") or frame.query_selector("a[href*='monitor']")
            if monitoring:
                monitoring.click()
                page.wait_for_timeout(2500)

        # ===== 6. FUXA HMI =====
        print("[6] FUXA HMI...")
        nav_click(page, "fuxa", 2000)

        frame = iframe_page(page, "fuxa-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(1000)

            # Login directly without waiting
            try:
                all_inputs = frame.query_selector_all('input')
                visible_text = [i for i in all_inputs if i.is_visible() and i.get_attribute("type") == "text"]
                visible_pass = [i for i in all_inputs if i.is_visible() and i.get_attribute("type") == "password"]

                if visible_text and visible_pass:
                    visible_text[-1].click()
                    page.keyboard.type("admin", delay=30)
                    visible_pass[-1].click()
                    page.keyboard.type("123456", delay=30)
                    page.wait_for_timeout(200)

                    ok_btn = frame.query_selector('button:has-text("OK")')
                    if ok_btn and ok_btn.is_visible():
                        ok_btn.click()
                        page.wait_for_timeout(3000)
            except Exception as e:
                print(f"    FUXA login error: {e}")

            page.wait_for_timeout(3000)

            try:
                pressure = frame.query_selector('button:has-text("Pressure")')
                if pressure and pressure.is_visible():
                    pressure.click()
                    page.wait_for_timeout(2500)

                system = frame.query_selector('button:has-text("System")')
                if system and system.is_visible():
                    system.click()
                    page.wait_for_timeout(2500)
            except Exception as e:
                print(f"    FUXA nav error: {e}")

        # ===== 7. IDS Dashboard =====
        print("[7] IDS Dashboard - Overview...")
        nav_click(page, "ids", 3000)

        frame = iframe_page(page, "ids-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(4000)

            for sel in ["#s-packets", "#s-total", "#s-critical"]:
                el = frame.query_selector(sel)
                if el:
                    box = el.bounding_box()
                    if box:
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            print("[8] IDS - Alerts tab...")
            alerts_btn = frame.query_selector('button[data-tab="alerts"]')
            if alerts_btn:
                alerts_btn.click()
                page.wait_for_timeout(5000)

            print("[9] IDS - Rules tab...")
            rules_btn = frame.query_selector('button[data-tab="rules"]')
            if rules_btn:
                rules_btn.click()
                page.wait_for_timeout(5000)

            print("[10] IDS - Challenges tab...")
            challenges_btn = frame.query_selector('button[data-tab="challenges"]')
            if challenges_btn:
                challenges_btn.click()
                page.wait_for_timeout(5000)

        # ===== 11. Engineering Workstation =====
        print("[11] Engineering Workstation...")
        nav_click(page, "engineeringws", 4000)

        frame = iframe_page(page, "engineeringws-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(3000)

            subprocess.run(
                ["docker", "exec", ENGWS_CONTAINER, "pkill", "-f", "openplc-editor"],
                capture_output=True, timeout=5,
            )
            page.wait_for_timeout(1000)
            print("    Opening CybICS project in OpenPLC Editor...")
            subprocess.Popen(
                ["docker", "exec", ENGWS_CONTAINER, "bash", "-c",
                 "DISPLAY=:1 /usr/local/bin/openplc-editor /root/Desktop/CybICS/ &"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            page.wait_for_timeout(15000)

            print("    Double-clicking CybICS in project tree...")
            engws_dblclick(100, 190)
            page.wait_for_timeout(3000)
            engws_dblclick(100, 190)
            page.wait_for_timeout(5000)

        # ===== 12. Attack Box =====
        print("[12] Attack Box...")
        nav_click(page, "attackmachine", 4000)
        page.wait_for_timeout(4000)

        # ===== BACK TO HOME =====
        print("[13] Back to home...")
        nav_click(page, "all", 3000)
        page.wait_for_timeout(2000)

        print("\nDemo complete!")
        browser.close()

    # Stop OBS recording
    time.sleep(1)
    print("Stopping OBS recording...")
    result = ws.stop_record()
    output_path = result.output_path
    print(f"Video saved: {output_path}")
    ws.disconnect()

    # Close OBS and Chrome
    time.sleep(2)
    obs_proc.terminate()
    chrome.terminate()
    chrome.wait(timeout=5)
    shutil.rmtree(chrome_profile, ignore_errors=True)

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    run_demo()
