# What is an Industrial Control System?

An **Industrial Control System (ICS)** is the combination of hardware and software that monitors and controls a physical process: a gas plant, a water works, a power grid, a production line. Unlike ordinary IT, an ICS acts on the real world. A wrong value does not corrupt a spreadsheet, it opens a valve.

This is why the priorities are inverted compared to IT. In IT the order is usually **confidentiality, integrity, availability**. In operational technology (OT) it is the reverse: keeping the process running safely comes first.

<figure>
<style>
/* The inversion is a reordering, so the figure reorders: the two outer goals
   trade places and the reader sees which one moved. Orange marks rank 1 and
   nothing else, in both the animated and the static version -- when it marked
   a goal instead, the two versions disagreed about what the colour meant. */
.pri {--p: 12s;}
.pri .swap-c {animation: p-right var(--p) ease-in-out infinite;}
.pri .swap-a {animation: p-left  var(--p) ease-in-out infinite;}
.pri .lab-it {animation: p-it    var(--p) steps(1,end) infinite;}
.pri .lab-ot {opacity:0; animation: p-ot var(--p) steps(1,end) infinite;}
.pri-static {display:none;}
@keyframes p-right {0%,25%{transform:translateX(0)} 38%,88%{transform:translateX(340px)}
                    100%{transform:translateX(0)}}
@keyframes p-left  {0%,25%{transform:translateX(0)} 38%,88%{transform:translateX(-340px)}
                    100%{transform:translateX(0)}}
@keyframes p-it {0%,31%{opacity:1} 31.01%,94%{opacity:0} 94.01%,100%{opacity:1}}
@keyframes p-ot {0%,31%{opacity:0} 31.01%,94%{opacity:1} 94.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .pri {display:none;}
  .pri-static {display:block;}
}
</style>
<svg class="pri" viewBox="0 0 520 96" role="img"
     aria-label="The same three security goals in one row, ordered most important on the left. IT ranks them confidentiality, integrity, availability; OT swaps the outer two, so availability leads and confidentiality comes last.">
  <text class="lab-it" x="10" y="20" font-size="13" font-weight="bold">IT priorities</text>
  <text class="lab-ot" x="10" y="20" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>

  <text x="20" y="60" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
  <text x="190" y="60" font-size="12" font-weight="bold" opacity="0.6">2.</text>
  <text x="360" y="60" font-size="12" font-weight="bold" opacity="0.6">3.</text>

  <g class="swap-c">
    <rect x="34" y="38" width="136" height="30" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="102" y="58" font-size="12" text-anchor="middle">Confidentiality</text>
  </g>
  <g class="swap-a">
    <rect x="374" y="38" width="136" height="30" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="442" y="58" font-size="12" text-anchor="middle">Availability</text>
  </g>
  <g>
    <rect x="204" y="38" width="136" height="30" rx="4" fill="currentColor" opacity="0.28" stroke="currentColor"/>
    <text x="272" y="58" font-size="12" text-anchor="middle">Integrity</text>
  </g>
  <text x="102" y="88" font-size="11" opacity="0.7" text-anchor="middle">most important</text>
  <text x="442" y="88" font-size="11" opacity="0.7" text-anchor="middle">least important</text>
</svg>
<svg class="pri-static" viewBox="0 0 520 134" role="img"
     aria-label="IT ranks the three goals confidentiality, integrity, availability. OT reverses the outer two: availability first, integrity second, confidentiality last.">
  <g font-size="12">
    <text x="10" y="20" font-size="13" font-weight="bold">IT priorities</text>
    <rect x="10" y="28" width="160" height="26" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="90" y="45" text-anchor="middle"><tspan fill="#ff6b00" font-weight="bold">1. </tspan>Confidentiality</text>
    <rect x="180" y="28" width="160" height="26" rx="4" fill="currentColor" opacity="0.28" stroke="currentColor"/>
    <text x="260" y="45" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="28" width="160" height="26" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="430" y="45" text-anchor="middle">3. Availability</text>

    <text x="10" y="86" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>
    <rect x="10" y="94" width="160" height="26" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="90" y="111" text-anchor="middle"><tspan fill="#ff6b00" font-weight="bold">1. </tspan>Availability</text>
    <rect x="180" y="94" width="160" height="26" rx="4" fill="currentColor" opacity="0.28" stroke="currentColor"/>
    <text x="260" y="111" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="94" width="160" height="26" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="430" y="111" text-anchor="middle">3. Confidentiality</text>
  </g>
</svg>
<figcaption>Integrity does not move. What changes is which of the other two you give up first &mdash; and above both of them sits safety, because the process must not hurt anyone.</figcaption>
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
    <rect x="70" y="210" width="440" height="40" rx="5" fill="#ff6b00" stroke="#ff6b00"/>
    <text x="82" y="235" style="fill:#1a1a1a">Level 0 &mdash; Process (sensors, actuators, valves)</text>
  </g>

  <line class="dmz" x1="70" y1="55" x2="510" y2="55" stroke="#ff6b00" stroke-dasharray="6 4"/>

  <g class="walk">
    <circle cx="40" cy="30" r="10" fill="#ff6b00"/>
    <text x="40" y="34" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">!</text>
  </g>

  <g class="note" font-size="11" font-weight="bold">
    <text x="70" y="308" fill="#ff6b00">CybICS has no boundary at all: one flat 172.18.0.0/24,</text>
    <text x="70" y="324" fill="#ff6b00">with the IDS watching it from the host itself.</text>
  </g>
