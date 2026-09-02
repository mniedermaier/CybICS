# CLAUDE.md

Guidance for Claude Code and other AI assistants working in this repository.
CybICS is an open-source ICS security training platform: a simulated gas pressure
control system (OpenPLC, FUXA, OPC-UA, S7comm, an IDS, CTF modules) that runs
virtually in Docker or on a Raspberry Pi Zero 2 W with a custom PCB and an STM32
running Zephyr. Component details live next to the code in `doc/README.md`,
`software/README.md`, `software/*/README.md`, `hardware/README.md`,
`tests/README.md` and `training/README.md`; read those before changing a component.

## Language

Everything that lands in git or on GitHub is written in **English**: commit
messages, branch names, PR titles and bodies, issues, review comments, code
comments and documentation. Reply to the user in whatever language they write,
but never carry that language into a git artefact. If the user hands you a
German issue or PR text to file, translate it rather than pasting it verbatim.

## Commits, branches and pull requests

Commits follow **Conventional Commits**: `<type>(<scope>): <subject>`.

- Types: `feat`, `fix`, `docs`, `test`, `ci`, `build`, `refactor`, `perf`, `chore`.
  Dependabot uses `pip` and `ci` as prefixes; leave those alone.
- Scopes are the component directories: `stm32`, `hwio-virtual`, `hwio-raspberry`,
  `openplc`, `fuxa`, `opcua`, `s7com`, `landing`, `ids`, `agent`, `attack-machine`,
  `engineeringws`, `rpi-image`, `tests`, `training`, `hardware`, `devcontainer`.
  Omit the scope when a change spans several components.
- Subject: imperative, lower-case first letter, no trailing period, at most 72
  characters. A breaking change gets `!` after the scope and a `BREAKING CHANGE:` footer.
- Body: explain *why*, not what the diff shows. State what was verified and how
  (which tests, against which stack, on which architecture). The history since
  2026 has many good examples; match that depth.
- Keep the attribution trailers the tooling adds (`Co-Authored-By`, `Claude-Session`).

Branches are `feature/<topic>`, `fix/<topic>`, `docs/<topic>`, `ci/<topic>`. All
work reaches `main` through a PR with one approving review. PRs are squash
merged, so the PR title must itself be a valid Conventional Commit subject. A PR
description has three sections: **Cause**, **Fix**, **Verified**. Stacked PRs say
so in the first line and name their base branch.

Never stage `.env`, `.dev.env`, `.docker.env/`, `software/build/`, anything
under `software/rpi-image/deploy/` or `pi-gen/work/`, `historian.sqlite`, `*.log`.
They are gitignored; if one shows up in `git status`, the checkout is wrong, not
the ignore file.

## Repository map

- `cybics.sh`: user-facing entry point (`start`, `stop`, `status`, `logs`, `update`,
  `clean`, `compose`). Drives `.devcontainer/virtual/docker-compose.yml`;
  `--mode minimal|full|withoutai` selects the compose profiles.
- `.devcontainer/`: `virtual/` (the full Docker testbed), `stm32/` (Zephyr
  toolchain), `raspberry/` (arm64 image builds). `prepare-env.sh` generates the
  `.env` files and must run before any manual `docker compose`.
- `software/`: one directory per service. `stm32/` holds the **reference**
  physical process model; `hwio-virtual/` mirrors it for Docker;
  `hwio-raspberry/` bridges I²C/GPIO on real hardware. `landing/` is the Flask
  CTF hub, `ids/` the rule-based IDS, `cybicsagent/` the Ollama RAG assistant,
  `rpi-image/` the pi-gen SD image (`pi-gen/` is a submodule, as is
  `OpenPLC/OpenPLC_v3`). `build.sh` and `installRPI.sh` serve the physical deployment.
- `tests/`: pytest suite, mostly against a live stack.
- `training/`: one directory per module; `training/README.md` has the learning
  path and the MITRE ATT&CK for ICS / D3FEND / NIST SP 800-82r3 mapping.
- `hardware/`: KiCad 8 PCB, KiBot config, enclosure. Generated docs are committed by CI.

## Running and testing

```bash
./cybics.sh start                 # full stack; --mode minimal for core services
pip install -r tests/requirements.txt   # nmap must be installed on the host
pytest tests/ --verbose
```

**Before opening a PR, run the full suite against a running stack.** That is the
acceptance bar for every change, not only for changes to the tested component.
Do not open a PR with a suite you did not run.

- `tests/conftest.py` gates the session on real readiness and **fails** when a
  service is missing. A stack that is down is a failure, never a reason to skip.
- Always run the whole directory. A hand-picked file list is how a new test file
  once silently never ran in CI.
