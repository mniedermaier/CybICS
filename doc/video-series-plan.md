# CybICS training video series — implementation plan

A complete, per-challenge video series. One video for each CTF challenge: first
explain what the challenge is about (the theory), then walk through it step by
step, with the actual work carried out in the **attack VM** (Kali) or the
**engineering VM** (OpenPLC Editor desktop).

This document is the plan only. Nothing here is built yet.

## 1. Goals and constraints

- **One video per challenge** — 22 challenges today (see the list at the end).
- **Each video: explain, then do.** Open with a clear explanation of the topic
  (what it is, why it matters, the MITRE mapping), then a step-by-step
  walkthrough.
- **Everything runs in the VMs.** Commands execute inside the Kali attack VM
  (`virtual-attack-machine-1`) or the engineering VM
  (`virtual-engineeringws-1`), against the real lab, so the footage is
  authentic.
- **Consistent look**, reusing the existing recorder stack (Xvfb + Chromium +
  ffmpeg), captions, the public-domain Piper voiceover, and the music cue.
- **Public-domain / permissive assets only** (LJ Speech voice, FluidR3
  soundfont, our own graphics), so the series is free to publish.

One exception: `uart_basic` is hardware-only. It cannot run in a VM and needs
the physical board, so it is produced separately (Phase 4).

## 2. What already exists to build on

- `doc/helper-scripts/record_demo.py` — records a Chromium page on a private
  Xvfb display with ffmpeg, burns lower-third captions from timed section
  marks, adds an intro/outro card, a music bed, and an optional Piper
  voiceover. This is the rendering and audio backbone.
- `doc/helper-scripts/compose_cue.py` — generates the music cue timed to the
  section marks.
- The **Theory Path** articles (`training/theory/`) — already written, with
  diagrams, and mapped to MITRE ATT&CK for ICS / D3FEND / IEC 62443 / NIST.
  These are the source for each video's "what this is about" opening.
- The **training READMEs** (`training/<id>/README.md`) — the audited, corrected
  step-by-step how-tos. These are the source for the walkthrough steps.
- The attack VM now ships the required tools (nmap, ffuf, dsniff/arpspoof,
  ettercap, hydra, wireshark/tshark, the Modbus fuzzer, opcua-client, wordlists)
  and the engineering VM has the OpenPLC Editor.

## 3. The core design decision: how to capture "work in the VM"

There are two kinds of steps, and they are captured differently.

### CLI steps (most challenges)

`nmap`, `ffuf`, `hydra`, `arpspoof`, the Modbus fuzzer, python attack scripts.

**Recommended: run the real command in the VM and present it in a controlled
on-screen terminal.** The engine does `docker exec virtual-attack-machine-1
<command>`, captures the real stdout/stderr and exit code, and renders it in a
terminal panel (command typed out, then the actual output streamed in). The
command genuinely runs in the attack VM against the live lab; we only control
the presentation so it is legible and reliable.

Why not drive the VM's own desktop terminal over noVNC: typing long commands
through the noVNC canvas is slow and flaky, and the tiny in-VNC font reads
poorly at 1080p. The controlled terminal is authentic (real execution, real
output) and reproducible.

### GUI steps (a few challenges)

Wireshark, the OpenPLC Editor (engineering VM), the FUXA HMI, the VNC desktops.

**Capture the actual GUI.** Two sub-options:
- Record the VM's noVNC view inside the recorder's Chromium and drive it via the
  canvas (the demo recorder already opens the OpenPLC Editor this way).
- Or grab the container's own X display directly (run `ffmpeg`/an X tool inside
  the container against display `:1`) for a crisper capture.

The hybrid — controlled terminal for CLI, real GUI capture for GUI — is the
recommendation. Each challenge is tagged CLI, GUI, or mixed (see §8).

## 4. Anatomy of one video (~2–4 min)

1. **Title card** — challenge name, category, points, MITRE technique. (Reuses
   the intro-card mechanism.)
2. **What this is about** (~30–45 s) — narrated explanation from the Theory Path
   article and the challenge description, over a diagram or the target view.
3. **The target** — a few seconds showing what we attack or defend (the landing
   view of the service, or the process on the HMI).
