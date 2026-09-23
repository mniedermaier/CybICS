# S7comm

**S7comm** is the proprietary protocol Siemens PLCs use for programming and data exchange. It rides on ISO-on-TCP (RFC 1006), which conventionally listens on port **102**.

CybICS gives you two of them. OpenPLC answers S7comm on the standard port 102, alongside its Modbus, DNP3 and EtherNet/IP servers. Separately, a small purpose-built S7 server runs on **port 1102** and impersonates a Siemens S7-300 well enough to answer nmap's `s7-info` script. That second one is the target of the *S7comm Scanning* challenge, and the unusual port is the first thing the challenge makes you deal with.

## Why S7comm needs a conversation, and Modbus does not

A Modbus client can send a write as its first packet and be done. S7comm cannot: three round trips have to complete before a single byte of device data comes back. Each one exists because of a layer the protocol is wrapped in.

<figure>
<style>
.s7h {--h: 12s;}
/* Six steps, strictly in order: the figure's whole claim is that nothing can
   be read until the three round trips are finished, so it has to be watched
   arriving one at a time. */
.s7h .st {opacity:0; animation: h-step var(--h) steps(1,end) infinite;}
.s7h .e1{animation-delay:0s}    .s7h .e2{animation-delay:1.1s}
.s7h .e3{animation-delay:2.2s}  .s7h .e4{animation-delay:3.3s}
.s7h .e5{animation-delay:4.4s}  .s7h .e6{animation-delay:5.5s}
.s7h .gate{animation: h-gate var(--h) steps(1,end) infinite;}
@keyframes h-step{0%{opacity:0} 0.01%,54%{opacity:1} 54.01%,100%{opacity:0}}
@keyframes h-gate{0%,50%{opacity:1} 50.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .s7h .st,.s7h .gate{animation:none}
  .s7h .st{opacity:1} .s7h .gate{opacity:0}
}
</style>
<svg class="s7h" viewBox="0 0 520 280" role="img"
     aria-label="A sequence diagram of an S7comm session. The client sends a COTP connection request and receives a confirm, then sends an S7 setup communication request and receives the agreed PDU size, and only then may it send a userdata request to read a system status list and receive the device identity.">
  <rect x="20" y="16" width="110" height="38" rx="5" fill="#ff6b00" opacity="0.85"/>
  <text x="75" y="40" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">client</text>
  <rect x="390" y="16" width="110" height="38" rx="5" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="445" y="34" text-anchor="middle" font-size="12" font-weight="bold">S7 server</text>
  <text x="445" y="48" text-anchor="middle" font-size="11">:102 or :1102</text>
  <line x1="75" y1="58" x2="75" y2="258" stroke="currentColor" stroke-opacity="0.3" stroke-dasharray="4 4"/>
  <line x1="445" y1="58" x2="445" y2="258" stroke="currentColor" stroke-opacity="0.3" stroke-dasharray="4 4"/>

  <g font-size="11" text-anchor="middle">
    <g class="st e1">
      <text x="260" y="78">COTP connection request</text>
      <path d="M 78 88 L 440 88" stroke="#ff6b00" stroke-width="2"/>
      <path d="M 432 83 L 442 88 L 432 93" fill="none" stroke="#ff6b00" stroke-width="2"/>
    </g>
    <g class="st e2">
      <text x="260" y="110">COTP connection confirm</text>
      <path d="M 442 120 L 80 120" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
      <path d="M 88 115 L 78 120 L 88 125" fill="none" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
    </g>
    <g class="st e3">
      <text x="260" y="142">S7 setup communication</text>
      <path d="M 78 152 L 440 152" stroke="#ff6b00" stroke-width="2"/>
      <path d="M 432 147 L 442 152 L 432 157" fill="none" stroke="#ff6b00" stroke-width="2"/>
    </g>
    <g class="st e4">
      <text x="260" y="174">setup response, PDU size agreed</text>
      <path d="M 442 184 L 80 184" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
      <path d="M 88 179 L 78 184 L 88 189" fill="none" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
    </g>
    <g class="st e5">
      <text x="260" y="206">userdata: read SZL 0x001c</text>
      <path d="M 78 216 L 440 216" stroke="#ff6b00" stroke-width="2"/>
      <path d="M 432 211 L 442 216 L 432 221" fill="none" stroke="#ff6b00" stroke-width="2"/>
    </g>
    <g class="st e6">
      <text x="260" y="238">system name, module type name</text>
      <path d="M 442 248 L 80 248" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
      <path d="M 88 243 L 78 248 L 88 253" fill="none" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
    </g>
  </g>
  <text class="gate" x="260" y="274" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">
    no device data has crossed yet
  </text>
