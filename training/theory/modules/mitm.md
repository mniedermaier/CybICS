# Man in the middle

In this challenge you place your attack machine between the FUXA HMI and the PLC, so that their conversation passes through you. On an industrial network the prize is rarely secret data. The dangerous move is to **lie in one direction**: let the operator's commands through untouched, and rewrite the readings on their way back, so the screen says everything is fine while the plant does something else.

## The idea

Picture a letter carrier who opens every envelope between two offices, reads it, and sometimes rewrites a line before sealing it again. Neither office notices, because each one still gets a letter that looks right. That carrier is a **man in the middle (MitM)**, which MITRE now calls an adversary in the middle.

To become that carrier on a local network you exploit **ARP**, the Address Resolution Protocol. Computers on the same network segment talk to each other by hardware address (the **MAC address**), so each host keeps an **ARP cache**: a small table that says "IP address 172.18.0.3 belongs to MAC address d6:10:...".

ARP has no proof of identity. When a host hears "172.18.0.3 is at my MAC", it simply believes the last message it heard. Sending such false messages is called **ARP spoofing** or **ARP poisoning**. Poison both sides, and both send their traffic to you.

<div class="callout analogy" markdown="1">
**Analogy:** ARP is like a building where anyone may change the name plates on the mailboxes. Nobody checks who swapped them.
</div>

## How it looks on CybICS

FUXA (`172.18.0.4`) polls OpenPLC (`172.18.0.3`) once a second over Modbus TCP on port 502. Your attack machine is `172.18.0.100` on the same Docker network, so you can reach both.

The challenge folder contains `mitm.py`, a small Modbus **proxy**: a program that accepts FUXA's connection on port 5020, opens its own connection to the PLC, and relays every request and answer. In between, it can change bytes. Out of the box it is set up to forge the readings of GST, HPT, the system sensor and the manual-mode flag.

