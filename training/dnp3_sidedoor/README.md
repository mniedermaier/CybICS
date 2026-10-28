# DNP3 Side Door

> **MITRE ATT&CK for ICS:** `Discovery` | [T0846 - Remote System Discovery](https://attack.mitre.org/techniques/T0846/) | `Impair Process Control` | [T1692.001 - Unauthorized Message: Command Message](https://attack.mitre.org/techniques/T1692/001/) | `Impact` | [T0831 - Manipulation of Control](https://attack.mitre.org/techniques/T0831/) | [T0826 - Loss of Availability](https://attack.mitre.org/techniques/T0826/)

## Overview

A PLC usually speaks more protocols than the plant uses, and every one of them
is a way in. The CybICS controller, OpenPLC at **172.18.0.3**, serves Modbus/TCP
on port 502 to the HMI and the I/O service. It also runs a **DNP3 outstation**
on port **20000**, mapped onto the same memory. Nothing in the plant uses it.

In the [S7 side door](../s7_sidedoor/README.md) challenge you were handed a
library. This time there is none: you find the DNP3 station, work out who it
will talk to, and build the frame that stops the plant byte by byte, checksums
and all. Then you put the plant back the way you found it.

## Background

### DNP3 in one page

**Distributed Network Protocol 3 (DNP3)** is the workhorse of electricity and
water utilities. A *master* (the control centre) polls and commands
*outstations* (the field devices). Each station has a **16-bit link address**,
separate from its IP address. An outstation acts only on frames that are
addressed to its own link address **and** come from the master address it is
configured for. Anything else is dropped without a word.

A DNP3 message travels in three layers inside the TCP payload:

**Link layer.** Ten bytes of header, then the user data:

| Bytes | Meaning |
|-------|---------|
| `05 64` | start bytes of every DNP3 frame |
| 1 byte | length: the user-data bytes that follow, plus 5 |
| 1 byte | control: `C4` = unconfirmed user data from a master, `C9` = request link status from a master |
| 2 bytes | destination link address, little-endian |
| 2 bytes | source link address, little-endian |
| 2 bytes | CRC-16/DNP of the 8 bytes above, little-endian |

The user data follows in **blocks of up to 16 bytes, each followed by its own
2-byte CRC**. A frame with a single wrong CRC is discarded silently.

**Transport and application layers**, the user data of a command:

| Byte(s) | Meaning |
|---------|---------|
| `C0` | transport header: first and final segment, sequence 0 |
| `C1` | application control: first and final fragment, sequence 1 |
| 1 byte | application function code: `01` read, `03` select, `04` operate (only after a matching select), `05` direct operate |
| 1 byte | object group, e.g. `29` = 41, Analog Output |
| 1 byte | object variation, e.g. `02` = 16-bit integer |
| `28` | qualifier: a 2-octet object count, then each point carries a 2-octet index prefix |
| 2 bytes | object count, little-endian (`01 00` for one point) |
| 2 bytes | point index, little-endian |
| 2 bytes | value, little-endian signed 16-bit |
| `00` | control status (the outstation fills it in its reply) |

Watch the count: with qualifier `28` it is **two** bytes. With one byte the
outstation answers "not enough data for the specified objects" and does nothing.

The CRC needs no library:

```python
import struct

def crc_dnp(data: bytes) -> bytes:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA6BC if crc & 1 else crc >> 1
    return struct.pack("<H", ~crc & 0xFFFF)
```

Check it before you rely on it: `crc_dnp(b"123456789")` must be `b"\x82\xea"`
(0xEA82).

### One memory, several doors

OpenPLC maps DNP3 points onto the PLC's IEC addresses. For **Analog Outputs**
(group 41) an index below 1024 is the output word `%QW<index>`, and an index of
**1024 + n** is the memory word **`%MWn`**, the same word Modbus calls holding
register 1024 + n. The PLC program (`software/OpenPLC/cybICS.st`, also
visible in OpenPLC's web interface under *Programs*) keeps its commands in
memory words:

| Variable | Address | Meaning |
|----------|---------|---------|
| `stop` | `%MW104` | 0 = run, anything else = **stop**: compressor and system valve off |
| `manual` | `%MW106` | 0 = automatic, anything else = manual |

## Where to run it

From the **attack shell** (WebShell view of the landing page, 172.18.0.100) or
the Kali attack machine, with plain `python3`. Target the PLC at
**172.18.0.3**, its address on the plant bridge, not `$DEVICE_IP`: only traffic
that crosses the bridge is seen by the IDS, and the IDS is your witness.

The IDS must be capturing (dashboard on port 8443, *Start* if it is stopped).

## Task

The flag has the format `CybICS(flag)`. It is revealed by **Verify** on the
challenge page when two things hold at the same time:

- the IDS saw a **DNP3 operate** reach OpenPLC's outstation that set the stop
  flag, within the last five minutes, and no later DNP3 operate put 0 back. The
  frame has to be one the outstation acts on: right link addresses, right CRCs,
  a well-formed object header, and an `04` operate only as the second half of
  a select-before-operate. Stopping the plant with the HMI's button or a
  Modbus write does not count;
- the plant **is stopped** at the moment you click Verify.

Then restore the plant (step 6). The plant is shared with everybody on the
board, so do not leave it stopped.

### Steps

1. **Find the door.** Scan the PLC for industrial ports beyond Modbus:
   ```bash
   nmap -Pn -p 102,502,20000,44818 172.18.0.3
   ```
   This takes well under a second. Which service is on 20000? nmap's name for
   it comes from the port number alone; the next step proves it. Adding `-sV`
   makes nmap probe each service, which takes two to three minutes on these
   ports with no output in between: the WebShell has not hung, it is waiting.

2. **Learn who may knock.** You do not know the outstation's link address, nor
   the master address it accepts, and a frame with the wrong pair gets no reply
   at all. You do have a frame that changes nothing and always gets an answer
   from the right station: **request link status** (control `C9`, no user
   data, so it is just the 10-byte header). The addresses of real devices are
   usually small numbers.

   Write a short Python script that builds that frame for every
   destination/source pair from 0 to 100, sends them all in **one** TCP
   connection (one `sendall` of the joined bytes), then reads whatever comes
   back for a second or two. Decode each reply with the link-layer table: the
   source of the reply is the outstation, the destination is the master it
   expects. Write both down.

   Your sweep is read-only. Which IDS rules do you expect it to raise?

3. **Build the stop frame.** Using the tables above, assemble the user data of
   a **Direct Operate** (`05`) on an **Analog Output, 16-bit** point. Which index is
   `%MW104`? Which value stops the plant? Then wrap it in a link frame with
   control `C4` and the address pair from step 2, adding the CRC after the
   header and after every block of user data. Print the bytes in hex and check
   them against the tables once more before you send them: a mistake costs
   nothing but silence.

4. **Stop the plant.** Send the frame to `172.18.0.3:20000` and read the reply.
   The outstation answers with function code `81` (response) and echoes your
   point; the very last byte before the final CRC is the control status, `00`
   for success (`0C` means the index is out of range). Watch the plant: the
   compressor stops and the system valve closes on the FUXA HMI (port 1881).
   The IDS dashboard shows a `dnp3_operate` alert naming the point and value.

5. **Verify.** Click **Verify** on the challenge page *while the plant is still
   stopped*.

6. **Restore the plant.** Send the same operate with the value 0 and check that
   the compressor runs again.

## Detect and defend

- **Detection.** The CybICS IDS has a rule for DNP3 commands:

  | Rule | Fires on | Severity |
  |---|---|---|
  | `dnp3_operate` | a DNP3 control request (write, select, operate, direct operate) to port 20000 | high |

  It checks the CRCs, decodes the function code, the link addresses and every
  analog-output and relay-output point with its value, and names them in the
  alert. Only an exact repeat of the previous command is folded within 30
  seconds, so stop, restore and stop again are three alerts. The rule records
  what was *sent*, not what the outstation did with it: a lone `04` operate
  that the outstation refused still raises an alert. An analyst (and this
  challenge's Verify) has to pair an operate with its select, or read the
  outstation's reply, before calling it a change to the process. Reads, link status
  requests and the outstation's replies raise nothing, which is why your
  address sweep went unremarked. A network monitor that spoke DNP3 could flag
  that too: a burst of link status requests to dozens of addresses is not what
  a real master sends.

- **Defence.** The real fix is to turn off the protocol the plant does not use:
  disable DNP3 in OpenPLC's *Settings*, or drop TCP 20000 on the PLC the way the
  [Modbus Firewall Rules](../defense_firewall/README.md) challenge drops 502 for
  everyone but the HMI and the I/O service. A firewall or an IDS scoped to one
  protocol is blind to every other protocol the device still answers. Where
  DNP3 is needed, DNP3 Secure Authentication (IEC 62351-5) makes the
  outstation challenge the master before it acts on a control request; link
  addresses are not a security mechanism, as step 2 showed.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | Sweeping link addresses to find the outstation's logical identifier and the master it accepts |
| Impair Process Control | Unauthorized Message: Command Message | [T1692.001](https://attack.mitre.org/techniques/T1692/001/) | Sending a hand-built DNP3 Direct Operate to the outstation |
| Impact | Manipulation of Control | [T0831](https://attack.mitre.org/techniques/T0831/) | Setting the PLC's stop flag over DNP3 |
| Impact | Loss of Availability | [T0826](https://attack.mitre.org/techniques/T0826/) | The gas plant stops producing until it is restored |

**Why this matters:** Industroyer, the malware behind the 2016 Kyiv blackout,
issued its commands in the grid's own protocols (IEC 60870-5-101/104, IEC 61850,
OPC DA). The commands were well formed and looked legitimate. This challenge is
the same idea in miniature: a device answers a protocol the operators forgot
about, and one well-formed command manipulates the process.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Inspecting DNP3 traffic, not only Modbus |
| Protocol Metadata Anomaly Detection | [D3-PMAD](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | Flagging control requests from a host that is not a DNP3 master |
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Dropping TCP 20000 on the PLC |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Configuration Management (CM)** | CM-7 | Least functionality: disable services such as an unused DNP3 outstation |
| **System and Communications Protection (SC)** | SC-7 | Boundary protection: block ports and protocols the process does not use |
| **System and Information Integrity (SI)** | SI-4 | System monitoring across every protocol a device exposes |

**Why NIST 800-82r3 matters here:** CM-7 (Least Functionality) is the direct
answer: a device should run only the services the process needs. SC-7 and SI-4
cover what cannot be removed: filter the port, and monitor every protocol, not
only the popular one.

</details>

## Hints

- No answer in step 2 at all? Check the length byte (5 for a frame without
  user data) and the header CRC, then widen the address range.
- The answer to a link status request has control `0B`. Its *source* is the
  outstation.
- Status `02` (no select)? You sent `04` operate on its own. The outstation
  runs an operate only right after a select (`03`) of the same objects with the
  previous application sequence number, so use `05` direct operate.
- No reply to your operate, or status `0C`? Compare your index with the mapping
  under *One memory, several doors*. No reply at all usually means a wrong CRC
  or a wrong address pair; "not enough data" usually means a 1-byte count.

## Solution

<details>
  <summary>Click to expand</summary>

`dnp3_stop.py` in this folder is the reference solution, standard library only.
It sweeps link addresses 0-100 with request link status frames, finds the
outstation at link address **10**, which accepts master **1** (OpenPLC's
`dnp3.cfg`: `local_address = 10`, `remote_address = 1`), and sends a Direct
Operate on Analog Output Int16 index **1128** (1024 + 104 = `%MW104`).

```bash
cd /CybICS/training/dnp3_sidedoor
python3 dnp3_stop.py 172.18.0.3 discover   # Outstation link address 10, it accepts master 1.
python3 dnp3_stop.py 172.18.0.3 stop       # index 1128 = 1, status SUCCESS
# click Verify on the challenge page
python3 dnp3_stop.py 172.18.0.3 restart    # index 1128 = 0, status SUCCESS
```

The stop frame on the wire, CRCs included:

```text
05 64 12 C4 0A 00 01 00 56 86                       link header + CRC
C0 C1 05 29 02 28 01 00 68 04 01 00 00 0E 1E        user data + CRC
```

</details>
