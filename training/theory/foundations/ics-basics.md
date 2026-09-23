# What is an Industrial Control System?

An **Industrial Control System (ICS)** is the combination of hardware and software that monitors and controls a physical process: a gas plant, a water works, a power grid, a production line. Unlike ordinary IT, an ICS acts on the real world. A wrong value does not corrupt a spreadsheet, it opens a valve.

This is why the priorities are inverted compared to IT. In IT the order is usually **confidentiality, integrity, availability**. In operational technology (OT) it is the reverse: keeping the process running safely comes first.

<figure>
<style>
/* The inversion is a reordering, so the figure reorders: the two outer goals
   trade places and the reader sees which one moved. */
.pri {--p: 12s;}
.pri .swap-c {animation: p-right var(--p) ease-in-out infinite;}
.pri .swap-a {animation: p-left  var(--p) ease-in-out infinite;}
.pri .lab-it {animation: p-it    var(--p) steps(1,end) infinite;}
.pri .lab-ot {opacity:0; animation: p-ot var(--p) steps(1,end) infinite;}
.pri .safety {opacity:0; animation: p-ot var(--p) steps(1,end) infinite;}
.pri .fallback {display:none;}
@keyframes p-right {0%,25%{transform:translateX(0)} 38%,88%{transform:translateX(340px)}
                    100%{transform:translateX(0)}}
@keyframes p-left  {0%,25%{transform:translateX(0)} 38%,88%{transform:translateX(-340px)}
                    100%{transform:translateX(0)}}
@keyframes p-it {0%,30%{opacity:1} 30.01%,92%{opacity:0} 92.01%,100%{opacity:1}}
@keyframes p-ot {0%,30%{opacity:0} 38%,88%{opacity:1} 92%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .pri .animated {display:none;}
  .pri .fallback {display:block;}
}
</style>
<svg class="pri" viewBox="0 0 520 150" role="img"
     aria-label="The same three security goals in two orders. IT ranks them confidentiality, integrity, availability. OT reverses the outer two: safety and availability first, confidentiality last.">
  <g class="animated">
    <text class="lab-it" x="10" y="26" font-size="13" font-weight="bold">IT priorities</text>
    <text class="lab-ot" x="10" y="26" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>

    <g class="swap-c">
      <rect x="10" y="44" width="160" height="30" rx="4" fill="currentColor" opacity="0.15" stroke="currentColor"/>
      <text x="90" y="64" font-size="12" text-anchor="middle">Confidentiality</text>
    </g>
    <g>
      <rect x="180" y="44" width="160" height="30" rx="4" fill="currentColor" opacity="0.25" stroke="currentColor"/>
      <text x="260" y="64" font-size="12" text-anchor="middle">Integrity</text>
    </g>
    <g class="swap-a">
      <rect x="350" y="44" width="160" height="30" rx="4" fill="#ff6b00" opacity="0.85"/>
      <text x="430" y="64" font-size="12" text-anchor="middle" style="fill:#1a1a1a">Availability</text>
    </g>

    <text class="safety" x="10" y="100" font-size="11" fill="#ff6b00">
      and above all of them, safety: the process must not hurt anyone
    </text>
    <text x="10" y="124" font-size="11" opacity="0.8">
      Integrity does not move. What changes is which of the other two you sacrifice first.
    </text>
  </g>

  <g class="fallback" font-size="12">
    <text x="10" y="22" font-size="13" font-weight="bold">IT priorities</text>
    <rect x="10" y="30" width="160" height="26" rx="4" fill="#ff6b00" opacity="0.85"/>
    <text x="90" y="47" text-anchor="middle" style="fill:#1a1a1a">1. Confidentiality</text>
    <rect x="180" y="30" width="160" height="26" rx="4" fill="currentColor" opacity="0.25" stroke="currentColor"/>
    <text x="260" y="47" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="30" width="160" height="26" rx="4" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="430" y="47" text-anchor="middle">3. Availability</text>

    <text x="10" y="92" font-size="13" font-weight="bold">OT priorities</text>
    <rect x="10" y="100" width="160" height="26" rx="4" fill="#ff6b00" opacity="0.85"/>
    <text x="90" y="117" text-anchor="middle" style="fill:#1a1a1a">1. Safety &amp; Availability</text>
    <rect x="180" y="100" width="160" height="26" rx="4" fill="currentColor" opacity="0.25" stroke="currentColor"/>
    <text x="260" y="117" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="100" width="160" height="26" rx="4" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="430" y="117" text-anchor="middle">3. Confidentiality</text>
  </g>
