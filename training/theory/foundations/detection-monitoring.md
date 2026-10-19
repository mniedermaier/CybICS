# Detection and monitoring

Most industrial protocols, Modbus among them, never ask a client who it is. So a defender cannot simply check "is this client allowed?". The question becomes "does this traffic look like the plant running normally?", and the tool that keeps asking it is an **Intrusion Detection System (IDS)**.

This article explains what an IDS does, how the one built into CybICS decides when to raise an alarm, and why tuning that decision is harder than it looks.

## What an IDS does

Think of a smoke detector. It does not put out fires, and it does not stop you from cooking. It only watches the air and shouts when something looks wrong. An IDS does the same for network traffic: it watches a copy of the packets and raises an **alert** when a rule matches.

Two families of rules exist:

- **Signature rules** look for something known to be bad: "a Modbus diagnostic request", "the word *login* in an HTTP request".
- **Anomaly rules** look for something unusual: "far more writes per second than the HMI ever sends".

Most real systems, CybICS included, mix both. A rule that counts events over time ("five ports in ten seconds") is the most common kind on the plant.

### Why passive matters in OT

An IDS only *watches*. Its big brother, the Intrusion **Prevention** System (IPS), also blocks traffic it does not like. In an office network that is often fine. In a plant, a wrongly blocked packet could mean the controller stops hearing a pressure sensor, and that is a safety problem. This is why operational technology (OT) networks lean heavily on passive monitoring: it can be wrong without hurting the process.

## Where the CybICS IDS sits

In a real plant, a network switch copies all traffic to a special **mirror port** (also called a SPAN port), and the IDS sensor listens there. CybICS does the same thing in software:

- The `ids` container runs with host networking, finds the Docker bridge that carries the `172.18.0.0/24` plant network, and captures from it with `tcpdump`.
- It only listens. The only port it opens is its own dashboard on **8443**, where you see alerts and rule statistics.
- To save effort it drops traffic it already knows is normal before any rule sees it: the steady Modbus polling between OpenPLC (172.18.0.3) and the hardware simulation `hwio` (172.18.0.2) or the FUXA HMI (172.18.0.4).

<div class="callout cybics" markdown="1">
**On CybICS:** open the IDS dashboard at port 8443 while you run an attack from the attack machine (172.18.0.100). Watching your own alerts appear is the fastest way to understand the rules below.
</div>

## How a packet finds its rule

The detector does not show every packet to every rule. It sorts packets by their **destination port**, the number that says which service a packet is for, and hands each one to the rules for that service.

<figure class="wide">
<style>
.dm-d {--d: 16s;}
/* Five beats: four ports that each take a branch, and then one that matches
   nothing and drops out of the bottom. The fifth is the still frame. */
.dm-d .pk {animation: dd-pk var(--d) cubic-bezier(.4,0,.2,1) infinite;}
.dm-d .l1 {animation: dd-l1 var(--d) steps(1,end) infinite;}
.dm-d .l2 {animation: dd-l2 var(--d) steps(1,end) infinite;}
.dm-d .l3 {animation: dd-l3 var(--d) steps(1,end) infinite;}
.dm-d .l4 {animation: dd-l4 var(--d) steps(1,end) infinite;}
.dm-d .p5 {animation: dd-p5 var(--d) steps(1,end) infinite;}
.dm-d .p1,.dm-d .p2,.dm-d .p3,.dm-d .p4 {opacity:0;}
.dm-d .p5 {opacity:1;}
.dm-d .p1 {animation: dd-p1 var(--d) steps(1,end) infinite;}
.dm-d .p2 {animation: dd-p2 var(--d) steps(1,end) infinite;}
.dm-d .p3 {animation: dd-p3 var(--d) steps(1,end) infinite;}
.dm-d .p4 {animation: dd-p4 var(--d) steps(1,end) infinite;}
.dm-d .pk {transform: translateY(168px);}
.dm-d .l1,.dm-d .l2,.dm-d .l3,.dm-d .l4 {stroke-width:0;}
@keyframes dd-pk {0%,18%{transform:translateY(0)}      20%,38%{transform:translateY(42px)}
                  40%,58%{transform:translateY(84px)}  60%,78%{transform:translateY(126px)}
                  80%,100%{transform:translateY(168px)}}