- `TEST_SERVER_IP` and `TEST_<SERVICE>_PORT` point the suite at a remote or
  relocated stack. `test_ids_rules.py` and `test_plant_model_parity.py` need no
  stack and are a quick check, not a substitute.

Firmware (Zephyr v4.3.0, SDK 0.17.4, board `nucleo_g070rb`):

```bash
docker compose -f .devcontainer/stm32/docker-compose.yml run --rm dev scripts/build.sh
```

CI builds with warnings as errors; a warning in `software/stm32/src/` is a
failed build. The toolchain is x86_64 only, see the comment in `software/build.sh`.

Claude has no access to the physical hardware. Changes to `hwio-raspberry`,
STM32 flashing, `installRPI.sh` or `rpi-image` can only be build-checked; say so
in the PR's Verified section.

Nine workflows in `.github/workflows/` must stay green. Two are unusual:
`kibotVerify.yml` auto-commits regenerated PCB docs back to the branch, and
`rpiImage.yml` builds the SD image only on `v*` tags and attaches it to the release.

## Things that must stay in sync

- **Two plant models.** `thread_physical` in `software/stm32/src/main.c` is the
  reference; `physical_process_thread` in `software/hwio-virtual/hardwareAbstraction.py`
  mirrors it. `tests/test_plant_model_parity.py` parses both with regexes and
  fails on drift. Change rates or guards in both, and update the parity test if
  you restructure either function.
- **Container IPs** (`172.18.0.0/24`) live in `.devcontainer/virtual/docker-compose.yml`
  and again in `KNOWN_SERVICES` in `software/ids/rules.py`.
- **Adding a service** touches `.devcontainer/virtual/docker-compose.yml`, the
  `IMAGES` list in `pushDockerRepos.yml`, `software/scripts/build-and-push-versioned.sh`,
  `display_services` in `cybics.sh`, `KNOWN_SERVICES` in `software/ids/rules.py`,
  `REQUIRED_SERVICES` in `tests/conftest.py` and `software/docker-compose.yaml`.
- **Zephyr and SDK versions**: `software/stm32/west.yml`, `ZEPHYR_SDK_VERSION` in
  `buildTest.yml`, the `compilerPath` in `.devcontainer/stm32/devcontainer.json`.
- **pymodbus** is on one version everywhere except `software/landing/`, which is
  still on 3.5.x with no recorded reason. The landing container carries a copy
  of `training/` and runs the modules from its webshell, so a bump there must be
  verified from that webshell. Do not bump it in passing.
- Python dependencies are pinned exactly and managed by Dependabot. Only
  `training/requirements.txt` is intentionally unpinned.

## Generated files: never edit by hand

`software/build/`, `software/stm32/proto/cybics.pb.{c,h}` (nanopb, from
`cybics.proto`), `hardware/pcb/docs/` and `hardware/pcb/pcb/` (KiBot),
`software/FUXA/fuxa-project.json` (export from the FUXA UI), `software/OpenPLC/openplc.db`.

## Things that look like secrets but are not

The OPC-UA test key in `software/opcua/certificates/trusted/`, the credential
list in `training/opcua/credentials.txt`, the Wi-Fi PSK, the OpenPLC and OPC-UA
demo logins and the UART menu password are deliberate parts of a training
platform. Leave them, do not rotate them, do not report them as findings.
TruffleHog only fails on *verified* live credentials, which is the actual bar.

The only real secrets are CI secrets. The Docker Hub push token is confined to
`pushDockerRepos.yml`; every other workflow uses the read-only token, guarded so
fork PRs fall back to anonymous pulls. Keep it that way.

## Training modules and CTF

- A module is `training/<name>/README.md`, optionally with a solution script and
  its own `requirements.txt`. Match the existing tone: technique, steps, then
  how to detect or defend.
- Every module has a row in the mapping table in `training/README.md`. Check
  technique IDs against the current MITRE catalogue; wrong IDs have shipped before.
- Flags have the form `CybICS(...)` and live in `software/landing/ctf_config.json`,
  `software/ids/ids_server.py`, `software/landing/app.py` and the firmware. A new
  challenge needs its `ctf_config.json` entry and a place where the flag is
  actually obtainable. Watch for `0` versus `O`.
- `tests/test_training.py` exercises the attack scenarios; add a test when a
  module has a verifiable effect.

## Blast radius

`landing` and `ids` run with host networking and `NET_ADMIN`/`NET_RAW`; the
landing page also mounts the Docker socket. Changes there affect the host, not
only the container. Use the smallest capability that does the job and mention
the blast radius in the PR.
