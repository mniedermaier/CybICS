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
.pri .fallback {display:none;}
@keyframes p-right {0%,25%{transform:translateX(0)} 38%,88%{transform:translateX(340px)}
                    100%{transform:translateX(0)}}
@keyframes p-left  {0%,25%{transform:translateX(0)} 38%,88%{transform:translateX(-340px)}
                    100%{transform:translateX(0)}}
@keyframes p-it {0%,31%{opacity:1} 31.01%,94%{opacity:0} 94.01%,100%{opacity:1}}
@keyframes p-ot {0%,31%{opacity:0} 31.01%,94%{opacity:1} 94.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .pri .animated {display:none;}
  .pri .fallback {display:block;}
}
</style>
<svg class="pri" viewBox="0 0 520 150" role="img"
     aria-label="The same three security goals in two orders. IT ranks them confidentiality, integrity, availability. OT reverses the outer two: safety and availability first, confidentiality last.">
  <g class="animated">
    <g font-size="11" opacity="0.7" text-anchor="middle">
      <text x="90" y="40">most important</text><text x="430" y="40">least important</text>
    </g>
    <text class="lab-it" x="10" y="26" font-size="13" font-weight="bold">IT priorities</text>
    <text class="lab-ot" x="10" y="26" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>

    <text x="20" y="66" font-size="12" font-weight="bold" opacity="0.65">1.</text>
    <g class="swap-c">
      <rect x="34" y="44" width="136" height="30" rx="4" fill="currentColor" opacity="0.15" stroke="currentColor"/>
      <text x="102" y="64" font-size="12" text-anchor="middle">Confidentiality</text>
    </g>
    <text x="360" y="66" font-size="12" font-weight="bold" opacity="0.65">3.</text>
    <g class="swap-a">
      <rect x="374" y="44" width="136" height="30" rx="4" fill="#ff6b00" opacity="0.85"/>
      <text x="442" y="64" font-size="12" text-anchor="middle" style="fill:#1a1a1a">Availability</text>
    </g>
    <text x="190" y="66" font-size="12" font-weight="bold" opacity="0.65">2.</text>
    <g>
      <rect x="204" y="44" width="136" height="30" rx="4" fill="currentColor" opacity="0.25" stroke="currentColor"/>
      <text x="272" y="64" font-size="12" text-anchor="middle">Integrity</text>
    </g>

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
<figcaption>Integrity does not move. What changes is which of the other two you give up first &mdash; and above both of them sits safety, because the process must not hurt anyone. A stopped process can be dangerous as well as expensive, so in OT availability leads and confidentiality comes last. That ordering explains what gets fixed first when something breaks; it does not explain why Modbus has no encryption. That has a simpler cause, and the next topic gets to it.</figcaption>
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
<svg class="pur" viewBox="0 0 520 340" role="img"
     aria-label="The five Purdue levels from enterprise IT down to the physical process. An intruder starting at the enterprise level descends one level at a time to the process. The DMZ boundary it crosses sits between Level 3 and the enterprise; CybICS has no such boundary: the plant components share one flat network, and the IDS watches from the host.">
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

  <g class="note" font-size="11" fill="#ff6b00" font-weight="bold">
    <text x="70" y="308">CybICS has no boundary at all: one flat 172.18.0.0/24,</text>
    <text x="70" y="324">with the IDS watching it from the host itself.</text>
  </g>
</svg>
<figcaption>Five levels, and one intruder walking down all of them. The descent is the point: each step is a different protocol and a different topic in this path, and the only thing that would have stopped it is a boundary CybICS deliberately does not have.</figcaption>
</figure>

## Where CybICS fits

CybICS is a small but complete ICS, and every simulated plant component sits on the same bridge network, `172.18.0.0/24`, with nothing between them. That is not an oversight &mdash; it is what makes the attacks in the later modules reachable from a single machine. Two services are deliberately outside it: the landing page and the IDS run on the *host* network, which is how the IDS gets to see traffic between containers it is not a party to.

| Purdue level | CybICS component | Address |
|---|---|---|
| Level 4/5 (Enterprise) | Attack machine, standing in for any compromised office host | 172.18.0.100 |
| Level 3 (Operations) | Engineering workstation | 172.18.0.10 |
| Level 2 (Supervisory) | FUXA HMI; OPC-UA and S7comm servers alongside it | 172.18.0.4, .5, .6 |
| Level 1 (Control) | OpenPLC runtime executing the plant program | 172.18.0.3 |
| Level 0 (Process) | `hwio`, which runs the gas pressure simulation and writes its readings into the PLC | 172.18.0.2 |

On real hardware, Level 0 is not a container at all: the STM32 on the CybICS board runs the process, and `hwio` becomes a genuine bridge, talking to it over I&sup2;C at address 0x20.