@keyframes dd-l1 {0%,19.9%{stroke-width:3} 20%,100%{stroke-width:0}}
@keyframes dd-l2 {0%,19.9%{stroke-width:0} 20%,39.9%{stroke-width:3} 40%,100%{stroke-width:0}}
@keyframes dd-l3 {0%,39.9%{stroke-width:0} 40%,59.9%{stroke-width:3} 60%,100%{stroke-width:0}}
@keyframes dd-l4 {0%,59.9%{stroke-width:0} 60%,79.9%{stroke-width:3} 80%,100%{stroke-width:0}}
@keyframes dd-p1 {0%,19.9%{opacity:1} 20%,100%{opacity:0}}
@keyframes dd-p2 {0%,19.9%{opacity:0} 20%,39.9%{opacity:1} 40%,100%{opacity:0}}
@keyframes dd-p3 {0%,39.9%{opacity:0} 40%,59.9%{opacity:1} 60%,100%{opacity:0}}
@keyframes dd-p4 {0%,59.9%{opacity:0} 60%,79.9%{opacity:1} 80%,100%{opacity:0}}
@keyframes dd-p5 {0%,79.9%{opacity:0} 80%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dm-d * {animation:none !important;} }
</style>
<svg class="dm-d" viewBox="0 0 400 258" role="img"
     aria-label="The detector's sorting step. A packet with destination port 502 is handed to the Modbus rules. Port 102 or 1102 goes to the S7 rule. Port 8080 or 1881 goes to the HTTP brute force rule. Port 4840 goes to the OPC-UA rule. A packet takes at most one branch, and a packet to any other port drops out of the bottom untested. Connection attempts, called SYN packets, are checked before the sorting step and always reach the port scan and SYN flood rules.">
  <text x="8" y="18" font-size="12" font-weight="bold">sorting by destination port</text>
  <g class="pk"><rect x="8" y="30" width="56" height="26" rx="4" fill="#ff6b00"/>
    <text x="36" y="47" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">packet</text></g>
  <g font-size="12">
    <rect class="l1" x="86" y="30" width="180" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00"/>
    <text x="96" y="47">port 502 &rarr; Modbus rules</text>
    <rect class="l2" x="86" y="72" width="180" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00"/>
    <text x="96" y="89">102 / 1102 &rarr; S7 rule</text>
    <rect class="l3" x="86" y="114" width="180" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00"/>
    <text x="96" y="131">8080 / 1881 &rarr; HTTP rule</text>
    <rect class="l4" x="86" y="156" width="180" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00"/>
    <text x="96" y="173">4840 &rarr; OPC-UA rule</text>
  </g>
  <g font-size="12" font-weight="bold">
    <text class="p1" x="278" y="47" fill="#ff6b00">tested, then done</text>
    <text class="p2" x="278" y="89" fill="#ff6b00">tested, then done</text>
    <text class="p3" x="278" y="131" fill="#ff6b00">tested, then done</text>
    <text class="p4" x="278" y="173" fill="#ff6b00">tested, then done</text>
    <text class="p5" x="78" y="216">no branch matches &mdash; no rule at all</text>
  </g>
  <text x="8" y="240" font-size="11" opacity="0.85">Connection attempts (SYN) are checked first, always. Within</text>
  <text x="8" y="254" font-size="11" opacity="0.85">one branch, several rules can fire on the same packet.</text>
</svg>
<figcaption>Sorting by port keeps the detector fast enough for a Raspberry Pi. It also means coverage is decided by the port list: a service on a port outside 502, 102, 1102, 8080, 1881 and 4840 is only watched by the connection-attempt rules.</figcaption>
</figure>

## Counting: thresholds and windows