4. **Step by step** — for each step: a caption and narration line, then the
   action:
   - CLI: the command typed into the terminal panel and its real output.
   - GUI: the real interface driven on screen.
   Steps come from the (already corrected) training README.
5. **Result** — the flag obtained, or the effect (an IDS alert appearing, the
   blow-out on the HMI, the flag accepted in the CTF UI).
6. **Outro card** — repo address, "next: <challenge>".

Captions, narration and the music bed are produced by the existing pipeline from
the per-step section marks, so all three stay in sync automatically.

## 5. Architecture: a config-driven series engine

To make 22 videos consistent and maintainable, drive each from a small script,
not bespoke code per video.

- **Per-challenge spec** (`doc/video-series/<id>.yaml` or `.py`): title, theory
  reference, target view, and an ordered list of steps. Each step is one of:
  - `say`: caption + narration only (for the explanation).
  - `run`: a command to execute in a named VM, with an optional expected marker
    in the output (e.g., the flag, an "open" port, an alert count).
  - `gui`: a GUI action (open a view, click, scroll) with a caption.
  - `show`: display a service view / the flag / an IDS alert for N seconds.
- **The engine** (`doc/video-series/render_series.py`): reads a spec, starts the
  Xvfb + ffmpeg capture, renders each step (terminal panel or GUI), records the
  section marks, then hands off to the existing caption/cue/narration steps and
  writes `<id>.mp4`. Shares helpers with `record_demo.py` (extract the common
  bits into a small module both use).
- **A shared "stage" page** (HTML served locally or a local file): a themed
  frame with a header (challenge title), a main area that can show a terminal, a
  slide, or an embedded service iframe, and a caption strip. The engine drives
  it with Playwright. Terminal output is injected as it returns from
  `docker exec`.

This means a new or changed challenge is a spec edit, and a series-wide restyle
is one change to the stage page.

## 6. State management (important)

The lab is stateful, so each recording must start from a known state:

- **Reset CTF progress** before/after where relevant (`/ctf/reset`).
- **Clear IDS alerts** (`/api/alerts/clear`) before detection/evasion videos so
  counts start at zero, and generate exactly the traffic the video shows.
- **Restore defaults** after defense videos (passwords, iptables rules) so the
  next recording starts clean — or record defense videos last.
- **Re-flash / reset the plant** where a video causes a blow-out.
- **Order-sensitive pairs**: the offensive video and its detection video should
  be recorded so the detection one sees the attack it describes.

The engine gets `setup` and `teardown` hooks per spec for this.

## 7. Audio, captions, branding

- **Narration**: Piper, `en_US-ljspeech-high` (public domain). A per-term
  pronunciation map (FUXA, OpenPLC, S7comm, Modbus, OPC-UA, nmap, ffuf) so
  acronyms are spoken correctly.
- **Captions**: burned-in lower-thirds in the CybICS style, as in the demo.
- **Music**: the composed cue as a quiet bed under the narration (as in the
  narrated demo).
- **Intro/outro**: the CybICS logo card; a consistent series lower-third with
  the challenge name and points.

## 8. Per-challenge breakdown (kind, VM, primary tools)

