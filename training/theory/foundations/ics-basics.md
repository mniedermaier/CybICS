# What is an Industrial Control System?

Somewhere near you, a computer is deciding when a pump starts, how far a valve opens, or how much pressure a pipe can take. Those computers are **Industrial Control Systems (ICS)**, and when they go wrong, the result is not a lost file but a flooded street or a burst tank. This first lesson explains what an ICS is, how its parts are arranged, and why protecting one is different from protecting an office network.

## A computer that moves things

An **Industrial Control System (ICS)** is the hardware and software that watches and steers a physical process: a gas plant, a water works, a power grid, a bottling line. The umbrella term for all of this technology is **Operational Technology (OT)**, as opposed to the **Information Technology (IT)** you know from laptops, servers and email.

The difference is what a mistake does. In IT, a wrong value corrupts a spreadsheet. In OT, a wrong value opens a valve, and the valve does not care whether the command came from the operator or from an attacker.

<div class="callout analogy" markdown="1">
**Analogy:** think of the thermostat at home. A sensor measures the temperature, a small controller compares it with your setting, and it switches the heating on or off. An ICS is the same idea, scaled up to tanks, turbines and pipelines, and connected to a network.
</div>

## Why OT puts safety and availability first

Security people often describe their goals with three words:

- **Confidentiality:** only the right people can read the data.
- **Integrity:** nobody can change the data without permission.
- **Availability:** the system works when you need it.

In IT, confidentiality usually comes first: a leaked customer database is the classic disaster. In OT the order flips. A plant that stops can be more dangerous than one running badly, so **availability** leads. Above all three sits **safety**: the process must never hurt people or the environment.

<figure class="wide">
<style>
/* The inversion is a reordering, so the figure reorders: the two outer goals
   trade places. Orange marks rank 1 and nothing else. The static two-row
   version is the default, so a browser without animation still sees both. */
.pri {--p: 12s;}
.pri .swap-c {animation: p-right var(--p) ease-in-out infinite;}
.pri .swap-a {animation: p-left  var(--p) ease-in-out infinite;}
.pri .lab-it {animation: p-it    var(--p) steps(1,end) infinite;}
.pri .lab-ot {opacity:0; animation: p-ot var(--p) steps(1,end) infinite;}
.pri {display:none;}
.pri-static {display:block;}
@media (prefers-reduced-motion: no-preference) {
  .pri {display:block;}
  .pri-static {display:none;}
}
@keyframes p-right {0%,25%{transform:translate(0,0)} 27%{transform:translate(16px,38px)}
                    36%{transform:translate(324px,38px)} 38%,88%{transform:translate(340px,0)}
                    90%{transform:translate(324px,38px)} 98%{transform:translate(16px,38px)}
                    100%{transform:translate(0,0)}}
@keyframes p-left  {0%,25%{transform:translate(0,0)} 27%{transform:translate(-16px,76px)}
                    36%{transform:translate(-324px,76px)} 38%,88%{transform:translate(-340px,0)}
                    90%{transform:translate(-324px,76px)} 98%{transform:translate(-16px,76px)}
                    100%{transform:translate(0,0)}}