A single Modbus write is normal; the HMI sends them whenever an operator clicks a button. Fifty writes in five seconds from a stranger is not. Most CybICS rules therefore count events inside a **sliding window**: "how many in the last *N* seconds?". When the count reaches the **threshold**, the rule fires.

Choosing those two numbers is a trade-off between two kinds of mistake:

| Mistake | What happens | Caused by |
|---|---|---|
| **False positive** | an alert for harmless traffic | threshold too low, window too long |
| **False negative** | an attack with no alert | threshold too high, window too short |

Too many false positives and operators learn to ignore the dashboard, which is as bad as having no IDS. Too many false negatives and the IDS misses the attack it was installed for. Try it yourself: the stream below mixes writes from a legitimate HMI with writes from an attacker.

<div data-widget="ids-threshold"></div>

<div data-widget="checkpoint" data-id="slow-attacker"></div>

Once a rule fires, a second timer starts: a **cooldown** of thirty seconds per rule and source address. During it, the same rule stays silent for the same source, so a flood of hundreds of writes produces one readable alert every thirty seconds instead of hundreds.

<figure class="wide">
<style>
.dm-c {--c: 15s;}
/* Writes arrive at a steady rate; the window count climbs to ten and fires;
   the cooldown then swallows every alert for thirty seconds while the window
   stays full, and the alert fires again when it runs out. */
.dm-c .bar  {transform-box: fill-box; transform-origin: left; animation: dc-bar var(--c) linear infinite;}
.dm-c .fire {opacity:0; animation: dc-fire var(--c) steps(1,end) infinite;}
.dm-c .mute {opacity:1; animation: dc-mute var(--c) steps(1,end) infinite;}
.dm-c .cool {transform-box: fill-box; transform-origin: left; animation: dc-cool var(--c) linear infinite;}
.dm-c .bar {transform: scaleX(1);}
.dm-c .cool {transform: scaleX(0.55);}
@keyframes dc-bar  {0%{transform:scaleX(0)} 30%,100%{transform:scaleX(1)}}
@keyframes dc-fire {0%,29.9%{opacity:0} 30%,42%{opacity:1} 42.01%,93.9%{opacity:0} 94%,100%{opacity:1}}
@keyframes dc-mute {0%,42%{opacity:0} 42.01%,93.9%{opacity:1} 94%,100%{opacity:0}}
@keyframes dc-cool {0%,29.9%{transform:scaleX(0)} 30%{transform:scaleX(0)} 94%,100%{transform:scaleX(1)}}
@media (prefers-reduced-motion: reduce) { .dm-c * {animation:none !important;} }
</style>
<svg class="dm-c" viewBox="0 0 400 190" role="img"
     aria-label="A counting rule with two timers. Modbus writes from an unexpected host accumulate in a thirty-second sliding window; the tenth one reaches the threshold and an alert fires. The window stays full because writes keep arriving, but a thirty-second cooldown per source and rule holds back every further alert until it runs out. A run of hundreds of writes therefore produces one alert every thirty seconds.">
  <text x="8" y="18" font-size="12" font-weight="bold">modbus_unauth_write: 10 writes in 30 s</text>
  <text x="8" y="44" font-size="11" opacity="0.85">sliding window</text>
  <rect x="8" y="52" width="280" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="bar" x="8" y="52" width="280" height="20" rx="4" fill="#ff6b00"/>
  <text x="298" y="67" font-size="12" font-weight="bold" fill="#ff6b00">full at 10</text>

  <text x="8" y="100" font-size="11" opacity="0.85">30 s cooldown, per source and rule</text>
  <rect x="8" y="108" width="280" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="cool" x="8" y="108" width="280" height="20" rx="4" fill="currentColor" fill-opacity="0.55"/>
  <text x="298" y="123" font-size="12" opacity="0.85">counting down</text>

  <text class="fire" x="8" y="156" font-size="13" font-weight="bold" fill="#ff6b00">ALERT &mdash; unauthorized Modbus writes</text>
  <text class="mute" x="8" y="156" font-size="13" font-weight="bold">window still full &mdash; alert held back</text>
  <text x="8" y="180" font-size="11" opacity="0.85">Hundreds of writes, one alert every 30 s.</text>
