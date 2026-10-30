# Reading an incident capture

In this challenge the attack is already over. The plant stopped three times in one night, and all you have is a recording of the network traffic at the PLC. You work out which device did it, which addresses it hid behind and exactly which messages stopped the plant. This is what an incident responder does after the alarm: turn a pile of packets into a timeline that others can act on.

## The idea

Think of a building where every letter is stamped with the sender's name, but anyone can write any name on the envelope. The post room also notes which mailbox slot each letter came through, and nobody can fake that. If letters "from the manager" arrive through the slot in the basement, you know who really sent them.

A network works the same way. Every frame on an Ethernet network carries two "from" fields:

- The **IP address** (Internet Protocol address) is the name on the envelope. The sender writes it, and nothing checks it.
- The **MAC address** (Media Access Control address) belongs to the network card that sent the frame. The switch learns it and forwards by it.

An attacker on the same network segment can claim another host's IP address. Its own card still sends the frames, so its MAC address follows it from one disguise to the next. The MAC can be changed too, but an attacker rarely changes it for every step, and that is what ties the steps together.

<figure>
<svg viewBox="0 0 520 170" role="img" aria-label="Two frames that both say they come from 172.18.0.4. The upper one carries the HMI's MAC address 02:42:ac:12:00:04 and writes 0 to the stop flag. The lower one carries a different MAC address, b8:27:eb..., and writes 1. The IP address is the same; the MAC address shows two different senders.">
  <g fill="none" stroke="currentColor" stroke-opacity="0.6">
    <rect x="10" y="20" width="500" height="54" rx="6"/>
    <rect x="10" y="96" width="500" height="54" rx="6"/>
    <path d="M190 20 V74 M350 20 V74 M190 96 V150 M350 96 V150"/>
  </g>
  <g fill="currentColor" font-size="12" text-anchor="middle">
    <text x="100" y="42" opacity="0.7">Ethernet: from</text>
    <text x="100" y="62">02:42:ac:12:00:04</text>
    <text x="270" y="42" opacity="0.7">IP: from</text>
    <text x="270" y="62">172.18.0.4</text>
    <text x="430" y="42" opacity="0.7">Modbus</text>
    <text x="430" y="62">stop flag = 0</text>
    <text x="100" y="118" opacity="0.7">Ethernet: from</text>
    <text x="100" y="138" font-weight="bold">b8:27:eb:..</text>
    <text x="270" y="118" opacity="0.7">IP: from</text>
    <text x="270" y="138">172.18.0.4</text>
    <text x="430" y="118" opacity="0.7">Modbus</text>
    <text x="430" y="138">stop flag = 1</text>
  </g>
</svg>
<figcaption>Same IP address, different network cards. Only the Ethernet layer shows that two devices are talking.</figcaption>
</figure>

## How it looks on CybICS

The capture comes from a **mirror port**: the switch copies every frame to and from the PLC (OpenPLC, `172.18.0.3`) to a recorder. You see the HMI (FUXA, `172.18.0.4`) polling the PLC once a second, the engineering workstation (`172.18.0.10`) reading values, and broadcasts that every port receives. The I/O service was filtered out to keep the file small.

Three kinds of evidence matter here:

- **ARP** (Address Resolution Protocol) frames, which say "this IP address is at this MAC address". A host that lies in them can make the PLC send another host's traffic to itself. That is ARP poisoning, which the Man in the middle lesson explains.
- **Commands to the PLC** over three protocols. The stop flag can be written over Modbus, over S7comm and over DNP3, and each looks different on the wire.
- **The PLC's answers.** The HMI reads the stop flag every second, so the answers show when the plant really stopped and when it ran again.

<div data-widget="checkpoint" data-id="witness"></div>

## How to approach it

Incident analysis is a loop: get an overview, form a question, filter, write down what you found, repeat.

1. **Overview first.** Wireshark's statistics list every MAC address and every conversation. Compare them with the hosts you know. Anything that does not belong is your first lead.
2. **Follow one identity.** Filter on the unknown MAC address and read its frames in time order. What does it do to learn the network? Which IP address does it use for that?
3. **Look for contradictions.** Two MAC addresses claiming the same IP address is never normal on a plant network. Note where the contradiction starts.
4. **Find the effect, then the cause.** Find every write to the stop flag, on every protocol. For each one, ask which card sent it and what value it wrote. Writes from the operator look the same at the IP layer.
5. **Confirm.** Every claim in your timeline should be backed by a frame number, so that someone else can check it.

Put an incident like this one in order and name the ATT&CK tactic of each step:

<div data-widget="sequence" data-id="incident"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: why the attacker needs ARP poisoning at all</summary>

Writing a false source address into one packet is easy. A TCP connection, which Modbus, S7comm and DNP3 all use here, needs more: the PLC answers the first packet, and the sender must see that answer to continue. The PLC sends the answer to whichever MAC address its ARP cache holds for that IP address. By poisoning the cache first, the attacker makes the PLC deliver the answers to its own card, so the forged connection works in both directions. It also receives everything else the PLC sends to the real host, which is why the poisoned host's normal traffic changes too.

</details>

## Detect and defend

- **Watch IP-to-MAC bindings.** An IP address that moves to a new MAC, or two MACs claiming one IP address, is what an ARP spoofing alert looks for. The CybICS IDS has such a rule.
- **Know your devices.** A plant network has a short, stable list of devices. A new vendor prefix in a MAC address is worth an alert by itself.
- **Inspect the command, not only the connection.** A rule that alerts on any write to the stop flag, on every protocol, catches what a Modbus-only rule misses.
- **Fix it at the switch.** Static ARP entries, Dynamic ARP Inspection and port security stop the poisoning; 802.1X keeps unknown devices off the network.
- **Keep recordings.** PLCs keep almost no logs. A mirror port with a ring buffer is often the only evidence after an incident.

<div class="callout cybics" markdown="1">
**In CybICS:** the IDS Forensics challenge reads alerts that a rule engine already summarised. This one starts one step earlier, from the raw frames, where nothing has been decided for you.
</div>

## Before you start

- [Network basics](/theory/networking)
- [Man in the middle](/theory/mitm)
- [IDS forensics](/theory/ids_forensics)
- [Incident response in OT](/theory/incident-response)

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The capture is generated by `software/scripts/generate_incident_pcap.py` and
is deterministic; the answers are graded on the board, never in the page. The
S7comm and DNP3 bytes were captured from the stack's own clients, so they
dissect like live traffic in Wireshark 4.x. The attack shell has tcpdump but
no tshark: `tcpdump -#` numbers only the frames that match its filter, so
students must number the whole file and grep. The Kali attack machine mounts
the repository at `/CybICS`, so the file is there without a rebuild.

</details>
