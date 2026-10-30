# DNP3, EtherNet/IP and friends

Modbus is the protocol you learn first, but a real plant speaks a mix of protocols from different industries and decades. Once you understand Modbus, you already know the questions to ask about every one of them.

## The same questions for every protocol

Industrial protocols differ in their byte layout, but share a family resemblance. When you meet a new one, ask five questions:

1. **Who talks to whom?** Is there a client and a server, a master and an outstation, or does everyone broadcast?
2. **How is data addressed?** By register number, by object, by name?
3. **Which commands change the plant?** Writes, "operate" commands, restarts, firmware downloads.
4. **Does it check who is asking?** Most were designed for closed networks and do not.
5. **How do you recognise it on the wire?** A port number, a magic byte, a Wireshark dissector.

<div class="callout analogy" markdown="1">
**Analogy:** protocols are like regional dialects. The words differ, but every dialect can ask a question, give an order and say "yes, done". Spot those three in one, and you will find them in the next.
</div>

## DNP3: the utility protocol

The **Distributed Network Protocol 3 (DNP3)** is the workhorse of electric and water utilities, especially in North America. It usually runs over TCP port **20000**.

- **Roles.** A **master** (the control centre) polls many **outstations** (remote substations or pumping stations).
- **Data.** Values are typed points: binary inputs, binary outputs, analog inputs, counters.
- **Unsolicited responses.** An outstation may report a change on its own instead of waiting to be polled.
- **Risky commands.** *Direct operate* switches an output in one step, and *cold restart* reboots the device.
- **Recognising it.** Every DNP3 link-layer frame starts with the two bytes `05 64`. Wireshark's display filter is `dnp3`.

An optional extension, **Secure Authentication**, lets an outstation challenge the master before obeying a critical command, but many installations do not enable it.

## EtherNet/IP and CIP: the factory protocol

**EtherNet/IP** (the "IP" stands for *Industrial Protocol*, not Internet Protocol) is common in factories, especially with Rockwell Automation / Allen-Bradley equipment. It is really two layers:

- **EtherNet/IP encapsulation** carries messages over TCP port **44818** for requests and replies ("explicit messaging") and UDP port **2222** for fast, cyclic I/O data ("implicit messaging").
- **CIP, the Common Industrial Protocol,** travels inside. CIP models a device as **objects** with attributes and services. The *Identity* object holds the vendor, product name and serial number.

A client first sends *Register Session* and gets a session handle back. This is bookkeeping, not a login: there is no password. A broadcast *List Identity* asks every device to introduce itself, which makes discovery easy for engineers and attackers alike. Wireshark's filters are `enip` and `cip`. **CIP Security** adds encryption and authentication, but older devices cannot use it.

<div data-widget="checkpoint" data-id="session"></div>

## Four more you will meet

| Protocol | Where | Transport | Note |
|---|---|---|---|
| **PROFINET** | Factories, Siemens-heavy plants | Mostly raw Ethernet, not IP | Its real-time traffic has no IP header and cannot be routed, so a port scanner will not see it. |
| **BACnet** | Building automation: heating, ventilation, access control | UDP port 47808 | Many building controllers answer a `Who-Is` broadcast. BACnet Secure Connect adds encryption. |
| **IEC 60870-5-104** | Power grids, especially in Europe | TCP port 2404 | The Industroyer malware used it against the Ukrainian grid in 2016 (see [the Ukraine case study](/theory/ukraine-grid)). |
| **IEC 61850** | Substations | MMS over TCP port 102, plus GOOSE directly on Ethernet | S7comm uses port 102 too, so "102 open" does not by itself mean "Siemens PLC". |

<details class="deep-dive" markdown="1">
<summary>Deep dive: more on DNP3, EtherNet/IP and the table</summary>

DNP3 is standardised as IEEE 1815. Each side has a 16-bit DNP3 address, separate from its IP address, and each point keeps a timestamped history of events, which suits slow radio and serial links. EtherNet/IP is maintained by the organisation ODVA.

PROFINET uses EtherType `0x8892`, and its devices are found with the *Discovery and Configuration Protocol* (Wireshark: `pn_dcp`). For BACnet, nmap has a `bacnet-info` script. IEC 60870-5-104 carries telecontrol between control centres and substations.

