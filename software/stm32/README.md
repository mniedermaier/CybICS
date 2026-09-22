# CybICS STM32 Firmware

## Overview
The STM32 firmware runs on the CybICS PCB and simulates the physical process (gas pressure control system). It runs on a STM32G070RB microcontroller using Zephyr RTOS.

## Hardware
- **Board**: STM32 Nucleo G070RB
- **MCU**: STM32G070RBTx (ARM Cortex-M0+, 64MHz)
- **Memory**: 128KB Flash, 36KB RAM
- **Communication**: UART (115200 baud), I2C (100kHz)

## Features
- Simulates industrial pressure control system
- 16x2 LCD display with system information
- LED indicators for process visualization
- UART menu interface (password: `cyb`)
- I2C communication with Raspberry Pi
- Reads the PCB revision from the version straps and adapts to it
- Front panel works on both board revisions: one button on v1.0, the 5-way
  navigation switch from v1.1

## Board Revision Detection

From PCB v1.1 the board encodes its revision as a 5-bit code on `PC11`..`PC15`,
one 1k resistor to GND per bit: **fitted = 0, omitted = 1**.
`src/hw_version.c` reads the straps once at startup; `hw_version_name()` and
`hw_version_code()` report the result.

Each strap is *probed*, not merely read. A single read cannot tell a missing
resistor from a missing footprint, so `probe_strap()` pulls the pin down, reads,
pulls it up and reads again:

| Reads low pulled down | Reads low pulled up | Meaning |
|---|---|---|
| yes | yes | resistor fitted -- 1k to GND beats the 25k-60k internal pull-up |
| yes | no | nothing on the pin; it follows whichever pull is on |
| no | -- | the pin is being driven; reported as a fault |

`hw_version_straps_fitted()` returns how many of the five are actually
soldered, which is what makes the next section work.

It is reported in three places: the boot log, UART menu option 5, and the
second line of the LCD's build-information screen (press the display button
until `Build <date>` appears), which reads `HH:MM:SS HW v1.1`.

The revision deliberately does *not* go on screen 0. The virtual plant in
`software/hwio-virtual/hardwareAbstraction.py` mirrors that screen, and it
has no PCB whose revision it could show.

One firmware image serves every board revision, so anything whose wiring
changed between revisions must branch on `hw_version_get()` rather than on a
build-time option.

A pre-v1.1 board has no strap footprints, so all five pins float high and read
`0b11111`; that code therefore means "v1.0, or a board whose straps were left
unpopulated" and is never assigned to a real revision. A code this firmware
does not recognise is treated as the newest revision it knows, because codes
are only assigned going forward.

When **no** strap resistor is fitted -- the ambiguous case above -- the firmware
asks PA8 instead, because the two revisions load that pin differently: v1.0 has
R36, 10k to GND, and v1.1 has only R54, 1k in series with a switch that is open
unless somebody is pressing it. A pin that follows the internal pull is
floating and the board is v1.1 or newer; a pin that stays low against the
pull-up has R36 on it and the board is v1.0. `hw_version_straps_missing()`
reports when the probe, rather than the straps, decided.

Two honest caveats. The margin is thin in one direction: against the 25k end of
the internal pull-up, R36 holds the pin at 0.94 V against a V_IL of 0.99 V, so
a v1.0 board with unlucky silicon could read as v1.1. And the probe is wrong in
either direction if the switch is held down during boot. That is why it runs
only when the strap code is already ambiguous and never overrides a board that
states its revision properly -- fit `R41`-`R44` and the question never arises.

## Front Panel

`src/ui_input.c` turns whatever switch the board has into events, so the
display code never learns which board it is running on:

| Board | Contacts | Pressed reads | Internal pull-up |
|---|---|---|---|
| v1.0 | one button, PA8 | high, via R37/R36 | no -- it would fight R36 |
| v1.1+ | 5-way switch: PA8 centre, PC6 up, PC7 right, PD8 left, PD9 down | low, common tied to GND | yes, on all five |

None of that can be decided at build time, because one image serves both, and
the devicetree cannot express it either -- which is why the pins are polled
here rather than handed to Zephyr's input subsystem.

Events are `UI_EVENT_NEXT` and `UI_EVENT_PREV`. Centre, down and right advance
a screen; up and left go back. The single button on a v1.0 board emits `NEXT`,
so **every screen stays reachable on both revisions**: the navigation switch is
allowed to make the UI quicker and never to make part of it unreachable.