</svg>
<figcaption>Three round trips before the first useful byte. None of them authenticates anything &mdash; the COTP exchange agrees addressing, and the S7 setup agrees a maximum PDU size. They are negotiation, not admission control, which is the difference that matters here.</figcaption>
</figure>

## The wrapping, and why there are exactly three layers

Each round trip belongs to a layer, and the layers exist because S7comm was lifted off a serial bus onto TCP without being redesigned. TPKT gives the byte stream the message boundaries that the original bus had for free; COTP carries the connection-oriented semantics the S7 layer assumes; S7comm itself is the part that talks about the PLC.

<figure>
<style>
.s7w {--w: 10s;}
/* The headers are prepended, one layer at a time, in the order the stack
   builds them -- which is the reverse of the order they are listed in a
   textbook, and the reason a capture shows TPKT first. */
.s7w .l {opacity:0; animation: w-add var(--w) steps(1,end) infinite;}
.s7w .w2{animation-delay:1.6s} .s7w .w3{animation-delay:3.2s} .s7w .w4{animation-delay:4.8s}
@keyframes w-add{0%{opacity:0} 0.01%,64%{opacity:1} 64.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .s7w .l{animation:none; opacity:1}
}
</style>
<svg class="s7w" viewBox="0 0 520 170" role="img"
     aria-label="One S7comm message being wrapped. The S7 protocol data unit is prepended with a three-byte COTP header, then a four-byte TPKT header, and the result is carried in a TCP stream. Widths are drawn to scale at eighteen units per byte.">
  <g font-size="11" text-anchor="middle">
    <g class="l w1">
      <rect x="138" y="52" width="360" height="40" rx="4" fill="#ff6b00" opacity="0.75"/>
      <text x="318" y="42">n bytes</text>
      <text x="318" y="77" style="fill:#1a1a1a" font-weight="bold">S7 PDU &mdash; function and data</text>
    </g>
    <g class="l w2">
      <rect x="84" y="52" width="54" height="40" rx="4" fill="currentColor" opacity="0.28" stroke="currentColor"/>
      <text x="111" y="42">3 B</text><text x="111" y="77">COTP</text>
    </g>
    <g class="l w3">
      <rect x="12" y="52" width="72" height="40" rx="4" fill="currentColor" opacity="0.2" stroke="currentColor"/>
      <text x="48" y="42">4 B</text><text x="48" y="77">TPKT</text>
    </g>
    <g class="l w4">
      <rect x="12" y="104" width="486" height="26" rx="4" fill="currentColor" opacity="0.12" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="255" y="122">TCP stream to port 102 (or 1102 here)</text>
    </g>
  </g>
  <text x="12" y="152" font-size="11" opacity="0.8">Drawn to scale at 18 units per byte, so the two headers really are that small</text>
  <text x="12" y="166" font-size="11" opacity="0.8">next to the payload they frame.</text>
</svg>
<figcaption>A capture reads outside in: TPKT first, then COTP, then S7. The stack builds it the other way round, which is what the figure steps through. TPKT's only job is to say how long the message is &mdash; the same job Modbus gives its own length field, and the same failure mode if it is wrong.</figcaption>
</figure>

## Reading device identity

The **SZL** (*Systemzustandsliste*, system status list) functions return identity records, and they need no credentials &mdash; the three round trips above are the entire barrier. A scanner can fingerprint a device before touching the process at all.

Two lists matter here. SZL `0x0011` is module identification, and the CybICS server answers it with a perfectly ordinary S7-300 identity. SZL `0x001c` is component identification, and that is where the flag is.

