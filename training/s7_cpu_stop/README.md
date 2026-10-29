# Stop Means Stop?

> **MITRE ATT&CK for ICS:** `Execution`, `Evasion` | [T0858 - Change Operating Mode](https://attack.mitre.org/techniques/T0858/) | `Evasion` `Impair Process Control` | [T1692.001 - Unauthorized Message: Command Message](https://attack.mitre.org/techniques/T1692/001/) | `Collection` | [T0868 - Detect Operating Mode](https://attack.mitre.org/techniques/T0868/)

## Overview
A PLC has an **operating mode**. In **RUN** it executes its program in a
loop, the *scan cycle*: read the inputs, run the logic, write the outputs. In
**STOP** the program halts and a real Siemens S7 CPU switches its outputs to a
safe state, which on a gas plant means compressor off and valves closed.
Engineers put a PLC in STOP to download a new program; attackers do it to
halt a process or to make room for their own code. ATT&CK for ICS calls this
*Change Operating Mode* (T0858). TRITON first checked which mode its target
safety controller was in, then used the mode to get its own code onto it.

S7comm, the protocol of Siemens PLCs, has a job for exactly this: **PLC
STOP**. It needs no password on a classic S7 CPU, and the CybICS controller,
OpenPLC at **172.18.0.3**, answers it on **port 102**.

Your goal is to send the PLC a STOP, read back what the PLC *says* its mode
is, and then find out from the plant what it *does*. The two are not the
same, and the lesson of this challenge is how you tell.

## Background

### Two ways to "stop" the CybICS plant

| What you change | How | Effect |
|-----------------|-----|--------|
| The program's `stop` variable (`%MW104`) | a memory write (Modbus, S7 or DNP3) | the program keeps running and itself switches compressor and valve off |
| The CPU's operating mode | an S7comm **PLC STOP** job (function `0x29`) | on a Siemens CPU: no program, outputs to the safe state |

The [S7 side door](../s7_sidedoor/README.md) challenge used the first. This
one is about the second: a single command with no address and no value.

### Asking the PLC what mode it is in

An S7 CPU publishes its state in **system status lists** (SZL, German
*System-Zustandsliste*), read-only records any S7 client may request. The
[S7comm scanning](../scanning2/README.md) challenge read the identity list
(SZL `0x0011`). The operating mode is in **SZL `0x0424`**. Its 20-byte record
starts with an event id (2 bytes) and an event class (1 byte); the **fourth
byte is the mode**:

| Mode byte | Meaning |
|-----------|---------|
| `0x08` | RUN |
| `0x04` | STOP |

### Do not trust the tool either

python-snap7 offers `client.get_cpu_state()`, which promises `S7CpuStatusRun`
or `S7CpuStatusStop`. In python-snap7 3.3.0, the version in the attack shell
and on the attack machine, that function **never asks the PLC for its mode**:
look at what it sends in a capture (step 4) and you will see a read request
with no items, and an answer the library has decided in advance. Sometimes
that malformed request even makes the call fail with `Data item is
truncated`; call it again and it answers as before. Part of this challenge is
noticing that, and reading the status list yourself with
`client.read_szl(0x0424, 0)`.

## Where to run it

From the **attack shell** (WebShell view of the landing page, 172.18.0.100)
or the Kali attack machine. Both have `python-snap7` and `pymodbus`.
Elsewhere:

```bash
pip install python-snap7 pymodbus
```

The IDS must be capturing (dashboard on port 8443, *Start* if it is stopped):
it is the witness that the STOP went over the network.

## Task

The flag has the format `CybICS(flag)`. **Verify** on the challenge page
reveals it when, at the same time:

- the IDS saw an **S7comm PLC STOP** to OpenPLC (172.18.0.3:102) within the
  last five minutes, and no warm or cold restart after it;
- the PLC's status list **reports STOP**;
- the PLC's program is **still running**: its heartbeat output keeps changing.

Then restart the CPU (step 7). The challenge expects you to leave it in RUN.

### Steps

1. **Connect.** Open `python3` and connect to rack 0, slot 1:
   ```python
   import snap7
   plc = snap7.client.Client()
   plc.connect("172.18.0.3", 0, 1)
   ```

2. **Read the mode from the status list.** python-snap7 3.3.0 hands you the
   record with the list's own 4-byte header (record length, record count) in
   front of it, so the mode is byte 7 of what it returns:
   ```python
   def cpu_mode():
       szl = plc.read_szl(0x0424, 0)
       raw = bytes(szl.Data[:szl.Header.LengthDR])
       print(raw.hex(" "))
       return raw[7]
   plc.get_cpu_state()
   hex(cpu_mode())     # 00 14 00 01 51 44 ff 08 ...  -> 0x8, RUN
   ```

3. **Send the STOP.**
   ```python
   plc.plc_stop()          # returns 0: the PLC acknowledged the job
   plc.get_cpu_state()     # what does the library say now?
   hex(cpu_mode())         # and what does the PLC say?
   ```
   The IDS dashboard shows an `s7_cpu_control` alert of severity critical.
   If the two answers disagree, find out which one asked the PLC.

4. *Optional:* **Look at the wire.** In a second WebShell tab,
   `tcpdump -i any -nX tcp port 102`, then call `plc.get_cpu_state()` and
   `cpu_mode()` again in the first. A status-list read is an S7 *userdata* request
   (ROSCTR `07`) that names SZL `04 24`. What does `get_cpu_state()` send?

5. **Ask the plant, not the PLC.** If the CPU had stopped, the program would
   no longer run. Watch what the program does for a few seconds over Modbus:
   ```python
   import time
   from pymodbus.client import ModbusTcpClient
   mb = ModbusTcpClient("172.18.0.3", port=502); mb.connect()
   for _ in range(10):
       heartbeat = mb.read_coils(0, count=1).bits[0]          # %QX0.0
       gst, _, hpt = mb.read_holding_registers(1124, count=3).registers
       print(f"heartbeat={int(heartbeat)}  gst={gst}  hpt={hpt}")
       time.sleep(0.5)
   ```
   Compare with the FUXA HMI (port 1881) and the 3D view of the plant (port
   8090). Is the heartbeat still blinking? Is the compressor still filling the
   high-pressure tank? Also look at OpenPLC's web interface (port 8080): what
   does its dashboard say about the runtime, and does its runtime log mention
   your STOP?

6. **Verify.** While the PLC still reports STOP, click **Verify** on the
   challenge page.

7. **Restart the CPU** and check that it is back in RUN:
   ```python
   plc.plc_hot_start()     # warm restart; plc.plc_cold_start() works too
   hex(cpu_mode())         # 0x8
   plc.disconnect(); mb.close()
   ```

`s7_cpu_stop.py` in this directory does steps 2, 3, 5 and 7 for you
(`python3 s7_cpu_stop.py`, `... stop`, `... watch`, `... start`).

### What just happened?

OpenPLC's S7 server is the Snap7 library, a software model of an S7 CPU. Snap7
acknowledges a PLC STOP and flips the mode in its status list, but OpenPLC
never looks at that mode: its scan cycle runs on regardless. A real S7 CPU
would have stopped and switched its outputs off. OpenPLC's own stop is the
*Stop PLC* button in its web interface, which really halts the program; it is
not part of this challenge, so leave it alone.

Neither result is safe to assume. The STOP was acknowledged (`0`), the PLC
reported STOP, and the plant kept running. Had you trusted the
acknowledgement or the status, you would have told the operators the
process was halted. What counts is **what the process does**, and that you
read from the process: sensors, outputs, the heartbeat.

The gap also hides attacks. A mode change that leaves the process looking
normal is one nobody notices unless they watch for the command itself, and
the command is exactly what an attacker sends before replacing a program.

## Detect and Defend

### Detection
- The CybICS IDS raises `s7_cpu_control` for every S7comm request that
  changes the CPU's operating mode: **critical** for a PLC STOP, high for a
  warm or cold restart, with the source host. It fires on the first request;
  no threshold to stay under. Status-list reads do not trigger it (they are
  `s7_enumeration`, like any S7comm traffic).
- Nothing in the CybICS plant changes the PLC's mode over the network. On a
  real plant a mode change outside a planned maintenance window, or from a
  host that is not the engineering workstation, is the alarm. ATT&CK's
  detection analytic for T0858 is exactly that: mode-change commands from a
  source that is not on the approved list.
- The PLC itself is a poor witness here: OpenPLC's runtime log lists S7
  connections but not your STOP (OpenPLC subscribes only to Snap7's
  connection events). Poll the mode from SZL `0x0424` and alert when it
  changes, and compare it with what the process does.

### Defense
- **Physical key switch.** Some controllers have a mode key. Locked in RUN,
  it refuses program changes from the network. The Triconex safety
  controllers TRITON attacked had reportedly been left in a key position that
  allowed programming over the network.
- **CPU protection levels.** Siemens S7 CPUs can require a password before a
  client may change memory, the program or the operating mode. Set one.
- **Close the door.** Filter port 102 on the PLC so only the engineering
  workstation reaches it, or turn the S7 server off in OpenPLC's *Settings*
  if nothing uses it:
  ```bash
  iptables -A INPUT -p tcp --dport 102 -j DROP
  ```
- **Monitor the process, not only the controller.** An independent signal
  (a heartbeat, a pressure trend on the HMI or the historian) tells you what
  the plant is doing whatever the controller reports.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Execution, Evasion | Change Operating Mode | [T0858](https://attack.mitre.org/techniques/T0858/) | An S7comm PLC STOP puts the CPU into STOP, a warm restart back into RUN |
| Evasion, Impair Process Control | Unauthorized Message: Command Message | [T1692.001](https://attack.mitre.org/techniques/T1692/001/) | The STOP is an unauthenticated command no operator sent |
| Collection | Detect Operating Mode | [T0868](https://attack.mitre.org/techniques/T0868/) | Reading the CPU's operating mode from its status list (SZL 0x0424) |

**Why this matters:** an operating mode change is one of the most consequential commands a controller accepts, and on many devices it needs nothing but network access. Monitoring has to catch the command itself and check it against what the process does, because the controller's own report is not proof.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Decode S7comm and alert on PLC STOP and PLC Control jobs |
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Allow port 102 only from the engineering workstation |
| Operational Process Monitoring | [D3-OPM](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/) | Judge the plant by its process values, not by the controller's status |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Access Control (AC)** | AC-3 | Enforce authorization for mode changes (key switch, CPU protection level) |
| **Configuration Management (CM)** | CM-7 | Least functionality: disable the S7 server when nothing needs it |
| **System and Information Integrity (SI)** | SI-4 | Monitor for mode-change commands and for process behaviour that contradicts the reported state |

</details>

## Hints

<details>
  <summary>💡 Hint 1</summary>

python-snap7 has `plc_stop()`, `plc_hot_start()` and `plc_cold_start()`. To
learn the mode, read the status list `0x0424` with `read_szl()` and look at
the bytes.

</details>

<details>
  <summary>💡 Hint 2</summary>

The PLC's program drives the heartbeat output `%QX0.0`, Modbus coil 0. A
stopped program cannot toggle it.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

From the attack shell:

```bash
cd /CybICS/training/s7_cpu_stop
python3 s7_cpu_stop.py           # mode from SZL 0x0424 next to get_cpu_state()
python3 s7_cpu_stop.py stop      # PLC STOP, then the mode again
python3 s7_cpu_stop.py watch     # heartbeat, GST and HPT for five seconds
```

Click **Verify** on the challenge page, then:

```bash
python3 s7_cpu_stop.py start     # warm restart, mode back to RUN
```

</details>