@keyframes p-it {0%,31%{opacity:1} 31.01%,94%{opacity:0} 94.01%,100%{opacity:1}}
@keyframes p-ot {0%,31%{opacity:0} 31.01%,94%{opacity:1} 94.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .pri {display:none;}
  .pri-static {display:block;}
}
</style>
<svg class="pri" viewBox="0 0 520 166" role="img"
     aria-label="The same three security goals in one row, ordered most important on the left. IT ranks them confidentiality, integrity, availability; OT swaps the outer two, so availability leads and confidentiality comes last.">
  <text class="lab-it" x="10" y="20" font-size="13" font-weight="bold">IT priorities</text>
  <text class="lab-ot" x="10" y="20" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>

  <text x="20" y="60" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
  <text x="190" y="60" font-size="12" font-weight="bold" opacity="0.78">2.</text>
  <text x="360" y="60" font-size="12" font-weight="bold" opacity="0.78">3.</text>

  <g class="swap-c">
    <rect x="34" y="38" width="136" height="30" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="102" y="58" font-size="12" text-anchor="middle">Confidentiality</text>
  </g>
  <g class="swap-a">
    <rect x="374" y="38" width="136" height="30" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="442" y="58" font-size="12" text-anchor="middle">Availability</text>
  </g>
  <g>
    <rect x="204" y="38" width="136" height="30" rx="4" fill="currentColor" fill-opacity="0.28" stroke="currentColor"/>
    <text x="272" y="58" font-size="12" text-anchor="middle">Integrity</text>
  </g>
  <text x="102" y="160" font-size="13" opacity="0.7" text-anchor="middle">most important</text>
  <text x="442" y="160" font-size="13" opacity="0.7" text-anchor="middle">least important</text>
</svg>
<svg class="pri-static" viewBox="0 0 520 134" role="img"
     aria-label="IT ranks the three goals confidentiality, integrity, availability. OT reverses the outer two: availability first, integrity second, confidentiality last.">
  <g font-size="12">
    <text x="10" y="20" font-size="13" font-weight="bold">IT priorities</text>
    <text x="4" y="45" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
    <rect x="22" y="28" width="148" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="96" y="45" text-anchor="middle">Confidentiality</text>
    <rect x="180" y="28" width="160" height="26" rx="4" fill="currentColor" fill-opacity="0.28" stroke="currentColor"/>
    <text x="260" y="45" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="28" width="160" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="430" y="45" text-anchor="middle">3. Availability</text>

    <text x="10" y="86" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>
    <text x="4" y="111" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
    <rect x="22" y="94" width="148" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="96" y="111" text-anchor="middle">Availability</text>
    <rect x="180" y="94" width="160" height="26" rx="4" fill="currentColor" fill-opacity="0.28" stroke="currentColor"/>
    <text x="260" y="111" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="94" width="160" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="430" y="111" text-anchor="middle">3. Confidentiality</text>
  </g>
</svg>
<figcaption>Integrity stays in the middle. What changes is which of the other two you give up first. Above both of them sits safety, because the process must not hurt anyone.</figcaption>
</figure>

This has practical consequences. A control system often runs for twenty or thirty years. It may never get a window in which it can be stopped and patched. A security tool that slows down the network, or locks out an operator after three wrong passwords, can itself become the hazard. OT security is the art of protecting a process without getting in its way.

<div data-widget="checkpoint" data-id="priorities"></div>

## The Purdue model: floors of a building

Real plants are big, so engineers describe their networks in layers. The usual picture is the **Purdue model** (Purdue Enterprise Reference Architecture), named after the university where it was drawn up. Think of it as a building: the offices are on the top floors and the machines are in the basement.

| Level | Name | What lives there |
|---|---|---|
| 4/5 | Enterprise | Office PCs, email, business systems |
| 3 | Operations | Engineering workstations, historians, plant-wide servers |
| 2 | Supervisory | Screens for operators (HMIs) and the systems that collect plant data |
| 1 | Control | The controllers (PLCs) that run the control logic |
| 0 | Process | Sensors, valves, pumps, motors: the physical plant |

Each level should mostly talk to its neighbours. The most important wall sits between the office (Level 4/5) and everything below it, usually built as an **OT DMZ**: a small buffer network so that no office PC ever talks directly to a controller.

<figure class="wide">
<style>
/* The intruder walks down the levels; the boundary it crosses is the one a
   DMZ should occupy. */
