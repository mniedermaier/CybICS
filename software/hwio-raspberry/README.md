# Raspberry Pi Hardware I/O Bridge

## Overview
The Raspberry Pi hardware I/O bridge (`hwio-raspberry`) is a Python-based service that acts as an interface between the physical STM32 hardware and the OpenPLC controller. It runs on the Raspberry Pi and enables communication between the microcontroller-based physical process simulation and the PLC software.

## Purpose
This component serves as the critical communication bridge in the physical CybICS setup:

1. **I2C Communication**: Reads sensor data from the STM32 microcontroller via I2C bus
2. **Modbus Bridge**: Writes sensor data to OpenPLC via Modbus TCP
3. **GPIO Control**: Controls indicator LEDs and actuator signals via Raspberry Pi GPIO pins
4. **Network Info**: Sends Raspberry Pi IP address to STM32 for display on LCD
5. **Board Revision**: Reads the version straps at startup and publishes the board revision for the landing page
5. **Heartbeat**: Provides visual indication that the system is running

## Board Revision Detection

From PCB v1.1 the board encodes its revision as a 5-bit code, once for each
controller. The Pi's copy is `R46`-`R50` on **GPIO17, 27, 22, 23 and 10** (BCM;
header pins 11, 13, 15, 16, 19). Each bit is one 10k resistor to GND read
against the internal pull-up: **fitted = 0, omitted = 1**.

`hw_version.py` reads them once at startup and writes the result to
`/var/lib/cybics/hardware.json` on a volume the landing page mounts read-only,
so the revision shows up under *Settings -> Board Revision*. A file rather than
an HTTP endpoint keeps this container inside its 48 MB limit and adds no
listening socket to a privileged process.

`software/stm32/src/hw_version.c` does the same job for the STM32's copy of the
straps on `PC11`-`PC15`. The two must agree on the encoding; the authoritative
table is in [`hardware/README.md`](../../hardware/README.md#version-coding).

Two things it will not pretend to know. A pre-v1.1 board has no strap
footprints, so every pin floats high and reads `0b11111` -- that code means
"v1.0, or a v1.1 assembled without them", and the description says so rather
than claiming v1.0. And a code this build does not recognise is reported as the
newest revision it does know, because codes are only assigned going forward;
falling back to v1.0 would be the damaging guess, since v1.0 is the one
revision whose front panel wiring differs.

## Architecture

### Communication Interfaces

#### I2C Bus (STM32 ↔ Raspberry Pi)
- **Protocol**: I2C (Inter-Integrated Circuit)
- **Bus**: I2C1 (Raspberry Pi channel 1)
- **STM32 Address**: 0x20 (I2C slave)
- **Data Transfer**:
  - **Read**: Sensor values (GST, HPT pressures)
  - **Write**: IP address for LCD display

#### Modbus TCP (Raspberry Pi → OpenPLC)
- **Protocol**: Modbus TCP
- **Target Host**: `openplc` (Docker service) or `localhost` (standalone)
- **Port**: 502
- **Register Mapping**:
  - Register 1124: GST (Gas Storage Tank) pressure
  - Register 1126: HPT (High Pressure Tank) pressure
  - Registers 1200-1206: Flag data
  - Registers 512-515: Actuator states (compressor, valves)


