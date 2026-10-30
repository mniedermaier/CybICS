# Plant physics sandbox

In this challenge you predict what the CybICS plant will do before anyone touches it. You use a copy of the plant that runs in your browser, set up situations an attacker could create, and read off what happens: when the gas runs out, when the safety valve opens, and how long one false sensor reading keeps a compressor running. Knowing the consequences in advance is what separates a planned attack from a lucky one, and a prepared defender from a surprised one.

## The idea

Pilots learn to handle an engine fire in a flight simulator, not in the air. The simulator follows the same physics as the aircraft, so whatever works there works in the real plane, and nothing burns when it goes wrong.

Industrial plants have the same kind of copy: a **process model**. It is a short list of rules that says how each value changes from one moment to the next. Engineers use it for a **consequence analysis**: what is the worst that one wrong output can do, and how much time is left before a safety layer acts?

Attackers ask the same question. The Stuxnet team had to know how far a centrifuge could be pushed before it broke, and reportedly found out on centrifuges of their own, not on the target. A model lets you ask "what if?" as often as you like, for free.

On CybICS an attacker has two simple levers:

- **Freeze the outputs.** Keep the compressor running, or the valve shut, whatever the pressures do.
- **Forge an input.** Make the Programmable Logic Controller (PLC) believe a pressure that is not real, so that it switches the outputs itself.

## How it looks on CybICS

The plant model runs in the I/O service (`hwio`) in Docker, and in the STM32 firmware on a board. It updates the pressures about once a second; one update is called a **tick**. The rules are short:

| In one tick, when... | High-pressure tank (HPT) | Gas storage tank (GST) |
|---|---|---|
| the compressor runs and the GST holds 50 bar or more | +1 bar | −2 bar |
| the compressor is off and the system valve open | −0 to 2 bar | |
| the refill is on (GST below 251) | | +0 to 3 bar |
| the blow-out valve is open | −0 to 1 bar | |

The **blow-out valve** opens above 220 bar and closes again at 200. It is mechanical, so it works without the PLC.

The PLC scans its program every 50 ms, twenty times per tick. In automatic mode it starts the compressor below 60 bar in the HPT and keeps it running up to 90. That memory is a **latch**: the PLC remembers whether the compressor was running, so the same reading can mean "on" or "off".

<div data-widget="plant-sandbox"></div>

The sandbox follows the same rules as `hwio` and the firmware, with real random draws. A test in the CybICS repository compares the three copies, so they cannot drift apart unnoticed.

<div data-widget="checkpoint" data-id="latch"></div>

## How to approach it

1. **Predict first, then run.** Write down what you expect before pressing *Run*. A model is only useful if it can surprise you.
2. **Set up one situation at a time.** Enter the start pressures, choose the mode and the outputs, then press *Reset to start*. The first update after that is tick 1.
3. **Read the log, not only the chart.** The log names the tick on which something changed and why: the valve opened, the refill stopped, the compressor ran out of gas to push.
4. **Count what really happened.** An output that is switched on is not the same as gas that moves. The sandbox counts the ticks in which the compressor actually moved gas, for the current run and since the start.
5. **Run a control.** Run the same start once without the attacker. A change is only a consequence of the attack if the plant without it does something different. Sometimes it does not: the plant would have done almost the same on its own.
6. **Repeat.** Press *Reset to start* a few times. If a result changes with the random draws, it depends on chance; if it practically never changes, the physics decides it.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the scan race</summary>

The PLC does not measure the HPT itself. The I/O service writes the pressure into holding register 1126 several dozen times a second, and the PLC reads that register in every scan. An attacker who writes the same register over Modbus races the I/O service: each scan sees whichever value arrived last.

If the attacker writes about as often as the I/O service, the attacker wins roughly half of the scans. Writing much faster wins more, but needs hundreds of writes a second, which is exactly what an intrusion detection system notices.

The latch changes the arithmetic. Below 90 bar, one won scan below 60 is enough to start the compressor, and every honest reading afterwards keeps it on, but only up to 90. In automatic mode the PLC would start it there anyway as soon as the consumer has drained the tank below 60, so a single forged scan only starts a normal cycle a little early. It hides in normal operation, and it cannot push the pressure past the cut-out. Above 90, every honest scan switches the compressor off again and every won scan back on, so it runs for about the share of scans the attacker wins. That is a real change, and it costs many writes. Try it with *in a share of the scans*.

The program also has a manual mode in which it writes no outputs at all. An attacker who sets that flag does not have to race anyone.

</details>

## Detect and defend

- **Know your own consequences.** The questions in this challenge are the ones a process hazard analysis asks. Answer them before an incident, not during one.
- **Alarm on the mode, not only on the values.** A switch to manual mode that no operator made is suspicious on its own, even when every pressure still looks normal.
- **Watch who writes sensor values.** A pressure register should have exactly one writer. A second one, at any rate, means a forged reading.
- **Make safety independent of the PLC.** On CybICS the relief valve vents more slowly than the compressor fills, so a compressor held on wins. A pressure switch wired to the compressor's power, or a valve sized for the full flow, would hold whatever the PLC believes.

<div class="callout cybics" markdown="1">
**In CybICS:** later on the path, the Flood & Overwrite challenge forges values on the live plant by brute force, and Physics Never Lies catches a forged reading afterwards. This challenge comes first: it shows what such a forgery would do to the plant, without touching it. A single forged scan hides inside a normal cycle and changes little; a lasting effect takes a flood of writes, or a single write to the mode register.
</div>

## Before you start

- [PLCs and the scan cycle](/theory/plc-fundamentals) for the scan, the latch and manual mode.
- [HMI and SCADA](/theory/hmi-scada) for how a PLC variable becomes a register number.
- [The gas pressure process](/theory/physical_process) for the tanks, the valves and their limits.
- [Programming the controller](/theory/plc_programming) for the program that switches the outputs.

Later on the path:

- [Modbus TCP](/theory/modbus) for the writes that forge a reading.
- [HMI project recon](/theory/hmi_project_recon) for reading the register map out of the HMI.
- [Flood & Overwrite](/theory/flood_overwrite) for forging a reading on the live plant.
- [Physics as a witness](/theory/physics_forensics)
- [Stuxnet (2010)](/theory/stuxnet)

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The sandbox is a third copy of the plant model (`PLANT_MODEL` and
`plantTick` in `software/landing/static/js/theory-widgets.js`), with the
PLC's automatic mode taken from the `scan-cycle` widget's `plcScan`.
`tests/test_plant_model_parity.py` checks its constants and order against
the firmware, and `tests/test_theory_content.py` checks `plcScan` against
`cybICS.st`. The challenge answers are graded on the board and appear
nowhere in the challenge page; `tests/test_plant_physics_sandbox_check.py`
derives them by executing the real hwio tick. The sandbox runs one PLC
decision block of twenty scans per tick and uses the coil the last scan
wrote, which is what hwio sees; the real plant's tick is about 1.05 to 1.1 s
and hwio's write rate depends on Modbus round trips, so the scan-race
shares are approximate. Students who know the latch rule can answer
situation 3 on paper; that is fine, it is the point.

</details>
