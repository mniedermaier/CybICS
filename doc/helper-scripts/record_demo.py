#!/usr/bin/env python3
"""
CybICS Demo Video Recorder (~2 minutes)
Navigates entirely through the landing page's built-in views.
"""

import os
from playwright.sync_api import sync_playwright

LANDING_URL = "http://localhost:80"
OUTPUT_DIR = os.path.expanduser("~/Videos/cybics-demo")
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH = 1920
HEIGHT = 1080


def smooth_scroll(page, distance, steps=5, delay=80):
    step = distance // steps
    for _ in range(steps):
        page.mouse.wheel(0, step)
        page.wait_for_timeout(delay)


def nav_click(page, view_name, wait=3000):
    """Click a nav button by its id via landing page."""
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
    """Get the inner page of an iframe by its element id."""
    el = page.query_selector(f"#{iframe_id}")
    if el:
        return el.content_frame()
    return None


def record_demo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        page = context.new_page()

        # ===== 1. LANDING PAGE - Home screen =====
        print("[1/10] Landing page - Home...")
        page.goto(LANDING_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Hover over service boxes on home screen
        for name in ["openplc", "fuxa", "ids", "vhardware", "engineeringws", "attackmachine"]:
            sel = f".service-box[onclick=\"updateView('{name}')\"]"
            hover_el(page, sel, 400)

        page.wait_for_timeout(1000)

        # ===== 2. CTF Training =====
        print("[2/10] CTF Training...")
        nav_click(page, "ctf", 3000)
        page.wait_for_timeout(1500)

        # Scroll inside the CTF content area (the home-screen div inside ctf card)
        # The CTF view replaces the home screen, so scroll the main content area
        smooth_scroll(page, 500, steps=10, delay=100)
        page.wait_for_timeout(1500)
        smooth_scroll(page, 500, steps=10, delay=100)
        page.wait_for_timeout(1500)
        smooth_scroll(page, 500, steps=10, delay=100)
        page.wait_for_timeout(1500)
        smooth_scroll(page, 500, steps=10, delay=100)
        page.wait_for_timeout(1500)

        # ===== 3. OpenPLC (via nav) =====
        print("[3/10] OpenPLC...")
        nav_click(page, "openplc", 3000)

        frame = iframe_page(page, "openplc-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(1500)

            # Login - click username field, type, click password, type, click LOGIN
            user_el = frame.query_selector('input[name="username"]')
            if user_el:
                user_el.click()
                page.wait_for_timeout(200)
                page.keyboard.type("openplc", delay=60)
                page.wait_for_timeout(300)

            pass_el = frame.query_selector('input[name="password"]')
            if pass_el:
                pass_el.click()
                page.wait_for_timeout(200)
                page.keyboard.type("openplc", delay=60)
                page.wait_for_timeout(300)

            # Click LOGIN button
            login_btn = frame.query_selector('button:has-text("LOGIN"), button:has-text("Login")')
            if login_btn:
                login_btn.click()
                page.wait_for_timeout(3000)

            # Browse dashboard - stay for a moment
            page.wait_for_timeout(2000)

            # Click Programs
            programs = frame.query_selector("text=Programs") or frame.query_selector("a[href*='program']")
            if programs:
                programs.click()
                page.wait_for_timeout(2500)

            # Click Monitoring
            monitoring = frame.query_selector("text=Monitoring") or frame.query_selector("a[href*='monitor']")
            if monitoring:
                monitoring.click()
                page.wait_for_timeout(2500)

            # Back to Dashboard
            dashboard = frame.query_selector("text=Dashboard") or frame.query_selector("a[href*='dashboard'], a[href='/']")
            if dashboard:
                dashboard.click()
                page.wait_for_timeout(2000)

        # ===== 4. FUXA HMI (via nav) =====
        print("[4/10] FUXA HMI...")
        nav_click(page, "fuxa", 4000)

        frame = iframe_page(page, "fuxa-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(2000)

            # FUXA shows a "Sign in..." modal dialog
            # Find the visible username and password inputs in the dialog
            try:
                # The dialog has Username label then input, Password label then input
                all_inputs = frame.query_selector_all('input')
                visible_text = [i for i in all_inputs if i.is_visible() and i.get_attribute("type") == "text"]
                visible_pass = [i for i in all_inputs if i.is_visible() and i.get_attribute("type") == "password"]

                if visible_text and visible_pass:
                    # Click and type username
                    visible_text[-1].click()
                    page.wait_for_timeout(200)
                    page.keyboard.type("admin", delay=60)
                    page.wait_for_timeout(300)

                    # Click and type password
                    visible_pass[-1].click()
                    page.wait_for_timeout(200)
                    page.keyboard.type("123456", delay=60)
                    page.wait_for_timeout(300)

                    # Click OK button
                    ok_btn = frame.query_selector('button:has-text("OK")')
                    if ok_btn and ok_btn.is_visible():
                        ok_btn.click()
                        page.wait_for_timeout(3000)
            except Exception as e:
                print(f"    FUXA login error: {e}")

            # Stay on FUXA for a bit to show the HMI
            page.wait_for_timeout(3000)

            # Click Pressure view
            try:
                pressure = frame.query_selector('button:has-text("Pressure")')
                if pressure and pressure.is_visible():
                    pressure.click()
                    page.wait_for_timeout(2500)

                # Click System view
                system = frame.query_selector('button:has-text("System")')
                if system and system.is_visible():
                    system.click()
                    page.wait_for_timeout(2500)

                # Back to Overview
                overview = frame.query_selector('button:has-text("Overview")')
                if overview and overview.is_visible():
                    overview.click()
                    page.wait_for_timeout(2000)
            except Exception as e:
                print(f"    FUXA nav error: {e}")

        # ===== 5. Virtual Hardware - 2D (Classic View) =====
        print("[5/10] Virtual Hardware - 2D...")
        nav_click(page, "vhardware", 4000)

        frame = iframe_page(page, "vhardware-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(4000)

            # Stay on Classic View (2D) to show PCB and sensor data
            page.wait_for_timeout(3000)

            # ===== 6. Virtual Hardware - 3D =====
            print("[6/10] Virtual Hardware - 3D...")
            tab_3d = frame.query_selector("text=3D Visualization")
            if tab_3d:
                tab_3d.click()
                page.wait_for_timeout(5000)

                # Drag to rotate the 3D view
                page.mouse.move(WIDTH // 2, HEIGHT // 2)
                page.wait_for_timeout(500)
                page.mouse.down()
                for i in range(20):
                    page.mouse.move(WIDTH // 2 + i * 15, HEIGHT // 2 + i * 5)
                    page.wait_for_timeout(50)
                page.mouse.up()
                page.wait_for_timeout(2000)

            # Switch back to Classic View
            tab_2d = frame.query_selector("text=Classic View")
            if tab_2d:
                tab_2d.click()
                page.wait_for_timeout(2000)

        # ===== 7. IDS Dashboard =====
        print("[7/10] IDS Dashboard - Overview...")
        nav_click(page, "ids", 3000)

        frame = iframe_page(page, "ids-iframe")
        if frame:
            try:
                frame.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(2500)

            # Overview tab - hover stat cards
            for sel in ["#s-packets", "#s-total", "#s-critical"]:
                el = frame.query_selector(sel)
                if el:
                    box = el.bounding_box()
                    if box:
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        page.wait_for_timeout(400)

            page.wait_for_timeout(1500)

            # Switch to Alerts tab
            print("[8/10] IDS - Alerts tab...")
            alerts_btn = frame.query_selector('button[data-tab="alerts"]')
            if alerts_btn:
                alerts_btn.click()
                page.wait_for_timeout(2500)

            # Switch to Rules tab
            print("[9/10] IDS - Rules tab...")
            rules_btn = frame.query_selector('button[data-tab="rules"]')
            if rules_btn:
                rules_btn.click()
                page.wait_for_timeout(2500)

            # Switch to Challenges tab
            challenges_btn = frame.query_selector('button[data-tab="challenges"]')
            if challenges_btn:
                challenges_btn.click()
                page.wait_for_timeout(2500)

            # Back to Overview
            overview_btn = frame.query_selector('button[data-tab="overview"]')
            if overview_btn:
                overview_btn.click()
                page.wait_for_timeout(1500)

        # ===== 10. Engineering Workstation & Attack Box =====
        print("[10/10] Engineering WS & Attack Box...")
        nav_click(page, "engineeringws", 4000)
        page.wait_for_timeout(3000)

        nav_click(page, "attackmachine", 4000)
        page.wait_for_timeout(3000)

        # ===== BACK TO HOME =====
        print("[End] Back to home...")
        nav_click(page, "all", 3000)
        page.wait_for_timeout(2000)

        # Close — finalizes video
        context.close()
        browser.close()

    # Find and rename the recorded video
    videos = sorted(
        [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".webm")],
        key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
        reverse=True,
    )
    if videos:
        src = os.path.join(OUTPUT_DIR, videos[0])
        dst = os.path.join(OUTPUT_DIR, "cybics-demo.webm")
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(src, dst)
        print(f"\nVideo saved: {dst}")
        size_mb = os.path.getsize(dst) / 1024 / 1024
        print(f"Size: {size_mb:.1f} MB")
    else:
        print("Warning: no video file found!")


if __name__ == "__main__":
    record_demo()