<figure class="wide">
<style>
.mm-q {--d: 14s; --on:#e06000; --onink:#1a1a1a;}
.mm-q .req  {animation: q-req var(--d) linear infinite;}
.mm-q .card {opacity:0; animation: q-card var(--d) steps(1,end) infinite;}
.mm-q .mt   {opacity:1; animation: q-mt var(--d) steps(1,end) infinite;}
.mm-q .rs1  {opacity:0; animation: q-rs1 var(--d) linear infinite;}
.mm-q .rs2  {opacity:0; animation: q-rs2 var(--d) linear infinite;}
.mm-q .scr  {opacity:0; animation: q-scr var(--d) steps(1,end) infinite;}
@keyframes q-req  {0%{transform:translateX(0); opacity:1}
                   36%{transform:translateX(236px); opacity:1}
                   40%,100%{transform:translateX(236px); opacity:0}}
@keyframes q-card {0%,10.6%{opacity:0} 10.7%,61.9%{opacity:1} 62%,100%{opacity:0}}
@keyframes q-mt   {0%,10.6%{opacity:1} 10.7%,61.9%{opacity:0} 62%,100%{opacity:1}}
@keyframes q-rs1  {0%,40%{transform:translateX(0); opacity:0}
                   42%{transform:translateX(0); opacity:1}
                   60%{transform:translateX(-102px); opacity:1}
                   62%,100%{transform:translateX(-102px); opacity:0}}
@keyframes q-rs2  {0%,60%{transform:translateX(0); opacity:0}
                   62%{transform:translateX(0); opacity:1}
                   80%,100%{transform:translateX(-160px); opacity:1}}
@keyframes q-scr  {0%,79.9%{opacity:0} 80%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .mm-q *{animation:none !important}
  .mm-q .req{opacity:1; transform:translateX(0)}
  .mm-q .rs1{opacity:1; transform:translateX(0)}
  .mm-q .rs2{opacity:1; transform:translateX(-160px)}
  .mm-q .card{opacity:1} .mm-q .mt{opacity:0}
  .mm-q .scr{opacity:1}
}
</style>
<svg class="mm-q" viewBox="0 0 460 274" role="img"
     aria-label="One FUXA poll crossing the attacker's proxy. The request, a read of eleven holding registers from 1124, is relayed to OpenPLC unchanged, but as it passes the proxy writes a note into its queue saying that GST will arrive in slot 0, HPT in slot 2, manual in slot 6 and the system sensor in slot 8. OpenPLC answers with the true values, GST 184 and HPT 58. The proxy uses the note to patch those slots to 200 and 95 and forwards the answer. The queue is empty again before the next poll.">
  <text x="14" y="20" font-size="12" font-weight="bold">one poll: relayed one way, rewritten the other</text>

  <rect x="14" y="84" width="92" height="44" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="60" y="104" text-anchor="middle" font-size="14" font-weight="bold">FUXA</text>
  <text x="60" y="120" text-anchor="middle" font-size="12" opacity="0.8">.0.4</text>
  <rect x="184" y="84" width="92" height="44" rx="6" fill="var(--on)"/>
  <text x="230" y="104" text-anchor="middle" font-size="14" style="fill:var(--onink)" font-weight="bold">proxy</text>
  <text x="230" y="120" text-anchor="middle" font-size="12" style="fill:var(--onink)">.0.100</text>
  <rect x="354" y="84" width="92" height="44" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="400" y="104" text-anchor="middle" font-size="14" font-weight="bold">OpenPLC</text>
  <text x="400" y="120" text-anchor="middle" font-size="12" opacity="0.8">.0.3</text>

  <text x="230" y="40" text-anchor="middle" font-size="12" opacity="0.8">request &mdash; relayed byte for byte</text>
  <g class="req">
    <rect x="110" y="46" width="100" height="22" rx="3" fill="none" stroke="var(--on)" stroke-width="1.5"/>
    <text x="160" y="61" text-anchor="middle" font-size="12" fill="var(--on)" font-weight="bold">read 1124 &times; 11</text>
  </g>

  <text x="230" y="150" text-anchor="middle" font-size="12" opacity="0.8">response &mdash; patched by slot, inside the proxy</text>
  <g class="rs1">
    <rect x="272" y="158" width="132" height="22" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="338" y="173" text-anchor="middle" font-size="11" font-family="monospace">1124=184 1126=58</text>
  </g>
  <g class="rs2">
    <rect x="170" y="158" width="132" height="22" rx="3" fill="var(--on)"/>
    <text x="236" y="173" text-anchor="middle" font-size="11" font-family="monospace" style="fill:var(--onink)" font-weight="bold">1124=200 1126=95</text>
  </g>

  <text x="14" y="200" font-size="11" opacity="0.85">the request pass notes where each target will sit in the coming answer</text>
  <rect x="140" y="206" width="180" height="46" rx="4" fill="currentColor" fill-opacity="0.10" stroke="currentColor" stroke-opacity="0.5"/>
  <g class="card" font-family="monospace" font-size="12" text-anchor="middle" font-weight="bold">
    <text x="230" y="224" fill="var(--on)">GST&rarr;0   HPT&rarr;2</text>
    <text x="230" y="242" fill="var(--on)">manual&rarr;6  sysSen&rarr;8</text>
  </g>
  <text class="mt" x="230" y="235" text-anchor="middle" font-size="12" opacity="0.72">queue empty</text>
  <text class="scr" x="14" y="264" font-size="11" opacity="0.85">The operator's screen now reads 95. The tank still holds 58.</text>
</svg>
<figcaption>FUXA asks for eleven holding registers starting at 1124 in one request. The answer carries only values, in order, with no addresses, so the proxy must remember from the request which slot holds which register.</figcaption>
</figure>

The forged values were chosen to look consistent. An HPT of 95 lies inside the 50-to-100 band in which the plant reports "operational", and the system sensor is forged to match, so the operator sees a calm, healthy plant.

Step through the attack yourself. Watch both ARP caches, the path the frames take and what the IDS notices.

<div data-widget="arp-spoof"></div>

<div data-widget="checkpoint" data-id="slots"></div>

## How to approach it

1. **Map the conversation.** Note the IP addresses of FUXA and OpenPLC and confirm that FUXA talks to port 502. A short capture with `tcpdump` or Wireshark shows the polling.
2. **Let traffic pass through you.** Turn on IP forwarding on the attack machine. Otherwise you would swallow every packet and the HMI would simply go dark, which is noticed at once.
3. **Poison both ARP caches.** Tell FUXA that the PLC's IP is at your MAC, and tell the PLC the same about FUXA. Tools: `arpspoof` (from the dsniff package), `ettercap` or a small `scapy` script. Keep both directions running.
4. **Watch the traffic cross your machine.** A capture on the attack machine should now show FUXA's polls.
5. **Rewrite, if you want to see the deception.** Run `mitm.py`. Read its settings first: it listens on port 5020 and needs the PLC's address as its upstream. The poisoned traffic still goes to port 502, so the proxy only sees it if FUXA is pointed at the proxy (that needs FUXA admin rights) or you redirect port 502 to 5020 on your machine.
6. **Verify on the challenge page.** It asks the IDS whether it saw the ARP poisoning.

<details class="deep-dive" markdown="1">
<summary>Deep dive: why the proxy patches by position</summary>

A Modbus read request says "start at 1124, give me 11 registers". The answer says only "22 bytes follow" and then the values, two bytes each, high byte first. Nothing in the answer says which number is the pressure.

So the proxy does its bookkeeping on the way out. It parses the request, works out that GST will be in slot 0, HPT in slot 2 and so on, and puts that map on a queue. When the answer comes back it takes the map off the queue and overwrites those slots. Because the proxy relays one request, then its answer, then the next request, the queue never holds more than one entry.

The same trick works for coils, where each value is a single bit inside a byte.

</details>

## Detect and defend

<figure class="wide">
<style>
.mm-a {--d: 11s; --on:#e06000;}
.mm-a .old,.mm-a .m1 {opacity:0; animation: a-old var(--d) steps(1,end) infinite;}
.mm-a .new,.mm-a .m2 {animation: a-new var(--d) steps(1,end) infinite;}
.mm-a .fire{animation: a-fire var(--d) steps(1,end) infinite;}
@keyframes a-old {0%,34%{opacity:1} 35%,100%{opacity:0}}
@keyframes a-new {0%,34%{opacity:0} 35%,100%{opacity:1}}
@keyframes a-fire{0%,44%{opacity:0} 45%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .mm-a *{animation:none !important}
  .mm-a .old,.mm-a .m1{opacity:0}
  .mm-a .new,.mm-a .m2,.mm-a .fire{opacity:1}
}
</style>
<svg class="mm-a" viewBox="0 0 460 128" role="img"
     aria-label="FUXA's ARP cache entry for the PLC's address is overwritten with the attacker's MAC. The IDS keeps a set of MACs per address; when the set for that address reaches two, the arp_spoof rule raises an alert.">
  <text x="14" y="28" font-size="13" opacity="0.8">FUXA's ARP cache for .0.3</text>
  <rect x="14" y="36" width="238" height="30" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.6"/>
  <text class="old" x="26" y="56" font-size="13" font-family="monospace" opacity="0.85">d6:10:7c:61:8a:64</text>
  <text class="new" x="26" y="56" font-size="13" font-family="monospace" fill="var(--on)" font-weight="bold">c6:76:2b:3f:44:40</text>
  <text x="166" y="56" font-size="13" opacity="0.72">last heard</text>

  <text x="276" y="28" font-size="13" opacity="0.8">the IDS remembers</text>
  <rect x="276" y="36" width="170" height="30" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.6"/>
  <text class="m1" x="288" y="56" font-size="13" font-family="monospace">1 MAC</text>
  <text class="m2" x="288" y="56" font-size="13" font-family="monospace" fill="var(--on)" font-weight="bold">2 MACs</text>

  <text class="fire" x="14" y="92" font-size="14" fill="var(--on)" font-weight="bold">arp_spoof &mdash; one address, two MACs</text>
  <text x="14" y="116" font-size="13" opacity="0.8">The cache believes the last reply; the IDS remembers every one.</text>
</svg>
<figcaption>The CybICS IDS rule <code>arp_spoof</code> does not see the interception itself. It notices that one IP address has been announced with more than one MAC address.</figcaption>
</figure>

- **Watch ARP.** An IP address that suddenly changes its MAC is the classic sign of poisoning, and it is what the CybICS IDS reports.
- **Fix the mapping.** Static ARP entries for critical devices, or switches with Dynamic ARP Inspection, refuse forged replies.
- **Segment the network.** If the attacker never shares a network segment with the HMI and the PLC, ARP tricks cannot reach them.
- **Authenticate the messages.** Protocols that sign their messages, such as OPC-UA with a secure policy or Modbus/TCP Security over TLS, make a rewritten answer detectable.
- **Cross-check the process.** An independent gauge or a second sensor path shows when the screen and the tank disagree.

In MITRE ATT&CK for ICS this is **T0830 Adversary-in-the-Middle**; forging the readings is **T1692.002 Unauthorized Message: Reporting Message** (formerly T0856 Spoof Reporting Message).

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

- The challenge is scored only on the IDS `arp_spoof` rule, so ARP poisoning alone wins the flag. Students who expect the HMI to change also need the proxy in the path.
- `mitm.py` ships with `MODBUS_SERVER_HOST = '172.17.0.1'`; students must point it at the PLC. ARP poisoning alone does not feed the proxy (it listens on 5020, the traffic goes to 502), so either repoint FUXA's device to the proxy or add an `iptables` REDIRECT rule. Repointing FUXA leaves no ARP trace and therefore does not score.
- The IDS keeps every MAC it has seen per IP until it restarts. Recreating a container gives it a new MAC, which also raises `arp_spoof`. Restart the IDS between groups if you want a clean dashboard.
- The proxy writes forged values little-endian at offset 10; this works only because all forged values are below 256 and the neighbouring high bytes are zero.

</details>

## Before you start

- [Modbus TCP](/theory/modbus): requests, answers and the register map.
- [The attack lifecycle](/theory/attack-lifecycle): where interception fits in an attack.
- [Wireshark capture](/theory/wireshark_capture): seeing the traffic you redirect.
- [HMI and SCADA](/theory/hmi-scada): why the operator trusts the screen.