</svg>
<figcaption>The same three goals, ordered differently. A stopped process can be dangerous as well as expensive, so in OT availability leads and confidentiality comes last &mdash; which is exactly why the protocols in the next few topics never bothered to encrypt anything.</figcaption>
</figure>

## The Purdue model

ICS networks are traditionally described with the **Purdue Enterprise Reference Architecture**, a layered model that separates the office from the plant floor. Each level talks mostly to its neighbours, and the security boundary that matters most sits between Level 3 and the enterprise above it &mdash; usually as an OT DMZ, so that no host in the office ever speaks directly to a controller.

<figure>
<style>
.pur {--u: 10s;}
/* The intruder walks down the levels. The boundary it crosses is the one the
   DMZ is supposed to occupy, so the crossing is the moment worth watching. */
.pur .walk {animation: u-walk var(--u) ease-in-out infinite;}
.pur .dmz  {animation: u-dmz  var(--u) linear infinite;}
.pur .note {opacity:0; animation: u-note var(--u) steps(1,end) infinite;}
@keyframes u-walk {0%,6%{transform:translateY(0)}      14%,22%{transform:translateY(0)}
                   30%,38%{transform:translateY(50px)}  46%,54%{transform:translateY(100px)}
                   62%,70%{transform:translateY(150px)} 78%,94%{transform:translateY(200px)}
                   100%{transform:translateY(0)}}
@keyframes u-dmz  {0%,24%{stroke-opacity:0.5; stroke-width:1.5}
                   26%,34%{stroke-opacity:1; stroke-width:3}
                   36%,100%{stroke-opacity:0.5; stroke-width:1.5}}
@keyframes u-note {0%,70%{opacity:0} 76%,96%{opacity:1} 96.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .pur .walk {animation:none; transform:translateY(200px);}
  .pur .dmz  {animation:none;}
  .pur .note {animation:none; opacity:1;}
}
</style>
<svg class="pur" viewBox="0 0 520 330" role="img"
     aria-label="The five Purdue levels from enterprise IT down to the physical process. An intruder starting at the enterprise level descends one level at a time to the process. The DMZ boundary it crosses sits between Level 3 and the enterprise; CybICS has no such boundary, only one flat network.">
  <g font-size="12">
    <rect x="70" y="10" width="440" height="40" rx="5" fill="currentColor" opacity="0.10" stroke="currentColor"/>
    <text x="82" y="35">Level 4/5 &mdash; Enterprise IT (ERP, email, internet)</text>
    <rect x="70" y="60" width="440" height="40" rx="5" fill="currentColor" opacity="0.14" stroke="currentColor"/>
    <text x="82" y="85">Level 3 &mdash; Operations (historian, engineering workstation)</text>
    <rect x="70" y="110" width="440" height="40" rx="5" fill="#ff6b00" opacity="0.30" stroke="#ff6b00"/>
    <text x="82" y="135">Level 2 &mdash; Supervisory (SCADA, HMI)</text>
    <rect x="70" y="160" width="440" height="40" rx="5" fill="#ff6b00" opacity="0.45" stroke="#ff6b00"/>
    <text x="82" y="185">Level 1 &mdash; Control (PLCs)</text>
    <rect x="70" y="210" width="440" height="40" rx="5" fill="#ff6b00" opacity="0.60" stroke="#ff6b00"/>
    <text x="82" y="235" style="fill:#1a1a1a">Level 0 &mdash; Process (sensors, actuators, valves)</text>
  </g>

  <line class="dmz" x1="70" y1="55" x2="510" y2="55" stroke="#ff6b00" stroke-dasharray="6 4"/>
  <text x="70" y="270" font-size="11" opacity="0.85">The IT/OT boundary belongs on the dashed line, between the enterprise and</text>
  <text x="70" y="286" font-size="11" opacity="0.85">everything that can reach a controller. An OT DMZ is how it is usually built.</text>

  <g class="walk">
    <circle cx="40" cy="30" r="10" fill="#ff6b00"/>
    <text x="40" y="34" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">!</text>
  </g>

  <text class="note" x="70" y="314" font-size="11" fill="#ff6b00" font-weight="bold">
    CybICS has no boundary at all: every service sits on one flat 172.18.0.0/24.
  </text>
