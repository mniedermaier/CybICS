# CybICS Home Page Rework — Implementation Plan

## Context

`rework_website.txt` asks to redesign the CybICS landing/home page into a "perfect home page" that gives a newcomer everything needed to start with CybICS from scratch — while **keeping the left sidebar nav as is**. The result must look professional and match the existing CybICS design language (orange `#ff6b00` accent, dark glass cards, Segoe UI).

Today the home screen (`software/landing/templates/index.html`, `#home-screen`) is just three grids of large clickable service cards (Core Services / Virtual Only / Tools) that duplicate the sidebar. There is no onboarding content: no greeting/repo link, no purpose/audience info, no access/credentials reference, no learning path, no topology diagram, and no tour.

The landing page is a Flask app (no build step, no bundler, offline-capable, CPU-conscious for Raspberry Pi). It is one self-contained `index.html` with inline `<style>` + inline `<script>`, rendered by `main_page()` in `software/landing/app.py` with `services=SERVICES` from `software/landing/utils/config.py`.

**Confirmed decisions:**
- **Interactive tour** → custom lightweight guided overlay step-tour (dimmed backdrop, highlight box, Next/Prev/Skip). No external libs.
- **Existing big service cards** → removed/condensed into the requested compact "Systems access" info box (URLs/IPs/ports/credentials table). Sidebar remains the way to open systems.

**Constraints:**
- Do not touch the sidebar markup/CSS/behavior.
- Keep everything compositor-cheap (transform/opacity only) — animations were deliberately trimmed for Pi CPU.
- Match existing tokens: accent `#ff6b00`, gradient `#ff6b00→#ff8c42→#ffa500`, card bg `linear-gradient(135deg, rgba(45,45,45,.9), rgba(30,30,40,.95))`, border `rgba(255,107,0,.3)`. Reuse `.service-section`, `.section-title`, `.section-description`, `.service-grid`.
- Support existing light mode (`body.light-mode`) for every new block.
- GitHub repo: https://github.com/mniedermaier/CybICS

## Stage 1 — Content data model + PLAN.md

- Create this `PLAN.md` at repo root.
- In `software/landing/utils/config.py`, add:
  - `ACCESS_INFO`: rows of `{system, url, ip, ports, username, password, note, virtual_only}` for Landing, OpenPLC, FUXA (viewer/operator/admin), IDS, Virtual Hardware, EngWS, Attack Box, OPC-UA, S7.
  - `PURDUE_LEVELS`: ISA-95/Purdue mapping (L0/1 process+PLC → L2 HMI/OPC-UA/S7 → L3/DMZ Landing/IDS/EngWS → external Attack Box).
- Pass both into `render_template('index.html', …)`.

## Stage 2 — Greeting banner + onboarding info boxes

- Greeting banner: "Welcome to CybICS", tagline, short intro, GitHub button linking to the repo (new tab).
- Info-box grid: Purpose, Physical vs Virtual description, Targeted audience (IEC 62443-aligned, Role Operator, hands-on goal).
- New `.info-box` CSS = lighter non-clickable variant of `.service-box`, with light-mode overrides.

## Stage 3 — Systems access info box

- "Systems access" section rendering `ACCESS_INFO` as a responsive table/card list: System · URL/Port · IP · Credentials · notes; virtual-only rows badged.
- Horizontally scrollable wrapper for narrow screens.
- Caption noting these are intentionally-insecure default lab credentials.

## Stage 4 — Learning Path (Theory placeholder + CTF)

- "Learning Path" section with two cards: Theory Path (placeholder/disabled) and CTF (brief intro, clickable → CTF view).

## Stage 5 — Network topology (ISA-95 / Purdue)

- "Network topology" section: inline SVG built from `PURDUE_LEVELS`, horizontal Purdue bands with systems + IPs, theme-aware, static (no animation), scrollable wrapper.

## Stage 6 — Interactive guided tour + polish

- "Take the tour" button in the banner.
- Self-contained JS step-tour: overlay, highlight ring, tooltip (title/text/Skip/Prev/Next/step dots). ~4 steps: sidebar, GitHub repo, access info, CTF/learning path. `Esc`/Skip closes; `localStorage` remembers "seen".
- Final polish: fade-in animations, light-mode contrast, mobile layout across all new blocks.

## Files modified

- `software/landing/utils/config.py` — `ACCESS_INFO`, `PURDUE_LEVELS`.
- `software/landing/app.py` — pass new data to template.
- `software/landing/templates/index.html` — new CSS + rebuilt `#home-screen` markup + tour JS. Sidebar untouched.
- `PLAN.md` — this file.

## Verification

- `docker compose -f docker-compose.dev.yaml up --build` → `http://localhost:80`.
- Verify: banner + GitHub link; info boxes render; access table correct and scrolls on narrow width; CTF card opens CTF view; topology SVG legible in light and dark mode; tour steps through sidebar → repo → access → CTF with Next/Prev/Skip/Esc and step dots; tour auto-shows once then respects `localStorage`.
- Responsive check at ~375px: no unintended horizontal scroll; sidebar auto-collapse unaffected.
- No new always-running JS timers/animations.
