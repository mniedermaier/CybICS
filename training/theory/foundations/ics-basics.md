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
@keyframes p-right {0%,25%{transform:translate(0,0)} 27%{transform:translate(16px,38px)}
                    36%{transform:translate(324px,38px)} 38%,88%{transform:translate(340px,0)}
                    90%{transform:translate(324px,38px)} 98%{transform:translate(16px,38px)}
                    100%{transform:translate(0,0)}}
@keyframes p-left  {0%,25%{transform:translate(0,0)} 27%{transform:translate(-16px,-38px)}
                    36%{transform:translate(-324px,-38px)} 38%,88%{transform:translate(-340px,0)}
                    90%{transform:translate(-324px,-38px)} 98%{transform:translate(-16px,-38px)}
                    100%{transform:translate(0,0)}}
@keyframes p-it {0%,31%{opacity:1} 31.01%,94%{opacity:0} 94.01%,100%{opacity:1}}
@keyframes p-ot {0%,31%{opacity:0} 31.01%,94%{opacity:1} 94.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .pri {display:none;}
  .pri-static {display:block;}
}
</style>
<svg class="pri" viewBox="0 0 520 130" role="img"
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
  <text x="102" y="122" font-size="11" opacity="0.7" text-anchor="middle">most important</text>
  <text x="442" y="122" font-size="11" opacity="0.7" text-anchor="middle">least important</text>
</svg>
<svg class="pri-static" viewBox="0 0 520 134" role="img"
     aria-label="IT ranks the three goals confidentiality, integrity, availability. OT reverses the outer two: availability first, integrity second, confidentiality last.">
  <g font-size="12">
    <text x="10" y="20" font-size="13" font-weight="bold">IT priorities</text>
    <text x="4" y="45" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
    <rect x="22" y="28" width="148" height="26" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="96" y="45" text-anchor="middle">Confidentiality</text>
    <rect x="180" y="28" width="160" height="26" rx="4" fill="currentColor" opacity="0.28" stroke="currentColor"/>
    <text x="260" y="45" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="28" width="160" height="26" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="430" y="45" text-anchor="middle">3. Availability</text>

    <text x="10" y="86" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>
    <text x="4" y="111" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
    <rect x="22" y="94" width="148" height="26" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="96" y="111" text-anchor="middle">Availability</text>
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
@keyframes u-walk {0%,6%{transform:translateY(0)}      14%,22%{transform:translateY(0)}
                   30%,38%{transform:translateY(50px)}  46%,54%{transform:translateY(100px)}
                   62%,70%{transform:translateY(150px)} 78%,94%{transform:translateY(200px)}
                   100%{transform:translateY(0)}}
@keyframes u-dmz  {0%,24%{stroke-opacity:0.5; stroke-width:1.5}
                   26%,34%{stroke-opacity:1; stroke-width:3}
                   36%,100%{stroke-opacity:0.5; stroke-width:1.5}}
@media (prefers-reduced-motion: reduce) {
  .pur .walk {animation:none; transform:translateY(200px);}
  .pur .dmz  {animation:none;}
}
</style>
<svg class="pur" viewBox="0 0 520 266" role="img"
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

</svg>
<figcaption>The dashed line is where the IT/OT boundary belongs: between the enterprise and everything that can reach a controller, usually built as an OT DMZ. An intruder that starts at the top reaches the process by descending all five levels, one protocol at a time. The descent is the point: each step is a different protocol and a different topic in this path, and the only thing that would have stopped it is a boundary CybICS deliberately does not have.</figcaption>
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

