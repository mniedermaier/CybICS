# Physics Never Lies

> **MITRE ATT&CK for ICS (reconstructed):** `Collection` | [T0830 - Adversary-in-the-Middle](https://attack.mitre.org/techniques/T0830/) | `Evasion` `Impair Process Control` | [T1692.002 - Unauthorized Message: Reporting Message](https://attack.mitre.org/techniques/T1692/002/) | `Impact` | [T0832 - Manipulation of View](https://attack.mitre.org/techniques/T0832/) | [T0831 - Manipulation of Control](https://attack.mitre.org/techniques/T0831/)
>
> **MITRE D3FEND:** [D3-OPM - Operational Process Monitoring](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/) | [D3-DLV - Domain Logic Validation](https://d3fend.mitre.org/technique/d3f:DomainLogicValidation/) | [D3-OLV - Operational Logic Validation](https://d3fend.mitre.org/technique/d3f:OperationalLogicValidation/)

## Overview
Late one night the operator noticed something odd: the compressor had been
running for more than a minute without a break, but the HMI showed a calm
high-pressure tank (HPT) in its normal band, rising so slowly that the
compressor never reached its cut-out. Nothing else looked wrong. There was
no alarm, the blow-out valve was closed and the IDS was silent. The on-call
engineer stopped the plant by hand and pulled the **historian export** of
the night before anyone touched anything.

The suspicion: someone sat between the plant's I/O and the PLC and fed it a
false value, so the PLC kept the compressor running while every screen
showed a normal plant. The question is *which* value, *since when*, and how
bad it really was in the tank.

You get **`historian.csv`**: one row per process cycle, about 50 minutes.
Every value in it is exactly what the PLC held at that moment, so a forged
value is in it as well, looking just as real as the others. Your only
witness is **physics**. The plant cannot do just anything from one second to
the next: gas does not appear from nowhere, and a compressor that runs puts
gas *somewhere*.

This is an offline forensics challenge. It needs nothing from the running
plant and works the same in a classroom without the testbed.

## Background

### The export

| Column | Register | Meaning |
|--------|----------|---------|
| `time` | | When the row was recorded (plant local time) |
| `gst` | HR 1124 (`%MW100`) | Gas storage tank (GST) pressure, bar |
| `hpt` | HR 1126 (`%MW102`) | High-pressure tank (HPT) pressure, bar |
| `sysSen` | HR 1132 (`%MW108`) | System sensor: 1 while the downstream system is supplied |
| `boSen` | HR 1134 (`%MW110`) | Blow-out sensor: 1 while the relief valve is open |
| `stop` | HR 1128 (`%MW104`) | Stop flag: 0 = run, 1 = stop |
| `compressor` | coil 1 | Compressor on (1) or off (0) |
| `systemValve` | coil 2 | System valve open (1) or closed (0) |
| `gstSig` | coil 3 | GST refill from the external supply on (1) or off (0) |

The I/O service (`hwio`, 172.18.0.2) runs the plant model. It advances the
plant in steps of about one second, called **ticks** or process cycles, and
writes the new pressures and sensors to the PLC. The PLC (every 50 ms)
decides the coils from those values. The historian records one row per
tick, so:

> The coils in a row are what the PLC set *after* seeing that row's values.
> They drive the change from that row to the **next** one.

### What the plant can do in one tick

These rules are the plant model, `physical_process_thread` in
`software/hwio-virtual/hardwareAbstraction.py` (the STM32 firmware runs the
same model on the physical board). From one row to the next, with the coils
of the first row:

| Situation (first row) | HPT change | GST change |
|-----------------------|-----------|-----------|
| `compressor` = 1 | **exactly +1** | **-2**, plus the refill if `gstSig` = 1 |
| `compressor` = 0, `systemValve` = 1 | -2, -1 or 0 (gas used downstream) | only the refill |
| `compressor` = 0, `systemValve` = 0 | 0 | only the refill |
| `gstSig` = 1 (refill on) | | **+0 to +3** on top of the above |
| `boSen` = 1 (relief valve open) | -1 or 0 on top of the above | |

The compressor only runs while the GST holds at least 50 bar (the PLC
switches it on only above 50), and the relief valve only opens above 220.

Two consequences matter for a forensic analyst:

- **Conservation of mass.** The compressor takes 2 bar out of the GST for
  every bar it puts into the HPT. While the refill is off, the gas that left
  the GST tells you exactly how much arrived in the HPT, whatever the HPT
  column says.
- **Redundant evidence.** `sysSen` is computed by the I/O service from the
  **real** HPT: it is 1 only while the real HPT is between 51 and 99 and the
  valve is open. The PLC opens the valve in exactly that band of the HPT
  *it sees*. So in automatic mode `sysSen` must equal `systemValve`.

### The PLC's control logic

From `software/OpenPLC/cybICS.st`, in automatic mode:

- compressor on when the HPT falls below 60 (and the GST is above 50),
  off again when the HPT reaches 90;
- GST refill on when the GST falls below 60, off again at 240;
- system valve open while 50 < HPT < 100;
- with the stop flag set, everything off.

## Where to run it

You need the file and anything that reads a CSV.

- **Download** it from the challenge page:
  [historian.csv](/ctf/challenge/physics_forensics/historian.csv)
  (in the repository: `training/physics_forensics/historian.csv`).
- **The attack shell** has it at
  `/CybICS/training/physics_forensics/historian.csv`, with Python 3, `awk`
  and the usual text tools. A spreadsheet works too: add a column with the
  change from the row above and filter.

## Task

Answer three questions on the challenge page:

1. **Which recorded value was forged?** The column name or its register.
2. The **time stamp of the first row the plant cannot have produced**, as
   written in the file. The time alone (`HH:MM:SS`) is enough.
3. The **real HPT pressure in the last row** of the export, in bar.

All three answers are graded together.

### Steps

1. **Get a feel for normal.** Plot or skim `hpt`, `gst` and `compressor`.
   A healthy night is a saw tooth: the compressor fills the HPT from about 60
   to 90, then the downstream system uses it up again. How long does the
   compressor normally run in one go?

2. **Do not trust what merely looks odd.** You will find stretches where
   nothing moves at all, and rows where the GST rises while the compressor
   runs. Check each against the rule table before you call it an attack:
   a stopped plant, or a refill overlapping the compressor, is physics, not
   forgery.

3. **Turn the rules into checks.** For every pair of rows, compute what the
   table allows for the second row from the first one and compare. Here is
   one rule as a pattern, "with the compressor off and the valve closed, the
   HPT stays where it is", in Python:

   ```python
   import csv
   rows = list(csv.DictReader(open("historian.csv")))
   for prev, row in zip(rows, rows[1:]):
       if prev["compressor"] == "0" and prev["systemValve"] == "0":
           if row["hpt"] != prev["hpt"]:
               print(row["time"], "HPT moved with nothing to move it:", prev["hpt"], "->", row["hpt"])
   ```

   and "without the refill, the GST never rises" in `awk` (column 2 is `gst`,
   column 9 is `gstSig`):

   ```bash
   awk -F, 'NR>2 && s==0 && $2>g {print $1, g, "->", $2} {s=$9; g=$2}' historian.csv | head
   ```

   Both print nothing: these two rules hold all night. Write the others from
   the table yourself (the compressor, the valve open, the refill) and the
   `sysSen` = `systemValve` check within a row. Before the attack, every row
   passes every rule.

4. **Find the first violation, not the most obvious one.** Several rules
   break during the attack, but not at the same moment. Which one breaks
   first? The row before it is the last one you can trust. Which column
   cannot be real there, and why can it not be one of the others?

5. **Reconstruct the truth.** From the last row you can trust to the end of
   the file, check which coils were set and whether the refill or the relief
   valve could have played a part. Then use conservation of mass: how much
   gas left the GST, and how much of it must be in the HPT now? Cross-check
   by counting the compressor ticks.

6. **Answer** the three questions on the challenge page and press *Verify*.

## Detect and Defend

### Detection
- **Check the physics, continuously.** Rules like the ones you wrote are
  cheap to run on live data: every tick, compare what the sensors say with
  what the actuators make possible. An attacker can forge a value, but has
  to forge *all* related values consistently to pass such a check, which is
  much harder.
- **Use redundant measurements.** `sysSen` gave the attacker away because it
  is computed from the real tank. Real plants add a second transmitter on a
  different path, or a local mechanical gauge an operator reads on rounds.
- **Watch the control behaviour.** A compressor that runs almost three times
  longer than ever before, without the pressure ever reaching its cut-out,
  is an anomaly even without any physics model.
- **Keep the historian.** Long, exact records are what made this analysis
  possible; keep them out of reach of the networks an attacker can touch.

### Defense
- **Protect the measurement path.** The I/O service writes the sensor values
  to the PLC over Modbus TCP, which has no integrity protection. An
  adversary in the middle (see the [MitM challenge](../mitm/README.md)) can
  change them. Segment the I/O network, lock ARP bindings and prefer
  protocols with authenticated, integrity-protected messages.
- **Interlocks that do not trust a single value.** A compressor run-time
  limit, or an interlock on the real tank pressure that does not pass
  through the PLC, keeps one forged value from driving the plant into
  danger. The mechanical blow-out valve is such a layer; it was never needed
  that night, but only because the operator stopped the plant in time.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques you reconstruct

| Tactic | Technique | ID | In the export |
|--------|-----------|-----|---------------|
| Collection | Adversary-in-the-Middle | [T0830](https://attack.mitre.org/techniques/T0830/) | The attacker sits between the I/O service and the PLC |
| Evasion, Impair Process Control | Unauthorized Message: Reporting Message | [T1692.002](https://attack.mitre.org/techniques/T1692/002/) | A forged sensor value reaches the PLC |
| Impact | Manipulation of View | [T0832](https://attack.mitre.org/techniques/T0832/) | The HMI and the historian show a normal tank |
| Impact | Manipulation of Control | [T0831](https://attack.mitre.org/techniques/T0831/) | The PLC keeps the compressor running on a false input |

### MITRE D3FEND - Defensive techniques you apply

| Technique | ID | Description |
|-----------|-----|-------------|
| Operational Process Monitoring | [D3-OPM](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/) | Analysing the physical parameters in the historian |
| Domain Logic Validation | [D3-DLV](https://d3fend.mitre.org/technique/d3f:DomainLogicValidation/) | Checking values against the physics of the plant |
| Operational Logic Validation | [D3-OLV](https://d3fend.mitre.org/technique/d3f:OperationalLogicValidation/) | Checking values against the control logic (`sysSen` and the valve) |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-4, SI-10 | Monitoring the process and validating input values |
| **Audit and Accountability (AU)** | AU-6 | Reviewing and analysing the recorded process data |
| **Incident Response (IR)** | IR-4 | Handling the incident from the evidence |
| **System and Communications Protection (SC)** | SC-8 | Integrity of the values on their way to the PLC |

</details>

## Hints

<details>
  <summary>💡 Hint 1</summary>

The compressor turns 2 bar of GST into 1 bar of HPT, every tick it runs.
Look for rows where the GST paid but the HPT did not receive.

</details>

<details>
  <summary>💡 Hint 2</summary>

`sysSen` and `systemValve` disagree for the first time well after the
attack started. `sysSen` only notices once the real HPT has left the band
the forged value stays in. The first broken rule is a different one.

</details>

<details>
  <summary>💡 Hint 3</summary>

During the attack the refill is off and the relief valve stays shut, so
every 2 bar the GST lost went into the HPT. Start from the HPT of the last
row you trust, not from the first forged one.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

`physics_check.py` implements the rule table and the `sysSen` check, lists
the first violation of each rule and does the mass balance:

```bash
cd /CybICS/training/physics_forensics
python3 physics_check.py historian.csv
python3 physics_check.py historian.csv --all   # every violation
```

Reading its output:

1. Before the attack every row passes. The planned stop (all coils 0, both
   pressures flat) and the refill ticks with the compressor on (GST up to +1)
   pass, because the rule table allows them.
2. The first violation is an `hpt-step`: the compressor ran, the GST fell by
   2, but `hpt` did not rise by 1. The GST behaves exactly as physics says
   in this and every later row, and the coils are what the PLC decided from
   the values it saw, so the forged value is **`hpt`** (holding register
   1126). The first violating row's time stamp is the second answer.
3. Later rows also break the `sysSen` rule: the valve is open for an HPT the
   PLC thinks is in the band, while the I/O service, which sees the real
   tank, says it is not. That is the moment the real HPT reached 100, not the
   start of the attack.
4. From the last consistent row to the end of the file the compressor runs
   every tick, the refill is off and the relief valve is closed, so the real
   HPT in the last row is the HPT of the last consistent row plus half of the
   GST that left the storage tank since then. This equals the number of
   compressor ticks. The script prints the result; that is the third answer.

Enter the three answers on the challenge page.

</details>

## For maintainers: regenerating the export

`historian.csv` is generated, never edited by hand:

```bash
python3 software/scripts/generate_physics_historian.py          # rewrite the file
python3 software/scripts/generate_physics_historian.py --key    # print the answers
```

The generator is deterministic and simulates the plant with a copy of the
hwio tick and the PLC's automatic mode. If you change the plant model or the
story, regenerate the file and update the expected values in
`software/landing/modules/defense_checks/check_physics_forensics.py`;
`tests/test_physics_forensics.py` fails until they match, and also when the
generator's copy of the plant drifts from `hardwareAbstraction.py`.
