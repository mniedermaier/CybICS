# HMI and SCADA

An operator in a control room cannot walk up to every tank and read its gauge. Instead, they watch a screen that shows the whole plant and has buttons to steer it. Because the operator trusts that screen completely, it is one of the most valuable targets in any ICS.

## The operator's window on the plant

A **Human-Machine Interface (HMI)** is the screen an operator uses to watch and control a process: tank levels, pressures, alarms, and buttons to start and stop things. **SCADA (Supervisory Control and Data Acquisition)** is the wider system behind it, which collects data from many controllers. In the [Purdue model](/theory/ics-basics) both sit on Level 2, one step above the PLCs.

In CybICS the HMI is **FUXA**, an open-source SCADA/HMI that you open in a browser on port **1881**.

<div class="callout analogy" markdown="1">
**Analogy:** an HMI is like the dashboard of a car. The fuel gauge is not the fuel; it is a needle driven by a sensor signal. If someone tampers with that signal, the gauge shows a full tank while the engine runs dry.
</div>

## The HMI only knows what the PLC tells it

FUXA is not wired to any sensor. It is a **Modbus client**: about once a second it asks OpenPLC for the current register values and draws them. A button press writes a coil or a register back. The link is plain [Modbus TCP](/theory/modbus) on port 502, with no login.

So the operator's picture is three hops away from the gas: sensor, PLC memory, HMI. The live values below are exactly what FUXA reads.

<div data-widget="plant-live" data-fields="gst,hpt,compressor,systemValve,boSen"></div>

