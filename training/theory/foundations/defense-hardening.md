# Defence in depth

No single security control protects a plant. Passwords get guessed, firewall rules have gaps, and patches arrive years late. The answer is **defence in depth**: several independent layers, so that an attacker who gets past one still meets the next, and a defender has time to notice.

This article covers the layers that matter most in operational technology (OT): segmentation, firewall rules, authentication and patching, and the standards that tie them together.

## Layers, not a single wall

Picture a medieval castle. There is a moat, then an outer wall, then an inner wall, then guards at the keep, and lookouts on the towers watching all of it. No part is perfect, but together they make an attack slow, difficult and visible.

In a plant, the layers look like this:

| Layer | Example | On CybICS |
|---|---|---|
| Physical | locked cabinets, no stray USB sticks | the board's UART header (see [UART Training Guide](/ctf/challenge/uart_basic)) |
| Network perimeter | firewall between office and plant | not modelled: the attack machine already sits inside |
| Segmentation | separate zones for HMI, controllers and safety | one flat network, `172.18.0.0/24` |
| Host hardening | only needed services, firewall on each device | `iptables` rules inside a container |
| Authentication | strong, unique passwords; certificates | OpenPLC and FUXA logins, OPC-UA users |
| Monitoring | an IDS watching traffic | the CybICS IDS ([Detection and monitoring](/theory/detection-monitoring)) |

One warning about the castle picture. On a network, an attacker does not have to break every wall in turn. Each control guards a **path**, and an attacker needs only one open path. A strong OpenPLC password does not help if the attacker can write Modbus registers without logging in at all, which is exactly what [Flood & Overwrite](/ctf/challenge/flood_overwrite) shows. Monitoring is the one layer that does not have to block anything: whichever path the attacker takes, if it is watched, the attempt is seen.

## Segmentation: zones and conduits

**Segmentation** means splitting a network into separate parts so that one compromised machine cannot reach everything. The standard OT vocabulary comes from IEC 62443:

- A **zone** is a group of devices that need the same level of protection, for example "all controllers" or "the operator workstations".
- A **conduit** is the controlled path between two zones, usually a firewall that only lets through the connections the plant really needs.

The [Purdue model](/theory/ics-basics) gives a typical layout: office IT at the top, then the operations zone with historians and HMIs, then the controllers, then the physical process. Traffic should only cross from one level to the next through a conduit, never jump straight from an office laptop to a PLC.

<div class="callout cybics" markdown="1">
**On CybICS:** every container shares one flat network. The attack machine (172.18.0.100) can reach OpenPLC (172.18.0.3), FUXA (172.18.0.4) and the OPC-UA server (172.18.0.5) directly. The [Network Segmentation](/ctf/challenge/defense_network_segmentation) challenge asks you to change that.
</div>

## Firewall rules: order and defaults

A firewall checks each connection against a list of rules **from top to bottom, and the first rule that matches decides**. Nothing after it is read. That makes order the most common source of mistakes: a "drop everything to port 502" rule placed above "allow FUXA to port 502" blocks the HMI too.

There are two ways to write a rule list:

- **Deny-list:** allow everything, then block the things you know are bad. Easy to start, but every gap you did not think of stays open.
- **Allow-list (default deny):** block everything, then allow the few connections the plant needs. More work up front, but a forgotten port is closed by default.

OT networks suit allow-lists well, because the traffic is predictable: the same few hosts talk to the same few ports all day. Try it with the CybICS hosts:

<div data-widget="firewall-rules"></div>

<div data-widget="checkpoint" data-id="rule-order"></div>

### Why blocking single ports is fragile

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

<div class="callout tip" markdown="1">
**Tip:** after writing a rule, test the *outcome*, not just the configuration. Try to connect from the attack machine to every port you meant to close. A rule that is listed but does not block is worse than no rule, because you believe you are safe.
</div>

## Authentication

**Authentication** is how a system checks who you are, usually with a password, sometimes with a certificate. In OT it fails in three typical ways:

- **No authentication at all.** Modbus TCP and classic S7comm accept commands from anyone who can reach the port. For them, the network layers above are the only gate.
- **Default credentials.** Devices ship with a factory login that is printed in the manual and never changed. The [OpenPLC](/ctf/challenge/password_openplc) and [FUXA](/ctf/challenge/password_attack) password challenges exploit exactly this.
- **Shared accounts.** One login used by every operator, so nobody can tell afterwards who did what.

Modern protocols do better. The CybICS OPC-UA server refuses anonymous sessions and wants a username and password or a client certificate, and it can encrypt the connection (see [OPC-UA](/theory/opcua-protocol)). The fixes for the web logins are simple and are the subject of the [Harden OpenPLC Credentials](/ctf/challenge/defense_openplc_password) and [Harden FUXA Credentials](/ctf/challenge/defense_fuxa_password) challenges.

## Patching in OT

In office IT, a security patch is often installed within days. In a plant it may take years, and there are reasons:

- **Uptime.** Installing a patch often means a restart, and some processes run for months without stopping.
- **Certification.** The vendor of a control system may only support it with tested software versions. Patching on your own can void that support.
- **Testing.** A patch that breaks a controller can halt production or create a safety hazard, so it has to be tested on a copy of the system first.
- **Age.** Controllers last fifteen to twenty years. Many run software that no longer gets patches at all.

Because of this, OT relies heavily on **compensating controls**: if you cannot fix the weakness itself, you put layers around it. Segmentation, strict firewall rules and monitoring are the usual ones, which is why they are the workhorses of ICS defence.

<div data-widget="checkpoint" data-id="compensating"></div>

## Standards: IEC 62443 and NIST SP 800-82

Two documents frame most OT security work:

- **IEC 62443** is the international standard family for industrial automation security. Beyond zones and conduits, it defines **security levels** (SL 1 to SL 4), from protection against casual mistakes up to protection against well-funded, skilled attackers, and requirements for asset owners, integrators and product vendors.
- **NIST SP 800-82** (currently revision 3) is the US guide to OT security. It explains how to apply general security controls, such as boundary protection (SC-7) or authenticator management (IA-5), to plants.

How to decide which zone needs which security level is a risk question, covered in [Asset inventory, risk and IEC 62443](/theory/risk-assessment).

## Putting it into practice on CybICS

The defence challenges each add one layer to the gas plant:

1. [Harden OpenPLC Credentials](/ctf/challenge/defense_openplc_password) and [Harden FUXA Credentials](/ctf/challenge/defense_fuxa_password): replace the default logins.
2. [Modbus Firewall Rules](/ctf/challenge/defense_firewall): on the OpenPLC container, allow port 502 only from `hwio` (172.18.0.2) and FUXA (172.18.0.4).
3. [Network Segmentation](/ctf/challenge/defense_network_segmentation): stop the attack machine reaching the controllers.
4. [IDS Monitoring & Tuning](/ctf/challenge/defense_ids_tuning): keep the watching layer running.

Keep availability in mind throughout. If your Modbus rule also blocks `hwio`, the PLC stops receiving tank pressures, and you have caused the outage an attacker wanted. In OT, a control that endangers the process is not a security win.
