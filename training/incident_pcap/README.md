# Incident PCAP

> **MITRE ATT&CK for ICS (reconstructed):** `Discovery` | [T0846 - Remote System Discovery](https://attack.mitre.org/techniques/T0846/) | [T0846.001 - Port Scan](https://attack.mitre.org/techniques/T0846/001/) | `Collection` | [T0830 - Adversary-in-the-Middle](https://attack.mitre.org/techniques/T0830/) | `Evasion` `Impair Process Control` | [T1692.001 - Unauthorized Message: Command Message](https://attack.mitre.org/techniques/T1692/001/) | `Impact` | [T0831 - Manipulation of Control](https://attack.mitre.org/techniques/T0831/) | [T0826 - Loss of Availability](https://attack.mitre.org/techniques/T0826/)
>
> **MITRE D3FEND:** [D3-NTA - Network Traffic Analysis](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | [D3-PMAD - Protocol Metadata Anomaly Detection](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | [D3-APCA - Application Protocol Command Analysis](https://d3fend.mitre.org/technique/d3f:ApplicationProtocolCommandAnalysis/)

## Overview
On a Saturday night the gas plant stopped three times within two minutes.
Each time the operator switched the plant back on with the HMI's STOP /
SHUTDOWN toggle and the plant came back, and
each time it stopped again. Only two hosts are supposed to write to the PLC:
the HMI and the engineering workstation. The operator did not press STOP,
and nobody was at the workstation.

Luckily the PLC's switch port is mirrored to a capture box. You get its
recording, **`incident.pcap`**: two minutes of everything sent to or from
the PLC, plus the broadcasts every port sees. There is no live stack to
poke at, no IDS alert and no log. Just frames.

Your goal is to **rebuild the incident from the capture**: find the device
behind it, every address it used or wore, the moment it started to lie
about who it is, and the three requests that stopped the plant.

This is an offline forensics challenge. It needs nothing from the running
plant and works the same in a classroom without the testbed.

## Background

### Who is who on the plant network

| Host | IP address | MAC address in the capture |
|------|-----------|----------------------------|
| OpenPLC (the PLC, where the capture was taken) | 172.18.0.3 | `02:42:ac:12:00:03` |
| FUXA (the HMI) | 172.18.0.4 | `02:42:ac:12:00:04` |
| Engineering workstation | 172.18.0.10 | `02:42:ac:12:00:0a` |

These MAC addresses are the ones in the capture; the containers of your own
stack have other, random ones.

The I/O service at 172.18.0.2 talks to the PLC about fifty times a second;
the capture box filtered it out (`not host 172.18.0.2`) to keep the file
small. Everything else that reached the PLC's port is in the file.

### Two identities: the IP address and the MAC address

Every frame on an Ethernet network carries two "from" fields:

- the **source MAC address** in the Ethernet header: the network card that
  put the frame on the wire. The switch learns it and forwards by it.
- the **source IP address** in the IP header: the address the sender
  *claims* to have. Nothing checks it. Any host on the segment can write any
  IP address into its packets.

Most tools show you the IP address, because that is what routing and
firewalls use. An attacker on the same network segment can borrow another
host's IP address. Borrowing its network card is much harder, so the source
MAC address of a frame is the better witness for *which device* sent it.
(A MAC address can be changed in software too; what matters here is that the
attacker kept one MAC for everything it did, so it ties all its actions together.)

### ARP and how it is poisoned

Before a host sends an IP packet to a neighbour it needs the neighbour's MAC
address. It asks with an **ARP request** ("who has 172.18.0.4? tell
172.18.0.3"), broadcast to everyone, and the owner answers with an **ARP
reply** ("172.18.0.4 is at 02:42:ac:12:00:04"). The answer is kept in the
**ARP cache** for a while.

ARP has no authentication, and most systems accept a reply they never asked
for. A host that sends the PLC "172.18.0.4 is at *my* MAC" makes the PLC
deliver everything meant for the HMI to that host instead. That is **ARP
poisoning**, the usual first step of an adversary-in-the-middle attack (see
the [MitM challenge](../mitm/README.md)). It also lets the attacker send
packets *from* the HMI's IP address and still receive the PLC's answers,
which a TCP connection needs.

Wireshark notices when two MAC addresses claim the same IP address and marks
the frame with *Duplicate IP address configured*.

### What a stop looks like on each door

The stop flag is one word in the PLC's memory, `%MW104` (0 = run, anything
else = stop). The PLC offers it through several protocols, as the
[S7 Side Door](../s7_sidedoor/README.md) and
[DNP3 Side Door](../dnp3_sidedoor/README.md) challenges show:

| Door | Port | Write of the stop flag |
|------|------|------------------------|
| Modbus TCP | 502 | function 6 (Write Single Register), register **1128**, value 1 |
| S7comm | 102 | *Write Var* to **DB1002**, byte address **208**, two bytes `00 01` |
| DNP3 | 20000 | *Direct Operate* on an Analog Output (object 41), index **1128**, value 1 |

When the operator toggles the HMI's STOP / SHUTDOWN button off, FUXA writes
0 to the same flag. A write of 0 restarts
the plant; it is not a stop.

## Where to run it

You need the file and a tool that reads captures.

- **Wireshark** is the easiest: on the Kali attack machine (`--mode full`),
  open `/CybICS/training/incident_pcap/incident.pcap`, or download the file
  on your own computer from the challenge page:
  [incident.pcap](/ctf/challenge/incident_pcap/incident.pcap)
  (in the repository it is `training/incident_pcap/incident.pcap`).
- **The attack shell** has no Wireshark, but `tcpdump` reads the file at
  `/CybICS/training/incident_pcap/incident.pcap`. It shows MAC addresses with
  `-e` and frame numbers with `-#`. It does not decode S7comm or DNP3, so you
  read those bytes yourself with `-X`. Python with scapy is there too.

**Frame numbers** are the position of a frame in the file, starting at 1,
exactly as Wireshark's *No.* column shows them. `tcpdump -#` numbers only the
frames that match its filter, so with tcpdump always read the whole file and
filter the output with `grep` instead.

## Task

Answer four questions on the challenge page:

1. The **MAC address** of the rogue device.
2. **Every IP address** the rogue device used for itself or impersonated.
3. The **number of the first frame** in which the rogue device claims an IP
   address that belongs to another host.
4. The **frame numbers of the three requests that stopped the plant**: the
   requests, not the PLC's replies.

All four answers are graded together.

### Steps

1. **Get an overview.** In Wireshark, *Statistics > Endpoints*, tab
   *Ethernet*, lists every MAC address in the file. *Statistics >
   Conversations* shows who talked to whom over which port. One MAC address
   does not belong to any host in the table above. Its vendor prefix may tell
   you what kind of device it is.

2. **Follow that MAC.** Filter on it:

   ```
   eth.addr == <the MAC>
   ```

   Read the frames in order. How does the device find out which addresses are
   free and who is on the network? What does it do next to the PLC itself?
   Which IP address does it use for that? With tcpdump:

   ```bash
   tcpdump -# -nn -e -r /CybICS/training/incident_pcap/incident.pcap | grep -i '<the MAC>' | head -60
   ```

3. **Look for lies in ARP.** Show only ARP replies and read who claims to be
   whom:

   ```
   arp.opcode == 2
   ```

   Compare the MAC in each reply with the table above. Wireshark's expert
   information (*Analyze > Expert Information*, or the filter
   `arp.duplicate-address-detected`) points at the conflicts. Note the first
   frame in which the rogue device claims somebody else's address, and which
   addresses it claims.

4. **Find every write to the stop flag.** Start with Modbus:

   ```
   modbus.func_code == 6 && modbus.reference_num == 1128
   ```

   Add the columns *Source MAC* (`eth.src`), *Source port* and the register
   value (`modbus.regval_uint16`). Which writes set the flag, which clear it,
   and which network card sent each one? Two frames from the same IP address
   can come from two different devices.

5. **Check the side doors.** Filter on `s7comm` and on `dnp3`. For each
   request, decide from the table in the background whether it writes the
   stop flag, and from `eth.src` which device sent it. A request from the
   engineering workstation's IP address is not necessarily from the
   engineering workstation.

6. **Cross-check with the plant.** FUXA reads registers 1124-1134 once a
   second (function 3). In the PLC's answers the fifth value is the stop
   flag. It turns 1 right after each real stop and back to 0 after each restart,
   which confirms your three frames. While the ARP cache is poisoned, look
   at the *destination* MAC of those answers too: whose card receives what
   the PLC sends to the HMI?

7. **Answer** the four questions on the challenge page and press *Verify*.

## Detect and Defend

### Detection
- **Watch IP-to-MAC bindings.** An IP address that suddenly answers from a
  new MAC, or two MACs that claim one address, is the signature of ARP
  poisoning. The CybICS IDS has an `arp_spoof` rule for it; `arpwatch` and
  most OT monitoring products do the same.
- **Know your devices.** A plant network has a short, stable list of MAC
  addresses. A new vendor prefix on it (here: a hobbyist computer next to
  industrial controllers) deserves an alert by itself.
- **Inspect commands, not only connections.** Every stop in this capture is
  a single, valid request. A rule that alerts on writes to the stop flag, on
  any protocol, catches all three; a rule on Modbus alone misses two.
- **Keep captures.** A mirror port with a ring buffer costs little and is
  often the only evidence after an incident, because PLCs keep almost no logs.

### Defense
- **Lock the bindings.** Static ARP entries on the PLC for the HMI and the
  workstation, or *Dynamic ARP Inspection* and port security on the switch,
  stop the poisoning.
- **Control which ports may connect.** 802.1X or MAC-based port security
  keeps an unknown device from joining the plant network at all.
- **Close the unused doors.** S7comm and DNP3 are not used by this plant
  (see [Close the Side Doors](../defense_unused_protocols/README.md)).
- **Do not trust the source address.** An allowlist by IP address (see
  [Trusted Writer](../fuxa_trusted_writer/README.md)) is only as good as the
  layer below it. Authenticated protocols, such as OPC UA with signed
  messages, do not have this weakness.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques you reconstruct

| Tactic | Technique | ID | In the capture |
|--------|-----------|-----|----------------|
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | ARP sweep of the plant subnet |
| Discovery | Remote System Discovery: Port Scan | [T0846.001](https://attack.mitre.org/techniques/T0846/001/) | Half-open TCP scan of the PLC |
| Collection | Adversary-in-the-Middle | [T0830](https://attack.mitre.org/techniques/T0830/) | ARP poisoning of the PLC for the HMI and the workstation |
| Evasion, Impair Process Control | Unauthorized Message: Command Message | [T1692.001](https://attack.mitre.org/techniques/T1692/001/) | Stop commands over Modbus, S7comm and DNP3 |
| Impact | Manipulation of Control | [T0831](https://attack.mitre.org/techniques/T0831/) | Setting the stop flag |
| Impact | Loss of Availability | [T0826](https://attack.mitre.org/techniques/T0826/) | The plant stops three times |

### MITRE D3FEND - Defensive techniques you apply

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Reading the capture to find unauthorized activity |
| Protocol Metadata Anomaly Detection | [D3-PMAD](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | IP-to-MAC conflicts and an unknown vendor prefix |
| Application Protocol Command Analysis | [D3-APCA](https://d3fend.mitre.org/technique/d3f:ApplicationProtocolCommandAnalysis/) | Recognising the stop command in three protocols |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Incident Response (IR)** | IR-4, IR-5 | Handling and tracking the incident from the evidence |
| **Audit and Accountability (AU)** | AU-6 | Reviewing and analysing recorded network activity |
| **System and Communications Protection (SC)** | SC-7, SC-23 | Boundary protection and session authenticity |
| **Identification and Authentication (IA)** | IA-3 | Device identification before a device may join the network |

</details>

## Hints

<details>
  <summary>💡 Hint 1</summary>

The vendor part of a MAC address (the first three bytes) belongs to a
manufacturer. Wireshark shows it resolved, for example `RaspberryPiF_...`. The
plant's hosts in this capture all start with `02:42`.

</details>

<details>
  <summary>💡 Hint 2</summary>

There are more writes to register 1128 than stops. Look at the value and at
`eth.src` of each one.

</details>

<details>
  <summary>💡 Hint 3</summary>

The S7comm stop is a *Write Var* job, the DNP3 stop a *Direct Operate*
request. The workstation also talks S7comm in the capture, before anything
unusual happens. Is it reading or writing?

</details>

## Solution

<details>
  <summary>Click to expand</summary>

In Wireshark:

1. *Statistics > Endpoints > Ethernet* shows `b8:27:eb:3c:9a:71`
   (`RaspberryPiF_3c:9a:71`, a Raspberry Pi), which is no plant host.
2. `eth.addr == b8:27:eb:3c:9a:71`: an ARP probe for 172.18.0.77, an ARP
   sweep of 172.18.0.1-30 and a SYN scan of the PLC, all from
   **172.18.0.77**.
3. `arp.opcode == 2`: frame **293** is the first reply from the Pi that says
   "172.18.0.4 is at b8:27:eb:3c:9a:71"; frame 294 does the same for
   172.18.0.10. Both repeat every four seconds, and Wireshark flags them as
   duplicate IP addresses (FUXA answered for 172.18.0.4 from its own MAC in
   frame 20, the workstation announced itself in frame 45).
4. `modbus.func_code == 6 && modbus.reference_num == 1128` shows four
   requests. Frame **345** writes 1, from 172.18.0.4 but from the Pi's MAC,
   on a new connection (port 51514). Frames 469, 672 and 840 write 0 from
   FUXA's real MAC on its polling connection: the operator's restarts.
5. `s7comm`: the workstation reads DB1002 in frame 56 (before the
   poisoning, from its own MAC). Frame **553** is a *Write Var* to DB1002
   byte 208 with data `00 01`, from 172.18.0.10 but from the Pi's MAC.
   `dnp3`: frame **736** is a *Direct Operate* on object 41 index 1128 with
   value 1, from 172.18.0.77.
6. FUXA's polls show the stop flag 1 after frames 345, 553 and 736 and 0
   after each restart.

Answers: MAC `b8:27:eb:3c:9a:71`; IP addresses `172.18.0.77, 172.18.0.4,
172.18.0.10`; first poisoning frame `293`; stop frames `345, 553, 736`.

The same with tcpdump in the attack shell:

```bash
F=/CybICS/training/incident_pcap/incident.pcap
tcpdump -# -nn -e -r $F | grep 'Reply' | grep -v '02:42:ac:12:00:0[34a] > ' | head -3
tcpdump -# -nn -e -r $F | grep -E 'b8:27:eb:3c:9a:71 > .*(\.502|\.102|\.20000): Flags \[P'
tcpdump -# -nn -e -X -r $F 'tcp' | less    # read the payload bytes of those frames
```

</details>

## For maintainers: regenerating the capture

`incident.pcap` is generated, never edited by hand:

```bash
python3 software/scripts/generate_incident_pcap.py          # rewrite the file
python3 software/scripts/generate_incident_pcap.py --key    # print the answers
```

The generator is deterministic. If you change the story, update the expected
values in `software/landing/modules/defense_checks/check_incident_pcap.py`
and the Solution above; `tests/test_incident_pcap.py` fails until they match.