<figure class="wide">
<style>
.hm-c {--p: 6s; --k: 18s;}
.hm-c:where(.light-mode *) .cmd {fill:#b34700;}
.hm-c:where(.light-mode *) rect[fill="#ff6b00"] {fill:#b34700;}
.hm-c:where(.light-mode *) text[style*="#1a1a1a"] {fill:#ffffff !important;}
/* The command and value round trip replays every 6 s; which link is under
   attack changes every 6 s, cycling through three over 18. */
.hm-c .cmd {animation: hc-cmd var(--p) ease-in-out infinite;}
.hm-c .val {animation: hc-val var(--p) ease-in-out infinite;}
.hm-c .k1,.hm-c .k3 {opacity:0;}
.hm-c .k2 {opacity:1;}
.hm-c .k1 {animation: hc-k1 var(--k) steps(1,end) infinite;}
.hm-c .k2 {animation: hc-k2 var(--k) steps(1,end) infinite;}
.hm-c .k3 {animation: hc-k3 var(--k) steps(1,end) infinite;}
@keyframes hc-cmd {0%{transform:translateX(0);   opacity:0}
                   4%{transform:translateX(0);   opacity:1}
                   40%{transform:translateX(172px); opacity:1}
                   46%,100%{transform:translateX(172px); opacity:0}}
@keyframes hc-val {0%,50%{transform:translateX(0); opacity:0}
                   54%{transform:translateX(0); opacity:1}
                   90%{transform:translateX(-172px); opacity:1}
                   96%,100%{transform:translateX(-172px); opacity:0}}
@keyframes hc-k1 {0%,33.32%{opacity:1} 33.33%,100%{opacity:0}}
@keyframes hc-k2 {0%,33.32%{opacity:0} 33.33%,66.65%{opacity:1} 66.66%,100%{opacity:0}}
@keyframes hc-k3 {0%,66.65%{opacity:0} 66.66%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .hm-c * {animation:none !important;} }
</style>
<svg class="hm-c" viewBox="0 0 360 204" role="img"
     aria-label="Four boxes in a row: operator, HMI FUXA on port 1881, PLC OpenPLC on Modbus port 502, and the plant. A command travels left to right from the operator to the plant; a measured value travels right to left back to the operator's screen. Three attacks cut the chain at three different links: guessing the HMI login, a man in the middle on the Modbus connection between HMI and PLC, and a register flood at the PLC end.">
  <g font-size="12" text-anchor="middle">
    <rect x="8" y="30" width="76" height="40" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="46" y="48" font-weight="bold">Operator</text><text x="46" y="62" font-size="11" opacity="0.85">eyes &amp; hands</text>
    <rect x="94" y="30" width="76" height="40" rx="5" fill="#ff6b00"/>
    <text x="132" y="48" font-weight="bold" style="fill:#1a1a1a">FUXA</text><text x="132" y="62" font-size="11" style="fill:#1a1a1a">:1881</text>
    <rect x="180" y="30" width="76" height="40" rx="5" fill="#ff6b00"/>
    <text x="218" y="48" font-weight="bold" style="fill:#1a1a1a">OpenPLC</text><text x="218" y="62" font-size="11" style="fill:#1a1a1a">:502</text>
    <rect x="266" y="30" width="86" height="40" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="309" y="48" font-weight="bold">the plant</text><text x="309" y="62" font-size="11" opacity="0.85">tanks, valves</text>
  </g>
  <g stroke="currentColor" stroke-opacity="0.65" stroke-width="2">
    <line x1="84" y1="50" x2="92" y2="50"/><line x1="170" y1="50" x2="178" y2="50"/><line x1="256" y1="50" x2="264" y2="50"/>
  </g>
  <text x="176" y="22" text-anchor="middle" font-size="11" opacity="0.85">Modbus TCP &mdash; the same writes anyone else can send</text>

  <circle class="cmd" cx="88" cy="86" r="6" fill="#ff6b00"/>
  <text x="88" y="104" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">command</text>
  <circle class="val" cx="260" cy="86" r="6" fill="currentColor" fill-opacity="0.85"/>
  <text x="260" y="104" text-anchor="middle" font-size="11" opacity="0.85">measured value</text>

  <g font-size="12" font-weight="bold">
    <g class="k1">
      <path d="M 132 122 L 132 78" stroke="#ff6b00" stroke-width="3"/>
      <path d="M 124 88 L 140 104 M 124 104 L 140 88" stroke="#ff6b00" stroke-width="3"/>
      <text x="8" y="146" fill="#ff6b00">Password Attack &mdash; guess the login</text>
      <text x="8" y="164" font-size="11" opacity="0.85">credentials and a path, in one step</text>
    </g>
    <g class="k2">
      <path d="M 176 122 L 176 60" stroke="#ff6b00" stroke-width="3"/>
      <path d="M 168 76 L 184 92 M 168 92 L 184 76" stroke="#ff6b00" stroke-width="3"/>
      <text x="8" y="146" fill="#ff6b00">Man in the Middle &mdash; sit on the wire</text>
      <text x="8" y="164" font-size="11" opacity="0.85">neither end can tell</text>
    </g>
    <g class="k3">
      <path d="M 218 122 L 218 78" stroke="#ff6b00" stroke-width="3"/>
      <path d="M 210 88 L 226 104 M 210 104 L 226 88" stroke="#ff6b00" stroke-width="3"/>
      <text x="8" y="146" fill="#ff6b00">Flood &amp; Overwrite &mdash; pin the register</text>
      <text x="8" y="164" font-size="11" opacity="0.85">no login, no wire access</text>
    </g>
  </g>
  <text x="8" y="194" font-size="11" opacity="0.85">Three challenges, three depths, one chain.</text>
</svg>
<figcaption>A command travels right and becomes a coil write; a measured value travels left and becomes a number on the screen. Three CybICS challenges cut this chain at three links.</figcaption>
</figure>

The FUXA login protects the *screen*, not the plant. Anyone who can reach port 502 on OpenPLC can skip the screen and send the very same writes the HMI sends.

<details class="deep-dive" markdown="1">
<summary>Deep dive: how FUXA is wired up in CybICS</summary>

FUXA runs in the container at `172.18.0.4`, with an `operator` account for running the plant and a `viewer` account for watching it. Its only device entry points at `openplc:502`: no username, no password, no encryption. Everything on its screens is a Modbus read of that one connection, and every button is a Modbus write over it.

</details>

## Counting from one or from zero

HMIs count Modbus addresses from one; the protocol counts from zero. So subtract one: FUXA's HPT at **1127** is register **1126** on the wire.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the off-by-one trap in FUXA</summary>

Every FUXA address is one higher than the real one, coils included: FUXA's compressor at 2 is coil 1. Read coil 2 instead and you get the system valve. Copy a number straight out of the HMI and you read the neighbouring word, which usually holds something plausible.

<figure class="wide">
<style>
.hm-a {--a: 9s;}
.hm-a:where(.light-mode *) rect[fill="#ff6b00"] {fill:#b34700;}
.hm-a:where(.light-mode *) text[style*="#1a1a1a"] {fill:#ffffff !important;}
/* The base state is the settled one, so the two labels never overprint. */
.hm-a .slide {opacity:0; transform: translateX(-86px);
              animation: ha-slide var(--a) cubic-bezier(.4,0,.2,1) infinite;}
.hm-a .off   {opacity:1; animation: ha-off var(--a) steps(1,end) infinite;}
@keyframes ha-slide {0%,22%{opacity:1; transform:translateX(0)}
                     43.9%{opacity:1; transform:translateX(-86px)}
                     44%,100%{opacity:0; transform:translateX(-86px)}}
@keyframes ha-off   {0%,43.9%{opacity:0} 44%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .hm-a * {animation:none !important;} }
</style>
<svg class="hm-a" viewBox="0 0 360 176" role="img"
     aria-label="FUXA lists the HPT tag at address 1127. That is a one-based Modbus address. On the wire the same word is holding register 1126, which the PLC program declares as percent MW 102. The tag address slides down by one to become the register address. Every coil is offset the same way: FUXA's compressor at 2 is coil 1.">
  <text x="8" y="18" font-size="12" font-weight="bold">The same word, counted twice</text>
  <rect x="8" y="34" width="158" height="44" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="87" y="52" text-anchor="middle" font-size="11" opacity="0.85">FUXA tag table</text>
  <text x="87" y="70" text-anchor="middle" font-size="13" font-weight="bold">HPT &rarr; address 1127</text>

  <rect x="194" y="34" width="158" height="44" rx="5" fill="#ff6b00"/>
  <text x="273" y="52" text-anchor="middle" font-size="11" style="fill:#1a1a1a">on the wire</text>
  <text class="slide" x="273" y="70" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">register 1127</text>
  <text class="off" x="273" y="70" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">register 1126</text>

  <text class="off" x="180" y="100" text-anchor="middle" font-size="12" fill="#ff6b00" font-weight="bold">&minus;1</text>
  <text x="8" y="128" font-size="12" opacity="0.9">FUXA counts from one. The protocol counts from zero.</text>
  <text x="8" y="146" font-size="12" opacity="0.9">&#37;MW102 &rarr; 1024 + 102 = 1126, listed as 1127.</text>
  <text x="8" y="168" font-size="11" opacity="0.85">Coils too: compressor at 2 is coil 1.</text>
</svg>
<figcaption>Copy a number out of the HMI into a Modbus client and you read the neighbouring word. It usually holds something plausible, so nothing warns you.</figcaption>
</figure>

</details>

<div data-widget="checkpoint" data-id="offset"></div>

## When the screen lies

Because the HMI only shows what the PLC holds, whoever changes the PLC's memory changes the operator's reality. In the [Flood & Overwrite](/theory/flood_overwrite) challenge, an attacker writes a low value such as 10 into register 1126 hundreds of times a second. That is faster than the plant simulation can put the real pressure back.

The PLC believes the tank is nearly empty, so it starts the compressor and shuts the system valve. The real pressure climbs, while the operator's trend shows a flat 10. One clue survives: the plant simulation (hwio) computes the blow-out flag `boSen` from the *real* pressure, so it switches on when the tank gets dangerously full.

<details class="deep-dive" markdown="1">
<summary>Deep dive: a recorded flood on the FUXA trend</summary>

hwio writes `boSen` into register 1134 and sets it once the real HPT pressure passes 220. The attacker only overwrites register 1126, so the flag keeps telling the truth.

<figure class="wide">
<style>
.hm-t {--t: 18s;}
/* Each trace draws on its own dash length, so both pens stay at the same
   moment in time. */
.hm-t .head {animation: ht-head var(--t) linear infinite;}
.hm-t .hpt  {stroke-dasharray:1400; animation: ht-hpt var(--t) linear infinite;}
.hm-t .bo   {stroke-dasharray:1000; animation: ht-bo  var(--t) linear infinite;}
.hm-t .alm  {opacity:1; animation: ht-alm var(--t) steps(1,end) infinite;}
@keyframes ht-head {0%{transform:translateX(0)} 92%,100%{transform:translateX(292px)}}
@keyframes ht-hpt  {0%{stroke-dashoffset:1400} 92%,100%{stroke-dashoffset:0}}
@keyframes ht-bo   {0%{stroke-dashoffset:1000} 92%,100%{stroke-dashoffset:0}}
@keyframes ht-alm  {0%,43.4%{opacity:0} 43.5%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .hm-t * {animation:none !important;} }
</style>
<svg class="hm-t" viewBox="0 0 360 240" role="img"
     aria-label="Two FUXA trends over one flood of register 1126 lasting three hundred and thirty seconds. The HPT trend sits at ten almost throughout, with a few single-sample spikes where a poll caught the real pressure between two forged writes. The spikes rise as the run goes on, from 131 to 254, because the real pressure is climbing. The blow-out flag from register 1134 steps from zero to one at a hundred and fifty-six seconds.">
  <text x="8" y="18" font-size="12" font-weight="bold">FUXA, &ldquo;System values&rdquo;, one flood, 330 s</text>

  <text x="52" y="38" font-size="11" opacity="0.85">HPT &mdash; register 1126 &mdash; what the trend shows</text>
  <polyline class="hpt" pathLength="1400" points="52,136 104,136 106,93 108,136 108,136 110,93 112,136 164,136 166,71 168,136 200,136 202,60 204,136 220,136 222,57 224,136 314,136 316,50 318,136 344,136" fill="none" stroke="#ff6b00" stroke-width="2.5" stroke-linejoin="round"/>
  <text x="114" y="88" font-size="11" fill="#ff6b00" font-weight="bold">131</text>
  <text x="172" y="66" font-size="11" fill="#ff6b00" font-weight="bold">195</text>
  <text x="228" y="52" font-size="11" fill="#ff6b00" font-weight="bold">234</text>
  <text x="322" y="46" font-size="11" fill="#ff6b00" font-weight="bold">254</text>
  <text x="348" y="140" text-anchor="end" font-size="11" opacity="0.85">10</text>

  <text x="52" y="158" font-size="11" opacity="0.85">boSen &mdash; register 1134 &mdash; the blow-out flag</text>
  <polyline class="bo" pathLength="1000" points="52,190 190,190 190,166 344,166" fill="none" stroke="currentColor" stroke-width="2.5" stroke-opacity="0.85"/>
  <text class="alm" x="344" y="162" text-anchor="end" font-size="11" font-weight="bold" fill="#ff6b00">alarm at 156 s</text>

  <line x1="52" y1="198" x2="344" y2="198" stroke="currentColor" stroke-opacity="0.6"/>
  <g class="head"><line x1="52" y1="198" x2="52" y2="208" stroke="currentColor" stroke-width="2"/></g>
  <g font-size="11" opacity="0.8">
    <text x="52" y="220" text-anchor="middle">0 s</text>
    <text x="185" y="220" text-anchor="middle">150</text>
    <text x="318" y="220" text-anchor="middle">300</text>
  </g>
  <text x="8" y="236" font-size="11" opacity="0.85">The spikes climb. That is the tank, seen through the gaps.</text>
</svg>
<figcaption>A recorded flood. The pressure trend shows the forged 10, except for a few lucky polls that caught the real value between two forged writes; those spikes climb because the real tank is filling. Meanwhile the blow-out flag switches on. A single odd sample looks like noise, but here it is the only true pressure reading on the screen.</figcaption>
</figure>

</details>

## Why attackers target the HMI

- **It holds valid credentials and a network path** to the controllers. Compromising it skips the hardest part of an attack.
- **It can command the process**, and its commands look exactly like an engineer's, because they are the same writes.
- **The operator trusts what it shows.** In [Stuxnet](/theory/stuxnet), the attackers played back recorded normal readings, prepared below the HMI, while the centrifuges were being damaged.

In CybICS, [Password Attack](/theory/password_attack) targets the FUXA login, [Man in the Middle](/theory/mitm) sits on the link to OpenPLC, and Flood & Overwrite pins the register the HMI reads. MITRE ATT&CK for ICS calls the effect on the operator **T0832 Manipulation of View**.

## Defending the supervisory layer

The key rule: **a value and the evidence that confirms it should not travel the same path.** In CybICS both come from the same PLC; they only disagree because `boSen` is calculated from something the attacker cannot reach. In a real plant, confirmation means a second sensor, a different protocol or a separate network.

Three habits protect this layer:

1. **Strong authentication on the HMI.** Default accounts like `operator`/`operator` are convenient in a lab and dangerous in a plant.
2. **Restrict who can reach the HMI and who can reach past it.** If only the HMI may talk Modbus to the PLC, a flood from anywhere else stands out. See [Defence in depth](/theory/defense-hardening).
3. **Give the operator at least one independent value.** When every number comes down the same wire, whoever owns that wire owns the operator's picture.