The contact-to-direction mapping comes from the SHOU HAN 7x7x5-6P-L WX outline
drawing (LCSC C2858287, sheet `KFC-A07-02-02-2CL`), where F2, F3, F5 and F4 sit
clockwise from the moving contact's upper-left face. `SW3` is placed unrotated
with its locating posts north and south, so that order reads as up, right, down,
left from in front of the board. Nobody has yet pressed a real one -- if a
direction turns out swapped, the four `nav_*` nodes in the overlay are the only
place to change.

Pins are polled every 20 ms and a contact has to agree three times, 60 ms,
before it counts. The switch bounces for up to 20 ms by its datasheet, so that
clears the worst case and still sits far below the ~150 ms at which a person
notices lag. There is deliberately no auto-repeat: with five screens it saves
nobody anything, and repeat is exactly what made the old one-second poll feel
broken -- hold the button for three seconds, advance three screens.

On a v1.0 board the four direction pins are left unconfigured, because `PC6`,
`PC7`, `PD8` and `PD9` are unconnected there and reading four floating inputs
would invent presses out of nothing.

## The LCD

Five screens, cycled with the front panel:

| # | Line 0 | Line 1 |
|---|---|---|
| 0 | `CybICS <version>` | uptime in seconds, right-aligned |
| 1 | WiFi mode | IP address, or the AP SSID suffix |
| 2 | `Physical/real:` | `GST:nnn HPT:nnn` |
| 3 | `Status:` | blowout / operational / valve closed / pressure high / low |
| 4 | `Build <date>` | `<time> HW <revision>` |

The strings live in one marked block in `src/main.c`, and
`software/hwio-virtual` declares the same block, so the panel reads the same in
front of the board and in the browser. `tests/test_display_parity.py` parses
both and fails if they drift apart.

The uptime comes from `k_uptime_get()`. It used to be a count of loop
iterations labelled as seconds, which drifted by however long the LCD writes
took -- minutes a day.

A line is written to the panel only when its text changed. A static screen
therefore costs nothing, where the old code rewrote all 32 characters every
second whether or not anything had moved.

The authoritative code table is in
[`hardware/README.md`](../../hardware/README.md#version-coding). Keep the two
in step when a revision is added.

## Building the Firmware

### Using VS Code Dev Container (Recommended)

1. Open the repository in VS Code
2. Press `F1` → "Dev Containers: Reopen in Container"
3. Choose "CybICS-stm32"
4. Build and flash:
   ```bash
   west build -b nucleo_g070rb
   west flash
   ```

### Using Docker (Raspberry Pi)

For automated flashing via Raspberry Pi GPIO:

```bash
cd software/stm32
./build-docker.sh
docker run --privileged -p 127.0.0.1:3333:3333 localhost:5050/cybics-stm32:latest
```

**Debugging the device from a workstation**

The container keeps OpenOCD running as a GDB server on port 3333, but the port
is bound to the Pi's loopback interface only. OpenOCD halts the core on any
incoming connection and nothing resumes it when the client leaves, so an
exposed port let a plain `nmap -sV` stop the physical process (#162). Forward
the port over SSH and point GDB at the local end:

```bash
ssh -L 3333:127.0.0.1:3333 pi@10.0.0.1
```

The `Attach with External RPi` and `Debug with External RPi` configurations in
`.vscode/launch.json` already target `localhost:3333`. Close the GDB session
cleanly, or run `monitor resume` before detaching, so the core keeps running.

**SWD Connections (Raspberry Pi → STM32):**
- GPIO 25 → SWCLK
- GPIO 24 → SWDIO
- GPIO 18 → NRST
- GND → GND

### Manual Build

If you have Zephyr SDK installed:

```bash
cd software/stm32
west build -b nucleo_g070rb
west flash
west attach  # View serial output
```

## Configuration

Edit `prj.conf` to change settings:

```ini
CONFIG_HEAP_MEM_POOL_SIZE=8192        # Heap size
CONFIG_MAIN_STACK_SIZE=2048           # Stack size
CONFIG_LOG_DEFAULT_LEVEL=3            # Log level (0-4)
CONFIG_SYS_CLOCK_HW_CYCLES_PER_SEC=64000000  # 64 MHz
```

## Debugging

### Enable debug logging
Edit `prj.conf`:
```ini
CONFIG_LOG_DEFAULT_LEVEL=4
CONFIG_LOG_MODE_IMMEDIATE=y
```

## Related Documentation
- [Hardware Overview](../../hardware/README.md)
- [Raspberry Pi I/O Bridge](../hwio-raspberry/README.md)
- [Zephyr Documentation](https://docs.zephyrproject.org/)