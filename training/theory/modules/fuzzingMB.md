# Modbus fuzzing

In this challenge you point a fuzzer at the PLC's Modbus port and let it send thousands of strange, broken and unusual messages. You are testing **robustness**: does the device answer politely, or does it hang, crash or do something it should not? Field devices are often built for a quiet, trusted network, so input their programmers never imagined can knock them over.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="A fuzzer sends many malformed Modbus frames to a Modbus server: diagnostic function code 8, the non-standard codes 67 and 68, and frames with wrong length fields.">
  <defs><marker id="fz" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="38" width="90" height="44" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="65" y="64" text-anchor="middle" font-size="11" fill="#1a1a1a">fuzzer</text>
  <g font-size="11" text-anchor="middle" fill="currentColor">
    <line x1="110" y1="48" x2="380" y2="48" stroke="#ff6b00" stroke-width="1.4" marker-end="url(#fz)"/>
    <line x1="110" y1="60" x2="380" y2="60" stroke="#ff6b00" stroke-width="1.4" marker-end="url(#fz)"/>
    <line x1="110" y1="72" x2="380" y2="72" stroke="#ff6b00" stroke-width="1.4" marker-end="url(#fz)"/>
    <text x="245" y="40">FC 8 diagnostics, FC 67/68 non-standard, bad lengths</text>
  </g>
  <rect x="382" y="38" width="118" height="44" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="441" y="64" text-anchor="middle" font-size="11">Modbus server</text>
</svg>
<figcaption>A fuzzer sweeps function codes and field values, including rarely used diagnostic codes and vendor-specific ones, and watches for a device that copes badly.</figcaption>
</figure>

## The idea

Imagine testing a vending machine by pressing buttons in every possible order, inserting coins that are slightly too small, and pressing "refund" while it is still dispensing. A well-built machine shrugs it off. A badly built one gets stuck, or hands out a free drink. **Fuzzing** is the same idea for software: you feed a program unexpected input on purpose, a lot of it, and watch what breaks.

There are two main styles:

- **Mutation-based fuzzing** takes a valid message and changes it: flips bytes, cuts it short, makes a length field lie.
- **Generation-based fuzzing** builds messages from the protocol's rules, including the corners that are rarely used.

A crash during fuzzing is a **finding**. For a defender, it is a bug to fix before an attacker finds it. For an attacker, a crash on an industrial controller is a way to stop a process, which MITRE ATT&CK for ICS calls **T0814 Denial of Service**.

## How it looks on CybICS

The target is the Modbus TCP service of the OpenPLC container at `172.18.0.3`, port **502**. A Modbus request has a small header (the MBAP header, which includes a length field), a **function code** that says what to do, and then the data. The fuzzer plays with all of these.

<div data-widget="modbus-frame" data-fc="6" data-address="1126" data-value="90"></div>

Use the frame builder above to see which bytes a fuzzer can change. Try a function code the PLC does not support, or a length that does not match the bytes that follow. A robust server answers with an **exception response**: the same function code with its top bit set (for example `0x86` instead of `0x06`) and an error number.

Two function codes matter for this challenge:

| Code | Name | Why it is interesting |
|---|---|---|
| `0x08` (8) | Diagnostics | Can restart communications or clear counters on some devices. |
| `0x2B` (43) | Encapsulated interface, used for Read Device Identification | Reveals vendor, model and firmware version. |

Neither belongs in normal CybICS traffic, which only reads and writes registers and coils.

<div data-widget="checkpoint" data-id="exception"></div>

## How to approach it

1. **Record a baseline.** Before you fuzz, note how the plant behaves: open the FUXA HMI and check that values update. You need to know what "normal" looks like to spot "broken".
2. **Get the fuzzer.** The challenge uses the open-source Modbus network fuzzer linked from the challenge page. It is a Python script with an interactive menu.
3. **Choose the target.** Enter the PLC's address and port 502.
4. **Pick a mode that covers diagnostics.** The menu offers single function codes, the base protocol and some vendor-specific codes. Make sure your run includes the diagnostic function code.
5. **Watch while it runs.** Keep the HMI open. Does the PLC still answer? Do values freeze? Does the fuzzer report timeouts?
6. **Verify on the challenge page.** It asks the IDS whether it saw your fuzzing traffic.

<div class="callout warning" markdown="1">
**Warning:** never fuzz a real plant that is running. A device that crashes under test may stop controlling a physical process. Fuzz in a lab like CybICS, or on a spare device.
</div>

## Detect and defend

Fuzzing traffic looks very different from the steady polling between an HMI and a PLC.

- **Protocol-aware monitoring.** The CybICS IDS has a rule, `modbus_diagnostic`, that raises an alert whenever a request uses function code 8 or 43. That is exactly the signal the challenge checks.
- **Allow-listing function codes.** If the HMI only ever uses reads and a few writes, a firewall or IDS can block or flag every other code.
- **Input validation in the device.** The real fix is firmware that checks every length and field and answers bad input with an exception instead of crashing.
- **Robustness testing before deployment.** Vendors and asset owners fuzz devices in the lab so a bug is found by them, not by an attacker.

<details class="deep-dive" markdown="1">
<summary>Deep dive: what makes a fuzzer find bugs</summary>

The most productive inputs sit right at a boundary: a length of 0, of 255, or one more than the buffer holds; a register count above the 125 the standard allows; a frame cut off in the middle. Bugs live where a programmer assumed "this can never happen".

A good fuzzer also needs a way to notice failure. Network fuzzers usually send a known-good request after each test case; if that stops being answered, the last few test cases are the suspects. Read Device Identification is also a reconnaissance tool: the answer tells an attacker exactly which firmware to look up, which ATT&CK lists as T0888 Remote System Information Discovery.

</details>

## Before you start

- [Modbus TCP](/theory/modbus): the frame layout and the function codes.

Later on the path:

- [Network scanning](/theory/scanning): finding port 502 in the first place.
- [Detection and monitoring](/theory/detection-monitoring): how rule-based detection works.
