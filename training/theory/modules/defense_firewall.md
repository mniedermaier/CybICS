# Host firewalling

In this challenge you put a firewall on the PLC itself, so that only the systems that really need Modbus can reach it. Modbus TCP has no password at all: anyone who can reach port 502 can read and write. After this module, the Flood & Overwrite attacks from the attack machine never get an answer.

## The idea

Think of a guest list at a club door. The bouncer checks each arrival against the list from top to bottom and acts on the first line that matches: "Alice: let in", "Bob: let in", "everyone else: turn away". Nobody is asked for a password; what counts is who you are and whether you are on the list.

A **host firewall** is that bouncer, running on the device it protects. On Linux the classic tool is `iptables`. Incoming packets pass through a list of rules called the `INPUT` **chain**, and each rule says which packets it matches (protocol, port, source address) and what to do with them: `ACCEPT`, `DROP` (silently discard) or `REJECT` (discard and tell the sender).

<div class="callout analogy" markdown="1">
**Order matters:** the first matching rule wins. If "everyone else: turn away" stands at the top of the list, Alice is turned away too, even though she is listed further down.
</div>

<figure>
<svg viewBox="0 0 520 140" role="img" aria-label="The HMI's Modbus traffic passes the firewall in front of the PLC's port 502, while traffic from the attacker is stopped at the firewall.">
  <defs><marker id="dfw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="currentColor"/></marker></defs>
  <rect x="20" y="20" width="110" height="36" rx="6" fill="none" stroke="currentColor" stroke-width="2"/>
  <rect x="20" y="84" width="110" height="36" rx="6" fill="none" stroke="#ff6b00" stroke-width="2" stroke-dasharray="5 3"/>
  <rect x="240" y="40" width="40" height="60" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-width="2"/>
  <rect x="380" y="50" width="120" height="40" rx="6" fill="none" stroke="currentColor" stroke-width="2"/>
  <g font-size="13" text-anchor="middle" fill="currentColor">
    <text x="75" y="43">HMI: accept</text>
    <text x="75" y="107">attacker: drop</text>
    <text x="260" y="75" font-weight="bold">FW</text>
    <text x="440" y="75">PLC :502</text>
  </g>
  <line x1="130" y1="38" x2="238" y2="58" stroke="currentColor" stroke-width="2"/>
  <line x1="280" y1="66" x2="376" y2="68" stroke="currentColor" stroke-width="2" marker-end="url(#dfw)"/>
  <line x1="130" y1="102" x2="226" y2="86" stroke="#ff6b00" stroke-width="2"/>
  <path d="M222 78 l10 10 M232 78 l-10 10" stroke="#ff6b00" stroke-width="3"/>
</svg>
<figcaption>A rule list on the PLC accepts Modbus from the HMI and drops it from the attacker, so only the traffic the process needs gets through.</figcaption>
</figure>

## How it looks on CybICS

OpenPLC runs at `172.18.0.3` and listens for Modbus TCP on port 502. Before you write a single rule, list everyone who legitimately talks Modbus to it:

| Host | Address | Why it needs port 502 |
|---|---|---|
| `hwio` | `172.18.0.2` | writes the simulated sensor values into the PLC |
| `fuxa` | `172.18.0.4` | the HMI reads values and sends operator commands |
| `opcua` | `172.18.0.5` | reads the plant values to publish them over OPC-UA |

Everything else, including the attack machine at `172.18.0.100`, has no business on port 502. You work inside the OpenPLC container with `docker exec`, which reaches the container without going over the network, so a wrong rule cannot lock you out.

When you press **Verify Defense**, the check looks for a `DROP` or `REJECT` rule on the container and then tries to connect to port 502 from the CybICS host itself and from the attack machine. Neither is on your list, so both connections have to fail. It also connects from inside `hwio`, `fuxa` and `opcua`: those three must still get through.

One side effect: the live plant views in these lessons also read the PLC from the CybICS host (`172.18.0.1`). Once your firewall is in place they show "plant not reachable". That is the firewall working, and a good reminder to list every reader before you block port 502 in a real plant.

## How to approach it

Try the order of rules here first. Move the rules around and watch which CybICS connections pass:

<div data-widget="firewall-rules"></div>

1. **Write the allow list.** One `ACCEPT` rule for port 502 per legitimate source from the table.
2. **Add the catch-all.** A final rule that drops all other traffic to port 502.
3. **Check the order.** `iptables -L INPUT -n --line-numbers` shows the chain as the kernel reads it, top to bottom.
4. **Check the plant.** Open the HMI and confirm the values still update. A firewall that stops the process is an outage, not a defense.
5. **Verify** in the challenge page.

<div data-widget="checkpoint" data-id="order"></div>

<div class="callout tip" markdown="1">
**Tip:** These rules live only in memory and disappear when the container restarts. On a real device you save them with `iptables-save` and load them at boot.
</div>

## Detect and defend

The firewall is the defense here; detection confirms it works.

- **Watch the drops.** Run a Modbus write from the attack machine. It should hang until it times out. Counters in `iptables -L -v` show how many packets each rule matched.
- **Mind the other doors.** OpenPLC also serves S7comm on port 102, DNP3 on 20000 and EtherNet/IP on 44818. A rule for 502 leaves those open, which the [S7 Side Door](/ctf/challenge/s7_sidedoor) challenge exploits; the next module, [Network segmentation](/theory/defense_network), closes the gap per host.
- **Remember what remains.** If the HMI itself is taken over, the attacker inherits its place on the allow list. That is why firewalls are combined with monitoring, as described in [Defence in depth](/theory/defense-hardening).

The attacks this blocks include Unauthorized Message: Command Message (T1692.001) and Brute Force I/O (T0806) from MITRE ATT&CK for ICS. NIST SP 800-82 calls the measure Boundary Protection (SC-7); D3FEND calls it Inbound Traffic Filtering (D3-ITF).

## Before you start

- [Modbus TCP](/theory/modbus): why port 502 has no authentication
- [Defence in depth](/theory/defense-hardening): firewalls as one layer among several
- [Flood & Overwrite](/theory/flood_overwrite): the attack this rule set stops
