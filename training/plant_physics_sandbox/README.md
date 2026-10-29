# Plant Physics Sandbox

> **MITRE ATT&CK for ICS:** `Impair Process Control` | [T1692.002 - Unauthorized Message: Reporting Message](https://attack.mitre.org/techniques/T1692/002/) | `Impact` | [T0831 - Manipulation of Control](https://attack.mitre.org/techniques/T0831/) | [T0880 - Loss of Safety](https://attack.mitre.org/techniques/T0880/)
>
> **MITRE D3FEND:** [D3-OPM - Operational Process Monitoring](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/) | [D3-OLV - Operational Logic Validation](https://d3fend.mitre.org/technique/d3f:OperationalLogicValidation/)

## Overview
The attackers behind the most damaging attacks on industrial plants did not
experiment on the live process. The Stuxnet team needed to know how far a
centrifuge could be pushed before it broke; the TRITON team reportedly built their
payload against the same safety controller model the plant used. Before they
touched the real plant, they knew **what it would do**.

A defender needs the same knowledge, for the opposite reason: to know which
single change to the plant is dangerous, how much time an operator has
before the relief valve opens, and whether a safety layer can keep up.

In this challenge you do that consequence analysis for the CybICS gas plant.
You do not touch the running plant. You use the **plant sandbox**, a copy of
the plant model that runs in your browser, and predict what the plant does in
three situations an attacker can create. Then you name the one register that
takes the PLC out of the game entirely.

## Background

### Ticks
The plant model (`hwio` in the virtual stack, the STM32 firmware on a board)
updates the pressures in steps of about one second, called **ticks**. In one
tick:

| When | High-pressure tank (HPT) | Gas storage tank (GST) |
|------|------|------|
| Compressor on, GST at **50 bar or more** and HPT below 255 | +1 bar | -2 bar |
| Compressor on, but the GST below 50 bar | no change | no change |
| Compressor off, system valve open | -0 to 2 bar (the consumer) | |
| Compressor off, system valve closed | no change | |
| Refill on and GST below 251 | | +0 to 3 bar on top |
| Blow-out valve open | -0 to 1 bar on top | |

The **blow-out valve** opens when the HPT is above 220 bar and stays open
until it falls back to 200. It is a mechanical relief valve: it works even if
the PLC is gone.

### The PLC
The PLC scans its program every 50 ms, about twenty times in each tick. In
**automatic mode** it switches the outputs from the pressures it reads:

- The compressor starts when the HPT is below 60 and the GST above 50. Once
  it runs, it keeps running while the HPT is below 90 (and the GST above 50).
  This memory is a **latch**: the same HPT of 75 means "on" while filling and
  "off" while draining.
- The system valve is open while the HPT is between 50 and 100.
- The refill starts below 60 bar in the GST and runs until 240.

The PLC also has a **STOP** flag (everything off) and a **MANUAL** flag. In
manual mode the program writes no output at all: the compressor, the valve
and the refill stay exactly as they were, or as somebody writes them over
Modbus. Both flags are holding registers. You find their addresses in the
[HMI Project Recon](../hmi_project_recon/README.md) challenge, or in the PLC
program in the CybICS repository, `software/OpenPLC/cybICS.st`: OpenPLC maps
`%MWn` to holding register 1024 + n.

### The scan race
The PLC does not measure the HPT itself. The I/O service writes the pressure
into a holding register several dozen times a second, and the PLC reads that
register in each scan. An attacker who writes the same register over Modbus
races the I/O service: each scan sees whichever value was written last.
Because of the latch, one won scan below 60 is enough to start the
compressor. Keeping it running above 90 means winning scans again and again.

## Where to run it

Open the Theory Path lesson **Plant physics sandbox** (landing page,
📚 *Theory*, or `/theory/plant_physics_sandbox`). The sandbox there needs no
running plant and changes nothing on it. It shows the tick, both pressures,
the outputs, the blow-out valve, a chart and a log of what happened on which
tick. Two counters show the ticks in which the compressor actually moved gas:
in the current (or last) compressor run, and since the start. The log also
names the length of each run when the compressor switches off.

The tick counter starts at 0 when you press *Reset to start*; the first
update after that is **tick 1**.

You can also work the situations out on paper from the table above. The
sandbox is faster, and it does not forget a rule.

## Task

Answer four questions on the challenge page. They are graded together.

**Situation 1: frozen with the refill off.** An attacker switched the plant
to manual mode while the compressor was running, then closed the system
valve with one coil write (in manual mode the PLC leaves it closed). The
refill is off. GST 150 bar, HPT 60 bar. The outputs stay that way. At which
HPT does the plant come to rest?

**Situation 2: frozen with the refill on.** The same, but the attacker also
switched the refill on, and the plant starts at GST 240 bar, HPT 90 bar.
On which tick does the blow-out valve open?

**Situation 3: one forged reading.** Automatic mode. The compressor is off
and the PLC's latch is not set; HPT 62 bar, GST 200 bar, the refill off. The
HPT is between 50 and 100, so the system valve is open and the consumer
draws gas. The attacker manages to make the PLC see an HPT of 40 bar in
**one single scan**; every scan after that reads the real value again. For
how many ticks does the compressor move gas before the PLC switches it off?
(Then compare with the same start and no attacker, step 4: the comparison
is the real lesson of this situation.)

**The shortcut.** Which holding register does an attacker write once to make
the outputs stay as they are, whatever the PLC reads afterwards? (The
address, as you would use it with pymodbus.)

### Steps

1. **Read the model.** Open the lesson and read *How it looks on CybICS*. Check
   the table above against the sandbox: step a few ticks with the compressor
   on and watch the GST pay 2 bar for every bar the HPT gains.

2. **Set up situation 1.** Enter the start pressures, choose *manual*, tick
   only the compressor, press *Reset to start*, then run until nothing moves
   any more. Read the log: why did the compressor stop moving gas although
   its output is still on? Which side of the rule (50 bar or more) decided the
   last transfer? Note that the PLC's own guard ("GST above 50") plays no
   part in manual mode.

3. **Set up situation 2.** Same mode, compressor and refill on, valve
   closed. Run and find the tick on which the blow-out valve opens in the
   log. Run on: does the relief valve get the tank back below 200? Why not?
   Repeat with *Reset to start* a few times. Does the tick change with the
   random draws? Explain why it practically never does.

4. **Set up situation 3, then a control run.** Choose *automatic*, set the
   start pressures, choose *in one single scan* with a forged value of 40,
   reset and step until the log says the compressor switched off. The log
   line and the counter *in this (or its last) run* give the answer; the
   latch rule above explains it. (If you run on, the PLC starts its next
   normal cycle and the counter starts again: read the first run.)

   Now the control run: set the attacker to *no*, reset and run the same
   start again. Watch the log: the consumer drains the HPT, and once it is
   below 60 the PLC starts the compressor by itself. Repeat the control run
   a few times. On which tick did the compressor start, and how many ticks
   did it move gas? How much earlier did the forged scan start it, and why
   was its run shorter? Then try a forged value of 60 and compare that run
   with the control run: why does that forged scan not latch the
   compressor?

   What the comparison shows: the forged scan did not create a new state.
   It started a normal compressor cycle a few ticks early, and the honest
   readings ended it at the usual cut-out. On an HMI trend that looks like
   normal operation, which is what makes it stealthy. It is also what
   limits it: one forged scan cannot push the HPT past 90, because the real
   readings decide when the compressor stops.

5. **Try a share of the scans.** An attacker who wants more than a normal
   cycle has to keep winning. With the real HPT above 90 (say 150) and the
   forged value in half of the scans, how often does the compressor run?
   What does that mean for an attacker who floods the register, and for the
   IDS that counts writes?

6. **Find the shortcut.** Every forged value is a race the attacker has to
   keep winning. Which flag in the program ends the race after one write?
   Find its holding register in the register map.

7. **Answer** the four questions on the challenge page and press *Verify*.

## Detect and Defend

### Detection
- **Watch the operating mode.** A switch to manual mode that no operator
  made is an alarm on its own. The CybICS IDS counts Modbus writes per
  host, not per register: one write from an unexpected host stays below its
  `modbus_unauth_write` threshold (10 writes in 30 s), so the shortcut of
  this challenge passes unnoticed. A rule that alerts on any write to the
  mode or stop register by anyone but the HMI would catch it.
- **Watch the writers of sensor registers.** The HPT register should only
  ever be written by the I/O service. Winning a useful share of the scans
  takes many writes a second, which the IDS does see: `modbus_unauth_write`
  after 10 writes in 30 s and `modbus_flood` after 50 in 5 s.
- **Compare the outputs with the physics.** A compressor that runs while the
  HPT is above its cut-out, or a plant whose outputs do not change for
  minutes while the pressures do, breaks the expected relation between
  process and control (see [Physics Never Lies](../physics_forensics/README.md)).
  Even the single forged scan of situation 3 leaves a trace there: the
  compressor started while the recorded HPT was still above 60, which the
  PLC's start rule never does on honest readings. A glance at the trend
  misses it; a rule that checks every compressor start against the
  recorded pressure does not.

### Defense
- **Do consequence analysis before an incident.** The questions you just
  answered are the ones a process hazard analysis asks: what is the worst
  state one wrong output can cause, and how long until a safety layer acts?
  Here the answer is uncomfortable: with the refill on, the relief valve
  cannot keep up with the compressor.
- **Do not let one register switch off the automation.** A manual mode
  should need a local key switch or a confirmed operator action, not one
  unauthenticated Modbus write.
- **Interlocks independent of the PLC.** A pressure switch wired to the
  compressor's power, a run-time limit, or a relief valve sized for the
  compressor's full flow does not care which value the PLC read.
- **Keep sensor values out of an attacker's reach.** Restrict who may write
  to the PLC (see [Modbus Firewall](../defense_firewall/README.md)) and keep
  the I/O network separate.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | In this challenge |
|--------|-----------|-----|-------------------|
| Impair Process Control | Unauthorized Message: Reporting Message | [T1692.002](https://attack.mitre.org/techniques/T1692/002/) | A forged HPT reading reaches the PLC (situation 3) |
| Impact | Manipulation of Control | [T0831](https://attack.mitre.org/techniques/T0831/) | Frozen outputs and a latch tricked into running the compressor |
| Impact | Loss of Safety | [T0880](https://attack.mitre.org/techniques/T0880/) | The relief valve cannot keep up with a compressor held on (situation 2) |

### MITRE D3FEND

| Technique | ID | Description |
|-----------|-----|-------------|
| Operational Process Monitoring | [D3-OPM](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/) | Watching the pressures, outputs and operating mode for states the plan does not allow |
| Operational Logic Validation | [D3-OLV](https://d3fend.mitre.org/technique/d3f:OperationalLogicValidation/) | Checking that the outputs match what the control logic would decide from the real values |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Risk Assessment (RA)** | RA-3 | Consequence analysis of what a manipulated output can do |
| **System and Information Integrity (SI)** | SI-4, SI-10 | Monitoring the process and validating the values the PLC acts on |
| **Access Control (AC)** | AC-3 | Who may write the mode and the sensor registers |
| **System and Communications Protection (SC)** | SC-8 | Integrity of the sensor values on their way to the PLC |

</details>

## Hints

<details>
  <summary>💡 Hint 1</summary>

In situation 1 count the transfers, not the bar. Each one costs the GST 2 bar
and is allowed while the GST holds 50 bar **or more** before the tick.

</details>

<details>
  <summary>💡 Hint 2</summary>

In situation 2 the compressor wins every tick while the GST holds 50 bar:
the HPT rises by exactly 1 bar until the valve opens. The refill only
decides whether the GST lasts. To run it below 50 before the valve opens,
the refill would have to draw 0 in nearly every tick, which practically
never happens; so the answer practically does not depend on the draws.

</details>

<details>
  <summary>💡 Hint 3</summary>

In situation 3 the forged scan only has to set the latch. Which rule keeps
it set on the real readings, and until which pressure? In the control run,
ask what the consumer does to the HPT while the compressor is off.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

1. The compressor keeps moving gas as long as the GST holds 50 bar or more
   at the start of a tick. Count the GST values from 150 down in steps of 2
   that are still 50 or more; each is one bar for the HPT. After the last one
   the GST is below 50 and the output stays on to no effect. The valve is
   closed and the compressor is on, so nothing consumes the gas: the HPT
   stays where the last transfer left it. A frequent wrong answer is one bar
   lower: that uses the PLC's guard "above 50", which does not apply when the
   PLC is in manual mode.
2. With the compressor on and the GST well above 50, the HPT rises by
   exactly one bar per tick from 90. The valve opens in the tick that takes
   the HPT above 220. From then on the compressor adds 1 bar and the valve
   removes 0 or 1, so the HPT never falls: it climbs to the top of the range
   and stays there, and the relief valve never closes again.
3. The forged 40 is below 60 and the GST above 50, so that one scan starts
   the compressor on tick 1. In every later scan the latch rule "running and
   below 90" holds on the real value, so the compressor runs from 62 until
   the HPT reaches 90, one bar per tick. In the scan that sees 90 the PLC
   switches it off. In the control run the valve is open and the compressor
   off, so the consumer drains the HPT by 0 to 2 bar a tick; once it reads
   below 60 (58 or 59) the PLC starts the compressor itself, usually on tick
   3 to 8, and it runs 31 or 32 ticks up to the same 90. The attack moved a
   normal cycle a few ticks earlier and made it shorter, nothing more. A
   forged 60 does not latch the compressor on its scan, because the start
   rule wants "below 60"; from then on that run is the control run.
4. MANUAL: `manual AT %MW...` in `software/OpenPLC/cybICS.st`; holding
   register 1024 + n for `%MWn`, or simply the MANUAL row of the register
   map from HMI Project Recon.

Enter the four answers on the challenge page.

</details>