</svg>
<figcaption>The window decides whether the behaviour counts as an attack; the cooldown decides how often you are told. That is also why the number of alerts on the dashboard is not the number of attack packets.</figcaption>
</figure>

## The nine CybICS rules

These are the rules in `software/ids/rules.py`, in plain words.

| Rule | Fires when | Severity | What it usually means |
|---|---|---|---|
| `port_scan` | one host tries 5 different ports on another host within 10 s | medium | someone is mapping the network |
| `syn_flood` | one host sends 100 connection attempts within 10 s | high | someone is trying to overload a service |
| `modbus_flood` | 50 Modbus writes within 5 s from a host other than `hwio`, FUXA or OpenPLC | critical | someone is pinning a register, as in Flood & Overwrite |
| `modbus_unauth_write` | 10 Modbus writes within 30 s from a host other than `hwio` or FUXA | high | a host that should never write is writing |
| `modbus_diagnostic` | any Modbus diagnostic (0x08) or device-identification (0x2B) request | medium | someone is fingerprinting the PLC |
| `s7_enumeration` | any S7comm data to port 102 or 1102 | medium | someone is talking Siemens S7 to the plant |
| `http_brute_force` | 5 login attempts to a web interface (8080 or 1881) within 30 s | high | password guessing |
| `arp_spoof` | one IP address shows up with more than one hardware (MAC) address | critical | a man-in-the-middle is redirecting traffic |
| `opcua_access` | OPC-UA traffic to port 4840 from a host that is not a plant service | low | an unexpected client is browsing the OPC-UA server |

Notice how often a rule depends on *who* sends the traffic. The IDS keeps a list of plant services by IP address and trusts their behaviour. That is a reasonable shortcut, and it is also exactly what an attacker tries to exploit: the [IDS Evasion](/ctf/challenge/ids_evasion) challenge is about staying below the rules or looking like someone they trust.

<div data-widget="checkpoint" data-id="which-rule"></div>

## From alert to action

An alert is only useful if someone reads it and acts. A good alert tells the analyst **what** happened, **who** did it and **what it probably means**. Each CybICS alert carries a rule name, a severity, the source and destination address, and a reference to an ATT&CK technique, so the analyst can look up the attacker's likely goal (see [The ICS attack lifecycle](/theory/attack-lifecycle)).

Defenders describe their own side with **MITRE D3FEND**, the defensive counterpart to ATT&CK. Watching traffic like this is *Network Traffic Analysis* (D3-NTA); the Modbus and S7 rules, which look at protocol fields, are a form of *Protocol Metadata Anomaly Detection* (D3-PMAD). What happens after the alert, containing and recovering, is covered in [Incident response in OT](/theory/incident-response).

<div class="callout tip" markdown="1">
**Rule of thumb:** a good ICS detection stays quiet on normal plant traffic, points to a technique an analyst can look up, and has been shown to fire at least once against the attack it claims to catch. The [Detect Port Scan](/ctf/challenge/detect_basic) and [IDS Challenge](/ctf/challenge/ids_challenge) exercises let you do exactly that.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: the IDS only sees the start of each packet</summary>

The capture runs with `tcpdump -s 128`: only the first 128 bytes of each frame are copied to the rules. That keeps the detector cheap enough for a Raspberry Pi Zero 2 W, and it is plenty for Modbus, but it limits what any rule can look at.

<figure class="wide">
<style>
.dm-s {--s: 11s;}
/* The frame stays put; what moves is the capture, taking its fixed-length
   bite and stopping. */
.dm-s .grab {transform-box: fill-box; transform-origin: left;
             animation: ds-grab var(--s) cubic-bezier(.4,0,.2,1) infinite;}