Everything above exists to run one small plant. A compressor pumps gas from a storage tank (**GST**) into a high pressure tank (**HPT**), and the downstream process draws from the HPT while the system valve is open &mdash; but only while the compressor is off, because the model gives the plant one job per tick. Both readings are a single byte, 0 to 255, and OpenPLC is the thing that decides: it reads the HPT pressure out of register 1126 and drives the compressor on coil 1. That loop &mdash; sensor, controller, actuator, process, sensor again &mdash; is what makes this a *control* system rather than a machine.

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
.plt .comp{fill:#ff6b00; animation: t-comp var(--t) steps(1,end) infinite;}
.plt .compt{animation: t-compt var(--t) steps(1,end) infinite;}
.plt .vent{opacity:0; animation: t-vent var(--t) steps(1,end) infinite;}
.plt .man {opacity:0; animation: t-hold var(--t) steps(1,end) infinite;}
.plt .sup {opacity:0; animation: t-man  var(--t) steps(1,end) infinite;}
.plt .ph-n{animation: t-phn var(--t) steps(1,end) infinite;}
.plt .ph-a{opacity:0; animation: t-man var(--t) steps(1,end) infinite;}
.plt .sv-open{animation: t-phn var(--t) steps(1,end) infinite;}
.plt .sv-shut{opacity:0; animation: t-man var(--t) steps(1,end) infinite;}
.plt .stuck{opacity:0; animation: t-stuck var(--t) steps(1,end) infinite;}
/* Every segment obeys the model: HPT can only fall while the compressor is off,
   GST can only fall while it is on, and two units of GST buy one of HPT unless
   the supply valve is feeding, which cuts the net drain to a quarter. The loop restarts
   with a hard cut at the boundary rather than animating the pressure back
   down, because nothing inside this loop can bring it down. */
@keyframes t-hpt {0%{transform:scaleY(0.235)}  12%{transform:scaleY(0.353)}
                  24%{transform:scaleY(0.235)} 30%{transform:scaleY(0.294)}
                  62%{transform:scaleY(0.863)} 82%{transform:scaleY(0.941)}
                  94%,100%{transform:scaleY(0.784)}}
@keyframes t-gst {0%{transform:scaleY(0.941)}  12%,24%{transform:scaleY(0.706)}
                  30%{transform:scaleY(0.588)} 62%{transform:scaleY(0.304)}
                  82%{transform:scaleY(0.225)} 100%{transform:scaleY(0.60)}}
@keyframes t-comp {0%,12%{fill:#ff6b00; fill-opacity:1} 12.01%,24%{fill:currentColor; fill-opacity:0.18}
                   24.01%,82%{fill:#ff6b00; fill-opacity:1} 82.01%,100%{fill:currentColor; fill-opacity:0.18}}
/* The label has to follow the box, or the dark ink sits on a dark panel. */
@keyframes t-compt{0%,12%{fill:#1a1a1a} 12.01%,24%{fill:currentColor}
                   24.01%,82%{fill:#1a1a1a} 82.01%,100%{fill:currentColor}}
@keyframes t-vent {0%,61.9%{opacity:0} 62%,94%{opacity:1} 94.01%,100%{opacity:0}}
@keyframes t-man  {0%,29.9%{opacity:0} 30%,100%{opacity:1}}
/* The badge has to stop when the compressor does, at 82%. */
@keyframes t-hold {0%,29.9%{opacity:0} 30%,82%{opacity:1} 82.01%,100%{opacity:0}}
@keyframes t-phn  {0%,29.9%{opacity:1} 30%,100%{opacity:0}}
@keyframes t-stuck{0%,93.9%{opacity:0} 94%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) {
  .plt .gst {animation:none; transform:scaleY(0.40);}
  .plt .hpt {animation:none; transform:scaleY(0.784);}
  .plt .comp {animation:none; fill:currentColor; fill-opacity:0.18;}
  .plt .compt{animation:none; fill:currentColor;}
  .plt .sup,.plt .ph-a,.plt .stuck,.plt .sv-shut {animation:none; opacity:1;}
  .plt .sv-open{animation:none; opacity:0;}
  .plt .man {animation:none; opacity:0;}
  .plt .vent{animation:none; opacity:0;}
  .plt .ph-n{animation:none; opacity:0;}
}
</style>
<svg class="plt" viewBox="0 0 460 320" role="img"
     aria-label="The CybICS control loop. OpenPLC reads the high pressure tank from register 1126 and drives the compressor on coil 1, holding the pressure between 60 and 90 while the system valve lets the downstream process draw from it. An operator then switches to manual mode, shuts the system valve and runs the compressor; the pressure climbs past 220, the relief valve opens but only halves the rate of rise, and when the compressor finally stops the pressure settles at 200 and stays there, because the shut valve leaves no consumer.">
  <!-- storage tank; the fill is 126 units tall with its base at y=198, so a
       value v sits at y = 198 - 126*v/255 -->
  <rect x="24" y="70" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl gst" x="26" y="72" width="52" height="126" fill="currentColor" opacity="0.35"/>
  <text x="52" y="216" text-anchor="middle" font-size="13" font-weight="bold">GST</text>
  <g class="sup">
    <path d="M 52 36 L 52 62" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 46 54 L 52 64 L 58 54" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="52" y="28" text-anchor="middle" font-size="13" fill="#ff6b00">supply</text>
  </g>

  <rect class="comp" x="134" y="115" width="90" height="40" rx="5" stroke="currentColor" stroke-opacity="0.5"/>
  <text class="compt" x="179" y="140" text-anchor="middle" font-size="13" font-weight="bold">compressor</text>
  <path d="M 84 135 L 130 135" stroke="currentColor" stroke-width="2"/>
  <path d="M 228 135 L 286 135" stroke="currentColor" stroke-width="2"/>
  <text x="179" y="176" text-anchor="middle" font-size="13" opacity="0.85">&minus;2 GST &rarr; +1 HPT</text>
  <g class="man">
    <rect x="132" y="90" width="94" height="20" rx="3" fill="#ff6b00"/>
    <text x="179" y="105" text-anchor="middle" font-size="13" style="fill:#1a1a1a" font-weight="bold">held on by hand</text>
  </g>

  <rect x="290" y="70" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl hpt" x="292" y="72" width="52" height="126" fill="#ff6b00" opacity="0.55"/>
  <text x="318" y="216" text-anchor="middle" font-size="13" font-weight="bold">HPT</text>
  <g font-size="12">
    <line x1="288" y1="89" x2="348" y2="89" stroke="#ff6b00" stroke-dasharray="4 3"/>
    <text x="354" y="86" fill="#ff6b00">220</text>
    <line x1="288" y1="99" x2="348" y2="99" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
    <text x="354" y="106" opacity="0.75">200</text>
    <line x1="288" y1="149" x2="348" y2="149" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
    <text x="354" y="152" opacity="0.75">100</text>
    <line x1="288" y1="168" x2="348" y2="168" stroke="currentColor" stroke-dasharray="4 3" stroke-opacity="0.6"/>
    <text x="354" y="172" opacity="0.75">60</text>
  </g>
  <g class="vent">
    <path d="M 318 62 L 318 36" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 312 44 L 318 34 L 324 44" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="318" y="26" text-anchor="middle" font-size="13" fill="#ff6b00" font-weight="bold">venting</text>
  </g>

  <!-- the system valve: the one thing the challenge asks you to close -->
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

  <rect x="160" y="242" width="180" height="44" rx="5" fill="currentColor" opacity="0.15" stroke="currentColor"/>
  <text x="250" y="262" text-anchor="middle" font-size="13" font-weight="bold">OpenPLC</text>
  <text x="250" y="278" text-anchor="middle" font-size="12" opacity="0.8">on below 60, off at 90</text>
  <path d="M 346 198 L 428 198 L 428 264 L 346 264" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 354 258 L 344 264 L 354 270" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="424" y="230" font-size="12" opacity="0.8" text-anchor="end">reads 1126</text>
  <path d="M 160 264 L 96 264 L 96 135 L 128 135" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 120 129 L 130 135 L 120 141" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="102" y="210" font-size="12" opacity="0.8">drives coil 1</text>

  <text class="stuck" x="354" y="122" font-size="12" fill="#ff6b00" font-weight="bold">stuck here</text>
  <text class="ph-n" x="10" y="308" font-size="13" opacity="0.85">automatic: the loop holds 60 to 90</text>
  <text class="ph-a" x="10" y="308" font-size="13" fill="#ff6b00" font-weight="bold">manual: the operator has the controls</text>
</svg>
<figcaption>The same plant twice: first with OpenPLC holding it between 60 and 90 with the system valve open, then with an operator in manual mode who has shut that valve. When the compressor finally stops, the pressure falls to 200 and no further. Without motion the figure shows that end state: valve shut, compressor stopped, the tank resting at 200.</figcaption>
</figure>

The attack is the second half of that loop, and it is not a network attack at all. The *Physical Process* challenge has you log in to the FUXA HMI as `operator:operator`, press **Manual / Automatic**, close the system valve and run the compressor. Every step is a legitimate operator action; the damage comes from the combination &mdash; a shut valve with a running compressor.

Three details make it work, and each of them is a design decision rather than a bug.

**Manual mode does not fail safe, it freezes.** The whole automatic block is wrapped in `IF manual < 1`, and the inner block has no `ELSE`. In manual mode OpenPLC stops assigning the compressor, the system valve and the supply valve entirely &mdash; they keep whatever value they had at the instant the operator switched over, and the panel hands all three to the operator. The `Comp.`, `SV` and `GST` buttons in FUXA write those same three coils, and each is gated on manual mode being on. The operator opens the supply deliberately &mdash; unless manual mode was entered during the tank's own refill window, in which case `gstSig` freezes on and the supply is already feeding. Either way it matters, because of the budget at the end of this section.

**The relief valve does not hold the tank, it only slows it.** Above 220 the blow-out valve opens and stays open until the pressure has fallen back to 200, but it vents a random 0 or 1 unit per tick &mdash; half a unit on average &mdash; against the compressor's steady +1. The net is still positive. The valve halves the rate of rise and the tank goes to 255 anyway. The last line of defence here is a spring, and the spring loses.

**And the damage does not undo itself.** Once the compressor stops, the only thing removing gas is the blow-out valve, which latches shut again at 200. The downstream consumer cannot help either. The valve is shut because the operator shut it, and handing the plant back to OpenPLC does not reopen it: the automatic rule only opens the valve between 50 and 100, and the tank is sitting at 200. The tank settles at 200 and sits there. Recovering it takes something from outside the loop &mdash; which is the part of an ICS incident that does not appear in the network capture.

For scale: draining two units of storage per unit of pressure, a completely full storage tank buys 103 units of pressure before the compressor stalls at the `gst >= 50` guard. That is not enough to reach 220 from the normal band on its own, which is exactly why the supply valve matters.

## Why it matters for security

Because these systems were built for reliability, not for hostile networks, most ICS protocols have **no authentication and no encryption**. OPC-UA, the newest thing on this plant, is the exception that shows the rule: it has sessions, certificates and users, and it is the only one of them that does. Any host that can reach a PLC can usually read and write its values. The rest of the Theory Path shows exactly how each protocol works, how that trust is abused, and how to detect and contain it.

> **Key idea:** in ICS security you are protecting a physical process. Every attack in the later modules ends in a real-world effect &mdash; a frozen reading, a forced valve, a tank driven past the pressure its relief valve can bleed off.
