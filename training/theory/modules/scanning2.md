# S7comm enumeration

In this challenge you ask a Siemens-style controller who it is. Using S7comm, the protocol of Siemens S7 PLCs, you read the device's identity record: model, hardware, firmware version and more. Attackers want this before they touch a process, because it tells them which exploits and which programming tools fit.

## The idea

A port scan tells you a door is open. Enumeration is knocking and asking the person behind it for their business card. Many industrial protocols have such a card built in, because engineering tools need to know exactly which device they are talking to before they upload a program.

S7comm keeps that information in the **System Status List (SZL)**, a set of numbered records inside the controller. Record `0x0011`, for example, is the module identification, and `0x001C` the component identification. Any client that completes the S7comm handshake can read them. There is no password: the protocol was designed for closed plant networks where everyone was trusted.

MITRE ATT&CK for ICS calls reading make, model and version *Remote System Information Discovery* (T0888). It usually follows *Remote System Discovery* (T0846), the scan that found the device.

<div class="callout analogy" markdown="1">
**Analogy:** A business card says what the person *claims* to be. It is good evidence when nobody has a reason to lie, and worthless when someone does. Device identity records are the same: a string the device chooses to send.
</div>

## How it looks on CybICS

The plant answers S7comm in two places, and neither of them is a real Siemens PLC.

<figure class="wide">
<style>
.s7-t {--t: 16s;}
.s7-t .prb {animation: st-prb var(--t) cubic-bezier(.4,0,.2,1) infinite;}
.s7-t .a1  {opacity:1; animation: st-a1 var(--t) steps(1,end) infinite;}
.s7-t .a2  {opacity:1; animation: st-a2 var(--t) steps(1,end) infinite;}
.s7-t .prb {transform: translateY(96px);}
@keyframes st-prb {0%,42%{transform:translateY(0)} 50%,100%{transform:translateY(96px)}}
@keyframes st-a1  {0%,17.9%{opacity:0} 18%,100%{opacity:1}}
@keyframes st-a2  {0%,67.9%{opacity:0} 68%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .s7-t * {animation:none !important;} }
</style>
<svg class="s7-t" viewBox="0 0 360 246" role="img"
     aria-label="The plant answers S7comm on two ports. Port 102 on the OpenPLC container is the snap7 library's server, and it reports the library defaults: a CPU 315-2 PN slash DP, system name SNAP7-SERVER, Original Siemens Equipment. Port 1102 on the s7com container is a hand-written server, and it reports a SIMATIC 300 identity with an extra Module Type field. Neither endpoint is a Siemens PLC and both claim to be one.">
  <text x="8" y="18" font-size="12" font-weight="bold">the same question, asked twice</text>
  <g class="prb"><rect x="8" y="28" width="64" height="24" rx="4" fill="#ff6b00"/>
    <text x="40" y="44" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">SZL read</text></g>

  <text x="86" y="44" font-size="12" font-weight="bold">172.18.0.3 : 102</text>
  <text x="86" y="60" font-size="11" opacity="0.85">OpenPLC&rsquo;s own snap7 server</text>
  <g class="a1" font-family="monospace" font-size="11">
    <text x="86" y="80">CPU 315-2 PN/DP</text>
    <text x="86" y="94">SNAP7-SERVER</text>
    <text x="86" y="108">Original Siemens Equipment</text>
  </g>
  <text class="a1" x="86" y="126" font-size="11" opacity="0.85">&mdash; the library&rsquo;s defaults</text>

  <text x="86" y="160" font-size="12" font-weight="bold">172.18.0.6 : 1102</text>
  <text x="86" y="176" font-size="11" opacity="0.85">s7com, a hand-written server</text>
  <g class="a2" font-family="monospace" font-size="11">
    <text x="86" y="196">6ES7 315-2AG10-0AB0</text>
    <text x="86" y="210">SIMATIC 300, v2.6.9</text>
    <text x="86" y="224" fill="#ff6b00" font-weight="bold">Module Type: ?</text>
  </g>
  <text class="a2" x="86" y="242" font-size="11" opacity="0.85">&mdash; the field the challenge is about</text>
</svg>
<figcaption>Port 102 belongs to OpenPLC, whose built-in snap7 server answers with the library&rsquo;s placeholder identity. Port 1102, on the separate <code>s7com</code> container, is a small Python server that presents a SIMATIC 300 record, including the <code>Module Type</code> field this challenge asks you to read. The real controller is OpenPLC, which is neither.</figcaption>
</figure>

Before the SZL read, every S7comm client goes through three steps: a TCP connection to the port, a COTP connection request (the transport layer S7comm runs on) and an S7 *Setup Communication*. You can take a real SZL request apart here:

<div data-widget="s7-layers" data-sample="szl"></div>

## How to approach it

1. Confirm both S7 ports are open with a port scan of the two hosts. Note which service name nmap gives port 1102; it is looked up from a port table, not observed.
2. nmap ships a script for exactly this job, `s7-info`, in its scripting engine (NSE). It performs the handshake and prints the identity fields. Run it against the OpenPLC host on port 102 first and compare the output with the figure above.
3. Now run it against 1102 and notice that nothing happens. Every NSE script contains a **portrule** near the top, a line that decides which ports the script considers itself responsible for. Open the script file and read that line.
4. Work out how to make nmap run the script against the port where the s7com server listens. The challenge material describes the usual way.
5. Read every field the script prints. The challenge is in one of them.

<div data-widget="checkpoint" data-id="portrule"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: why the service name does not help</summary>

The `s7-info` portrule accepts a port either by number or by service name `iso-tsap`. That name comes from `nmap-services`, the port-number table, where 102 is `iso-tsap` and 1102 is `adobeserver-1`. So the name check only ever matches 102, which is already in the number list. Version detection (`-sV`) does not help either: `nmap-service-probes` has no S7comm probe that would rename 1102.

If you work on your own machine, keep a backup of any NSE script you change. On a shared attack machine, someone may already have edited it.

</details>

## Detect and defend

S7comm enumeration is easy to spot, because legitimate S7comm traffic comes from a short, known list of engineering stations and HMIs. The CybICS IDS has an `s7_enumeration` rule that raises a medium-severity alert for any S7comm payload sent to port 102 or 1102, whoever sends it. Your scan will show up in the IDS alerts, whether it succeeds or not.

Defences:

- **Allow-listing.** Only the engineering workstation and the HMI should ever talk S7comm to a controller. A firewall rule or an IDS alert for every other source enforces this. See [Host firewalling](/theory/defense_firewall).
- **Segmentation.** Keep the protocol on the control network, away from office systems. See [Network segmentation](/theory/defense_network).
- **Protection levels.** Real Siemens CPUs can require a password before a client may change the program and, at higher levels, before it may read data. Use them.
- **Distrust identities.** Asset inventories should record what a device *is*, verified on site, not only what it reports.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

`s7_server_custom.py` dispatches on a single comparison: SZL `0x0011` gets the module record, and every other identifier, including ones that do not exist, gets the extended record with the challenge field. A real CPU answers an unknown SZL with an error. Students who craft their own requests may reach the field this way without the NSE script; that is a fair route and a good discussion point about trusting identity data.

</details>

## Before you start

- [S7comm](/theory/s7comm) for the protocol layers and the SZL.
- [Network scanning](/theory/scanning) for finding the ports in the first place.
