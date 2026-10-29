# Register Map Recon

> **MITRE ATT&CK for ICS:** `Collection` | [T0861 - Point & Tag Identification](https://attack.mitre.org/techniques/T0861/) | [T0801 - Monitor Process State](https://attack.mitre.org/techniques/T0801/) | [T0802 - Automated Collection](https://attack.mitre.org/techniques/T0802/)

## Overview
The HMI shows an operator a handful of values: two tank pressures, a few
switches. The PLC behind it holds far more. Its program keeps internal
memory words that decide what the plant does next, and on most controllers
that memory answers every read, whether or not anyone ever drew it on a
screen.

In this challenge you have **no register map, no program and no HMI project**.
You only read. By sampling the PLC's memory over time and watching how each
word behaves, you find the two words the control logic uses to *remember*
whether the compressor and the tank refill are running, work out which is
which and at what pressure one of them lets go, and then locate the same word
in a second protocol the PLC speaks.

This is how real attackers learn a process before they touch it, and it is
also how an engineer documents a controller nobody has the project for any
more.

## Background

### One memory, many address spaces

OpenPLC, the PLC at **172.18.0.3**, keeps its program variables in located
memory areas. The one that matters here is `%MW`, the *memory words*: 16-bit
values the program uses for its own bookkeeping. OpenPLC publishes that area
over every protocol it speaks, each with its own numbering:

| View | Where `%MWn` appears | Counts from |
|------|----------------------|-------------|
| PLC program (IEC 61131-3) | `%MWn` | 0 |
| Modbus TCP, port 502 | holding register **1024 + n** | 0 (on the wire) |
| HMI tools such as FUXA | holding register **1025 + n** | 1 |
| S7comm (Snap7), port 102 | data block **DB1002**, byte offset **2n** (a big-endian word) | 0 |

Holding registers 0 to 1023 are a different area (`%QW`, analog outputs, all
0 here). The same word therefore has at least four names. An attacker who
copies a number from one tool into another without translating it reads or
writes the wrong word, and on a plant that is not a harmless mistake.

### What a latch is

A tank controller that switched a pump on below 60 and off above 60 would
chatter: on, off, on, off, many times a second around the threshold. Real
logic uses **hysteresis**: switch on below a low threshold, keep running until
a high threshold, then stay off until the value drops below the low one again.
To do that the program has to remember whether the pump is currently running.
That memory is a *latch* (or *seal-in*), usually a word that is only ever 0
or 1.

A latch is valuable to an attacker: it tells you the thresholds the operator
designed the plant around, and on many PLCs it can be written like any other
word.

## Where to run it

From the **attack shell** (WebShell view of the landing page, 172.18.0.100)
or the Kali attack machine. You need Python with `pymodbus` (both have it);
the attack shell also has `python-snap7` for the optional S7 check.

## Task

The flag has the format `CybICS(flag)`. Enter four answers on the challenge
page and click **Verify**:

1. the holding register (wire address, from 0) of the **compressor latch**;
2. the holding register (wire address, from 0) of the **refill latch**, the
   one that remembers that the gas storage tank (GST) is being refilled;
3. the **HPT value** at which the compressor latch releases (falls back to 0);
4. the **byte offset in DB1002** at which the compressor latch appears over
   S7comm.

All four have to be right at once; the page does not say which one is wrong.

### Steps

1. **Take one snapshot.** Read the first 256 words of the `%MW` area and
   print only the non-zero ones:
   ```bash
   python3 - <<'EOF'
   from pymodbus.client import ModbusTcpClient
   c = ModbusTcpClient("172.18.0.3", port=502); c.connect()
   words = []
   for start in range(1024, 1280, 125):
       n = min(125, 1280 - start)
       words += c.read_holding_registers(start, count=n).registers
   c.close()
   print({1024 + i: v for i, v in enumerate(words) if v})
   EOF
   ```
   One snapshot is not a map: a latch that is 0 right now looks exactly like
   an unused word.

2. **Sample over time.** Repeat the read every half second for about ten
   minutes and keep every sample. The plant runs in two cycles of very
   different length: the compressor starts and stops roughly once a minute,
   but one refill of the gas storage tank (GST), from nearly empty to nearly
   full and back down, takes around ten. A window shorter than one full cycle
   of each misses switches. `map_registers.py` in this directory does the
   sampling for you:
   ```bash
   cd /CybICS/training/register_map_recon
   python3 map_registers.py --seconds 600 --csv /tmp/hr.csv
   ```
   It only reads. Read its source before you run it; it is short.

3. **Classify every word.** For each address, look at the values it took:
   - always 0: unused (or not used *yet*, which is why the window matters);
   - one constant value: configuration or data blocks, not process state;
   - many different values that drift: an **analog** process value;
   - only 0 and 1, changing: a **flag**: a latch, a state bit or a counter
     bit. A word that sat at 1 (or 0) the whole time may be a flag that simply
     did not switch inside your window: sample longer before you decide.

   Do the same for coils 0 to 7, the PLC's digital outputs. One coil
   switches on and off every second whatever the plant does: that is the
   heartbeat LED, not a latch.

4. **Name the analog values.** You should find two analog words close to each
   other. Open the HMI (`http://<board>:1881`, no login needed to watch) and
   compare: which word follows the GST, which the HPT?

5. **Tie each flag to the process.** For every flag word, note the analog
   values at the instant it switched from 0 to 1 and from 1 to 0
   (`map_registers.py` prints exactly that). A latch switches at the same
   values every cycle, and those values are its thresholds. The compressor
   latch switches on when the HPT is low and lets go when the HPT is high;
   the refill latch follows the GST. Also check which coil changes at the
   same moment: a latch usually drives an output.

6. **Translate.** Turn the compressor latch's wire address into its `%MW`
   index, then into the S7comm data block and byte offset with the table in
   the background section.

7. **Confirm over S7comm (optional, read-only).** The same word through the
   other door:
   ```bash
   python3 - <<'EOF'
   import struct, snap7
   plc = snap7.client.Client(); plc.connect("172.18.0.3", 0, 1)
   print(struct.unpack(">H", plc.db_read(1002, <byte offset>, 2)))
   plc.disconnect()
   EOF
   ```
   It must match what Modbus says at the same moment. This read raises an
   `s7_enumeration` alert on the IDS dashboard; your Modbus reads did not.
   (If someone has solved *Close the Side Doors*, port 102 is closed and this
   step fails; the translation still holds.)

8. **Verify.** Enter the four answers on the challenge page.

Only read. Writing a latch makes the PLC start or stop the compressor or the
refill, and the plant is shared with everyone else on the board.

## Detect and Defend

### Detection
- The CybICS IDS does **not** flag Modbus reads, at any rate. Reads are
  normal polling traffic: FUXA, the OPC-UA server and the hardware bridge read
  the PLC many times a second. A sweep is only visible if you compare *who*
  reads *what*: the HMI reads a dozen fixed addresses, a sweep reads hundreds,
  including words no client ever asked for, from a host that never polled
  before.
- Your S7comm read in step 7 did raise an alert (`s7_enumeration`), because
  no plant service speaks S7comm. A second protocol into the same memory is
  a second, often less-watched, way to read it, and here at least a noisier
  one.
- A baseline of normal clients and their address ranges (what an OT
  monitoring product calls an *asset and communication baseline*) turns an
  unusual reader or an unusual range into an alert.

### Defense
- **Limit who can reach the PLC.** Only the HMI, the hardware bridge and the
  OPC-UA server need port 502. Everything else should not be able to ask; see
  [Modbus Firewall Rules](../defense_firewall/README.md) and
  [Network Segmentation](../defense_network/README.md).
- **Expose only what clients need.** Many PLCs and gateways can publish a
  restricted Modbus map rather than the whole memory. OpenPLC cannot, which is
  a reason to put a filtering gateway or firewall that inspects addresses in
  front of it.
- **Close the protocols nobody uses.** Every protocol that maps the same memory
  is another way in, see [Close the Side Doors](../defense_unused_protocols/README.md).
- **Assume the map leaks.** Hiding a register is not a control: anything that
  answers a read can be found by reading. Defend the *writes* and the network
  path, and watch for unusual readers.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Collection | Point & Tag Identification | [T0861](https://attack.mitre.org/techniques/T0861/) | Working out what each register means, including words no HMI shows, and their names in other protocols |
| Collection | Monitor Process State | [T0801](https://attack.mitre.org/techniques/T0801/) | Watching the plant's values over time to learn its thresholds |
| Collection | Automated Collection | [T0802](https://attack.mitre.org/techniques/T0802/) | A script that sweeps and samples the PLC's memory |

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Spot clients that read address ranges no normal client reads |
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Only the plant's own clients reach port 502 and 102 |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Communications Protection (SC)** | SC-7 | Boundary protection around the controller |
| **Configuration Management (CM)** | CM-7 | Least functionality: unused protocols closed |
| **System and Information Integrity (SI)** | SI-4 | Monitoring for unusual readers and address ranges |

</details>

## Hints

<details>
  <summary>💡 Hint 1</summary>

A word that reads 0 now can still be in use, and so can a word that read 1
all along. Sample long enough for the compressor to start and stop several
times and for the GST to be refilled once: ten minutes is a safe window.

</details>

<details>
  <summary>💡 Hint 2</summary>

Two flag words, two tanks. Look at both analog values at every switch of
each flag. The one whose switches always happen at the same HPT values belongs
to the compressor; read the release value from the 1 -> 0 switches.

</details>

<details>
  <summary>💡 Hint 3</summary>

Wire address minus 1024 is the `%MW` index. Two bytes per word.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

From the attack shell:

```bash
cd /CybICS/training/register_map_recon
python3 map_registers.py --seconds 600
```

Two holding registers in the `%MW` area are flags: **1224** and **1226**.
1224 switches to 1 when the HPT (holding register 1126) drops below 60 and back
to 0 when it reaches **90**; coil 1, the compressor output, follows it. 1226
switches to 1 when the GST (1124) drops below 60 and back to 0 near 240; coil
3 follows it. 1224 is `%MW200` (the program calls it `compressorState`), so
over S7comm it is DB1002 byte offset **400**. Enter 1224, 1226, 90 and 400.

</details>
