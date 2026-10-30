# DNP3 Side Door

In this challenge you stop the CybICS gas plant without touching Modbus at all.
The PLC answers a second industrial protocol, DNP3, on a port the Modbus
defences never watch, and a single well-formed command over it shuts the
process down. You will build that command, checksums and all, by hand.

## The idea

A controller rarely speaks only one protocol. It is like a house with a
guarded front door and a back door nobody remembers: you can bolt the front
door as hard as you like, but the back door still opens onto the same hallway.

**Distributed Network Protocol 3 (DNP3)** is that back door here. It is a
protocol common in electricity and water utilities, where a *master* polls and
commands *outstations* (the field devices). The important point for this
challenge is that DNP3 and Modbus reach the *same* memory inside the PLC. A
defence that filters or watches one protocol does nothing about the other.

DNP3 is also stricter than Modbus about how a message is formed. Every frame
begins with the bytes `05 64`, and a checksum called **CRC-16/DNP** protects
every 16-byte block. Get one byte wrong and the outstation drops the frame in
silence. So, unlike a Modbus request, you cannot throw a rough DNP3 frame at
the device and hope — you have to assemble it correctly.

<div class="callout analogy" markdown="1">
**Analogy:** Modbus is a postcard anyone can scribble. DNP3 is a form with a
checksum box on every line: fill one line in wrong and the clerk bins the whole
form without a word.
</div>

## How it looks on CybICS

OpenPLC enables a DNP3 outstation and the lab publishes it alongside the usual
services. The PLC you already know from the Modbus challenges carries it:

| Port | Protocol | On the PLC at 172.18.0.3 |
|---|---|---|
| 502 | Modbus/TCP | The protocol fuxa and hwio use to read and write the plant |
| 20000 | DNP3 | An outstation with its own DNP3 link address, which answers only the one master address it is configured for |

The outstation maps DNP3 *analog outputs* onto the same memory Modbus uses.
An index below 1024 is an output word; an index of **1024 + n** is the memory
word `%MWn`, which Modbus calls holding register 1024 + n. The PLC program keeps
its commands, the stop flag among them, in such memory words, and the challenge
page tells you which word is which. From there it is a sum you can do yourself.
Writing the stop flag is exactly what the *Flood & Overwrite* lesson did over
Modbus — the compressor switches off and the system valve closes — but here the
command travels over DNP3.

A port scan from the attack machine shows the extra service as `20000/tcp open
dnp`. nmap names it from the port number alone, without talking to it; a DNP3
request, or a Wireshark capture filtered on `dnp3`, confirms it.

## How to approach it

Think of it in three moves: find the door, learn who may knock, then knock.

1. **Find the door.** Scan the PLC and spot port 20000 next to the familiar 502.
2. **Learn who may knock.** Every DNP3 station has its own 16-bit link
   address, separate from its IP address. The outstation ignores any frame that
   is not addressed to it *and* sent from the master address it expects, so a
   guess is met with silence. A *request link status* frame is tiny and changes
   nothing, so you can send one for every pair of small addresses in one burst.
   Only the right pair gets an answer, and the answer names both addresses.
3. **Knock.** Build a DNP3 **Direct Operate** on an Analog Output whose index
   is the stop flag's memory word, worked out with the 1024 + n rule, and give
   it a value that means "stop". That means stacking three layers inside the TCP
   payload — the link header, a transport byte, and the application function
   code and object — and computing the CRC over each block. The challenge page
   walks through every byte and hands you the CRC routine.

<div class="callout tip" markdown="1">
**Tip:** Build the frame once in Python and print its bytes before you send it.
A wrong CRC produces no error message, just silence, so comparing your bytes to
the worked example in the challenge is the fastest way to find a mistake.
</div>

When the plant stops, verify while it is still stopped, then operate the same
index with 0 to bring it back. The plant is shared with everyone on the board, so do
not leave it stopped.

<div class="checkpoint" data-widget="checkpoint" data-id="which-door"></div>

## Detect and defend

A monitor only sees the protocols it understands. The CybICS IDS reads DNP3 on
port 20000 with a rule of its own:

| Rule | Fires on | Severity |
|---|---|---|
| `dnp3_operate` | A DNP3 control request (select, operate, direct operate, write) to port 20000 | high |

The rule recognises the `05 64` start bytes, checks the CRCs, reads the
application function code and decodes the points and values of an operate. A
frame with a wrong CRC is ignored, because the outstation ignores it too. The
IDS also reads the outstation's reply and files it with the alert, so an
analyst can tell an attempt the outstation refused or dropped from a command it
actually carried out: only the reply says what happened to the process. Plain
reads and link status requests raise nothing, the same way the Modbus rules
ignore reads, so the address sweep itself goes unremarked.

The stronger defence is to remove the door. The plant never uses DNP3, so the
outstation should be switched off, or its port filtered the way the Modbus
firewall challenge filters 502. The lesson is general: a firewall or a monitor
scoped to one protocol is blind to every other protocol the device still
answers.

## Before you start

- [DNP3, EtherNet/IP and friends](/theory/other-protocols)
- [Modbus TCP](/theory/modbus)
- [The ICS attack lifecycle](/theory/attack-lifecycle)