</svg>
<figcaption>The dashed line is where the IT/OT boundary belongs: between the enterprise and everything that can reach a controller, usually built as an OT DMZ. Five levels, and one intruder walking down all of them. The descent is the point: each step is a different protocol and a different topic in this path, and the only thing that would have stopped it is a boundary CybICS deliberately does not have.</figcaption>
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
.plt {--t: 20s;}
/* transform-box defaults to view-box for SVG, so `center bottom` would anchor
   at the bottom of the *viewBox*, not of the rect -- which put the fills
   outside their tanks entirely. fill-box anchors on the element's own box. */
.plt .lvl {transform-box: fill-box; transform-origin: bottom;}
.plt .gst {animation: t-gst var(--t) linear infinite;}
.plt .hpt {animation: t-hpt var(--t) linear infinite;}
.plt .comp{animation: t-comp var(--t) steps(1,end) infinite;}
.plt .vent{opacity:0; animation: t-vent var(--t) steps(1,end) infinite;}
.plt .man {opacity:0; animation: t-man  var(--t) steps(1,end) infinite;}
.plt .sup {opacity:0; animation: t-man  var(--t) steps(1,end) infinite;}
.plt .ph-n{animation: t-phn var(--t) steps(1,end) infinite;}
.plt .ph-a{opacity:0; animation: t-man var(--t) steps(1,end) infinite;}
.plt .stuck{opacity:0; animation: t-stuck var(--t) steps(1,end) infinite;}
/* Every segment obeys the model: HPT can only fall while the compressor is off,
   GST can only fall while it is on, and two units of GST buy one of HPT unless
   the supply valve is feeding, which halves the net drain. The loop restarts
   with a hard cut at the boundary rather than animating the pressure back
   down, because nothing inside this loop can bring it down. */
@keyframes t-hpt {0%{transform:scaleY(0.235)}  12%{transform:scaleY(0.353)}
                  24%{transform:scaleY(0.235)} 30%{transform:scaleY(0.294)}
                  62%{transform:scaleY(0.863)} 82%,88%{transform:scaleY(0.941)}
                  94%,100%{transform:scaleY(0.784)}}
@keyframes t-gst {0%{transform:scaleY(0.941)}  12%,24%{transform:scaleY(0.706)}
                  30%{transform:scaleY(0.588)} 62%{transform:scaleY(0.304)}
                  82%{transform:scaleY(0.225)} 88%{transform:scaleY(0.245)}
                  94%{transform:scaleY(0.40)}  100%{transform:scaleY(0.60)}}