<figure>
<style>
.s7z {--z: 13s;}
.s7z .q1,.s7z .a1 {opacity:0; animation: z-in var(--z) steps(1,end) infinite;}
.s7z .q2,.s7z .a2 {opacity:0; animation: z-in var(--z) steps(1,end) infinite; animation-delay:3.4s;}
.s7z .q1{animation-delay:0.2s} .s7z .a1{animation-delay:1.4s}
.s7z .q2{animation-delay:3.4s} .s7z .a2{animation-delay:4.6s}
.s7z .hit{animation: z-hit var(--z) steps(1,end) infinite;}
@keyframes z-in {0%{opacity:0} 0.01%,88%{opacity:1} 88.01%,100%{opacity:0}}
@keyframes z-hit{0%,48%{fill:currentColor} 48.01%,88%{fill:#ff6b00} 88.01%,100%{fill:currentColor}}
@media (prefers-reduced-motion: reduce){
  .s7z .q1,.s7z .a1,.s7z .q2,.s7z .a2{animation:none; opacity:1}
  .s7z .hit{animation:none; fill:#ff6b00}
}
</style>
<svg class="s7z" viewBox="0 0 520 260" role="img"
     aria-label="Two system status list queries. SZL 0x0011 returns the module order number 6ES7 315-2AG10-0AB0 and basic hardware SIMATIC 300. SZL 0x001c returns the system name SIMATIC 300(1) and, in the module type name field, the flag CybICS(s7comm_analysis_complete).">
  <rect x="14" y="14" width="96" height="34" rx="5" fill="#ff6b00" opacity="0.85"/>
  <text x="62" y="36" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">nmap</text>
  <rect x="404" y="14" width="102" height="34" rx="5" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="455" y="36" text-anchor="middle" font-size="12" font-weight="bold">s7com :1102</text>

  <g class="q1">
    <path d="M 114 31 L 398 31" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 390 26 L 400 31 L 390 36" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="256" y="25" text-anchor="middle" font-size="11">SZL 0x0011</text>
  </g>
  <g class="a1" font-size="11">
    <rect x="14" y="58" width="492" height="56" rx="4" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.4"/>
    <text x="26" y="78" opacity="0.75">Module</text>
    <text x="180" y="78" font-family="monospace">6ES7 315-2AG10-0AB0</text>
    <text x="26" y="100" opacity="0.75">Basic hardware</text>
    <text x="180" y="100" font-family="monospace">SIMATIC 300</text>
    <text x="400" y="78" opacity="0.7">an ordinary</text>
    <text x="400" y="100" opacity="0.7">S7-300 identity</text>
  </g>

  <g class="q2">
    <path d="M 114 141 L 398 141" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 390 136 L 400 141 L 390 146" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="256" y="135" text-anchor="middle" font-size="11">SZL 0x001c</text>
  </g>
  <g class="a2" font-size="11">
    <rect x="14" y="168" width="492" height="58" rx="4" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.4"/>
    <text x="26" y="188" opacity="0.75">System name</text>
    <text x="180" y="188" font-family="monospace">SIMATIC 300(1)</text>
    <text x="26" y="212" opacity="0.75">Module type name</text>
    <text class="hit" x="180" y="212" font-family="monospace" font-weight="bold">CybICS(s7comm_analysis_complete)</text>
  </g>
  <text x="14" y="248" font-size="11" opacity="0.8">Neither query needed a credential. The only thing in the way was three round trips.</text>
</svg>
<figcaption>The same device, asked two questions. The first answer is what a real S7-300 would say; the second carries the flag in its module type name field. Enumeration maps to MITRE ATT&amp;CK for ICS <strong>T0846 Remote System Discovery</strong> and <strong>T0861 Point &amp; Tag Identification</strong>.</figcaption>
</figure>

There is a catch, and it is the point of the challenge. Nmap's `s7-info` script has its port rule hard-coded to 102, so pointing it at 1102 does nothing at all unless you override the rule. Discovering *that* is the exercise: a scanner's defaults encode assumptions about where services live, and a service that moved is invisible to a tool that never asks.

## Security relevance

Classic S7comm on the S7-300 and S7-400 has no authentication. Siemens added S7comm-Plus with anti-replay and integrity checking for the S7-1200 and S7-1500, but the installed base still speaks the old protocol, and CybICS models the old one.

The CybICS IDS treats S7comm bluntly. Rule 6 raises an alert for **any** S7comm packet with a payload, to either port 102 or 1102, from any source &mdash; there is no allowlist and no rate threshold, only a thirty-second cooldown per source address so one scan does not produce a thousand alerts. That is a deliberate choice worth arguing with: it is the only Modbus-or-S7 rule in the file with no exemptions, which makes it perfectly sensitive and completely unable to tell an engineer from an attacker. In a plant where engineering traffic is routine, a rule like this is either disabled within a week or ignored, and both outcomes are worse than a narrower rule. Fixing that is what the *IDS Monitoring & Tuning* challenge is about.