</details>

## What they have in common

Look back at question 4. Almost every protocol here was designed for a closed network of trusted devices, so they share these weaknesses:

- **No authentication by default.** Anyone who can reach the port can read and, usually, write. This is the same problem you know from [Modbus TCP](/theory/modbus).
- **No encryption.** Values and commands travel as plain bytes that anyone on the path can read or change.
- **Built-in discovery.** Broadcast identity queries hand an attacker a list of devices, vendors and firmware versions.
- **Powerful maintenance commands.** Restart, stop, write program, change configuration.
- **Security add-ons that are rarely switched on.** DNP3 Secure Authentication, CIP Security, BACnet Secure Connect and IEC 62351 for the power protocols exist, but old devices often cannot run them, and plants replace devices only every few decades.

## In CybICS: four protocols on one PLC

The OpenPLC runtime at `172.18.0.3` does not only speak Modbus. It runs four industrial servers, all published by the Docker setup:

| Port | Protocol | What OpenPLC implements |
|---|---|---|
| 502/tcp | Modbus TCP | The full register and coil map you know |
| 102/tcp | S7comm | A Siemens-style server (see [S7comm](/theory/s7comm)) |
| 20000/tcp | DNP3 | An outstation built on the OpenDNP3 library, DNP3 address 10, expecting master address 1 |
| 44818/tcp | EtherNet/IP | Session registration and Allen-Bradley PCCC messages carried inside it, a small subset of the full standard |

All of them map onto the same PLC memory. Blocking port 502 therefore does not protect the HPT pressure value: the same memory is reachable through the next port along. The *DNP3 side door* challenge stops the plant through port 20000.

OpenPLC also starts a management **REST API** on 8443/tcp (HTTPS). It is not an industrial protocol, but it is one more door into the same controller that the plant never uses. The challenge *The forgotten API* walks through it.

**Spotting them with nmap.** A service scan of the PLC from the attack machine, as in the *Service scanning* challenge, shows lines like `20000/tcp open dnp?` and `44818/tcp open EtherNetIP-2?`. The question mark means nmap is guessing from the port number, because it could not confirm the protocol from the reply. That is normal for industrial services.

**Spotting them in Wireshark.** Capture on the attack machine while you connect to port 20000 or 44818, then apply the filter `dnp3` or `enip`. Wireshark decodes the traffic only if it really is that protocol, the confirmation nmap could not give.

<div class="callout cybics" markdown="1">
**Defender's view:** the CybICS IDS has rules for Modbus, S7comm, OPC-UA and web logins, but none that look inside DNP3 or EtherNet/IP. A scan still trips the port-scan rule, but a single well-formed DNP3 command would pass unremarked. Every protocol your monitoring cannot read is a blind spot.
</div>

<div data-widget="checkpoint" data-id="question-mark"></div>

A port number, a typical industry, a header or a byte pattern can each tell you which protocol you are looking at. Match each clue below to its protocol.

<div data-widget="sequence" data-id="match"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: DNP3 layers and why PROFINET hides from scanners</summary>

DNP3 has its own three layers inside the TCP payload. The **link layer** frame starts with `05 64`, then a length, a control byte and the destination and source DNP3 addresses, protected by a CRC every 16 bytes. The **transport function** splits long messages into fragments. The **application layer** carries a function code (for example `0x01` read, `0x05` direct operate, `0x0D` cold restart) followed by object headers that name the point group and variation. Because of the CRCs, a hand-built DNP3 frame with a single wrong byte is silently dropped, which makes fuzzing it more work than fuzzing Modbus.

PROFINET real-time frames sit directly on Ethernet with EtherType `0x8892`. There is no IP header, so routers do not forward them and tools like nmap, which work on IP, never see them. Discovery uses *DCP Identify* multicast frames on the local segment. To inventory PROFINET devices you must be on the same Layer 2 segment and listen, or send DCP yourself, which brings back the risks of active scanning discussed in [Asset inventory, risk and IEC 62443](/theory/risk-assessment).

</details>
