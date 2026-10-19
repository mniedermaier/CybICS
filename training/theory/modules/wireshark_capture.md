# Capturing Modbus traffic

In this challenge you record the network traffic of the CybICS plant and read data straight out of it. Modbus TCP sends everything in plain text, so anyone with the right position on the network can read every value the plant's devices exchange. You will learn to capture, filter and decode that traffic with Wireshark.

## The idea

Most traffic on the internet today is encrypted: if you intercept it, you see scrambled bytes. Industrial protocols such as Modbus TCP are older and were designed for closed networks. They send their messages as readable **plaintext**, like a postcard rather than a sealed letter. Everyone who handles the postcard can read it.

A **packet capture** records every message, called a packet, that passes a network interface. Wireshark is the standard tool to record and inspect captures; `tshark` and `tcpdump` do the same on the command line. Wireshark knows Modbus, so it splits each packet into its fields and shows you the function code, the register address and the values.

MITRE ATT&CK for ICS calls this *Network Sniffing* (T0842). It is completely passive: the attacker sends nothing, so the devices and most detection systems never notice.

## How it looks on CybICS

Several programs talk Modbus to OpenPLC (172.18.0.3, port 502) all the time. The busiest is the `hwio` container (172.18.0.2), which simulates the plant: it writes the sensor values many times a second and reads back the actuator coils. The others only read: the FUXA HMI, the OPC-UA server and, while you have a lesson with a live plant view open, this landing page.

<details class="deep-dive" markdown="1">
<summary>Deep dive: who talks to the PLC, and how often</summary>

<figure class="wide">
<svg viewBox="0 0 520 150" role="img" aria-label="The hwio container sends Modbus write requests to OpenPLC on port 502. A capture point on the network path copies every packet to Wireshark, which shows the function code, the start register and the register values in plain text.">
  <g font-size="12" text-anchor="middle">
    <rect x="20" y="30" width="110" height="40" rx="6" fill="#ff6b00"/><text x="75" y="48" style="fill:#1a1a1a" font-weight="bold">hwio</text><text x="75" y="63" font-size="11" style="fill:#1a1a1a">172.18.0.2</text>
    <rect x="390" y="30" width="110" height="40" rx="6" fill="#ff6b00"/><text x="445" y="48" style="fill:#1a1a1a" font-weight="bold">OpenPLC</text><text x="445" y="63" font-size="11" style="fill:#1a1a1a">172.18.0.3:502</text>
    <line x1="130" y1="50" x2="390" y2="50" stroke="currentColor" stroke-width="2"/>
    <text x="260" y="40" font-size="11">write registers: function code, address, values</text>
    <line x1="260" y1="50" x2="260" y2="100" stroke="#ff6b00" stroke-width="2" stroke-dasharray="4 3"/>
    <rect x="195" y="100" width="130" height="32" rx="5" fill="currentColor" fill-opacity="0.15" stroke="#ff6b00"/>
    <text x="260" y="121">Wireshark</text>
  </g>
  <text x="20" y="146" font-size="11" opacity="0.85">Nothing in the packet is encrypted. Whoever sees it can read it.</text>
</svg>
<figcaption>Modbus requests carry the function code, the register address and the values in readable form. A capture point anywhere on the path sees all of it.</figcaption>
</figure>

- **hwio** (172.18.0.2) writes the pressures and sensor values about every 20 milliseconds and reads the coils that switch the compressor and the valves.
- **FUXA** (172.18.0.4), the HMI, reads the values it displays once a second.
- **The OPC-UA server** (172.18.0.5) reads six registers every two seconds and offers them to OPC-UA clients.
- **The landing page** reads the plant registers once a second, but only while a lesson with a live plant widget is open. It runs on the host, so its packets come from 172.18.0.1, the host's address on the container network.

</details>

Here is what one of those writes looks like on the wire. Change the fields and watch the bytes change:

<div data-widget="modbus-frame" data-fc="6" data-address="1126" data-value="75"></div>

Register values are just 16-bit numbers. A program can put anything into them, including text: each register then holds two characters, one per byte. The decoder shows how that works with a harmless example:

<div data-widget="register-decoder" data-values="18533,27756,28416"></div>

Where you capture matters. A network switch forwards each packet only to its destination, so a random machine on the same network does not see other machines' conversations. You need a position on the path. On CybICS there are three:

- **The landing page's network analyzer** (Sharky, at `/network`) runs on the host and sees the container network. It can export a capture file for Wireshark.
- **The host itself.** On the board, the README shows how to run `tcpdump` on the `br-cybics` bridge over SSH and pipe it into Wireshark.
- **A man in the middle**, which redirects traffic through your machine. That is a separate challenge: [Man in the middle](/theory/mitm).

## How to approach it

1. Start a capture from one of the positions above and let it run for 30 to 60 seconds. The plant talks constantly, so you will get plenty.
2. Open the capture in Wireshark. You will see thousands of packets, most of them between `hwio` and OpenPLC.
3. Narrow it down with a display filter. `modbus` shows only Modbus; a filter on `modbus.func_code` shows one kind of request. Think about which function codes *write* data.
4. Learn what normal looks like: who talks to whom, how often, and which registers they use. Whatever you cannot explain deserves a closer look.
5. Remember that a register is only a number until you know how to read it. The decoder above shows one way to read it.

<div data-widget="checkpoint" data-id="filter"></div>

<div class="callout tip" markdown="1">
**Tip:** In Wireshark, right-click a field in the packet details and choose *Apply as Filter*. That builds the filter expression for you.
</div>

## Detect and defend

Passive sniffing is almost impossible to detect, because the attacker sends nothing. The CybICS IDS has no rule for it, and neither do most others. Defenders therefore focus on the position the attacker needs, and on what the traffic reveals:

- **Protect capture positions.** Mirror ports on switches, the host of a container network and network taps are as sensitive as the PLC itself.
- **Watch for redirection.** Getting onto the path often needs ARP spoofing, which is detectable. The CybICS IDS has a rule for it.
- **Encrypt where possible.** Modbus/TCP Security wraps Modbus in TLS on port 802. Where devices cannot do that, a VPN tunnel between network zones protects the traffic in transit.
- **Segment the network** so that only the devices that need the traffic can reach it. See [Network segmentation](/theory/defense_network).
- **Keep secrets out of process data.** Anything written into a register can be read by everyone on the path.

## Before you start

- [Modbus TCP](/theory/modbus) for the frame, the function codes and the registers.

Later on the path:

- [The ICS attack lifecycle](/theory/attack-lifecycle) for where collection fits.
