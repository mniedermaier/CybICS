# Packet Anatomy

> **MITRE ATT&CK for ICS:** `Collection` | [T0801 - Monitor Process State](https://attack.mitre.org/techniques/T0801/) | `Impair Process Control` | [T1692.001 - Unauthorized Message: Command Message](https://attack.mitre.org/techniques/T1692/001/)

## Overview
Tools such as pymodbus, Wireshark and the IDS show you a Modbus message as
neat fields: "read 3 registers at 1124". On the wire there are no fields,
only bytes. Before you capture traffic, fuzz a PLC or write a detection
rule, you have to be able to go from one to the other in your head: which
byte is the length, where the address starts, what an error looks like.

In this lab you **build Modbus/TCP frames byte by byte, send the read-only
ones to the CybICS PLC with nothing but a raw TCP connection, and take its
answers apart.** No library does the encoding for you. You hand in four
frames as hex; the board takes each one apart and checks every field.

## Background

### The Modbus/TCP frame

Every Modbus/TCP message, request or response, is a 7-byte **MBAP header**
(Modbus Application Protocol header) followed by the **PDU** (Protocol Data
Unit): a function code and its data. All numbers are big-endian, high byte
first.

| Bytes | Field | Meaning |
|-------|-------|---------|
| 2 | Transaction ID | Chosen freely by the client; the server copies it into its answer so the client can match them |
| 2 | Protocol ID | Always `00 00` for Modbus |
| 2 | Length | Number of bytes that **follow** this field: the unit ID plus the PDU |
| 1 | Unit ID | Which device behind a gateway is meant; OpenPLC answers any value and copies it back |
| 1 | Function code | What to do |
| n | Data | Depends on the function code |

The length field is the classic mistake: it does not count the transaction
ID, the protocol ID or itself.

### The three function codes of this lab

**03 Read Holding Registers.** The request names a start address and a
quantity:

| Request PDU | | Response PDU | |
|---|---|---|---|
| `03` | function | `03` | function |
| 2 bytes | start address | 1 byte | byte count = 2 &times; quantity |
| 2 bytes | quantity | 2 bytes each | the register values, in order |

A read always returns a **contiguous block**. If you want registers 10 and
12, you ask for 10, 11 and 12 and ignore 11.

**16 (`0x10`) Write Multiple Registers.** One frame writes a contiguous
block:

| Request PDU | Meaning |
|---|---|
| `10` | function |
| 2 bytes | start address |
| 2 bytes | quantity of registers |
| 1 byte | byte count = 2 &times; quantity |
| 2 bytes each | the new values |

**Exceptions.** When a server refuses a request it answers with the
function code **plus `0x80`** (the top bit set) and one exception code:
`01` illegal function, `02` illegal data address, `03` illegal data value,
`04` server device failure. A refused read of holding registers therefore
comes back as function `83`.

A worked example that is *not* one of your answers: setting HPT (holding
register 1126 = `04 66`) to 90 (`00 5a`) with function 06 and transaction
ID 1 is

```
00 01  00 00  00 06  01  06  04 66  00 5a
 tid   proto  len   unit fc  addr   value
```

Six bytes follow the length field (unit, function, two for the address, two
for the value), so the length is `00 06`.

### Where the plant's values live

The PLC program (`software/OpenPLC/cybICS.st`) declares its variables with
fixed addresses:

```
gst     AT %MW100 : UINT;   (* pressure in the gas storage tank *)
hpt     AT %MW102 : UINT;   (* pressure in the high-pressure tank *)
stop    AT %MW104 : UINT;   (* 1 = plant stopped *)
manual  AT %MW106 : UINT;   (* 1 = manual mode *)
```

OpenPLC puts memory word `%MWn` at **holding register 1024 + n**. These are
addresses as they go on the wire, counted from 0. The words between them
(`%MW101`, `%MW103`, ...) are declared nowhere and always read 0.

## Where to run it

From the **attack shell** (WebShell view of the landing page, 172.18.0.100)
or the Kali attack machine. You need `printf`, `nc` and `xxd` (or `od`), or a
few lines of Python with the `socket` module. Talk to the PLC at
**172.18.0.3:502**, its address on the plant network.

## Task

Hand in four frames as hex on the challenge page. Spaces between the bytes
are fine.

1. **A read request** that gets GST **and** HPT in **one** frame, and nothing
   more than it has to.
2. **The PLC's response** to exactly that request, as it came back.
3. **A write request** that sets STOP **and** MANUAL to 0 in **one** frame.
   **Do not send it.** The plant is shared, and the board checks the bytes,
   not the effect.
4. **The PLC's answer to a read of a holding register it does not have.**

### Steps

1. **Work out the addresses.** Turn `%MW100`, `%MW102`, `%MW104` and `%MW106`
   into holding register numbers, then into two hex bytes each.

2. **Build the read request on paper first.** Pick a transaction ID, then
   write down every field in order. Count the bytes after the length field
   before you fill it in.

3. **Send it with a raw TCP connection.** `printf` turns `\xNN` escapes into
   bytes, `nc` sends them and `xxd` shows the answer as hex:

   ```bash
   printf '\x00\x09\x00\x00\x00\x06\x01\x03\x04\x64\x00\x01' | nc -w 2 172.18.0.3 502 | xxd
   ```

   That example reads only GST. Change it into your frame. If nothing comes
   back, your length field is probably too large: the PLC waits for bytes
   that never arrive. If it is too small, the PLC sees a cut-off request and
   answers with an exception (function `83`, code `03`).

4. **Take the response apart.** Mark the transaction ID, the length, the
   byte count and each register. Check that the transaction ID and unit ID
   are the ones you sent, and that GST and HPT are plausible tank pressures
   (0 to 255). Copy the response exactly as it came back.

5. **Build the write request.** One frame, function 16, starting at STOP.
   Remember that a block is contiguous. Check the length field and the
   byte count twice. Do not send it.

6. **Provoke an exception.** OpenPLC's holding registers end below 9000.
   Read one register at 9000 or above (a read changes nothing), with the
   address as two hex bytes, and take the answer apart: which bit tells you
   it is an error, and which byte says why?

7. **Hand in.** Paste the four frames on the challenge page. The check is
   all or nothing; it does not say which frame is wrong.

The Theory Path lesson *Packet anatomy* has a frame builder that shows
every byte; use it to check your work, not instead of it.

## Detect and Defend

### Detection

- **Reads are invisible to the CybICS IDS.** Its Modbus rules look only at
  write requests and at the diagnostic function codes 8 and 43. Your read
  request and the exception probe raise no alert, which is exactly why
  reconnaissance by reading is attractive.
- **Writes are journaled.** Every Modbus write the IDS sees, by whom, to
  which address and with which values, lands in its write journal
  (`/api/modbus/writes` on the IDS, port 8443), even when no rule fires. A
  single write from the attack shell stays below the unauthorised-write
  threshold (10 writes in 30 seconds) but is still on record.
- **Exceptions are a signal.** A normal HMI never reads past the end of the
  PLC's memory. Exception responses with code `02` from a client that is
  not an operator station are a strong hint of probing or fuzzing. Wireshark
  shows them with the filter `modbus.exception_code`.
- **Malformed frames are a signal too.** A wrong length field or a protocol
  ID other than 0 never comes from a correct client.

### Defense

- **Nothing in the frame says who sent it.** There is no user, no password
  and no signature in any field you built. Whoever can reach port 502 can
  send these bytes. Restrict port 502 to the hosts that need it (see the
  *Modbus Firewall Rules* challenge).
- **Inspect, do not just forward.** A Modbus-aware firewall or proxy can
  allow function 03 for monitoring stations and refuse 06 and 16 from
  everyone but the HMI.
- **Validate on the PLC side.** Writable flags such as STOP and MANUAL should
  be accepted only from expected clients, or moved behind a protocol with
  authentication.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Collection | Monitor Process State | [T0801](https://attack.mitre.org/techniques/T0801/) | A hand-built Modbus read returns the live tank pressures |
| Impair Process Control | Unauthorized Message: Command Message | [T1692.001](https://attack.mitre.org/techniques/T1692/001/) | The write frame is a complete command message; nothing in it is checked against its sender |

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Decode Modbus frames and journal writes and exceptions |
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Only expected clients reach port 502 |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Communications Protection (SC)** | SC-7 | Boundary protection around the PLC's Modbus port |
| **Audit and Accountability (AU)** | AU-2, AU-12 | Record Modbus writes and exceptions with their source |
| **System and Information Integrity (SI)** | SI-4 | Monitor for malformed frames and probing |

</details>

## Hints

<details>
  <summary>💡 Hint 1</summary>

GST and HPT are not next to each other. A read covers a block; how many
registers does the smallest block holding both of them contain?

</details>

<details>
  <summary>💡 Hint 2</summary>

The length field counts the unit ID and the PDU. For a read request that is
always 6. For a response or a write, count again: it is not 6.

</details>

<details>
  <summary>💡 Hint 3</summary>

If the board refuses your response, check that it belongs to *your*
request: same transaction ID, same unit ID, and exactly as many registers
as you asked for. If it refuses your exception, look at the exception code:
a frame with a wrong length is refused for a different reason than a
register that does not exist.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

GST is `%MW100` = holding register 1124 (`04 64`), HPT 1126, STOP 1128
(`04 68`), MANUAL 1130.

- **Read:** start 1124, quantity 3 (1124, 1125, 1126). Length 6.
- **Response:** the same transaction and unit ID, length 9, function 03,
  byte count 6, three registers (GST, 0, HPT).
- **Write:** function 16, start 1128, quantity 3 (1128, 1129, 1130), byte
  count 6, six zero bytes. Length 13 (`00 0d`).
- **Exception:** a read beyond the last holding register (OpenPLC answers
  up to 8191) comes back with function `83` and code `02`, illegal data
  address. Length 3.

The solution script builds all four, sends the two reads and prints the
answers. It never sends the write:

```bash
cd /CybICS/training/packet_anatomy
python3 frames.py
```

Paste its four `read_request`, `read_response`, `write_request` and
`exception` lines on the challenge page.

</details>