## The process you are actually protecting

Everything above exists to run one small plant. A compressor pumps gas from a storage tank (**GST**) into a high pressure tank (**HPT**), and the downstream process draws from the HPT while the system valve is open. Both readings are a single byte, 0 to 255, and OpenPLC is the thing that decides: it reads the HPT pressure out of register 1126 and drives the compressor on coil 1. That loop &mdash; sensor, controller, actuator, process, sensor again &mdash; is what makes this a *control* system rather than a machine.

Left alone, the loop is dull on purpose. OpenPLC starts the compressor when the HPT falls below 60 and stops it at 90, so the pressure saws gently between the two, comfortably inside the 50-to-100 band in which the plant reports itself healthy. Nothing ever goes near the relief valve.

<figure>
<style>
.plt {--t: 18s;}
.plt .lvl {transform-origin: center bottom;}
.plt .gst {animation: t-gst var(--t) linear infinite;}
.plt .hpt {animation: t-hpt var(--t) linear infinite;}
.plt .comp{animation: t-comp var(--t) steps(1,end) infinite;}
.plt .vent{opacity:0; animation: t-vent var(--t) steps(1,end) infinite;}
.plt .atk {opacity:0; animation: t-atk  var(--t) steps(1,end) infinite;}
.plt .sup {opacity:0.25; animation: t-sup var(--t) steps(1,end) infinite;}
.plt .ph-n{animation: t-phn var(--t) steps(1,end) infinite;}
.plt .ph-a{opacity:0; animation: t-atk var(--t) steps(1,end) infinite;}
/* Every segment obeys the plant model: two units of GST buy one of HPT, and
   the HPT can only fall while the compressor is off. The tank is never drawn
   falling under a running compressor, because the model cannot do that. */
@keyframes t-hpt {0%{transform:scaleY(0.235)}  15%{transform:scaleY(0.353)}
                  30%{transform:scaleY(0.235)} 36%{transform:scaleY(0.294)}
                  60%{transform:scaleY(0.471)} 78%{transform:scaleY(0.863)}
                  86%,92%{transform:scaleY(0.878)} 100%{transform:scaleY(0.235)}}
@keyframes t-gst {0%{transform:scaleY(0.941)}  15%,30%{transform:scaleY(0.706)}
                  36%{transform:scaleY(0.588)} 60%{transform:scaleY(0.235)}
                  78%{transform:scaleY(0.204)} 92%{transform:scaleY(0.196)}
                  100%{transform:scaleY(0.941)}}
