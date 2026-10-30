# The S7 side door

In this challenge you stop the CybICS plant without touching Modbus. The controller also speaks S7comm, the protocol of Siemens PLCs, and that second protocol reaches exactly the same variables. It is the lesson every firewall rule written for one protocol has to learn: closing a door helps only if it was the only door.

## The idea

A Programmable Logic Controller (PLC) keeps its program's variables in memory: pressures, set points, a "stop" switch. Protocols such as Modbus or S7comm are only ways in from the network. Each one gives the same memory a different address, the way one house can have a front door, a garage door and a cellar door.

<div class="callout analogy" markdown="1">
**Analogy:** a security guard checks everyone at the front door. The garage door is unlocked and nobody is posted there. Anyone who notices can walk in, and the house does not care which door they used.
</div>

Neither Modbus nor classic S7comm asks for a password. If a client can reach the port, it can read and write. A defender who blocks only Modbus port 502 has therefore not taken control away from an attacker; the attacker just uses another protocol. MITRE ATT&CK for ICS calls such a forged write an *Unauthorized Message: Command Message* (T1692.001), and taking the process away from its program *Manipulation of Control* (T0831).

## How it looks on CybICS

OpenPLC at `172.18.0.3` runs the plant program and opens several servers at once: Modbus on 502, S7comm on 102, DNP3 on 20000 and EtherNet/IP on 44818. The program keeps its process values and commands in **memory words** called `%MW`. One of them is the stop switch:

| Variable | PLC address | Over Modbus | Over S7comm |
|---|---|---|---|
| `stop` | `%MW104` | holding register 1128 | data block `DB1002`, bytes 208 and 209 |
| `manual` | `%MW106` | holding register 1130 | `DB1002`, bytes 212 and 213 |

The S7 server built into OpenPLC (the snap7 library) shows the whole `%MW` area as one **data block**, `DB1002`: a numbered chunk of memory that S7 clients read and write by byte offset. Each word is two bytes, so `%MWn` starts at byte `2n`. A value is stored with the high byte first (big-endian), as everywhere in S7comm.

While `stop` is anything but 0, the program switches the compressor and the system valve off and keeps them off. Watch them here while you work on the challenge:

<div data-widget="plant-live" data-fields="hpt,compressor,systemValve"></div>

<div data-widget="checkpoint" data-id="offset"></div>

## How to approach it

1. **Find the second door.** A port scan of the PLC shows 102 open next to 502. The [S7comm Scanning](/ctf/challenge/scanning2) challenge already talked to it.
2. **Read before you write.** Connect with an S7 client library (python-snap7 is installed in the attack shell), read a few words of `DB1002` and compare them with the pressures on the HMI. If they match, you have found the right memory.
3. **Work out the address.** Turn the PLC address of the stop switch into a byte offset in the data block.
4. **Write one word.** Set the switch, watch the plant react, and verify the challenge while the plant is stopped.
5. **Put it back.** Write 0 to `stop` and to `manual`. The plant is shared with everyone else on the board.

<details class="deep-dive" markdown="1">
<summary>Deep dive: what a write looks like on the wire</summary>

An S7comm request sits inside TPKT and COTP, like every S7comm message. The S7 header has a *ROSCTR* byte (1 = job) and the parameter part starts with a function code: `0x04` is Read Var, `0x05` is Write Var. Each item then names the memory area (`0x84` = data block, `0x82` = process outputs), the data block number and a start address counted in **bits**, so byte 208 travels as `208 x 8 = 1664 = 0x000680`. The data part carries the value. A write of 1 to `DB1002` byte 208 is 37 bytes in total.

</details>

## Detect and defend

The CybICS IDS raises `s7_enumeration` for any S7comm traffic and, since it decodes the S7 header, a separate high-severity `s7_write` alert for each write request. The alert names the area, the data block, the byte offset and the value, so an analyst sees "`DB1002.DBB208` = `0001`" rather than "some S7 traffic". Nothing in the plant writes over S7comm, so in CybICS every such alert deserves attention.

Defences:

- **Close every door.** A firewall on the PLC must cover every protocol it serves, not just Modbus. Allow-list the few hosts that need each one and drop the rest. See [Host firewalling](/theory/defense_firewall).
- **Turn off what you do not use.** OpenPLC can disable its S7 server in its settings. A protocol that is off cannot be abused. This is the principle of *least functionality*.
- **Watch the process, too.** The stop switch changing without an operator action on the HMI is suspicious, whatever protocol changed it.
- **Use device protection where it exists.** Real Siemens CPUs can require a password before a client may write.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The verify module looks at the newest `s7_write` alert to 172.18.0.3:102 whose decoded items touch `DB1002` bytes 208-209: it must have written a non-zero value, within the last five minutes by the IDS clock, and `stop` must still be set when Verify is clicked. Stopping the plant from the HMI or over Modbus does not pass, not even after an earlier S7 stop that was restored over S7 (the restore is the newest alert) or that is older than five minutes. The module reads `stop` over Modbus and falls back to its own S7 read when port 502 is firewalled, so that read shows up as an `s7_enumeration` alert from 172.18.0.1. The IDS snap length is 128 bytes, so very large multi-item writes are decoded only partly; a plain `db_write` is well inside it. The challenge leaves the plant stopped until the student restores it; `python3 s7_sidedoor.py restore` in the attack shell resets `stop` and `manual`.

</details>

## Before you start

- [S7comm](/theory/s7comm) for TPKT, COTP and the S7 header.
- [S7comm enumeration](/theory/scanning2) for the two S7 servers on CybICS.

Later on the path:

- [Host firewalling](/theory/defense_firewall): the Modbus firewall this challenge walks around.
