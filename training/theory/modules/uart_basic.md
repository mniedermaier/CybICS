# UART and hardware access

In this challenge you talk to the CybICS microcontroller over a plain serial line, find its login prompt and get past a weak password. No network is involved at all. That is the point: physical access to a circuit board often opens a door that every firewall and IDS on the network never sees. This module needs the physical CybICS board; the virtual Docker setup has no serial console.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="A serial console between the STM32 microcontroller and the Raspberry Pi: three wires, transmit, receive and ground, at 115200 baud, 8 data bits, no parity, 1 stop bit.">
  <rect x="30" y="40" width="150" height="46" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="105" y="60" text-anchor="middle" font-size="11">STM32 board</text>
  <text x="105" y="76" text-anchor="middle" font-size="11">TX / RX / GND pins</text>
  <g stroke="#ff6b00" stroke-width="2">
    <line x1="180" y1="55" x2="330" y2="55"/>
    <line x1="180" y1="63" x2="330" y2="63"/>
    <line x1="180" y1="71" x2="330" y2="71"/>
  </g>
  <text x="255" y="46" text-anchor="middle" font-size="11">3 wires</text>
  <rect x="332" y="40" width="160" height="46" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="412" y="60" text-anchor="middle" font-size="11" fill="#1a1a1a">Raspberry Pi + terminal</text>
  <text x="412" y="76" text-anchor="middle" font-size="11" fill="#1a1a1a">115200 8N1</text>
</svg>
<figcaption>A serial console needs only three wires. It sits below the network, so network security controls never see it.</figcaption>
</figure>

## The idea

A **UART** (Universal Asynchronous Receiver-Transmitter) is the simplest way for two chips to talk: one wire to send (TX), one to receive (RX) and a shared ground (GND). Bits go out one after another at an agreed speed, the **baud rate**. There is no address, no encryption and no login in the wire itself.

Engineers love UARTs for debugging. Almost every embedded device, from a home router to a PLC, has a few small pads on its board that carry a **serial console**: boot messages, debug output and often a command menu. On a finished product those pads are frequently still there.

<div class="callout analogy" markdown="1">
**Analogy:** the network is the front door with a guard. The UART is the service hatch at the back of the building that the builders used and nobody bricked up.
</div>

If the console is protected at all, it is usually by a short password typed in by hand. An attacker who can touch the board can try passwords as long as they like, with nobody watching.

## How it looks on CybICS

The CybICS PCB carries an STM32 microcontroller running the Zephyr real-time operating system. It simulates the gas plant and drives the LEDs and the display. Its serial console is wired to the Raspberry Pi on the same board, where it appears as `/dev/serial0`.

| Setting | Value |
|---|---|
| Speed | 115200 baud |
| Frame | 8 data bits, no parity, 1 stop bit (8N1) |
| Where you connect from | the Raspberry Pi, after logging in with SSH |
| What you see | log messages and a password prompt |

The prompt guards a small menu with the plant status, controls and system information. The challenge page tells you how the password is built: three lowercase letters. Work out how many combinations that allows before you start; it tells you how long a full search can take.

<div data-widget="checkpoint" data-id="keyspace"></div>

## How to approach it

1. **Get onto the Pi.** Log in to the Raspberry Pi with SSH, using the board's address on your network.
2. **Open the serial port.** Use a terminal program such as `picocom` on `/dev/serial0` at 115200 baud. Press Enter and read what the device prints.
3. **Understand the prompt.** What happens after a wrong password? Does it slow down, lock you out or simply ask again? That decides whether guessing is practical.
4. **Automate the guessing.** Typing 17,576 passwords by hand is not realistic. The challenge folder contains `bruteforce_login.py`, which tries every combination of a given length over the serial line and stops when the device reports a successful login. Close `picocom` first: only one program can use the port at a time.
5. **Be patient.** At one or two attempts per second a full search takes hours. Leave it running.
6. **Explore the menu** once you are in, and look at what an attacker at this console can learn.

<details class="deep-dive" markdown="1">
<summary>Deep dive: finding a UART on an unknown board</summary>

On a board you have never seen, look for a row of three or four pads or pins near the processor, sometimes labelled TX, RX, GND and VCC. A multimeter finds ground (continuity to the shield or a ground plane). The TX pin of a running device flickers while it prints at boot, which a logic analyser or an oscilloscope shows clearly, and the timing of the shortest pulse gives you the baud rate.

Connect a 3.3 V USB-to-serial adapter: its RX to the board's TX, its TX to the board's RX, and ground to ground. Never connect VCC, and check the voltage first; a 5 V adapter can damage a 3.3 V chip.

</details>

## Detect and defend

Serial attacks are hard to detect from the network, because they never touch it. Defence is mostly about the hardware and the firmware.

- **Physical access control.** Lock cabinets and control rooms, and use tamper seals so an opened case is noticed.
- **Remove or disable debug ports** in production firmware, or require a strong, per-device credential.
- **No hard-coded passwords.** A password compiled into the firmware is the same on every unit and cannot be changed by the owner. In MITRE ATT&CK for ICS this is **T1694.002 Insecure Credentials: Hardcoded Credentials**.
- **Slow down guessing.** A delay after each failure, or a lockout after a few, turns a search of hours into one of months.
- **Log console logins** to a place the operator can see, so a successful login is not silent.

## Before you start

- [ICS basics](/theory/ics-basics): what the microcontroller does in the plant.
- [PLC fundamentals](/theory/plc-fundamentals): controllers and their I/O.
- [Password attacks](/theory/password_attack): how keyspace size decides the time a guess takes.