| # | Challenge | Kind | VM | Main tools / actions |
|---|---|---|---|---|
| 1 | scanning | CLI | attack | nmap -sV, service banners |
| 2 | scanning2 | CLI | attack | S7 enumeration on :102 |
| 3 | wireshark_capture | GUI+CLI | attack | tshark/Wireshark, decode Modbus writes |
| 4 | password_attack | CLI | attack | ffuf vs FUXA login |
| 5 | password_openplc | CLI | attack | ffuf vs OpenPLC login, read user flag |
| 6 | flood_overwrite | CLI | attack | python/pymodbus write flood → verify |
| 7 | fuzzingMB | CLI | attack | Modbus fuzzer incl. FC 0x08 → verify |
| 8 | mitm | CLI | attack | arpspoof between HMI and PLC → verify |
| 9 | opcua | CLI | attack | opcua client, reach the admin value |
| 10 | plc_programming | GUI | engineering | OpenPLC Editor: modify, compile, download → verify |
| 11 | physical_process | GUI | (HMI) | show the process, cause/observe blow-out |
| 12 | detect_basic | CLI+web | attack + IDS view | scan, then find the port_scan alert |
| 13 | detect_overwrite | CLI+web | attack + IDS view | flood, then find the modbus_flood alert |
| 14 | ids_challenge | CLI+web | attack + IDS view | several attacks → intrusion flag |
| 15 | ids_forensics | web | IDS view | read the alert buffer, answer questions |
| 16 | ids_evasion | CLI+web | attack + IDS view | low-and-slow writes, no alert → flag |
| 17 | defense_openplc_password | GUI | OpenPLC web | change the password → verify |
| 18 | defense_fuxa_password | GUI | FUXA web | change the password → verify |
| 19 | defense_firewall | CLI | (OpenPLC container) | iptables allow only HMI → verify |
| 20 | defense_network_segmentation | CLI | (PLC + OPC-UA) | iptables block attacker → verify |
| 21 | defense_ids_tuning | web | IDS view | confirm engine active, rules firing |
| 22 | uart_basic | hardware | physical board | serial console, separate production |

## 9. Roadmap

- **Phase 0 — spike (1 video).** Build the engine and stage, produce `scanning`
  end to end (title, theory intro, live nmap in the attack VM shown in the
  terminal panel, the flag, outro, captions, voice, music). Validates the whole
  pipeline. Review and lock the look.
- **Phase 1 — CLI offensive** (scanning2, wireshark_capture, password_attack,
  password_openplc, flood_overwrite, fuzzingMB, mitm, opcua).
- **Phase 2 — detection & IDS** (detect_basic, detect_overwrite, ids_challenge,
  ids_forensics, ids_evasion), with state setup/teardown.
- **Phase 3 — GUI** (plc_programming, physical_process, defense_openplc_password,
  defense_fuxa_password).
- **Phase 4 — remaining defense** (defense_firewall,
  defense_network_segmentation, defense_ids_tuning).
- **Phase 5 — hardware** (uart_basic) on the real board.
- **Phase 6 — series polish**: a short series intro, consistent outro pointing
  to the next video, a playlist, and per-video YouTube metadata (title,
  description, chapters, tags).

## 10. Deliverables

- `doc/video-series/render_series.py` — the engine.
- `doc/video-series/stage.html` — the themed stage page.
- `doc/video-series/<id>.yaml` — one spec per challenge.
- A shared module factored out of `record_demo.py` (capture, captions, cue,
  narration) used by both.
- The rendered `.mp4` files (kept out of git; written to `~/videos/` or a
  chosen output dir).

## 11. Decisions (locked)

1. **Capture style for CLI steps** — *superseded*. The lesson now shows the
   **real attack-VM desktop**: the renderer opens a terminal on the Kali
   machine's display `:1` and types each command into it with `xdotool`, and the
   live desktop is embedded over noVNC. So the footage is the genuine attack VM
   running the attack, not a reconstructed terminal panel. (The earlier decision
   was a controlled terminal fed by `docker exec` output; that path still exists
   for specs without `vm_desktop`.) GUI steps still capture the real interface.
2. **Video length / depth** — fuller **4–5 min** per challenge: a proper theory
   opening, and each step explained, not just shown. Specs should budget
   several `say` beats and generous per-step narration.
3. **Voice** — public-domain Piper `en_US-ljspeech-high`, with a per-term
   pronunciation map.
4. **Output location** — `~/videos/` (a dated subfolder per render run).

With 4–5 min videos the theory opening carries more weight, so each spec pulls a
fuller summary from its Theory Path article and adds "why it matters" and MITRE
context as narration, not just captions.

## 12. Risks

- Driving GUI tools (Wireshark, OpenPLC Editor) reliably on the virtual display
  is the fiddliest part; budget extra time for Phases 3–4.
- State bleed between recordings (alerts, changed passwords, blow-outs) must be
  handled by setup/teardown, or videos will contradict each other.
- The attack-VM image must contain the tools (added recently); the running
  container may need a rebuild/pull before recording.
- Voiceover pronunciation of acronyms needs a small phonetic map.
- Total volume is large (21 VM videos + 1 hardware); plan to batch-render.
