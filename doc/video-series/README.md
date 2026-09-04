# CybICS training video series

Tooling to render one lesson video per CTF challenge. See
`doc/video-series-plan.md` for the overall plan and decisions.

## Layout

- `render_series.py` — the renderer. Reads a spec, runs its CLI steps for real
  in the named VM (`docker exec`), shows the real output in an on-screen
  terminal, embeds real service views for GUI steps, and produces an narrated
  MP4 with captions and an optional music bed.
- `stage.html` — the themed "stage" the renderer drives (header, slide,
  terminal, iframe and caption modes).
- `specs/<id>.json` — one lesson per challenge. A spec is a list of beats:
  - `card` — title / outro card.
  - `say` — an explanation slide (`head`, `body` HTML) with narration.
  - `run` — a command executed in the VM; its real output is streamed in the
    terminal. Fields: `cmd`, optional `hl` (regex to highlight), `max_lines`.
  - `show` — embed a URL (a service view) for `seconds`.
  Every beat has a `say` string (the narration) and an optional `caption`.

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
