# The 3D plant view

A map of the Three.js scene in the `hwio` container: what it is made of, what
drives it, what it costs, and the traps that are specific to this one.

Read this before changing the scene. It exists because the code is 1800 lines of
JavaScript living inside a Python string, with no build step, no module
boundaries and no type checking — the structure is real, but nothing in the file
announces it.

## Where it lives

| | |
|---|---|
| Source | `software/hwio-virtual/hardwareAbstraction.py`, lines ~731–2534 |
| Form | a JavaScript string passed to `ui.add_body_html()` / `ui.run_javascript()` |
| Served by | NiceGUI, `hwio` container, <http://127.0.0.1:8090/> |
| Three.js | **r128**, vendored at `software/hwio-virtual/static/js/three.min.js` |
| Rebuild | `docker compose -f .devcontainer/virtual/docker-compose.yml up -d --build hwio` |

There is no bundler and no hot reload. Every change is a container rebuild, which
makes a fast verification loop worth more here than in a normal front end — see
[Verifying](#verifying).

**Write for r128, not for current Three.js.** Almost every Three.js answer online
is written against a later release and will fail silently rather than loudly.
The differences that have already bitten this scene:

- `renderer.outputEncoding = THREE.sRGBEncoding` — *not* `outputColorSpace`,
  which does not exist in r128 and assigns without error.
- `THREE.Plane(normal, constant)` keeps the half-space where
  `normal · p + constant ≥ 0`. The sign trips people up.
- `renderer.render()` is a property of the **instance**, not of
  `WebGLRenderer.prototype`. Patching the prototype to count frames does
  nothing at all, silently. Reach the renderer through `window.CybICS3D`.

## World

Metres, +Y up, the plant laid out along X with the camera looking down −Z.

| | |
|---|---|
| Camera | `PerspectiveCamera(60°, aspect, 0.1, 1000)` at `(0, 10, 25)`, looking at the origin |
| Ground | concrete slab at `y = 0`, with a steel grating platform above it |
| GST vessel | left, around `x = −7` |
| HPT vessel | right, around `x = +7` |
| Compressor | centre, body at `y = 1` |
| Chimney | beside HPT, the tallest object in the scene |
| Vessel barrel | `LIQUID_H = 8.0` tall, `LIQUID_R = 1.85` radius |
| Vessel heads | hemispherical, one radius deep at each end, so the vessel spans `−1.85 … 9.85` |

## Sections, in build order

`init3D()` builds these in sequence, yielding to the browser between them.

| # | Section | What it puts in the scene |
|---|---|---|
| 1 | Background | canvas gradient + dot texture, drawn once |
| 2 | Camera, renderer | tone mapping, sRGB output, shadow settings |
| 3 | Environment | 64×32 canvas gradient through `PMREMGenerator` |
| 4 | Lighting | ambient, key directional, fill, accent, 3 spots |
| 5 | Site | concrete floor and expansion-joint grid |
| 6 | Platform | grating bars, cross bars, edge beams, orange safety strips |
| 7 | Text sprites | `makeTextSprite()`, canvas-textured labels |
| 8 | Liquid | the volumetric fill, shared by both vessels |
| 9 | GST | shell, liquid, legs, bands, gauge, manhole + bolts, heads, ladder, indicator, label |
| 10 | HPT | the same, minus the ladder, plus a safety valve |
| 11 | Compressor | skid, body, motor, cooling fins, indicator, control panel, fan |
| 12 | Pipework | inlet, outlet, blowout, flanges with bolt rings, four elbows |
| 13 | Chimney | base, stack, four bands, top cap, heat glow ring |
| 14 | Cabinet, LED panel | the status wall, right of HPT |
| 15 | Particles | gas flow along the outlet pipe; flame at the chimney |
| 16 | Overlay | the HTML status card, not Three.js |
| 17 | Data binding | `fetchData()` |
| 18 | `window.CybICS3D` | the tuning handle |
| 19 | Animation loop | gated and capped |

## Data binding

`fetchData()` polls `/api/state` and is the only path from the plant to the
picture. **The plant data is the truth**: nothing here may smooth, lag or invent
a value.

| Field | Drives |
|---|---|
| `gst`, `hpt` (0–255) | `userData.setLevel(v / 255)` on each vessel's liquid |
| `compressor` | fan speed, body emissive, indicator, point light, gas particles |
| `boSen` | flame particles and the flame light |
| various | the LED panel and the HTML status overlay |

`setLevel(frac)` places the surface so the **volume** below it is `frac` of the
whole vessel, domes included — not the height. `liquidLevel()` bisects
`liquidVolume()` 40 times because the closed form needs a cubic root inside the
heads. Half the pressure is half the tank, which is what anyone reading the
picture assumes.

## What `window.CybICS3D` exposes

```js
CybICS3D.scene / .renderer / .camera   // the objects themselves
CybICS3D.exposure(0.9)                 // overall brightness
CybICS3D.ambient(0.3)                  // flatter or more contrasty
CybICS3D.fill(v) / .accent(v)
CybICS3D.report()                      // current values, to paste back
```

It is also the entry point every tool in `tools/3d/` uses, and the signal that
the scene has finished building (`typeof window.CybICS3D === 'object'`).

## Measured cost

Real numbers from `tools/3d/capture.py`, not estimates. Hardware GL here is an
Intel HD 4000 (2012, Mesa) — deliberately weak, so passing on it means
something. All figures at the `overview` camera: **draw calls depend on frustum
culling, so two cameras are not comparable.**

| | before the restyle | now |
|---|---|---|
| tab-open → scene exists | 1.8 s | 1.0 s |
| draw calls | 241 | 178 |
| triangles | 21 866 | 21 866 |
| meshes | 232 | 168 |
| distinct materials | 108 | 108 |
| lights | 9 | 6 |
| shadow casters | 187 | 123 |
| textures | 13 | 10 |
| frame, rAF-driven | 22.4 ms | 22.5 ms |
| outline segments | — | ~3 500, in one draw call |

Three corrections to what the scene looks like it costs:

- Reading the source suggests ~58 meshes and ~39 materials. At runtime it was
  **232 meshes and 108 materials**, because the grating bars, railings, ladder
  rungs, flange bolts and LED dots are built in loops. Any budget reasoned from
  the source is wrong by a factor of four.
- The GPU is not the bottleneck. The scene is **draw-call bound**, not triangle
  bound: 178 calls for 21 866 triangles. Merging the grating's 65 bars into one
  mesh removed 64 draw calls and changed nothing in the picture.
- **Frame time on this host is not a reliable signal at the ten-millisecond
  level.** The identical scene has measured anywhere between 22 ms and 60 ms
  across runs, and an ablation contradicted a same-page A/B taken minutes
  earlier. Use draw calls, mesh counts and outline segment counts — which are
  deterministic — and quote frame time only from repeated readings.

## Budget

| | now | target |
|---|---|---|
| meshes / materials / lights | 168 / 108 / 6 | no worse |
| tab-open → first frame | 1.0 s hw, ~4 s sw | < 1.5 s |
| shadow passes per frame | 1, maps drawn once | keep at 1 |
| frame, hardware GL | ~22 ms | ≤ 20 ms |
| draw calls | 178 | ≤ 400 |
| page survives 60 s | yes behind the guard | yes |

Hard rules:

- **The page must never reload itself.** NiceGUI logs `reloading because
  implicit handshake failed` when the main thread has starved its websocket.
  That is a build failure, not a flake. Run the control too — the same page with
  the 3D tab closed — so a reload is known to be ours.
- Nothing that does not move gets its shadow redrawn. `shadowMap.autoUpdate =
  false` with one explicit `needsUpdate` is already in place. Keep it.
- The loop stays gated on visibility and capped. It must not render while the
  user is on the other tab.
- The software-renderer fallback stays. `softwareRenderer` detection refuses to
  build the scene without acceleration and `?force3d=1` overrides that; the
  measurements above show why the override is not a default.
- Every claim of "faster" comes with before and after numbers from the driver.

## Verifying

`tools/3d/`:

- **`cdp.py`** — a stdlib-only Chrome DevTools Protocol client. No dependencies,
  because this has to run wherever the stack runs.
- **`capture.py`** — opens the page, clicks the 3D tab, waits for `CybICS3D`,
  optionally pins levels / camera / exposure, writes a PNG and a JSON sidecar.

```bash
tools/3d/capture.py --hardware-gl --gst 200 --hpt 60 --out docs/3d/shots/a.png
tools/3d/capture.py --soak 60          # does the page take itself down?
```

Three things the driver had to learn the hard way, all encoded in it now:

- Headless Chrome falls back to SwiftShader even when a GPU is present.
  `--use-gl=angle --use-angle=gl` is the combination that reaches the DRI node;
  `--use-gl=egl` yields no WebGL context at all. Trust the `gpu` field of the
  report, never the flag.
- Everything cheap is read the moment the scene exists, and the screenshot is
  taken **before** the frame-rate window. On a software renderer the page has a
  few seconds before NiceGUI reloads it, and a run that returns a traceback
  instead of a picture has told us nothing.
- A probe that fails is recorded under `skipped` with its reason. A bare `null`
  that could mean "measured nothing", "the page died" or "the expression was
  wrong" is worse than no number, and this tool only has value if it is believed.

`submit_ms` and `frame_ms` answer different questions. `submit_ms` times
`render()` in a tight loop, which through ANGLE measures main-thread command
submission only — `gl.finish()` does not reach across the process boundary.
`frame_ms` drives `render()` from `requestAnimationFrame`, so each frame waits
for the previous one to be presented, which is the real end-to-end cost.

## Known-good and known-bad, from scars

- A **transparent enclosure must not write depth.** Both vessel shells carry
  `depthWrite: false`. When they did not, they wrote depth over their own
  contents and the liquid was invisible — a fault that survived two wrong
  diagnoses reasoned from the code and was found in one screenshot once the
  vessel was rendered on its own.
- `animate(now)` is called once with `now === undefined`; without a guard the
  `NaN` poisons the frame cap permanently.
- The clipped liquid body is open at the cut, so it is `DoubleSide` with a disc
  riding at the surface to close it.
