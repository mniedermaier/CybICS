# Defence in depth

No single security control protects a plant. Passwords get guessed, firewall rules have gaps, and patches arrive years late. The answer is **defence in depth**: several independent layers, so that an attacker who gets past one still meets the next, and a defender has time to notice.

## Layers, not a single wall

Picture a castle: a moat, two walls, guards at the keep and lookouts on the towers. No part is perfect, but together they make an attack slow and visible. A plant's layers range from locked cabinets through firewalls and passwords to an IDS.

One warning: on a network, an attacker need not break every wall in turn. Each control guards a **path**, and one open path is enough. A strong OpenPLC password does not help if Modbus registers can be written without any login, as [Flood & Overwrite](/ctf/challenge/flood_overwrite) shows. Monitoring blocks nothing, but it sees an attempt on any path it watches.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the layers on CybICS</summary>

| Layer | Example | On CybICS |
|---|---|---|
| Physical | locked cabinets, no stray USB sticks | the board's UART header (see [UART Training Guide](/ctf/challenge/uart_basic)) |
| Network perimeter | firewall between office and plant | not modelled: the attack machine already sits inside |
| Segmentation | separate zones for HMI, controllers and safety | one flat network, `172.18.0.0/24` |
| Host hardening | only needed services, firewall on each device | `iptables` rules inside a container |
| Authentication | strong, unique passwords; certificates | OpenPLC and FUXA logins, OPC-UA users |
| Monitoring | an IDS watching traffic | the CybICS IDS ([Detection and monitoring](/theory/detection-monitoring)) |

</details>

## Segmentation: zones and conduits

**Segmentation** splits a network into separate parts, so one compromised machine cannot reach everything. Its OT vocabulary comes from IEC 62443:

- A **zone** is a group of devices that need the same protection, such as "all controllers".
- A **conduit** is the controlled path between two zones, usually a firewall that lets through only the connections the plant needs.

In the [Purdue model](/theory/ics-basics), traffic should cross levels only through a conduit, never jump straight from an office laptop to a PLC. IEC 62443 also gives each zone a target **security level**; choosing it is covered in [Asset inventory, risk and IEC 62443](/theory/risk-assessment).

<div class="callout cybics" markdown="1">
**On CybICS:** every container shares one flat network. The attack machine can reach OpenPLC, FUXA and the OPC-UA server directly. The [Network Segmentation](/ctf/challenge/defense_network_segmentation) challenge asks you to change that.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: security levels and NIST SP 800-82</summary>

IEC 62443 is the international standard family for industrial automation security. It defines four **security levels**, SL 1 to SL 4, from protection against casual mistakes up to protection against well-funded, skilled attackers. It also sets requirements for asset owners, integrators and product vendors.

The other document that frames most OT security work is **NIST SP 800-82** (revision 3), the US guide to applying general security controls to plants. It maps the controls of NIST SP 800-53 onto plants, for example boundary protection (SC-7) or authenticator management (IA-5).

</details>

## Firewall rules: order and defaults

A firewall checks each connection against a list of rules **from top to bottom, and the first rule that matches decides**. So order is the most common mistake: a "drop everything to port 502" rule above "allow FUXA to port 502" blocks the HMI too.

Rule lists come in two kinds:

- **Deny-list:** allow everything, then block what you know is bad. Every gap you did not think of stays open.
- **Allow-list (default deny):** block everything, then allow the few connections the plant needs. A forgotten port is closed by default.

OT networks suit allow-lists, because the traffic is predictable: the same few hosts talk to the same few ports all day. Try it:

<div data-widget="firewall-rules"></div>

<div data-widget="checkpoint" data-id="rule-order"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: why blocking single ports is fragile</summary>

A deny-list has to know every door. The figure shows what happens if you block only the three ports you have heard of on the OpenPLC container.

<figure class="wide">
<style>
.dh-p {--p: 18s;}
/* The verdicts accumulate rather than replacing each other, so the figure
   ends on the whole comparison, which is also the still frame. */
.dh-p .prb {animation: dp-prb var(--p) cubic-bezier(.4,0,.2,1) infinite;}
.dh-p .g1 {animation: dp-g1 var(--p) steps(1,end) infinite;}
.dh-p .g2 {animation: dp-g2 var(--p) steps(1,end) infinite;}
.dh-p .g3 {animation: dp-g3 var(--p) steps(1,end) infinite;}
.dh-p .g4 {animation: dp-g4 var(--p) steps(1,end) infinite;}
.dh-p .g5 {animation: dp-g5 var(--p) steps(1,end) infinite;}
.dh-p .g6 {animation: dp-g6 var(--p) steps(1,end) infinite;}
.dh-p .prb {transform: translateY(175px);}
.dh-p .ldr {stroke:currentColor; stroke-opacity:0.7; stroke-dasharray:3 3;}
@keyframes dp-prb {0%,13%{transform:translateY(0)}     16.7%,30%{transform:translateY(35px)}
                   33.3%,46%{transform:translateY(70px)}  50%,63%{transform:translateY(105px)}
                   66.7%,80%{transform:translateY(140px)} 83.3%,100%{transform:translateY(175px)}}
