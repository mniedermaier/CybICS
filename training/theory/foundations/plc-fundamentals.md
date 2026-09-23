# PLCs and the scan cycle

A **Programmable Logic Controller (PLC)** is the small, rugged computer at the heart of a control system. It reads sensors, runs a control program, and drives actuators &mdash; over and over, thousands of times a minute. In CybICS the PLC role is played by **OpenPLC**.

## The scan cycle

A PLC does not run like a normal program that starts, does work, and exits. It runs a **cyclic scan**: an endless loop of three phases repeated every few milliseconds.

<figure>
<style>
.pl-c {--c: 4.5s;}
.pl-c .dot   {animation: c-run var(--c) linear infinite;}
.pl-c .ph1   {animation: c-p1 var(--c) steps(1,end) infinite;}
.pl-c .ph2   {animation: c-p2 var(--c) steps(1,end) infinite;}
.pl-c .ph3   {animation: c-p3 var(--c) steps(1,end) infinite;}
.pl-c .lab   {opacity:0;}
.pl-c .l1{animation: c-l var(--c) steps(1,end) infinite;}
.pl-c .l2{animation: c-l var(--c) steps(1,end) infinite; animation-delay: 1.5s;}
.pl-c .l3{animation: c-l var(--c) steps(1,end) infinite; animation-delay: 3s;}
@keyframes c-run{from{offset-distance:0%} to{offset-distance:100%}}
@keyframes c-p1{0%,33%{opacity:1} 33.01%,100%{opacity:0.55}}
@keyframes c-p2{0%,33%{opacity:0.55} 33.01%,66%{opacity:1} 66.01%,100%{opacity:0.55}}
@keyframes c-p3{0%,66%{opacity:0.55} 66.01%,100%{opacity:1}}
@keyframes c-l{0%,33%{opacity:1} 33.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .pl-c .dot,.pl-c .ph1,.pl-c .ph2,.pl-c .ph3,.pl-c .lab{animation:none}
  .pl-c .ph1,.pl-c .ph2,.pl-c .ph3{opacity:0.85}
  .pl-c .dot{offset-distance:0%}
  .pl-c .l1{opacity:1}
}
</style>
<svg class="pl-c" viewBox="0 0 440 280" role="img"
     aria-label="The PLC scan cycle: a marker travels endlessly from read inputs, to run program, to write outputs, and back, highlighting each phase in turn.">
  <defs>
    <marker id="ah" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/>
    </marker>
  </defs>
  <circle cx="210" cy="130" r="95" fill="none" stroke="currentColor" stroke-opacity="0.25" stroke-width="2"/>

  <g font-size="12" text-anchor="middle">
    <g class="ph1">
      <rect x="150" y="10" width="120" height="42" rx="6" fill="#ff6b00"/>
      <text x="210" y="30" fill="#1a1a1a" font-weight="bold">1. Read inputs</text>
      <text x="210" y="45" fill="#1a1a1a" font-size="11">sensors &rarr; memory</text>
    </g>
    <g class="ph2">
      <rect x="300" y="150" width="120" height="42" rx="6" fill="#ff6b00"/>
      <text x="360" y="170" fill="#1a1a1a" font-weight="bold">2. Run program</text>
      <text x="360" y="185" fill="#1a1a1a" font-size="11">logic on the values</text>
    </g>
    <g class="ph3">
      <rect x="0" y="150" width="120" height="42" rx="6" fill="#ff6b00"/>
      <text x="60" y="170" fill="#1a1a1a" font-weight="bold">3. Write outputs</text>
      <text x="60" y="185" fill="#1a1a1a" font-size="11">memory &rarr; actuators</text>
    </g>
  </g>

  <path d="M270 40 A95 95 0 0 1 350 150" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M300 185 A95 95 0 0 1 120 185" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M70 150 A95 95 0 0 1 150 40" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>

  <circle class="dot" r="7" fill="#ff6b00" stroke="#1a1a1a" stroke-width="1"
          style="offset-path: path('M210 35 A95 95 0 0 1 360 171 A95 95 0 0 1 60 171 A95 95 0 0 1 210 35'); offset-rotate: 0deg;"/>

  <g text-anchor="middle" font-size="11">
    <text x="210" y="128" opacity="0.7">scan cycle</text>
    <text x="210" y="144" opacity="0.7">(every few ms)</text>
    <text class="lab l1" x="210" y="252" fill="#ff6b00">every input is sampled once, here &mdash; nothing re-reads them later</text>
    <text class="lab l2" x="210" y="252" fill="#ff6b00">the whole program runs on that frozen snapshot</text>
    <text class="lab l3" x="210" y="252" fill="#ff6b00">only now do the outputs reach the plant, all at once</text>
  </g>
