# Whispering PLC

> **MITRE ATT&CK for ICS (reconstructed):** `Command and Control` | [T0869 - Standard Application Layer Protocol](https://attack.mitre.org/techniques/T0869/) | [T0885 - Commonly Used Port](https://attack.mitre.org/techniques/T0885/)
>
> **MITRE D3FEND:** [D3-NTA - Network Traffic Analysis](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | [D3-PMAD - Protocol Metadata Anomaly Detection](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | [D3-APCA - Application Protocol Command Analysis](https://d3fend.mitre.org/technique/d3f:ApplicationProtocolCommandAnalysis/)

## Overview
The plant team wants to tighten the PLC: only the hosts that really need
Modbus should get it, and only for the registers they really need. Before
anyone writes such a **read allowlist**, someone has to find out who reads
what today. So the team recorded four minutes of Modbus/TCP at the PLC's
mirror port on an ordinary afternoon: **`baseline.pcap`**.

Nothing happened that afternoon. The plant ran, nobody wrote to the PLC,
and the CybICS IDS raised no alert. Every request in the file is a read.

One of those reads does not belong. An implant is sending data out of the
plant network, hidden in Modbus requests that look exactly like polling.
Your job is to **find the reader that does not belong, measure its rhythm,
decode what it is saying and work out the allowlist that would have made it
loud**.

This is an offline forensics challenge. It needs nothing from the running
plant and works the same in a classroom without the testbed.

## Background

### Who reads the PLC

| Host | IP address | MAC address in the capture | What it does over Modbus |
|------|-----------|----------------------------|--------------------------|
| OpenPLC (the PLC, where the capture was taken) | 172.18.0.3 | `02:42:ac:12:00:03` | answers on port 502 |
| FUXA (the HMI) | 172.18.0.4 | `02:42:ac:12:00:04` | polls the values on its screens |
| OPC-UA gateway | 172.18.0.5 | `02:42:ac:12:00:05` | copies values into its OPC-UA address space for the office network |

The I/O service at 172.18.0.2, which moves the sensor values and outputs
between the plant and the PLC, writes to the PLC about forty times a
second and never reads holding registers. The capture box filtered it out
(`tcp port 502 and not host 172.18.0.2`) to keep the file small.

### A read can carry data too

A Modbus read request is twelve bytes. Besides the function code it carries
a **start address** (two bytes) and a **quantity** (two bytes):

```
00 2a  00 00  00 06  01  03  00 64  00 02
tid    proto  len    unit fc start   quantity
```

The PLC answers with the values, and the client is happy. But the *client*
chooses the start address and the quantity freely. Anyone who can watch the
traffic, or who sits upstream of it, can read those choices as data: one
request can carry two or even four bytes of whatever the sender wants. That
is a **covert channel**, a way to move information inside traffic whose
purpose is something else.

An implant on a host that is allowed to talk Modbus can use it to send a
heartbeat ("I am alive"), status or small stolen secrets, through a port the
firewall already opens and in a protocol nobody looks at closely. ATT&CK
for ICS calls this *Standard Application Layer Protocol* (T0869) over a
*Commonly Used Port* (T0885).

### Why the IDS stayed silent

The CybICS IDS counts and inspects Modbus **writes** (floods, writes from
unexpected hosts) and diagnostic function codes. Reads are never inspected,
because every HMI and gateway reads all day long. An attacker who only
reads is invisible to it. Reading an address the plant does not use does
not even fail: OpenPLC holds a large `%MW` memory area and answers a read of
an unused word with 0.

### Regular is not suspicious, in a plant

In office networks, "beacon detection" looks for a host that contacts the
same server at a very regular interval. In a plant that rule fires on
everything: HMIs, gateways and historians poll on fixed timers by design.
Rhythm only helps once you know *which conversation* to look at and what
the normal rhythms are.

### What a read allowlist is

A read allowlist names, for every legitimate client, which function codes
and which address ranges it may use. Anything else is an alert (or, in a
firewall that understands Modbus, dropped). The interesting design
question is how precise it must be: by host only, by host and function
code, or by host, function code and address range.

## Where to run it

You need the file and a tool that reads captures.

- **Wireshark** is the easiest: on the Kali attack machine (`--mode full`),
  open `/CybICS/training/modbus_covert_c2/baseline.pcap`, or download the
  file on your own computer from the challenge page:
  [baseline.pcap](/ctf/challenge/modbus_covert_c2/baseline.pcap)
  (in the repository it is `training/modbus_covert_c2/baseline.pcap`).
- **The attack shell** has no Wireshark, but `tcpdump` reads the file at
  `/CybICS/training/modbus_covert_c2/baseline.pcap` and shows the bytes with
  `-X`, and Python is there to do the rest.
- **`read_allowlist.py`** in this folder tries an allowlist you write as JSON
  against the capture and counts, per TCP connection, the requests it would
  pass and flag. Start with `allowlist.example.json`:

  ```bash
  cd /CybICS/training/modbus_covert_c2
  python3 read_allowlist.py baseline.pcap allowlist.example.json
  ```

## Task

Answer four questions on the challenge page:

1. The **client IP address and TCP port** of the implant's connection, for
   example `10.0.0.1:40000`.
2. The **interval** in seconds between two of the implant's requests.
3. The **message** that the implant's requests spell, once, without the
   character that separates the repetitions.
4. The **holding-register range** (first-last) that a read allowlist for
   function code 3 must permit so that the plant's legitimate readers keep
   working.

All four answers are graded together.

### Steps

1. **Group by conversation.** In Wireshark, *Statistics > Conversations*,
   tab *TCP*. How many Modbus connections are there, and which host opened
   each one? Compare that with the table above. A host with *two*
   connections to the same PLC deserves a question: why would one program
   need two?

2. **Describe each connection's normal.** For each connection, filter on its
   client port and look at what it asks for:

   ```
   tcp.srcport == <port> && modbus.func_code
   ```

   Add the columns *Function Code* (`modbus.func_code`), *Reference Number*
   (`modbus.reference_num`) and *Word Count* (`modbus.word_cnt`). Which
   addresses does it read, how many at once, and does the set repeat? A
   legitimate poller asks for the same few registers again and again.

3. **Measure the rhythm.** With one connection filtered, add the column
   *Delta time displayed* (`frame.time_delta_displayed`). Polling programs
   run on a timer, so every connection here is regular. Note each
   connection's cycle and how much it wanders. Is one of them suspiciously
   *exact*, or does it run on a rhythm no screen needs?

4. **Find the odd reader.** One connection asks for addresses no other
   client ever reads, and never the same one for long. Write its start
   addresses down in **hexadecimal** (right-click the column, or use
   `tcpdump -X` and read bytes 9 and 10 of the Modbus data). What stays the
   same in every address, and what changes?

5. **Decode.** The part that changes is one byte. Look it up in an ASCII
   table. The message repeats; find the separator and write it down once.

6. **Design the allowlist.** Write a rule set for `read_allowlist.py` that
   lets every legitimate request pass and flags the implant. First run the
   example, which allows both hosts completely: what does it flag? Then
   narrow the rules by function code and address range until the implant
   stands out and nothing else does. The range you needed for function 3 is
   your fourth answer.

7. **Answer** the four questions on the challenge page and press *Verify*.

## Detect and Defend

### Detection
- **Allowlist per client, function code and range.** A host-only
  allowlist passes everything here, because the implant lives on an allowed
  host. Adding the function code still passes it: it only reads. Only the
  address range separates it. OT monitoring products build this table
  automatically during a learning phase; the result is only as good as the
  baseline, so check what you are learning before you trust it.
- **Watch new connections from known hosts.** A second long-lived Modbus
  session from a gateway that normally holds one is a change worth a look.
- **Compare a client to its own past.** A poller reads the same set of
  registers forever. A client whose start addresses keep changing, or that
  reads words no HMI tag and no gateway node uses, is not polling.
- **Use rhythm last, not first.** In a plant every poller is periodic.
  Timing helps to confirm a suspicion and to tell a script from a scan cycle
  (an exact interval that matches no configured poll rate), not to start one.

### Defense
- **Enforce, not only detect.** A Modbus-aware firewall or the PLC's own
  access rules can drop reads outside the allowlist, so the channel does not
  even reach the network beyond the PLC.
- **Protect the gateway.** The OPC-UA gateway bridges the office network and
  the plant. Harden it, monitor its processes and treat it as the boundary
  it is.
- **Limit what leaves.** Data hidden in reads still has to be seen by
  someone. Segmenting the plant network and restricting who can capture or
  mirror its traffic leaves the implant talking to nobody.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques you uncover

| Tactic | Technique | ID | In the capture |
|--------|-----------|-----|----------------|
| Command and Control | Standard Application Layer Protocol | [T0869](https://attack.mitre.org/techniques/T0869/) | Status data hidden in Modbus read requests |
| Command and Control | Commonly Used Port | [T0885](https://attack.mitre.org/techniques/T0885/) | The channel uses port 502, which the plant must keep open |

### MITRE D3FEND - Defensive techniques you apply

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Reading the baseline capture per connection |
| Protocol Metadata Anomaly Detection | [D3-PMAD](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | A second session from one host and an exact, unexplained interval |
| Application Protocol Command Analysis | [D3-APCA](https://d3fend.mitre.org/technique/d3f:ApplicationProtocolCommandAnalysis/) | Checking each read's function code and address range against an allowlist |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Communications Protection (SC)** | SC-7 | Boundary protection: only the needed protocol functions cross |
| **Access Control (AC)** | AC-4 | Information flow enforcement by client, function and range |
| **System and Information Integrity (SI)** | SI-4 | System monitoring against a known-good baseline |
| **Audit and Accountability (AU)** | AU-6 | Reviewing and analysing recorded network activity |

</details>

## Hints

<details>
  <summary>💡 Hint 1</summary>

The IP address is not the unit to look at here: one host has two
connections. Statistics > Conversations > TCP shows them side by side.

</details>

<details>
  <summary>💡 Hint 2</summary>

Write the start addresses of the odd connection in hex, for example
`0x0548`. The high byte never changes. The low byte is printable ASCII:
`0x48` is `H`.

</details>

<details>
  <summary>💡 Hint 3</summary>

The legitimate readers read different amounts and in different orders, but
the set of registers they touch is the same, and it is small. The FUXA
request with the largest quantity tells you most of it.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

In Wireshark:

1. *Statistics > Conversations > TCP* shows three connections to
   172.18.0.3:502: one from FUXA and **two from 172.18.0.5**. One of the two
   carries about fifteen times as many requests as the other.
2. Filter each connection with `tcp.srcport == <port> && modbus.func_code`.
   FUXA reads one block of holding registers and four coils every second.
   The gateway's busy connection reads six single registers every two
   seconds, always the same six. The quiet connection reads one register at
   a time, and every request asks for a different address far above the
   plant's registers.
3. With the quiet connection filtered, *Delta time displayed* is the same
   to within a fraction of a millisecond for every request, while FUXA and
   the gateway's poll wander by a few milliseconds and drift. That interval
   is the second answer.
4. In hex every address of the quiet connection starts with the same high
   byte; the low byte is an ASCII character. Read in order, they spell a
   short sentence that repeats, separated by `|`. The recording starts in
   the middle of it.
5. The allowlist that works: FUXA may read function 3 on its block and
   function 1 on coils 0-3; the gateway may read function 3 on the same
   block. `read_allowlist.py` then flags only the quiet connection.

In the attack shell, without Wireshark:

```bash
cd /CybICS/training/modbus_covert_c2
python3 - <<'EOF'
import struct
data = open("baseline.pcap", "rb").read()
pos, conns = 24, {}
while pos < len(data):
    sec, usec, n, _ = struct.unpack("<IIII", data[pos:pos + 16])
    raw = data[pos + 16:pos + 16 + n]; pos += 16 + n
    t = 14 + (raw[14] & 15) * 4
    sport, dport = struct.unpack("!HH", raw[t:t + 4])
    mb = raw[t + (raw[t + 12] >> 4) * 4:]
    if dport == 502 and len(mb) >= 12:
        src = ".".join(map(str, raw[26:30]))
        conns.setdefault((src, sport), []).append((sec + usec / 1e6, mb[7], *struct.unpack("!HH", mb[8:12])))
for (src, port), reqs in conns.items():
    gaps = [round(b[0] - a[0], 4) for a, b in zip(reqs, reqs[1:])]
    print(src, port, len(reqs), "requests, gaps", min(gaps), "-", max(gaps),
          "fc/start/qty:", sorted({r[1:] for r in reqs})[:8])
EOF
```

The connection whose start addresses keep changing is the implant. Decode
it by adding, at the end of the script (with its address and port filled in):

```python
print("".join(chr(start & 0xFF) for _, _, start, _ in conns[("<ip>", <port>)]))
```

Then write your allowlist JSON as in step 5 and confirm it with
`read_allowlist.py`.

</details>

## For maintainers: regenerating the capture

`baseline.pcap` is generated, never edited by hand:

```bash
python3 software/scripts/generate_covert_c2_pcap.py          # rewrite the file
python3 software/scripts/generate_covert_c2_pcap.py --key    # print the answers
```

The generator is deterministic; the polling patterns of FUXA and the
gateway are measured from the virtual stack (see its docstring). If you
change the story, update the expected values in
`software/landing/modules/defense_checks/check_modbus_covert_c2.py`;
`tests/test_modbus_covert_c2.py` fails until they match.