@keyframes t-comp{0%,15%{fill:#ff6b00} 15.01%,30%{fill:currentColor}
                  30.01%,92%{fill:#ff6b00} 92.01%,100%{fill:currentColor}}
@keyframes t-vent{0%,77.9%{opacity:0} 78%,93%{opacity:1} 93.01%,100%{opacity:0}}
@keyframes t-atk {0%,35.9%{opacity:0} 36%,92%{opacity:1} 92.01%,100%{opacity:0}}
@keyframes t-sup {0%,59.9%{opacity:0.25} 60%,100%{opacity:1}}
@keyframes t-phn {0%,35.9%{opacity:1} 36%,92%{opacity:0} 92.01%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) {
  .plt .gst {animation:none; transform:scaleY(0.204);}
  .plt .hpt {animation:none; transform:scaleY(0.878);}
  .plt .comp{animation:none; fill:#ff6b00;}
  .plt .vent,.plt .atk,.plt .ph-a {animation:none; opacity:1;}
  .plt .sup {animation:none; opacity:1;}
  .plt .ph-n{animation:none; opacity:0;}
}
</style>
<svg class="plt" viewBox="0 0 520 300" role="img"
     aria-label="The CybICS control loop. OpenPLC reads the high pressure tank from register 1126 and drives the compressor on coil 1. Normally the pressure saws between 60 and 90. When an attacker holds the compressor on, the storage tank drains two units for every one gained, the external supply valve opens to keep feeding it, and the pressure climbs past 220 where the relief valve opens but cannot bring it back.">
  <!-- storage tank; fill is 126 units tall with its base at y=188, so a value
       v sits at y = 188 - 126*v/255 -->
  <rect x="40" y="60" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl gst" x="42" y="62" width="52" height="126" fill="currentColor" opacity="0.35"/>
  <text x="68" y="52" text-anchor="middle" font-size="12" font-weight="bold">GST</text>
  <text x="68" y="206" text-anchor="middle" font-size="11" opacity="0.8">storage</text>
  <g class="sup">
    <path d="M 68 60 L 68 34" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 62 42 L 68 32 L 74 42" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="68" y="26" text-anchor="middle" font-size="11" fill="#ff6b00">supply</text>
  </g>

  <!-- compressor -->
  <rect class="comp" x="150" y="105" width="90" height="40" rx="5" opacity="0.8"/>
  <text x="195" y="130" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">compressor</text>
  <path d="M 100 125 L 146 125" stroke="currentColor" stroke-width="2"/>
  <path d="M 244 125 L 296 125" stroke="currentColor" stroke-width="2"/>
  <text x="195" y="164" text-anchor="middle" font-size="11" opacity="0.85">&minus;2 GST &rarr; +1 HPT</text>
  <g class="atk">
    <rect x="148" y="80" width="94" height="20" rx="3" fill="#ff6b00"/>
    <text x="195" y="94" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">coil 1 forced on</text>
  </g>

  <!-- high pressure tank -->
  <rect x="300" y="60" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl hpt" x="302" y="62" width="52" height="126" fill="#ff6b00" opacity="0.55"/>
  <text x="328" y="52" text-anchor="middle" font-size="12" font-weight="bold">HPT</text>
  <text x="328" y="206" text-anchor="middle" font-size="11" opacity="0.8">high pressure</text>
  <g font-size="11">
    <line x1="296" y1="79" x2="360" y2="79" stroke="#ff6b00" stroke-dasharray="4 3"/>
    <text x="364" y="83" fill="#ff6b00">220</text>
    <line x1="296" y1="89" x2="360" y2="89" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
    <text x="364" y="93" opacity="0.75">200</text>
    <line x1="296" y1="143" x2="360" y2="143" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
    <text x="364" y="147" opacity="0.75">90</text>
    <line x1="296" y1="158" x2="360" y2="158" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
    <text x="364" y="162" opacity="0.75">60</text>
  </g>
  <g class="vent">
    <path d="M 328 60 L 328 34" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 322 42 L 328 32 L 334 42" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="340" y="30" font-size="11" fill="#ff6b00" font-weight="bold">venting</text>
  </g>

  <!-- the controller, and the two wires that make this a loop -->
  <rect x="170" y="232" width="160" height="44" rx="5" fill="currentColor" opacity="0.15" stroke="currentColor"/>
  <text x="250" y="252" text-anchor="middle" font-size="12" font-weight="bold">OpenPLC</text>
  <text x="250" y="268" text-anchor="middle" font-size="11" opacity="0.8">on below 60, off at 90</text>
  <path d="M 392 190 L 392 254 L 336 254" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 344 248 L 334 254 L 344 260" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 356 190 L 392 190" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="398" y="218" font-size="11" opacity="0.8">reads 1126</text>
  <path d="M 170 254 L 126 254 L 126 125 L 144 125" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 136 119 L 146 125 L 136 131" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="120" y="218" font-size="11" opacity="0.8" text-anchor="end">drives coil 1</text>

  <text class="ph-n" x="10" y="292" font-size="11" opacity="0.85">normal operation</text>
  <text class="ph-a" x="10" y="292" font-size="11" fill="#ff6b00" font-weight="bold">under attack</text>
  <text x="510" y="292" font-size="11" opacity="0.7" text-anchor="end">both tanks read 0 to 255</text>
</svg>
<figcaption>The same loop twice: first doing its job, then with coil 1 held on from outside. Watch the storage tank during the attack &mdash; it gives up two units for every one the high pressure tank gains, and would stall long before 220 if nothing refilled it. The external supply valve is what keeps the attack fed.</figcaption>
</figure>

The attack is the second half of that loop, and it is worth being precise about why it succeeds. A mechanical relief valve opens above 220 and stays open until the pressure falls back under 200, but it can bleed off at most one unit per tick while the compressor adds one every tick. It cannot win while the compressor runs; it can only stop things getting worse. Nothing here is a digital protection that an attacker disables &mdash; the last line of defence is a spring, and the attacker simply out-paces it.

The storage tank is the other half of the answer. Draining two units per unit gained, a full tank buys about 90 units of pressure and no more, which from the normal band would stop short of 220. What closes the gap is the external supply: OpenPLC opens it whenever the storage tank falls below 60, so the tank hovers just above the level at which the compressor would stall, and the pressure keeps creeping up. That is the *Physical Process* challenge, and the interesting part of it is that every component involved is behaving exactly as designed.

## Why it matters for security

Because these systems were built for reliability, not for hostile networks, most ICS protocols have **no authentication and no encryption**. Any host that can reach a PLC can usually read and write its values. The rest of the Theory Path shows exactly how each protocol works, how that trust is abused, and how to detect and contain it.

> **Key idea:** in ICS security you are protecting a physical process. Every attack in the later modules ends in a real-world effect &mdash; a frozen reading, a forced valve, a tank driven past the pressure its relief valve can bleed off.
