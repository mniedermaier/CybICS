# CybICS training video series

Tooling to render one lesson video per CTF challenge. See
`doc/video-series-plan.md` for the overall plan and decisions.

## Layout

- `render_series.py` — the renderer. Reads a spec, runs its CLI steps for real
  in the named VM, embeds real service views for GUI steps, and produces a
  narrated MP4 with captions and an optional music bed.
- `stage.html` — the themed "stage" the renderer drives (header, slide,
  terminal, iframe/attack-VM and caption modes).
- `specs/<id>.json` — one lesson per challenge. A spec is a list of beats:
  - `card` — title / outro card.
  - `say` — an explanation slide (`head`, `body` HTML) with narration.
  - `run` — a command executed in the VM. With `"vm_desktop": true` at the top
    of the spec (recommended), the renderer embeds the **real attack-VM desktop**
    over noVNC and types the command into a real terminal on it, so the footage
    shows the genuine Kali machine running the attack; `run_seconds` caps how
    long to wait for the command. Without `vm_desktop`, the command runs via
    `docker exec` and its output is replayed in a styled terminal panel (fields
    `hl` regex-highlight and `max_lines`).
  - `show` — embed a URL (a service view) for `seconds`.
  - `vm_web` — drive the attack VM's own browser (Firefox kiosk) to perform the
    challenge, e.g. submit the flag in the real CTF UI. Fields: `url` and an
    ordered `actions` list (`click: [x,y]`, `type: "..."`, `key: "..."`, each
    with an optional `wait`). The renderer resets CTF progress first so the
    solve on screen is genuine.
  - `web` — drive the real web frontend inside the stage (legacy path).
  Every beat has a `say` string (the narration) and an optional `caption`.

The top of a spec also carries `seq` and `slug`, which name the output file
`cybics-<seq>-<slug>.mp4` — see `naming.md` for the series numbering.

## The attack runs in the real attack VM

`vm_desktop` specs show the actual Kali attack machine. The renderer inherits
the running XFCE session inside `virtual-attack-machine-1`, opens one maximized
`xfce4-terminal` on display `:1`, and uses `xdotool` to type each command and
press Enter — so the viewer watches the real desktop execute the real attack,
with genuine output. The desktop is embedded over noVNC (port 6081) with
`resize=remote`, so it fills the frame crisply at 1080p. This needs `xdotool`
and `wmctrl` in the attack-VM image (added to its Dockerfile).

## Requirements

- Playwright + its Chromium, `piper-tts`, `ffmpeg`, `Xvfb`, and `fluidsynth`
  (only for `--music`).
- A Piper voice model. The default is the public-domain LJ Speech voice:
  ```
  mkdir -p ~/.local/share/piper-voices
  curl -L https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ljspeech/high/en_US-ljspeech-high.onnx      -o ~/.local/share/piper-voices/en_US-ljspeech-high.onnx
  curl -L https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ljspeech/high/en_US-ljspeech-high.onnx.json -o ~/.local/share/piper-voices/en_US-ljspeech-high.onnx.json
  ```
- The full lab running (`./cybics.sh start`), so the VMs and services exist.

## Render a lesson

```
python3 render_series.py --spec specs/scanning.json --music
# or with an explicit voice / output:
python3 render_series.py --spec specs/scanning.json \
    --voice ~/.local/share/piper-voices/en_US-ljspeech-high.onnx \
    --out ~/videos/scanning.mp4 --music
```

Output defaults to `~/videos/series-<date>/<id>.mp4`. The `<id>_work/` folder
beside it holds the raw capture and per-beat narration; it can be deleted.

## Notes

- CLI commands run for real against the live lab, so the terminal output is
  genuine. Keep commands fast (seconds) for smooth pacing.
- Narration pronunciation of acronyms is spelled phonetically in the `say`
  text (e.g. "S seven comm", "O P C U A").
- Rendered videos are not committed to git.