</svg>
<figcaption>One scan: read all inputs into memory, run the whole program on that snapshot, then
write all outputs at once. Then repeat. The phases never overlap, which is what makes a PLC's
timing predictable &mdash; and what makes the next figure inevitable.</figcaption>
</figure>

## The snapshot is why forcing a value does not stick

The program works on a **snapshot** taken at the start of the scan, and an output it sets is only applied at the end. Write a register from outside &mdash; over Modbus, say &mdash; and you have changed a value that the next scan is about to recompute from its own inputs.

<figure>
<style>
.pl-o {--o: 7s;}
.pl-o .atk {animation: o-atk var(--o) linear infinite;}
.pl-o .v45 {animation: o-v45 var(--o) steps(1,end) infinite;}
.pl-o .v90 {opacity:0; animation: o-v90 var(--o) steps(1,end) infinite;}
.pl-o .scan{animation: o-scan var(--o) linear infinite;}
.pl-o .note{opacity:0; animation: o-note var(--o) steps(1,end) infinite;}
@keyframes o-atk {0%{transform:translateX(0);opacity:0} 5%{opacity:1}
                  24%{transform:translateX(150px);opacity:1} 28%,100%{opacity:0}}
@keyframes o-v90 {0%,26%{opacity:0} 28%,62%{opacity:1} 64%,100%{opacity:0}}
@keyframes o-v45 {0%,26%{opacity:1} 28%,62%{opacity:0} 64%,100%{opacity:1}}
@keyframes o-scan{0%,40%{transform:translateX(0);opacity:0} 44%{opacity:1}
                  60%{transform:translateX(118px);opacity:1} 66%,100%{opacity:0}}
@keyframes o-note{0%,66%{opacity:0} 70%,94%{opacity:1} 100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .pl-o .atk,.pl-o .v45,.pl-o .v90,.pl-o .scan,.pl-o .note{animation:none}
  .pl-o .atk,.pl-o .scan,.pl-o .note{opacity:1}
  .pl-o .v45{opacity:1} .pl-o .v90{opacity:0}
}
</style>
<svg class="pl-o" viewBox="0 0 520 220" role="img"
     aria-label="An attacker writes 90 into a holding register; the value changes, then the next scan cycle recomputes it from the sensors and it snaps back to 45.">
  <rect x="10" y="20" width="104" height="40" rx="5" fill="#ff6b00" opacity="0.85"/>
  <text x="62" y="36" text-anchor="middle" font-size="11" fill="#1a1a1a" font-weight="bold">Attacker</text>
  <text x="62" y="50" text-anchor="middle" font-size="11" fill="#1a1a1a">Modbus FC 06</text>

  <rect x="290" y="14" width="140" height="52" rx="5" fill="currentColor" opacity="0.18" stroke="currentColor"/>
  <text x="360" y="32" text-anchor="middle" font-size="11" font-weight="bold">holding register</text>
  <text x="330" y="52" text-anchor="middle" font-size="11">1126 =</text>
  <text class="v45" x="386" y="53" text-anchor="middle" font-size="15" font-weight="bold">45</text>
  <text class="v90" x="386" y="53" text-anchor="middle" font-size="15" font-weight="bold" fill="#ff6b00">90</text>

  <g class="atk">
    <rect x="124" y="30" width="150" height="20" rx="3" fill="#ff6b00"/>
    <text x="199" y="44" text-anchor="middle" font-size="11" fill="#1a1a1a">write 1126 = 90</text>
  </g>

  <rect x="10" y="108" width="500" height="44" rx="5" fill="currentColor" opacity="0.08" stroke="currentColor" stroke-opacity="0.3"/>
  <text x="18" y="102" font-size="11" opacity="0.75">the next scan, a few milliseconds later</text>
  <g font-size="11" text-anchor="middle">
    <rect x="22" y="116" width="110" height="28" rx="4" fill="currentColor" opacity="0.2"/>
    <text x="77" y="134">read sensors</text>
    <rect x="146" y="116" width="110" height="28" rx="4" fill="currentColor" opacity="0.2"/>
    <text x="201" y="134">recompute</text>
    <rect x="270" y="116" width="110" height="28" rx="4" fill="currentColor" opacity="0.2"/>
    <text x="325" y="134">write outputs</text>
  </g>
  <rect class="scan" x="22" y="112" width="110" height="36" fill="none" stroke="#ff6b00" stroke-width="3" rx="4"/>

  <g class="note">
    <text x="260" y="180" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">
      the register is back to 45 &mdash; the scan did not care what was in it
    </text>
    <text x="260" y="198" text-anchor="middle" font-size="11" opacity="0.85">
      to hold a value you must write faster than the scan, or change the program
    </text>
  </g>