@keyframes dp-g1 {0%,13%{opacity:0} 13.1%,100%{opacity:1}}
@keyframes dp-g2 {0%,29.9%{opacity:0} 30%,100%{opacity:1}}
@keyframes dp-g3 {0%,46.5%{opacity:0} 46.6%,100%{opacity:1}}
@keyframes dp-g4 {0%,63.2%{opacity:0} 63.3%,100%{opacity:1}}
@keyframes dp-g5 {0%,79.9%{opacity:0} 80%,100%{opacity:1}}
@keyframes dp-g6 {0%,96.5%{opacity:0} 96.6%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dh-p * {animation:none !important;} }
</style>
<svg class="dh-p" viewBox="0 0 360 280" role="img"
     aria-label="The attack machine probes six service ports in turn. Three have a blocking rule: port 8080 for the OpenPLC web interface, port 502 for Modbus and port 4840 for OPC-UA. Ports 102 for S7comm, 20000 for DNP3 and 44818 for EtherNet slash IP have no rule and stay open. All six verdicts stay on screen once reached, so the figure ends showing three doors shut and three open.">
  <text x="8" y="18" font-size="12" font-weight="bold">the attack machine tries every listening port</text>
  <g class="prb"><rect x="8" y="32" width="78" height="26" rx="4" fill="#ff6b00"/>
    <text x="47" y="49" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">172.18.0.100</text></g>
  <g font-size="12">
    <text x="96" y="45">:8080 &rarr; web UI</text>
    <text x="96" y="80">:502 &rarr; Modbus</text>
    <text x="96" y="115">:4840 &rarr; OPC-UA</text>
    <text x="96" y="150">:102 &rarr; S7comm</text>
    <text x="96" y="185">:20000 &rarr; DNP3</text>
    <text x="96" y="220">:44818 &rarr; EtherNet/IP</text>
  </g>
  <g class="ldr">
    <line x1="90" y1="53" x2="344" y2="53"/><line x1="90" y1="88" x2="344" y2="88"/>
    <line x1="90" y1="123" x2="344" y2="123"/><line x1="90" y1="158" x2="344" y2="158"/>
    <line x1="90" y1="193" x2="344" y2="193"/><line x1="90" y1="228" x2="344" y2="228"/>
  </g>
  <g font-size="12" font-weight="bold" text-anchor="end">
    <text class="g1" x="344" y="45">DROP</text>
    <text class="g2" x="344" y="80">DROP</text>
    <text class="g3" x="344" y="115">DROP</text>
    <text class="g4" x="344" y="150" fill="#ff6b00">open</text>
    <text class="g5" x="344" y="185" fill="#ff6b00">open</text>
    <text class="g6" x="344" y="220" fill="#ff6b00">open</text>
  </g>
  <text x="8" y="252" font-size="11" opacity="0.85">Three rules written, six ports answering. The three left open</text>
  <text x="8" y="268" font-size="11" opacity="0.85">all reach the same controller memory.</text>
</svg>
<figcaption>Besides its web interface and Modbus, OpenPLC also speaks S7comm (102), DNP3 (20000) and EtherNet/IP (44818), and all of them reach the same values the PLC holds. Blocking by port only works if you know every port, so check with a scan (see <a href="/theory/scanning">Network scanning</a>). A rule that drops everything from an untrusted host closes all of them at once.</figcaption>
</figure>

</details>

<div class="callout tip" markdown="1">
**Tip:** test the *outcome*: from the attack machine, try every port you meant to close. A rule that does not block is worse than none: you believe you are safe.
</div>

## Authentication

**Authentication** checks who you are, with a password or a certificate. In OT it fails in three typical ways:

- **None at all.** Modbus TCP and classic S7comm accept commands from anyone who reaches the port; the network layers are their only gate.
- **Default credentials.** Devices ship with a factory login nobody changes. The [OpenPLC](/ctf/challenge/password_openplc) and [FUXA](/ctf/challenge/password_attack) password challenges exploit exactly this.
- **Shared accounts.** Every operator uses one login, so nobody can tell who did what.

Modern protocols do better: the CybICS [OPC-UA](/theory/opcua-protocol) server refuses anonymous sessions.

## Patching in OT

Office IT installs a patch within days; a plant may take years, for good reasons:

- **Uptime.** A patch often means a restart, and some processes run for months non-stop.
- **Certification.** The vendor may only support tested software versions.
- **Testing.** A faulty patch can create a safety hazard, so it is tested on a copy first.
- **Age.** Controllers last fifteen to twenty years, often longer than their patch support.

So OT relies on **compensating controls**: if you cannot fix a weakness, put layers around it: segmentation, strict firewall rules and monitoring.

<div data-widget="checkpoint" data-id="compensating"></div>

## Putting it into practice on CybICS

Each defence challenge adds one layer:

1. [Harden OpenPLC Credentials](/ctf/challenge/defense_openplc_password) and [Harden FUXA Credentials](/ctf/challenge/defense_fuxa_password): replace the default logins.
2. [Modbus Firewall Rules](/ctf/challenge/defense_firewall): on the OpenPLC container, allow port 502 only from the plant's own Modbus clients: `hwio` (172.18.0.2), FUXA (172.18.0.4) and the OPC-UA server (172.18.0.5).
3. [Network Segmentation](/ctf/challenge/defense_network_segmentation): stop the attack machine reaching the controllers.
4. [IDS Monitoring & Tuning](/ctf/challenge/defense_ids_tuning): keep the watching layer running.

Mind availability: if your Modbus rule also blocks `hwio`, the PLC stops receiving tank pressures: you have caused the outage an attacker wanted. Block the OPC-UA server, and its clients lose their view of the plant. In OT, a control that endangers the process is not a security win.