</svg>
<figcaption>Five levels, and one intruder walking down all of them. The descent is the point: each step is a different protocol and a different topic in this path, and the only thing that would have stopped it is a boundary CybICS deliberately does not have.</figcaption>
</figure>

## Where CybICS fits

CybICS is a small but complete ICS, and every component sits on the same bridge network, `172.18.0.0/24`. That is not an oversight &mdash; it is what makes the attacks in the later modules reachable from a single machine.

| Purdue level | CybICS component | Address |
|---|---|---|
| Level 4/5 (Enterprise) | Attack machine, standing in for any compromised office host | 172.18.0.100 |
| Level 3 (Operations) | Engineering workstation | 172.18.0.10 |
| Level 2 (Supervisory) | FUXA HMI; OPC-UA and S7comm servers alongside it | 172.18.0.4, .5, .6 |
| Level 1 (Control) | OpenPLC runtime executing the plant program | 172.18.0.3 |
| Level 0 (Process) | `hwio`, the bridge to the gas pressure process | 172.18.0.2 |

On real hardware, Level 0 is not a container at all: the STM32 on the CybICS board runs the process, and `hwio` talks to it over I&sup2;C.

## The process you are actually protecting

Everything above exists to run one small plant. Gas is pumped from a storage tank (**GST**) into a high pressure tank (**HPT**), and the downstream process draws from the HPT while the system valve is open. Both tank readings are a single byte, 0 to 255.

<figure>
<style>
.plt {--t: 14s;}
.plt .lvl {transform-origin: center bottom;}
.plt .gst {animation: t-gst var(--t) linear infinite;}
.plt .hpt {animation: t-hpt var(--t) linear infinite;}
.plt .comp{animation: t-comp var(--t) steps(1,end) infinite;}
.plt .vent{opacity:0; animation: t-vent var(--t) steps(1,end) infinite;}
.plt .bo  {opacity:0; animation: t-vent var(--t) steps(1,end) infinite;}
/* Two units of GST buy one unit of HPT, so the left tank empties twice as
   fast as the right one fills -- the ratio is the plant's, not decoration. */
@keyframes t-gst {0%{transform:scaleY(0.98)} 72%{transform:scaleY(0.20)}
                  86%{transform:scaleY(0.20)} 100%{transform:scaleY(0.98)}}
@keyframes t-hpt {0%{transform:scaleY(0.24)} 72%{transform:scaleY(0.88)}
                  86%{transform:scaleY(0.79)} 100%{transform:scaleY(0.24)}}