</svg>
<figcaption>A single write to an output the program computes is undone within milliseconds. That
is why the <em>Flood &amp; overwrite</em> challenge writes in a tight loop rather than once, and why
the <em>PLC Programming</em> challenge &mdash; changing the logic itself &mdash; is the more durable
attack. It is also why an operator can watch a value flicker and never see the cause.</figcaption>
</figure>

Two attacks follow directly from this one property. Writing *faster than the scan* keeps the value pinned, which is a flood and is noisy. Changing the *program* makes the PLC compute the attacker's value itself, which is quiet and survives a restart.

## IEC 61131-3 languages

PLC programs are written in the languages standardised by **IEC 61131-3**. The two you meet in CybICS are:

- **Ladder Diagram (LD)** &mdash; a graphical notation that looks like a relay wiring diagram. Power flows left to right through contacts and coils.
- **Structured Text (ST)** &mdash; a Pascal-like textual language. The CybICS plant program `cybICS.st` is written in ST.

<figure>
<style>
.pl-r {--r: 4s;}
.pl-r .flow {stroke-dasharray: 6 8; animation: r-flow var(--r) linear infinite;}
.pl-r .gap  {animation: r-gap var(--r) steps(1,end) infinite;}
.pl-r .coil {animation: r-coil var(--r) steps(1,end) infinite;}
.pl-r .seg2 {opacity:0.25; animation: r-seg var(--r) steps(1,end) infinite;}
@keyframes r-flow{to{stroke-dashoffset:-56}}
@keyframes r-gap {0%,45%{transform:translateY(0)} 50%,95%{transform:translateY(-15px)} 100%{transform:translateY(0)}}
@keyframes r-seg {0%,45%{opacity:0.25} 50%,95%{opacity:1} 100%{opacity:0.25}}
@keyframes r-coil{0%,45%{opacity:0.3} 50%,95%{opacity:1} 100%{opacity:0.3}}
@media (prefers-reduced-motion: reduce){
  .pl-r .flow,.pl-r .gap,.pl-r .seg2,.pl-r .coil{animation:none}
  .pl-r .seg2,.pl-r .coil{opacity:1}
  .pl-r .gap{transform:translateY(-15px)}
}
</style>
<svg class="pl-r" viewBox="0 0 460 92" role="img"
     aria-label="A ladder rung: the start contact closes, power flows along the rung, and the motor coil energises; when the contact opens the coil falls dark again.">
  <line x1="20" y1="10" x2="20" y2="80" stroke="currentColor" stroke-width="2"/>
  <line x1="440" y1="10" x2="440" y2="80" stroke="currentColor" stroke-width="2"/>
  <line class="flow" x1="20" y1="45" x2="120" y2="45" stroke="#ff6b00" stroke-width="2"/>

  <line x1="120" y1="30" x2="120" y2="60" stroke="currentColor" stroke-width="2"/>
  <g class="gap"><line x1="150" y1="30" x2="150" y2="60" stroke="currentColor" stroke-width="2"/></g>
  <text x="112" y="24" font-size="11">start</text>

  <line class="seg2 flow" x1="150" y1="45" x2="360" y2="45" stroke="#ff6b00" stroke-width="2"/>
  <g class="coil">
    <path d="M360 30 A18 15 0 0 0 360 60" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <path d="M392 30 A18 15 0 0 1 392 60" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <line x1="392" y1="45" x2="440" y2="45" stroke="#ff6b00" stroke-width="2"/>
  </g>
  <text x="360" y="24" font-size="11" fill="#ff6b00">motor</text>
  <text x="20" y="78" font-size="11" opacity="0.7">left rail (power)</text>
  <text x="440" y="78" font-size="11" opacity="0.7" text-anchor="end">right rail</text>
</svg>
<figcaption>A single ladder rung. The notation is literal: it was drawn for electricians who
were replacing relay cabinets, so a closed contact really does let power through to a coil. The
CybICS program expresses the same logic in Structured Text.</figcaption>
</figure>

Watch the rung: the contact closes, power reaches the coil, the motor runs &mdash; and stops the moment it opens again. That literalness is the point of the notation.

## How the outside world reaches the PLC

The program's variables are mapped to memory addresses (`%IX`, `%QX`, `%MW` &hellip;) that are exposed over industrial protocols. OpenPLC publishes them over Modbus, S7comm, DNP3 and EtherNet/IP at the same time. That is convenient for integration &mdash; and, because those protocols do not authenticate, convenient for an attacker.

Uploading a **new program** to a running controller is one of the most impactful actions in ICS: it changes how the process behaves. That is exactly the *PLC Programming* challenge, and it maps to MITRE ATT&CK for ICS **T0843 Program Download**.