.dm-s .cut  {opacity:1; animation: ds-cut var(--s) steps(1,end) infinite;}
.dm-s .lost {opacity:1; animation: ds-cut var(--s) steps(1,end) infinite;}
.dm-s .grab {transform: scaleX(1);}
@keyframes ds-grab {0%{transform:scaleX(0)} 28%,100%{transform:scaleX(1)}}
@keyframes ds-cut  {0%,29.9%{opacity:0} 30%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dm-s * {animation:none !important;} }
</style>
<svg class="dm-s" viewBox="0 0 400 190" role="img"
     aria-label="One frame on the wire, drawn to scale by byte count. Fourteen bytes of Ethernet header, twenty of IP, thirty-two of TCP, then the payload. The capture keeps one hundred and twenty-eight bytes, so the copy the rules see stops after sixty-two bytes of payload. A Modbus write request is twelve bytes and fits easily. An HTTP request line fits too; the body of the request does not.">
  <text x="8" y="18" font-size="12" font-weight="bold">one frame, drawn by byte count</text>
  <g>
    <rect x="8"  y="34" width="28"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="38" y="34" width="40"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="80" y="34" width="64"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="146" y="34" width="124" height="34" rx="3" fill="#ff6b00"/>
    <rect class="lost" x="270" y="34" width="122" height="34" rx="3" fill="#ff6b00" fill-opacity="0.12" stroke="#ff6b00" stroke-dasharray="4 3"/>
    <rect class="grab" x="8" y="28" width="262" height="46" rx="3" fill="none" stroke="#ff6b00" stroke-width="3"/>
    <g font-size="11" text-anchor="middle">
      <text x="22" y="55">Eth</text><text x="22" y="66" font-size="11" opacity="0.8">14</text>
      <text x="58" y="55">IP</text><text x="58" y="66" font-size="11" opacity="0.8">20</text>
      <text x="112" y="55">TCP</text><text x="112" y="66" font-size="11" opacity="0.8">32</text>
      <text x="208" y="55" style="fill:#1a1a1a" font-weight="bold">payload the rules see</text>
      <text x="208" y="66" style="fill:#1a1a1a">62 bytes</text>
      <text x="331" y="55" fill="#ff6b00" font-weight="bold">never captured</text>
    </g>
  </g>
  <g class="cut">
    <line x1="270" y1="26" x2="270" y2="80" stroke="#ff6b00" stroke-width="3"/>
    <text x="264" y="94" text-anchor="end" font-size="12" font-weight="bold" fill="#ff6b00">tcpdump -s 128 cuts here</text>
  </g>
  <text x="8" y="130" font-size="12" opacity="0.9">A Modbus write request is 12 bytes. It fits easily.</text>
  <text x="8" y="150" font-size="12" opacity="0.9">An HTTP request line fits. A request body does not.</text>
  <text x="8" y="176" font-size="11" opacity="0.85">Anything past byte 62 of the payload is invisible to every rule.</text>
</svg>
<figcaption>Real header sizes on the CybICS bridge: 14 bytes of Ethernet, 20 of IP, and 32 of TCP because Linux adds timestamp options. That leaves 62 bytes of payload, enough for a complete Modbus request and for the first line of an HTTP request.</figcaption>
</figure>

Every IDS makes a trade-off like this between depth of inspection and cost. Commercial OT sensors parse whole protocol sessions, which needs far more computing power than a small board has.

</details>

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

- Trust in the rules is keyed on source IP (`KNOWN_SERVICES` in `rules.py`), and the BPF filter in `detector.py` drops hwio/FUXA to OpenPLC Modbus traffic before any rule runs. A host that takes over or spoofs one of those addresses is not flagged by the Modbus rules. OpenPLC is exempt from `modbus_flood` but not from `modbus_unauth_write`.
- `http_brute_force` only counts POSTs containing `login` or `auth`; FUXA's `/api/signin` contains neither, so FUXA password guessing raises no alert.
- Some `mitre` fields on alerts use older IDs (T0855, T0856, T0812, now T1692.001, T1692.002, T1694.001), and `syn_flood` is labelled T0836 Modify Parameter, which a SYN flood does not do. Worth discussing when students look the IDs up.

</details>