@keyframes t-comp {0%,12%{fill:#ff6b00} 12.01%,24%{fill:currentColor}
                   24.01%,82%{fill:#ff6b00} 82.01%,100%{fill:currentColor}}
@keyframes t-vent {0%,61.9%{opacity:0} 62%,94%{opacity:1} 94.01%,100%{opacity:0}}
@keyframes t-man  {0%,29.9%{opacity:0} 30%,100%{opacity:1}}
@keyframes t-phn  {0%,29.9%{opacity:1} 30%,100%{opacity:0}}
@keyframes t-stuck{0%,93.9%{opacity:0} 94%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) {
  .plt .gst {animation:none; transform:scaleY(0.40);}
  .plt .hpt {animation:none; transform:scaleY(0.784);}
  .plt .comp{animation:none; fill:currentColor;}
  .plt .man,.plt .sup,.plt .ph-a,.plt .stuck {animation:none; opacity:1;}
  .plt .vent{animation:none; opacity:0;}
  .plt .ph-n{animation:none; opacity:0;}
}
</style>
<svg class="plt" viewBox="0 0 520 300" role="img"
     aria-label="The CybICS control loop. OpenPLC reads the high pressure tank from register 1126 and drives the compressor on coil 1, holding the pressure between 60 and 90. An operator then switches to manual mode, closes the system valve and runs the compressor; the pressure climbs past 220, the relief valve opens but only halves the rate of rise, and when the compressor finally stops the pressure settles at 200 and stays there, because above 100 the system valve is shut and there is no consumer left.">
  <!-- storage tank; the fill is 126 units tall with its base at y=188, so a
       value v sits at y = 188 - 126*v/255 -->
  <rect x="40" y="60" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl gst" x="42" y="62" width="52" height="126" fill="currentColor" opacity="0.35"/>
  <text x="68" y="52" text-anchor="middle" font-size="12" font-weight="bold">GST</text>
  <text x="68" y="206" text-anchor="middle" font-size="11" opacity="0.8">storage</text>
  <g class="sup">
    <path d="M 24 60 L 24 36" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 18 44 L 24 34 L 30 44" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="8" y="28" font-size="11" fill="#ff6b00">supply, frozen open</text>
  </g>

  <!-- compressor -->
  <rect class="comp" x="150" y="105" width="90" height="40" rx="5" opacity="0.8"/>
  <text x="195" y="130" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">compressor</text>
  <path d="M 100 125 L 146 125" stroke="currentColor" stroke-width="2"/>
  <path d="M 244 125 L 296 125" stroke="currentColor" stroke-width="2"/>
  <text x="195" y="164" text-anchor="middle" font-size="11" opacity="0.85">&minus;2 GST &rarr; +1 HPT</text>
  <g class="man">
    <rect x="148" y="80" width="94" height="20" rx="3" fill="#ff6b00"/>
    <text x="195" y="94" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">held on by hand</text>
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
    <line x1="296" y1="139" x2="360" y2="139" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
    <text x="364" y="143" opacity="0.75">100</text>
    <line x1="296" y1="158" x2="360" y2="158" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
    <text x="364" y="162" opacity="0.75">60</text>
  </g>
  <g class="vent">
    <path d="M 344 60 L 344 36" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 338 44 L 344 34 L 350 44" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="356" y="32" font-size="11" fill="#ff6b00" font-weight="bold">venting</text>
  </g>
  <text class="stuck" x="364" y="103" font-size="11" fill="#ff6b00" font-weight="bold">stuck here</text>

  <!-- the controller, and the two wires that make this a loop -->
  <rect x="170" y="232" width="160" height="44" rx="5" fill="currentColor" opacity="0.15" stroke="currentColor"/>
  <text x="250" y="252" text-anchor="middle" font-size="12" font-weight="bold">OpenPLC</text>
  <text x="250" y="268" text-anchor="middle" font-size="11" opacity="0.8">on below 60, off at 90</text>
  <path d="M 356 190 L 392 190 L 392 254 L 336 254" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 344 248 L 334 254 L 344 260" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="398" y="218" font-size="11" opacity="0.8">reads 1126</text>
  <path d="M 170 254 L 126 254 L 126 125 L 144 125" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 136 119 L 146 125 L 136 131" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="120" y="218" font-size="11" opacity="0.8" text-anchor="end">drives coil 1</text>

  <text class="ph-n" x="10" y="292" font-size="11" opacity="0.85">automatic: the loop holds 60 to 90</text>
  <text class="ph-a" x="10" y="292" font-size="11" fill="#ff6b00" font-weight="bold">manual: the operator has the controls</text>
</svg>
<figcaption>The same plant twice: first with OpenPLC holding it between 60 and 90, then with an operator in manual mode. Watch what happens when the compressor finally stops &mdash; the pressure falls to 200 and no further.</figcaption>
</figure>

The attack is the second half of that loop, and it is not a network attack at all. The *Physical Process* challenge has you log in to the FUXA HMI as `operator:operator`, press **Manual / Automatic**, close the system valve and run the compressor. Every step is a legitimate operator action; the damage comes from the order they are done in.

Three details make it work, and each of them is a design decision rather than a bug.

**Manual mode does not fail safe, it freezes.** The whole automatic block is wrapped in `IF manual < 1`, and the inner block has no `ELSE`. In manual mode OpenPLC stops assigning the compressor, the system valve and the supply valve entirely &mdash; they keep whatever value they had at the instant the operator switched over. Whether the supply valve happens to be frozen open decides whether there is enough gas to finish the job, which is why the exercise wants a charged storage tank before you start.

**The relief valve does not hold the tank, it only slows it.** Above 220 the blow-out valve opens and stays open until the pressure falls back under 200, but it vents a random 0 or 1 unit per tick &mdash; half a unit on average &mdash; against the compressor's steady +1. The net is still positive. The valve halves the rate of rise and the tank goes to 255 anyway. The last line of defence here is a spring, and the spring loses.

**And the damage does not undo itself.** Once the compressor stops, the only thing removing gas is the blow-out valve, which latches shut again at 200. The downstream consumer cannot help: OpenPLC opens the system valve only while the pressure is between 50 and 100, so above 100 there is no consumer at all. The tank settles at 200 and sits there. Recovering it takes something from outside the loop &mdash; which is the part of an ICS incident that does not appear in the network capture.

For scale: draining two units of storage per unit of pressure, a completely full storage tank buys 103 units of pressure before the compressor stalls at the `gst >= 50` guard. That is not enough to reach 220 from the normal band on its own, which is exactly why the supply valve matters.

## Why it matters for security

Because these systems were built for reliability, not for hostile networks, most ICS protocols have **no authentication and no encryption**. OPC-UA, the newest thing on this plant, is the exception that shows the rule: it has sessions, certificates and users, and it is the only one of them that does. Any host that can reach a PLC can usually read and write its values. The rest of the Theory Path shows exactly how each protocol works, how that trust is abused, and how to detect and contain it.

> **Key idea:** in ICS security you are protecting a physical process. Every attack in the later modules ends in a real-world effect &mdash; a frozen reading, a forced valve, a tank driven past the pressure its relief valve can bleed off.
