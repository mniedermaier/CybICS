# Packet anatomy

In this challenge you build Modbus messages yourself, byte by byte, send the ones that only read to the CybICS PLC, and take its answers apart. No library and no Wireshark do the work for you. Every later challenge that captures, fuzzes or detects traffic expects you to read bytes this way.

## The idea

A tool shows a Modbus message as tidy fields: "read 3 registers starting at 1124". On the network there are no fields, only a row of bytes. The protocol is the agreement about which byte means what. Once you know that agreement, you can read any capture and write any message, with or without a tool.

<div class="callout analogy" markdown="1">
**Analogy:** a paper form has boxes with labels. Send the same form as one long line of characters, without the labels, and only someone who knows the layout ("characters 1 to 2 are the order number, 3 to 4 are always zero...") can read it. A protocol specification is that layout.
</div>

A **byte** is two hexadecimal (hex) digits, from `00` to `ff`. Numbers bigger than 255 take two bytes, high byte first: 1126 is `04 66`.

## How it looks on CybICS

The PLC is OpenPLC at `172.18.0.3`, port 502. Every Modbus/TCP message, question or answer, has the same two parts:

| Part | Bytes | Field |
|---|---|---|
| MBAP header | 2 | Transaction ID: any number, copied into the answer |
| | 2 | Protocol ID: always `00 00` |
| | 2 | Length: how many bytes follow this field |
| | 1 | Unit ID: which device behind a gateway; OpenPLC copies it back |
| PDU | 1 | Function code: what to do |
| | n | Data, which depends on the function code |

The **MBAP header** (Modbus Application Protocol header) frames the message for TCP. The **PDU** (Protocol Data Unit) is the actual request. Try the builder: change a field and watch the bytes, or click a byte group to see what it is.

<div data-widget="modbus-frame" data-fc="6" data-address="1126" data-value="90"></div>

<div data-widget="checkpoint" data-id="length"></div>

Three rules cover most of what you will meet:

- **Reads and writes cover a block.** Function 03 reads and function 16 writes a run of neighbouring registers, given as a start address and a quantity. To get registers 10 and 12 in one message, you ask for 10, 11 and 12.
- **Answers echo the question.** The response carries the same transaction ID and unit ID, then the function code, a byte count and the values. That is how a client matches answers to questions.
- **Errors set the top bit.** A refused request comes back with the function code plus `0x80` and one exception code, for example `02` "illegal data address". A refused read (03) therefore answers with `83`.

## How to approach it

1. **Find the addresses.** The PLC program fixes where each value lives, as memory words such as `%MW100`. The challenge page explains how OpenPLC turns a memory word into a register number.
2. **Write each frame on paper first.** Field by field, in order. Count the bytes after the length field before you fill it in.
3. **Send only what reads.** A raw TCP connection (`nc`, or Python's `socket` module) carries your bytes unchanged. Read requests change nothing in the plant. Write frames you build, but do not send: the plant is shared.
4. **Take every answer apart.** Mark each field of the response. Check that it belongs to your question.
5. **Provoke an error on purpose.** Ask for a register the PLC does not have and see what a refusal looks like.

<details class="deep-dive" markdown="1">
<summary>Deep dive: recognising other protocols by their first bytes</summary>

The same skill works for every industrial protocol. A capture rarely labels itself, but the first bytes usually give it away:

| First bytes | Protocol | Why |
|---|---|---|
| any, any, `00 00` | Modbus/TCP | The protocol ID at bytes 3 and 4 is always zero |
| `03 00` | S7comm | A TPKT header (version 3); the S7 part starts later with `32` |
| `48 45 4c` | OPC UA | ASCII `HEL`, the Hello message; others are `ACK`, `OPN`, `MSG` |
| `05 64` | DNP3 | The fixed start bytes of every link-layer frame |
| `63 00` | EtherNet/IP | Command 0x0063, ListIdentity, written low byte first |

EtherNet/IP is the odd one out: it writes numbers **little-endian**, low byte first, where Modbus, S7comm and the DNP3 start bytes read high byte first. Getting the byte order wrong is the most common decoding mistake.

S7comm wraps its message in two older layers, like a letter in an envelope in a parcel:

<div data-widget="s7-layers" data-sample="setup"></div>

<div data-widget="sequence" data-id="protocols"></div>

</details>

## Detect and defend

Nothing in any field says who sent a frame: there is no user, no password and no signature. Whoever can reach port 502 can send exactly the bytes the HMI sends, and the PLC cannot tell them apart.

For a defender that means:

- **Reads are quiet.** The CybICS IDS watches Modbus writes and diagnostic requests; an ordinary read raises no alert. Watching which hosts read at all is the only way to notice reconnaissance.
- **Writes leave a trace.** The IDS keeps a journal of every Modbus write it sees, with source, address and values, even when no rule fires.
- **Errors are a signal.** A normal HMI never asks for a register that does not exist. Exception responses and malformed frames, such as a wrong length field, point to probing or fuzzing.
- **Limit and inspect.** A firewall that lets only the HMI and the I/O service reach port 502 removes most of the risk. A Modbus-aware filter can additionally allow reads for monitoring and refuse writes from everyone else.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The challenge grades four hex frames all or nothing in `check_packet_anatomy.py`: an FC 03 read of 1124 quantity 3, the PLC's matching response (same transaction and unit ID, byte count 6, any values), an FC 16 write of 1128 quantity 3 with three zero words, and an exception response 83 02. Transaction and unit IDs are free, so there is no single string to pass around, but a student who understood the frames can of course tell a classmate the fields. The response is not compared with live values, which change; a hand-made response that is structurally right passes. Nothing is sent to the plant by the grader. The modbus-frame widget can build all three requests; it does not tell the student which addresses and quantities to use.

</details>

## Before you start

- [Modbus TCP](/theory/modbus)

Later on the path:

- [Capturing Modbus traffic](/theory/wireshark_capture)
- [S7comm](/theory/s7comm)
- [DNP3, EtherNet/IP and friends](/theory/other-protocols)