@keyframes t-comp{0%,84%{fill:#ff6b00} 84.01%,100%{fill:currentColor}}
@keyframes t-vent{0%,69%{opacity:0} 70%,86%{opacity:1} 86.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .plt .gst {animation:none; transform:scaleY(0.20);}
  .plt .hpt {animation:none; transform:scaleY(0.88);}
  .plt .comp{animation:none; fill:#ff6b00;}
  .plt .vent,.plt .bo {animation:none; opacity:1;}
}
</style>
<svg class="plt" viewBox="0 0 520 250" role="img"
     aria-label="The CybICS plant. A compressor moves gas from the storage tank into the high pressure tank, taking two units from one to add one to the other. Above 220 the blow-out valve opens and vents until the pressure falls back below 200. The system reports healthy only while the high pressure tank sits between 50 and 100 with the valve open.">
  <!-- storage tank -->
  <rect x="40" y="60" width="60" height="140" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl gst" x="42" y="62" width="56" height="136" fill="currentColor" opacity="0.35"/>
  <text x="70" y="52" text-anchor="middle" font-size="12" font-weight="bold">GST</text>
  <text x="70" y="218" text-anchor="middle" font-size="11" opacity="0.8">storage</text>

  <!-- compressor -->
  <rect class="comp" x="160" y="110" width="90" height="40" rx="5" opacity="0.8"/>
  <text x="205" y="135" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">compressor</text>
  <path d="M 104 130 L 156 130" stroke="currentColor" stroke-width="2"/>
  <path d="M 254 130 L 306 130" stroke="currentColor" stroke-width="2"/>
  <text x="205" y="168" text-anchor="middle" font-size="11" opacity="0.85">&minus;2 GST &rarr; +1 HPT per tick</text>

  <!-- high pressure tank -->
  <rect x="310" y="60" width="60" height="140" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl hpt" x="312" y="62" width="56" height="136" fill="#ff6b00" opacity="0.55"/>
  <text x="340" y="52" text-anchor="middle" font-size="12" font-weight="bold">HPT</text>
  <text x="340" y="218" text-anchor="middle" font-size="11" opacity="0.8">high pressure</text>

  <!-- thresholds, placed at their real values on a 0-255 scale -->
  <line x1="306" y1="81" x2="404" y2="81" stroke="#ff6b00" stroke-dasharray="4 3"/>
  <text x="408" y="85" font-size="11" fill="#ff6b00">220 blow-out opens</text>
  <line x1="306" y1="91" x2="374" y2="91" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
  <text x="408" y="99" font-size="11" opacity="0.75">200 closes again</text>
  <rect x="306" y="145" width="68" height="27" fill="currentColor" opacity="0.12"/>
  <text x="408" y="165" font-size="11" opacity="0.85">50&ndash;100 healthy band</text>

  <!-- venting -->
  <g class="vent">
    <path d="M 340 60 L 340 30" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 334 38 L 340 28 L 346 38" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="356" y="34" font-size="11" fill="#ff6b00" font-weight="bold">venting</text>
  </g>
  <text class="bo" x="40" y="244" font-size="11" fill="#ff6b00" font-weight="bold">
    The relief valve vents more slowly than the compressor fills. A compressor stuck on wins.
  </text>
  <text x="40" y="20" font-size="11" opacity="0.8">Both readings are one byte: 0 to 255.</text>
</svg>
<figcaption>The plant, at the rates it actually runs. A mechanical relief valve opens above 220 and stays open until the pressure falls back under 200 &mdash; but it vents at most one unit per tick while the compressor adds one every tick, so holding the compressor on is enough to drive the tank somewhere the safety device cannot recover it. That is the <em>Physical Process</em> challenge, and it is why the last line of defence here is mechanical, not digital.</figcaption>
</figure>

## Why it matters for security

Because these systems were built for reliability, not for hostile networks, most ICS protocols have **no authentication and no encryption**. Any host that can reach a PLC can usually read and write its values. The rest of the Theory Path shows exactly how each protocol works, how that trust is abused, and how to detect and contain it.

> **Key idea:** in ICS security you are protecting a physical process. Every attack in the later modules ends in a real-world effect &mdash; a frozen reading, a forced valve, a tank driven past the pressure its relief valve can bleed off.