.pur {--u: 10s;}
.pur .walk {animation: u-walk var(--u) ease-in-out infinite;}
.pur .dmz  {animation: u-dmz  var(--u) linear infinite;}
.pur:where(.light-mode *) .intr {fill:#b34700;}
.pur:where(.light-mode *) .intr-t {fill:#ffffff !important;}
@keyframes u-walk {0%,6%{transform:translateY(0)}      14%,22%{transform:translateY(0)}
                   30%,38%{transform:translateY(50px)}  46%,54%{transform:translateY(100px)}
                   62%,70%{transform:translateY(150px)} 78%,94%{transform:translateY(200px)}
                   100%{transform:translateY(0)}}
@keyframes u-dmz  {0%,24%{stroke-opacity:0.75; stroke-width:2}
                   26%,34%{stroke-opacity:1; stroke-width:3}
                   36%,100%{stroke-opacity:0.75; stroke-width:2}}
@media (prefers-reduced-motion: reduce) {
  .pur .walk {animation:none; transform:translateY(200px);}
  .pur .dmz  {animation:none;}
}
</style>
<svg class="pur" viewBox="0 0 520 266" role="img"
     aria-label="The five Purdue levels from enterprise IT down to the physical process. An intruder starting at the enterprise level descends one level at a time to the process. The dashed DMZ boundary it crosses sits between Level 3 and the enterprise.">
  <g font-size="14">
    <rect x="70" y="10" width="440" height="40" rx="5" fill="currentColor" fill-opacity="0.10" stroke="currentColor"/>
    <text x="82" y="35">Level 4/5 &mdash; Enterprise IT</text>
    <rect x="70" y="60" width="440" height="40" rx="5" fill="currentColor" fill-opacity="0.14" stroke="currentColor"/>
    <text x="82" y="85">Level 3 &mdash; Operations</text>
    <rect x="70" y="110" width="440" height="40" rx="5" fill="#ff6b00" fill-opacity="0.30" stroke="#ff6b00"/>
    <text x="82" y="135">Level 2 &mdash; Supervisory (SCADA, HMI)</text>
    <rect x="70" y="160" width="440" height="40" rx="5" fill="#ff6b00" fill-opacity="0.45" stroke="#ff6b00"/>
    <text x="82" y="185">Level 1 &mdash; Control (PLCs)</text>
    <rect x="70" y="210" width="440" height="40" rx="5" fill="#ff6b00" stroke="#ff6b00"/>
    <text x="82" y="235" style="fill:#1a1a1a">Level 0 &mdash; Process (sensors, valves)</text>
  </g>

  <line class="dmz" x1="70" y1="55" x2="510" y2="55" stroke="#ff6b00" stroke-dasharray="6 4"/>

  <g class="walk">
    <circle class="intr" cx="40" cy="30" r="10" fill="#ff6b00"/>
    <text class="intr-t" x="40" y="34" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">!</text>
  </g>
</svg>
<figcaption>The dashed line is where the IT/OT boundary belongs, usually built as an OT DMZ. An intruder who starts in the office has to walk down every level to reach the process. Each step is a different service and a different lesson in this path. CybICS deliberately leaves the wall out, so you can practise every step from one machine.</figcaption>
</figure>

### Where CybICS fits

CybICS is a small but complete ICS. Every plant container sits on one Docker network, `172.18.0.0/24`, with no walls between them. That is a teaching choice: it lets you reach every target from the attack machine. Click a host below to see its address, its ports and the attacks that target it.

<div data-widget="purdue-explorer"></div>

| Purdue level | CybICS component | Address |
|---|---|---|
| 4/5 Enterprise | Attack machine, standing in for a compromised office PC | 172.18.0.100 |
| 3 Operations | Engineering workstation | 172.18.0.10 |
| 2 Supervisory | FUXA HMI and the OPC-UA server | 172.18.0.4, .5 |
| 1 Control | OpenPLC, running the plant program, and the S7comm server, which plays a Siemens PLC | 172.18.0.3, .6 |
| 0 Process | `hwio`, which simulates the gas plant | 172.18.0.2 |

The landing page and the Intrusion Detection System (IDS) run on the host's own network instead, which lets the IDS see traffic between the containers.

## The CybICS gas plant

All of this exists to run one small plant. It has five parts you will meet again and again:

- **Gas storage tank (GST):** the supply. An external refill valve tops it up.
- **Compressor:** pumps gas from the GST into the high-pressure tank.
- **High-pressure tank (HPT):** the tank that matters. Its pressure is the number everyone watches.
- **System valve:** lets the downstream process draw gas from the HPT.
- **Blow-out valve:** a relief valve that opens when the HPT pressure gets dangerously high.

Each reading is a single byte, from 0 to 255. The controller, OpenPLC, reads the HPT pressure and switches the compressor. It starts the compressor when the pressure drops below 60 and stops it at 90. It opens the system valve while the pressure is between 50 and 100, the band in which the plant reports itself healthy.

That cycle of **sensor, controller, actuator, process, sensor again** is the **control loop**. It is what makes this a *control* system rather than just a machine. You will see exactly how the controller makes its decisions in [PLCs and the scan cycle](/theory/plc-fundamentals).

<figure class="wide">
<style>
.plt {--t: 20s; --on:#ff6b00; --on-ink:#1a1a1a;}
.plt:where(.light-mode *) {--on:#b34700; --on-ink:#ffffff;}
.plt:where(.light-mode *) .hpt {fill:#b34700;}
.plt:where(.light-mode *) .gst {opacity:0.55;}
/* fill-box anchors the scale on each fill's own bottom edge. */
.plt .lvl {transform-box: fill-box; transform-origin: bottom;}
.plt .gst {transform: scaleY(0.941);}
.plt .hpt {transform: scaleY(0.235);}
.plt .compt {fill:var(--on-ink);}
.plt .gst {animation: t-gst var(--t) linear infinite;}
.plt .hpt {animation: t-hpt var(--t) linear infinite;}
.plt .comp{fill:var(--on); animation: t-comp var(--t) steps(1,end) infinite;}
.plt .compt{animation: t-compt var(--t) steps(1,end) infinite;}
.plt .vent{opacity:0; animation: t-vent var(--t) steps(1,end) infinite;}
.plt .man {opacity:0; animation: t-hold var(--t) steps(1,end) infinite;}
.plt .sup {opacity:0; animation: t-man  var(--t) steps(1,end) infinite;}
.plt .ph-n{animation: t-phn var(--t) steps(1,end) infinite;}
.plt .ph-a{opacity:0; animation: t-man var(--t) steps(1,end) infinite;}
.plt .lbl200{animation: t-n200 var(--t) steps(1,end) infinite;}
.plt .stuck{opacity:0; animation: t-stuck var(--t) steps(1,end) infinite;}
.plt .rst  {opacity:0; animation: t-rst   var(--t) steps(1,end) infinite;}
.plt .sv-open{animation: t-phn var(--t) steps(1,end) infinite;}
.plt .sv-shut{opacity:0; animation: t-man var(--t) steps(1,end) infinite;}
/* Timings come from one chained run of physical_process_thread: automatic
   60-90 twice, then manual with the valve shut, venting above 220, settling
   at 200 while the supply refills the GST. */
@keyframes t-hpt {0%{transform:scaleY(0.235)}     5.90%{transform:scaleY(0.353)}
                  11.84%{transform:scaleY(0.235)} 14.85%{transform:scaleY(0.294)}
                  43.78%{transform:scaleY(0.867)} 61.98%,63.94%{transform:scaleY(1)}
                  85.31%,100%{transform:scaleY(0.784)}}
@keyframes t-gst {0%{transform:scaleY(0.941)}     5.90%,11.84%{transform:scaleY(0.706)}
                  14.85%{transform:scaleY(0.588)} 43.78%{transform:scaleY(0.298)}
                  61.98%{transform:scaleY(0.212)} 63.94%{transform:scaleY(0.236)}
                  85.31%{transform:scaleY(0.871)} 89.19%,100%{transform:scaleY(0.984)}}
@keyframes t-comp {0%,5.90%{fill:var(--on); fill-opacity:1}
                   5.91%,11.84%{fill:currentColor; fill-opacity:0.18}
                   11.85%,63.94%{fill:var(--on); fill-opacity:1}
                   63.95%,100%{fill:currentColor; fill-opacity:0.18}}
@keyframes t-compt{0%,5.90%{fill:var(--on-ink)} 5.91%,11.84%{fill:currentColor}
                   11.85%,63.94%{fill:var(--on-ink)} 63.95%,100%{fill:currentColor}}
@keyframes t-vent {0%,43.77%{opacity:0} 43.78%,85.31%{opacity:1} 85.32%,100%{opacity:0}}
@keyframes t-man  {0%,14.84%{opacity:0} 14.85%,100%{opacity:1}}
@keyframes t-hold {0%,14.84%{opacity:0} 14.85%,63.94%{opacity:1} 63.95%,100%{opacity:0}}
@keyframes t-phn  {0%,14.84%{opacity:1} 14.85%,100%{opacity:0}}
@keyframes t-stuck{0%,85.30%{opacity:0} 85.31%,100%{opacity:1}}
@keyframes t-n200 {0%,85.30%{opacity:0.75} 85.31%,100%{opacity:0}}
@keyframes t-rst  {0%,97.49%{opacity:0} 97.50%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) {
  /* The frozen frame is the end state: compressor stopped, valve shut, the
     pressure resting at 200 and the storage tank refilled. */
  .plt .gst {animation:none; transform:scaleY(0.984);}
  .plt .hpt {animation:none; transform:scaleY(0.784);}
  .plt .comp {animation:none; fill:currentColor; fill-opacity:0.18;}
  .plt .compt {animation:none; fill:currentColor;}
  .plt .sup,.plt .ph-a,.plt .stuck,.plt .sv-shut {animation:none; opacity:1;}
  .plt .lbl200 {animation:none; opacity:0;}
  .plt .rst {animation:none; opacity:0;}
  .plt .sv-open{animation:none; opacity:0;}
  .plt .man {animation:none; opacity:0;}
  .plt .vent{animation:none; opacity:0;}
  .plt .ph-n{animation:none; opacity:0;}
}
</style>
<svg class="plt" viewBox="0 0 460 320" role="img"
     aria-label="The CybICS control loop. OpenPLC reads the high pressure tank from register 1126 and drives the compressor on coil 1, holding the pressure between 60 and 90 while the system valve lets the downstream process draw from it. Then an operator in manual mode shuts the system valve and keeps the compressor running; the pressure climbs past 220 and the relief valve opens, which only slows the rise. When the compressor finally stops, the pressure settles at 200 and stays there, because the shut valve leaves no consumer.">
  <rect x="24" y="70" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl gst" x="26" y="72" width="52" height="126" fill="currentColor" opacity="0.6"/>
  <text x="52" y="216" text-anchor="middle" font-size="13" font-weight="bold">GST</text>
  <g class="sup">
    <path d="M 52 36 L 52 62" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 46 54 L 52 64 L 58 54" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="52" y="28" text-anchor="middle" font-size="13" fill="#ff6b00">supply</text>
  </g>

  <rect class="comp" x="134" y="115" width="90" height="40" rx="5" stroke="currentColor" stroke-opacity="0.5"/>
  <text class="compt" x="179" y="140" text-anchor="middle" font-size="13" font-weight="bold" fill="currentColor">compressor</text>
  <path d="M 84 135 L 130 135" stroke="currentColor" stroke-width="2"/>
  <path d="M 228 135 L 286 135" stroke="currentColor" stroke-width="2"/>
  <text x="179" y="176" text-anchor="middle" font-size="13" opacity="0.85">&minus;2 GST &rarr; +1 HPT</text>
  <g class="man">
    <rect x="132" y="90" width="94" height="20" rx="3" fill="var(--on)"/>
    <text x="179" y="105" text-anchor="middle" font-size="13" style="fill:var(--on-ink)" font-weight="bold">held on by hand</text>
  </g>

  <rect x="290" y="70" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl hpt" x="292" y="72" width="52" height="126" fill="#ff6b00"/>
  <text x="318" y="216" text-anchor="middle" font-size="13" font-weight="bold">HPT</text>
  <g font-size="11">
    <line x1="288" y1="89" x2="348" y2="89" stroke="currentColor" stroke-width="2" stroke-dasharray="5 5"/>
    <line x1="288" y1="89" x2="348" y2="89" stroke="var(--on-ink)" stroke-width="2" stroke-dasharray="5 5" stroke-dashoffset="5"/>
    <text x="284" text-anchor="end" y="85" fill="#ff6b00" font-weight="bold">220</text>
    <line x1="288" y1="99" x2="348" y2="99" stroke="currentColor" stroke-dasharray="5 5" stroke-opacity="0.8"/>
    <line x1="288" y1="99" x2="348" y2="99" stroke="var(--on-ink)" stroke-dasharray="5 5" stroke-dashoffset="5" stroke-opacity="0.8"/>
    <text class="lbl200" x="284" text-anchor="end" y="111" opacity="0.75">200</text>
    <line x1="288" y1="149" x2="348" y2="149" stroke="currentColor" stroke-dasharray="5 5" stroke-opacity="0.8"/>
    <line x1="288" y1="149" x2="348" y2="149" stroke="var(--on-ink)" stroke-dasharray="5 5" stroke-dashoffset="5" stroke-opacity="0.8"/>
    <text x="284" text-anchor="end" y="153" opacity="0.75">100</text>
    <line x1="288" y1="168" x2="348" y2="168" stroke="currentColor" stroke-dasharray="5 5" stroke-opacity="0.8"/>
    <line x1="288" y1="168" x2="348" y2="168" stroke="var(--on-ink)" stroke-dasharray="5 5" stroke-dashoffset="5" stroke-opacity="0.8"/>
    <text x="284" text-anchor="end" y="172" opacity="0.75">60</text>
  </g>
  <g class="vent">
    <path d="M 318 62 L 318 36" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 312 44 L 318 34 L 324 44" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="318" y="26" text-anchor="middle" font-size="13" fill="#ff6b00" font-weight="bold">venting</text>
  </g>

  <text x="372" y="210" text-anchor="middle" font-size="13" font-weight="bold">SV</text>
  <path d="M 346 186 L 398 186" stroke="currentColor" stroke-width="2"/>
  <g class="sv-open">
    <path d="M 364 178 L 364 194 L 380 186 Z" fill="none" stroke="currentColor" stroke-width="2"/>
    <path d="M 380 178 L 380 194 L 364 186 Z" fill="none" stroke="currentColor" stroke-width="2"/>
    <text x="372" y="226" text-anchor="middle" font-size="13" opacity="0.8">open</text>
  </g>
  <g class="sv-shut">
    <path d="M 364 178 L 364 194 L 380 186 Z" fill="#ff6b00"/>
    <path d="M 380 178 L 380 194 L 364 186 Z" fill="#ff6b00"/>
    <text x="372" y="226" text-anchor="middle" font-size="13" fill="#ff6b00" font-weight="bold">shut</text>
  </g>

  <rect x="160" y="242" width="180" height="44" rx="5" fill="currentColor" fill-opacity="0.15" stroke="currentColor"/>
  <text x="250" y="262" text-anchor="middle" font-size="13" font-weight="bold">OpenPLC</text>
  <text x="250" y="278" text-anchor="middle" font-size="13" opacity="0.8">on below 60, off at 90</text>
  <path d="M 346 198 L 428 198 L 428 264 L 346 264" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 354 258 L 344 264 L 354 270" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="336" y="236" font-size="14" opacity="0.8" text-anchor="end">reads 1126</text>
  <path d="M 160 264 L 96 264 L 96 135 L 128 135" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 120 129 L 130 135 L 120 141" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="102" y="210" font-size="12" opacity="0.8">drives coil 1</text>

  <text class="stuck" x="284" y="112" text-anchor="end" font-size="13" fill="#ff6b00" font-weight="bold">stuck here</text>
  <text class="ph-n" x="10" y="308" font-size="13" opacity="0.85">automatic: the loop holds 60 to 90</text>
  <text class="ph-a" x="10" y="308" font-size="13" fill="#ff6b00" font-weight="bold">manual: the operator has the controls</text>
  <text class="rst" x="450" y="308" font-size="13" text-anchor="end" font-weight="bold" fill="#ff6b00">loop restarts &mdash; the plant does not</text>
</svg>
<figcaption>The same plant twice. First OpenPLC holds the HPT between 60 and 90 with the system valve open. Then an operator in manual mode shuts the valve and keeps the compressor running: the pressure climbs past 220, the blow-out valve vents, and when the compressor stops the tank stays stuck at 200. With reduced motion the figure shows that end state.</figcaption>
</figure>

Left alone, the loop is calm on purpose: the pressure saws gently between 60 and 90 and never goes near the blow-out valve. The danger starts when someone takes the loop out of the controller's hands. The figure shows that case. With the system valve shut and the compressor kept running, gas has nowhere to go. The blow-out valve opens above 220, but it vents more slowly than the compressor pumps, so it only slows the rise.

Notice that nothing in that story needs a network attack. Every action is something an operator is allowed to do; the damage comes from the *combination*. The [Physical Process challenge](/ctf/challenge/physical_process) asks you to reproduce this through the operator's own screen.

<details class="deep-dive" markdown="1">
<summary>Deep dive: why the damage does not undo itself</summary>

The plant model lives in two files that must agree: `thread_physical` in `software/stm32/src/main.c` (the reference, running on the real board) and `physical_process_thread` in `software/hwio-virtual/hardwareAbstraction.py` (its mirror in Docker). In each tick:

- With the compressor on, and only while the GST holds at least 50, the GST loses 2 and the HPT gains 1.
- With the compressor off and the system valve open, the downstream process draws a random 0 to 2 from the HPT.
- Above 220 the blow-out valve opens and stays open until the HPT falls to 200. It vents a random 0 or 1 per tick, so on average half a unit against the compressor's steady one.

Once the compressor stops, the only thing removing gas is the blow-out valve, and it closes again at 200. The downstream process cannot help, because the valve is shut. Handing the plant back to automatic mode does not reopen it either: OpenPLC only opens the system valve while the pressure is between 50 and 100. The tank sits at 200 until a person deliberately opens the valve by hand. That is typical of real incidents: the controller's own logic does not bring the plant back, and the recovery happens on the plant floor, not in the network capture.

On the physical CybICS board, Level 0 is not a container at all. The STM32 microcontroller runs the process model, and `hwio` becomes a real bridge that talks to it over I&sup2;C at address 0x20.

</details>

## Why ICS security is different

Most industrial protocols, such as [Modbus](/theory/modbus) and [S7comm](/theory/s7comm), have **no authentication and no encryption**. That is not carelessness. They were designed for a serial cable inside a locked cabinet, where the cabinet door was the access control. When the cable became a network, the protocols stayed the same. Anyone who can reach a controller on the network can usually read and write its values.

[OPC-UA](/theory/opcua-protocol), the newest protocol on the plant, is the exception: it has users, passwords and certificates. The CybICS server even lists the `Anonymous` login option and an unencrypted `NoSecurity` mode alongside its encrypted one. Advertising an option is not the same as accepting it, though. The server's user manager refuses every anonymous session, so you need a real account or a trusted certificate. That is why the OPC-UA challenge is about guessing a weak password and finding certificates that were left lying around, not about walking in.

<div class="callout cybics" markdown="1">
**In CybICS:** every attack in the later modules ends in a physical effect: a frozen reading, a forced valve, a tank driven past what its relief valve can handle. Keep the gas plant in mind as you read on. It is the thing you are protecting.
</div>

<div data-widget="checkpoint" data-id="purdue"></div>
