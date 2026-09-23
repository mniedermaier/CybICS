# PLCs and the scan cycle

A **Programmable Logic Controller (PLC)** is the small, rugged computer at the heart of a control system. It reads sensors, runs a control program, and drives actuators &mdash; over and over, on a fixed period that never varies. In CybICS the PLC role is played by **OpenPLC**, running the plant program `software/OpenPLC/cybICS.st`.

## The scan cycle

A PLC does not run like a normal program that starts, does work, and exits. It runs a **cyclic scan**: an endless loop of three phases. The CybICS program declares its period in its own configuration &mdash; `TASK TaskMain(INTERVAL := T#50ms, PRIORITY := 0)` &mdash; so this PLC scans **every 50 ms, twenty times a second**. That number is worth remembering; most of what follows is a consequence of it.

<figure>
<style>
.pl-c {--c: 4.5s;}
.pl-c .dot {animation: c-run var(--c) linear infinite;}
.pl-c .ph1 {animation: c-p1 var(--c) steps(1,end) infinite;}
.pl-c .ph2 {animation: c-p2 var(--c) steps(1,end) infinite;}
.pl-c .ph3 {animation: c-p3 var(--c) steps(1,end) infinite;}
@keyframes c-run{from{offset-distance:0%} to{offset-distance:100%}}
@keyframes c-p1{0%,33%{opacity:1} 33.01%,100%{opacity:0.55}}
@keyframes c-p2{0%,33%{opacity:0.55} 33.01%,66%{opacity:1} 66.01%,100%{opacity:0.55}}
@keyframes c-p3{0%,66%{opacity:0.55} 66.01%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .pl-c .dot,.pl-c .ph1,.pl-c .ph2,.pl-c .ph3{animation:none}
  .pl-c .ph1,.pl-c .ph2,.pl-c .ph3{opacity:0.85}
  .pl-c .dot{offset-distance:0%}
}
</style>
<svg class="pl-c" viewBox="0 0 440 210" role="img"
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

  <!-- cx/cy place the marker on phase 1 where offset-path is unsupported. -->
  <circle class="dot" cx="210" cy="35" r="7" fill="#ff6b00" stroke="#1a1a1a" stroke-width="1"
          style="offset-path: path('M210 35 A95 95 0 0 1 360 171 A95 95 0 0 1 60 171 A95 95 0 0 1 210 35'); offset-rotate: 0deg;"/>

  <g text-anchor="middle" font-size="11">
    <text x="210" y="128" opacity="0.7">scan cycle</text>
    <text x="210" y="144" opacity="0.7">every 50 ms</text>
  </g>
</svg>
<figcaption>One scan: read all inputs into memory, run the whole program on that snapshot, then write all outputs at once. Then repeat, 50 ms later.</figcaption>
</figure>

Each phase does something the next one depends on, and they never overlap:

1. **Every input is sampled once, here.** Nothing re-reads a sensor later in the scan, so the program cannot see a value change halfway through its own logic.
2. **The whole program runs on that frozen snapshot.** Two lines that both read `hpt` are guaranteed to see the same `hpt`.
3. **Only now do the outputs reach the plant, all at once.** An output your program set on line 10 does not physically move anything until the scan ends.

That last point is where security starts, because it means every output the program computes is rewritten from scratch, 20 times a second, whatever anybody else put there.

## What the scan overwrites, and what it does not

Write a value into the PLC from outside &mdash; over Modbus, say &mdash; and whether it sticks depends entirely on **who owns that address**. This is the single most useful thing to understand about attacking a PLC, and it is easy to get backwards.

- **Coil 1 is the compressor**, declared `compressor AT %QX0.1` and assigned on every scan by `IF compressorState = 1 THEN compressor := TRUE; ELSE compressor := FALSE;`. The program computes it, so the program owns it. Force it with Modbus FC 05 and the next scan puts back whatever the logic says &mdash; within 50 ms, every time.
- **Register 1126 is the HPT pressure**, declared `hpt AT %MW102`. The program only ever *reads* it: it appears in comparisons and is never on the left of an assignment. Nothing in the scan restores it. What restores it is `hwio`, the bridge standing in for the sensor, which writes the true pressure back every 20 ms.

Both values snap back, but for opposite reasons and on different clocks &mdash; and an attacker who confuses the two will build the wrong attack.

<figure>
<style>
.pl-t {--t: 10s;}
/* The playhead is real time: the two bars can only end where their owner's
   next tick falls, so the figure is a measurement, not an illustration. */
.pl-t .head {animation: t-head var(--t) linear infinite;}
.pl-t .barA {opacity:0; animation: t-barA var(--t) steps(1,end) infinite;}
.pl-t .barB {opacity:0; animation: t-barB var(--t) steps(1,end) infinite;}
.pl-t .fixA {opacity:0; animation: t-fixA var(--t) steps(1,end) infinite;}
.pl-t .fixB {opacity:0; animation: t-fixB var(--t) steps(1,end) infinite;}
.pl-t .shot {opacity:0; animation: t-shot var(--t) steps(1,end) infinite;}
@keyframes t-head{0%{transform:translateX(0)} 70%,100%{transform:translateX(410px)}}
@keyframes t-shot{0%,10.4%{opacity:0} 10.5%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes t-barA{0%,10.4%{opacity:0} 10.5%,17.4%{opacity:1} 17.5%,100%{opacity:0}}
@keyframes t-barB{0%,10.4%{opacity:0} 10.5%,13.9%{opacity:1} 14%,100%{opacity:0}}
@keyframes t-fixA{0%,17.4%{opacity:0} 17.5%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes t-fixB{0%,13.9%{opacity:0} 14%,96%{opacity:1} 96.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .pl-t .head{animation:none; transform:translateX(410px)}
  .pl-t .barA,.pl-t .barB{animation:none; opacity:1}
  .pl-t .fixA,.pl-t .fixB,.pl-t .shot{animation:none; opacity:1}
}
</style>
<svg class="pl-t" viewBox="0 0 520 210" role="img"
     aria-label="A timeline over 200 milliseconds. An attacker writes at 30 milliseconds. Coil 1 is restored by the PLC scan at 50 milliseconds; register 1126 is restored by hwio at 40 milliseconds. The two are owned by different writers running at different rates.">
  <!-- time axis: t = 0 at x = 90, 2.05 px per millisecond -->
  <g font-size="11" opacity="0.7">
    <line x1="90" y1="182" x2="500" y2="182" stroke="currentColor"/>
    <text x="90"    y="198" text-anchor="middle">0</text>
    <text x="192.5" y="198" text-anchor="middle">50</text>
    <text x="295"   y="198" text-anchor="middle">100</text>
    <text x="397.5" y="198" text-anchor="middle">150</text>
    <text x="500"   y="198" text-anchor="middle">200 ms</text>
  </g>

  <!-- row A: the PLC scan, one tick every 50 ms -->
  <text x="10" y="52" font-size="11" font-weight="bold">coil 1</text>
  <text x="10" y="66" font-size="11" opacity="0.75">the scan</text>
  <text x="10" y="79" font-size="11" opacity="0.75">owns it</text>
  <line x1="90" y1="40" x2="500" y2="40" stroke="currentColor" stroke-opacity="0.2"/>
  <g stroke="currentColor" stroke-opacity="0.45">
    <line x1="90"    y1="34" x2="90"    y2="74"/><line x1="192.5" y1="34" x2="192.5" y2="74"/>
    <line x1="295"   y1="34" x2="295"   y2="74"/><line x1="397.5" y1="34" x2="397.5" y2="74"/>
    <line x1="500"   y1="34" x2="500"   y2="74"/>
  </g>
  <rect class="barA" x="151.5" y="44" width="41" height="22" rx="3" fill="#ff6b00"/>
  <text class="fixA" x="200" y="60" font-size="11" fill="#ff6b00" font-weight="bold">back to what the logic says, after 20 ms</text>

  <!-- row B: hwio, one write every 20 ms -->
  <text x="10" y="122" font-size="11" font-weight="bold">reg 1126</text>
  <text x="10" y="136" font-size="11" opacity="0.75">hwio</text>
  <text x="10" y="149" font-size="11" opacity="0.75">owns it</text>
  <line x1="90" y1="110" x2="500" y2="110" stroke="currentColor" stroke-opacity="0.2"/>
  <g stroke="currentColor" stroke-opacity="0.45">
    <line x1="90"  y1="104" x2="90"  y2="144"/><line x1="131" y1="104" x2="131" y2="144"/>
    <line x1="172" y1="104" x2="172" y2="144"/><line x1="213" y1="104" x2="213" y2="144"/>
    <line x1="254" y1="104" x2="254" y2="144"/><line x1="295" y1="104" x2="295" y2="144"/>
    <line x1="336" y1="104" x2="336" y2="144"/><line x1="377" y1="104" x2="377" y2="144"/>
    <line x1="418" y1="104" x2="418" y2="144"/><line x1="459" y1="104" x2="459" y2="144"/>
    <line x1="500" y1="104" x2="500" y2="144"/>
  </g>
  <rect class="barB" x="151.5" y="114" width="20.5" height="22" rx="3" fill="#ff6b00"/>
  <text class="fixB" x="180" y="130" font-size="11" fill="#ff6b00" font-weight="bold">back to the real pressure, after 10 ms</text>

  <!-- the attacker's single write -->
  <g class="shot">
    <line x1="151.5" y1="26" x2="151.5" y2="160" stroke="#ff6b00" stroke-width="2" stroke-dasharray="4 3"/>
    <text x="151.5" y="20" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">one write, t = 30 ms</text>
  </g>

  <line class="head" x1="90" y1="26" x2="90" y2="176" stroke="currentColor" stroke-width="2" stroke-opacity="0.55"/>
</svg>
<figcaption>Two addresses, two owners, two clocks. The attacker's single write lands at the same instant in both rows, but the PLC's next scan is up to 50 ms away while <code>hwio</code>'s next write is at most 20 ms away &mdash; so the register is recaptured sooner than the coil, by a process that is not the PLC at all.</figcaption>
</figure>

Two attacks follow from this. Writing *faster than whoever owns the address* keeps the value pinned: that is the **Flood &amp; Overwrite** challenge, whose script `flooding_hpt.py` hammers register 1126 with the value **10** in a tight loop. It has to beat `hwio`'s 20 ms, not the PLC's 50 ms, and it is noisy for exactly that reason. Changing the *program* instead makes the PLC compute the attacker's value itself &mdash; quiet, and it survives a restart. That is the **PLC Programming** challenge.

There is a third door, and it is in the logic: the program only computes its outputs while `stop` and `manual` are both clear. Set `manual`, and the whole block that assigns the coils is skipped &mdash; nothing restores them, and a forced coil simply stays forced. A control system's own operating modes are part of its attack surface.

## IEC 61131-3 languages

PLC programs are written in the languages standardised by **IEC 61131-3**. The one you actually meet in CybICS is **Structured Text (ST)**, a Pascal-like textual language: `cybICS.st` is ST from top to bottom, and the *PLC Programming* challenge has you compile and upload a modified copy of it.

**Ladder Diagram (LD)** is the notation you will meet everywhere else in industry, so it is worth being able to read one rung. Below is the compressor rule from `cybICS.st` &mdash; `IF hpt < 60 AND compressorState = 0 AND gst > 50 THEN compressorState := 1` &mdash; drawn the way an electrician would have wired it.

<figure>
<style>
.pl-r {--r: 5s;}
/* Contacts close by shortening the gap between the plates, which is what a
   contact physically does; the rung can only light once both have closed. */
.pl-r .flow {stroke-dasharray: 6 8; animation: r-flow 1.2s linear infinite;}
.pl-r .bl1  {animation: r-close1 var(--r) steps(1,end) infinite;}
.pl-r .bl2  {animation: r-close2 var(--r) steps(1,end) infinite;}
.pl-r .mid  {opacity:0.2; animation: r-mid var(--r) steps(1,end) infinite,
                        r-flow 1.2s linear infinite;}
.pl-r .rest {opacity:0.2; animation: r-live var(--r) steps(1,end) infinite,
                        r-flow 1.2s linear infinite;}
.pl-r .coil {opacity:0.25; animation: r-live var(--r) steps(1,end) infinite;}
@keyframes r-flow  {to{stroke-dashoffset:-56}}
@keyframes r-close1{0%,15%{transform:translateX(0)} 20%,88%{transform:translateX(-22px)}
                    93%,100%{transform:translateX(0)}}
@keyframes r-close2{0%,35%{transform:translateX(0)} 40%,88%{transform:translateX(-22px)}
                    93%,100%{transform:translateX(0)}}
@keyframes r-mid   {0%,18%{opacity:0.2} 20%,88%{opacity:1} 93%,100%{opacity:0.2}}
@keyframes r-live  {0%,38%{opacity:0.2} 40%,88%{opacity:1} 93%,100%{opacity:0.2}}
@media (prefers-reduced-motion: reduce){
  .pl-r .flow,.pl-r .bl1,.pl-r .bl2,.pl-r .mid,.pl-r .rest,.pl-r .coil{animation:none}
  .pl-r .bl1,.pl-r .bl2{transform:translateX(-22px)}
  .pl-r .mid,.pl-r .rest,.pl-r .coil{opacity:1}
}
</style>
<svg class="pl-r" viewBox="0 0 520 110" role="img"
     aria-label="A ladder rung with two contacts in series. The first closes when HPT is below 60, the second when GST is above 50; only with both closed does power reach the compressor coil.">
  <line x1="20" y1="14" x2="20" y2="86" stroke="currentColor" stroke-width="2"/>
  <line x1="500" y1="14" x2="500" y2="86" stroke="currentColor" stroke-width="2"/>

  <line class="flow" x1="20" y1="50" x2="130" y2="50" stroke="#ff6b00" stroke-width="2"/>
  <line x1="130" y1="34" x2="130" y2="66" stroke="currentColor" stroke-width="2"/>
  <g class="bl1"><line x1="174" y1="34" x2="174" y2="66" stroke="currentColor" stroke-width="2"/></g>
  <text x="152" y="26" font-size="11" text-anchor="middle">hpt &lt; 60</text>

  <line class="mid flow" x1="152" y1="50" x2="270" y2="50" stroke="#ff6b00" stroke-width="2"/>
  <line x1="270" y1="34" x2="270" y2="66" stroke="currentColor" stroke-width="2"/>
  <g class="bl2"><line x1="314" y1="34" x2="314" y2="66" stroke="currentColor" stroke-width="2"/></g>
  <text x="292" y="26" font-size="11" text-anchor="middle">gst &gt; 50</text>

  <line class="rest flow" x1="292" y1="50" x2="420" y2="50" stroke="#ff6b00" stroke-width="2"/>
  <g class="coil">
    <path d="M420 34 A18 16 0 0 0 420 66" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <path d="M452 34 A18 16 0 0 1 452 66" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <line x1="452" y1="50" x2="500" y2="50" stroke="#ff6b00" stroke-width="2"/>
  </g>
  <text x="436" y="26" font-size="11" text-anchor="middle" fill="#ff6b00">compressor</text>
  <text x="20" y="102" font-size="11" opacity="0.7">left rail (power)</text>
  <text x="500" y="102" font-size="11" opacity="0.7" text-anchor="end">right rail</text>
</svg>
<figcaption>One rung, two contacts in series, one coil. The notation is literal &mdash; it was drawn for electricians replacing relay cabinets &mdash; so a series connection really is a logical AND, and the coil is dark until the last contact closes. The compressor in CybICS obeys exactly this rung; it is simply written as an <code>IF</code>.</figcaption>
</figure>

## How the outside world reaches the PLC

The program's variables are bound to memory addresses in their declarations: `%QX0.1` for the compressor output, `%MW102` for the HPT reading. OpenPLC exposes those over industrial protocols, with `%QX0.0`&ndash;`%QX0.3` appearing as Modbus coils 0&ndash;3 and each `%MW`*n* as holding register 1024 + *n*. That is why HPT, declared `%MW102`, is register **1126** &mdash; the same arithmetic gives 1124 for GST and 1132 and 1134 for the two status words.

OpenPLC publishes the same memory over Modbus, S7comm, DNP3 and EtherNet/IP simultaneously, which is convenient for integration and equally convenient for an attacker: as deployed here, none of them authenticate. Blocking one port does not close the door, because the same address is reachable through the next protocol along &mdash; a point the *Network Segmentation* and *Firewall* modules make concrete.

Uploading a **new program** to a running controller is one of the most impactful actions in ICS: it changes how the process behaves, permanently, and no amount of watching register values will reveal it. That is exactly the *PLC Programming* challenge, and it maps to MITRE ATT&CK for ICS **T0843 Program Download**.
