# PLCs and the scan cycle

A **Programmable Logic Controller (PLC)** is the small, rugged computer at the heart of a control system. It reads sensors, runs a control program, and drives actuators &mdash; over and over, on a fixed period that never varies. In CybICS the PLC role is played by **OpenPLC**, running the plant program `software/OpenPLC/cybICS.st`.

## The scan cycle

A PLC does not run like a normal program that starts, does work, and exits. It runs a **cyclic scan**: an endless loop of three phases. The CybICS program declares its period in its own configuration &mdash; `TASK TaskMain(INTERVAL := T#50ms, PRIORITY := 0)` &mdash; so this PLC scans **every 50 ms, twenty times a second**. That number is worth remembering; most of what follows is a consequence of it.

<figure>
<style>
.pl-c {--c: 6s;}
/* The marker is moved with transform:translate along the ring that is actually
   drawn. offset-path composes on top of cx/cy rather than replacing them, so a
   circle given both renders at double its coordinates -- which put this marker
   off-canvas for most of every loop. */
.pl-c .dot {animation: c-run var(--c) linear infinite;}
.pl-c .ph1 {animation: c-p1 var(--c) steps(1,end) infinite;}
.pl-c .car1,.pl-c .car2,.pl-c .car3 {opacity:0;}
.pl-c .car1{animation: c-p1t var(--c) steps(1,end) infinite;}
.pl-c .car2{animation: c-p2t var(--c) steps(1,end) infinite;}
.pl-c .car3{animation: c-p3t var(--c) steps(1,end) infinite;}
.pl-c .atk {opacity:0; animation: c-atk var(--c) steps(1,end) infinite;}
.pl-c .gone{opacity:0; animation: c-gone var(--c) steps(1,end) infinite;}
.pl-c .ph2 {animation: c-p2 var(--c) steps(1,end) infinite;}
.pl-c .ph3 {animation: c-p3 var(--c) steps(1,end) infinite;}
@keyframes c-run{0%{transform:translate(0px,0px)} 8.333%{transform:translate(38px,10.2px)} 16.67%{transform:translate(65.8px,38px)} 25%{transform:translate(76px,76px)} 33.33%{transform:translate(65.8px,114px)} 41.67%{transform:translate(38px,141.8px)} 50%{transform:translate(0px,152px)} 58.33%{transform:translate(-38px,141.8px)} 66.67%{transform:translate(-65.8px,114px)} 75%{transform:translate(-76px,76px)} 83.33%{transform:translate(-65.8px,38px)} 91.67%{transform:translate(-38px,10.2px)} 100%{transform:translate(-0px,0px)}}
/* The active phase is marked with an outline, not by dimming the others: an
   orange panel at 0.55 opacity puts its dark label at 2.57:1. */
@keyframes c-p1{0%,16.7%{stroke-width:3} 16.71%,83.2%{stroke-width:0} 83.3%,100%{stroke-width:3}}
@keyframes c-p2{0%,16.7%{stroke-width:0} 16.71%,50%{stroke-width:3} 50.01%,100%{stroke-width:0}}
@keyframes c-p3{0%,50%{stroke-width:0} 50.01%,83.2%{stroke-width:3} 83.3%,100%{stroke-width:0}}
@keyframes c-p1t{0%,16.7%{opacity:1} 16.71%,83.2%{opacity:0} 83.3%,100%{opacity:1}}
@keyframes c-p2t{0%,16.7%{opacity:0} 16.71%,50%{opacity:1} 50.01%,100%{opacity:0}}
@keyframes c-p3t{0%,50%{opacity:0} 50.01%,83.2%{opacity:1} 83.3%,100%{opacity:0}}
@keyframes c-atk{0%,11.9%{opacity:0} 12%,66%{opacity:1} 66.01%,100%{opacity:0}}
@keyframes c-gone{0%,66.9%{opacity:0} 67%,96%{opacity:1} 96.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .pl-c .dot,.pl-c .ph1,.pl-c .ph2,.pl-c .ph3{animation:none}
  .pl-c .ph1{stroke-width:3}
  .pl-c .dot{transform:translate(0,0)}
  .pl-c .car1,.pl-c .gone{opacity:1}
  .pl-c .car2,.pl-c .car3,.pl-c .atk{opacity:0}
}
</style>
<svg class="pl-c" viewBox="0 0 440 244" role="img"
     aria-label="The PLC scan cycle as a ring. A marker travels clockwise past three boxes in turn: read inputs, run program, write outputs, and back to the start.">
  <defs>
    <marker id="ah" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/>
    </marker>
  </defs>
  <circle cx="220" cy="140" r="76" fill="none" stroke="currentColor" stroke-opacity="0.25" stroke-width="2"/>
  <path d="M 239.7 66.6 A76 76 0 0 1 293.4 159.7" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M 273.7 193.7 A76 76 0 0 1 166.3 193.7" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M 146.6 159.7 A76 76 0 0 1 200.3 66.6" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>

  <g font-size="12" text-anchor="middle">
    <rect class="ph1" x="152" y="10" width="136" height="44" rx="6" fill="#ff6b00" stroke="currentColor" stroke-width="0"/>
    <text x="220" y="31" style="fill:#1a1a1a" font-weight="bold">1. Read inputs</text>
    <text x="220" y="46" style="fill:#1a1a1a" font-size="11">sensors &rarr; memory</text>
    <rect class="ph2" x="300" y="176" width="136" height="44" rx="6" fill="#ff6b00" stroke="currentColor" stroke-width="0"/>
    <text x="368" y="197" style="fill:#1a1a1a" font-weight="bold">2. Run program</text>
    <text x="368" y="212" style="fill:#1a1a1a" font-size="11">logic on the values</text>
    <rect class="ph3" x="4" y="176" width="136" height="44" rx="6" fill="#ff6b00" stroke="currentColor" stroke-width="0"/>
    <text x="72" y="197" style="fill:#1a1a1a" font-weight="bold">3. Write outputs</text>
    <text x="72" y="212" style="fill:#1a1a1a" font-size="11">memory &rarr; actuators</text>
  </g>

  <circle class="dot" cx="220" cy="64" r="7" fill="#ff6b00" stroke="#1a1a1a" stroke-width="1"/>
  <g text-anchor="middle" font-size="12">
    <text class="car1" x="220" y="136" fill="#ff6b00" font-weight="bold">reads hpt = 75</text>
    <text class="car2" x="220" y="136" fill="#ff6b00" font-weight="bold">decides: keep it on</text>
    <text class="car3" x="220" y="136" fill="#ff6b00" font-weight="bold">writes coil 1 = on</text>
    <text x="220" y="156" opacity="0.7" font-size="11">one scan, 50 ms</text>
  </g>
  <g font-size="11">
    <text class="atk" x="4" y="164" fill="#ff6b00" font-weight="bold">attacker: FC 05 sets coil 1 = off</text>
    <text class="gone" x="4" y="164" opacity="0.75">&hellip; and phase 3 has just overwritten it</text>
  </g>
</svg>
<figcaption>One scan: read all inputs into memory, run the whole program on that snapshot, then write all outputs at once. Then repeat, 50 ms later. The outlined box is the phase the marker is passing.</figcaption>
</figure>

Each phase does something the next one depends on, and they never overlap:

1. **Every input is sampled once, here.** Nothing re-reads a sensor later in the scan, so the program cannot see a value change halfway through its own logic.
2. **The whole program runs on that frozen snapshot.** Two lines that both read `hpt` are guaranteed to see the same `hpt`.
3. **Only now do the outputs reach the plant, all at once.** An output your program set on line 10 does not physically move anything until the scan ends.

That last point is where security starts, because it means every output the program computes is rewritten from scratch, 20 times a second, whatever anybody else put there &mdash; at least while the plant is in automatic mode, which the next section qualifies.

CybICS bends phase 1, and the way it bends it is the reason this page has a second half. `cybICS.st` declares no `%I` address of any kind: its variables are `%QX` outputs and `%MW` memory words, nothing else. `hpt` is not a sensor the PLC samples, it is a memory word that `hwio` pushes in from outside over Modbus. Phase 1 has nothing local to read. That is exactly why a value the program treats as a pressure reading is something a stranger on the network can set.

## What the scan overwrites, and what it does not

Write a value into the PLC from outside &mdash; over Modbus, say &mdash; and whether it sticks depends entirely on **who owns that address**. This is the single most useful thing to understand about attacking a PLC, and it is easy to get backwards.

- **Coil 1 is the compressor**, declared `compressor AT %QX0.1` and assigned on every scan by `IF compressorState = 1 THEN compressor := TRUE; ELSE compressor := FALSE;`. The program computes it, so the program owns it. Force it with Modbus FC 05 and the next scan puts back whatever the logic says &mdash; within 50 ms, every time.
- **Register 1126 is the HPT pressure**, declared `hpt AT %MW102`. The program only ever *reads* it: it appears in comparisons and is never on the left of an assignment. Nothing in the scan restores it. What restores it is `hwio`, the bridge standing in for the sensor, which writes the true pressure back every 20 ms.

Both values snap back, but for opposite reasons and on different clocks &mdash; and an attacker who confuses the two will build the wrong attack.

<figure>
<style>
.pl-t {--t: 14s;}
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
@keyframes t-barA{0%,10.4%{opacity:0} 10.5%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes t-barB{0%,10.4%{opacity:0} 10.5%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes t-fixA{0%,17.4%{opacity:0} 17.5%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes t-fixB{0%,13.9%{opacity:0} 14%,96%{opacity:1} 96.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .pl-t .head{animation:none; transform:translateX(410px)}
  .pl-t .barA,.pl-t .barB{animation:none; opacity:1}
  .pl-t .shot{animation:none; opacity:1}
  /* The bars and the restore captions are mutually exclusive states, so
     the frozen frame keeps the bars and drops the captions. */
  .pl-t .fixA,.pl-t .fixB{animation:none; opacity:0}
}
</style>
<svg class="pl-t" viewBox="0 0 520 210" role="img"
     aria-label="A timeline over 200 milliseconds. An attacker writes at 30 milliseconds. Coil 1 is restored by the PLC scan at 50 milliseconds; register 1126 is restored by hwio at 40 milliseconds. The two are owned by different writers running at different rates.">
  <!-- time axis: t = 0 at x = 90, 2.05 px per millisecond -->
  <g font-size="11" opacity="0.7">
    <line x1="90" y1="182" x2="500" y2="182" stroke="currentColor"/>
    <text x="90"    y="198" text-anchor="middle">0 ms</text>
    <text x="192.5" y="198" text-anchor="middle">50</text>
    <text x="295"   y="198" text-anchor="middle">100</text>
    <text x="397.5" y="198" text-anchor="middle">150</text>
    <text x="500"   y="198" text-anchor="middle">200</text>
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
  <g class="fixA"><path d="M 192.5 44 L 188 36 L 197 36 Z" fill="#ff6b00"/><text x="200" y="40" font-size="11" fill="#ff6b00" font-weight="bold">the scan puts it back</text></g>

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
  <g class="fixB"><path d="M 172 114 L 167.5 106 L 176.5 106 Z" fill="#ff6b00"/><text x="180" y="110" font-size="11" fill="#ff6b00" font-weight="bold">hwio puts it back</text></g>

  <!-- the attacker's single write -->
  <g class="shot">
    <line x1="151.5" y1="26" x2="151.5" y2="160" stroke="#ff6b00" stroke-width="2" stroke-dasharray="4 3"/>
    <text x="151.5" y="20" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">one write, t = 30 ms</text>
  </g>

  <g class="head">
    <line x1="90" y1="24" x2="90" y2="178" stroke="currentColor" stroke-width="2.5"/>
    <path d="M 84 178 L 96 178 L 90 188 Z" fill="currentColor"/>
  </g>
</svg>
<figcaption>Two addresses, two owners, two clocks. The attacker's single write lands at the same instant in both rows, but the PLC's next scan is up to 50 ms away while <code>hwio</code>'s next write is at most 20 ms away. Averaged over where the write happens to land, the coil is free for 25 ms and the register for 10 &mdash; and the thing that takes the register back is not the PLC at all. The orange bars are how long the attacker's value actually stood.</figcaption>
</figure>

Two attacks follow from this. Writing *faster than whoever owns the address* keeps the value pinned: that is the **Flood &amp; Overwrite** challenge, whose script `flooding_hpt.py` hammers register 1126 with the value **10** in a tight loop. It has to beat `hwio`'s 20 ms, not the PLC's 50 ms, and it is noisy for exactly that reason. Changing the *program* instead makes the PLC compute the attacker's value itself &mdash; quiet, and it survives a restart. That is the **PLC Programming** challenge.

There is a third door, and it is in the logic &mdash; but only one of the two obvious candidates is really a door. The coil-assigning block sits inside `IF stop < 1` and then `IF manual < 1`. Setting `stop` looks like it should free the coils and does the opposite: the `ELSE` branch runs instead and drives `compressor`, `systemValve` and `gstSig` to `FALSE`, twenty times a second. Pin a coil on that way and you are fighting the program harder, not less.

Setting `manual` is the door. The inner `IF` has no `ELSE`, so in manual mode nothing assigns those three coils at all &mdash; a forced coil simply stays forced. The one exception is `heartbeat` on coil 0, which is written above both guards and keeps blinking whatever mode the plant is in. A control system's own operating modes are part of its attack surface, and the mode that does nothing is more dangerous than the one that shouts.

## IEC 61131-3 languages

PLC programs are written in the languages standardised by **IEC 61131-3**. The one you actually meet in CybICS is **Structured Text (ST)**, a Pascal-like textual language: `cybICS.st` is ST from top to bottom, and the *PLC Programming* challenge has you compile and upload a modified copy of it.

**Ladder Diagram (LD)** is the notation you will meet everywhere else in industry, so it is worth being able to read one rung. Below is the compressor rule from `cybICS.st` drawn the way an electrician would have wired it. It is two statements, not one: `IF hpt < 60 AND compressorState = 0 AND gst > 50` starts the compressor, and `ELSIF hpt < 90 AND compressorState = 1 AND gst > 50` keeps it running. (`gst` is the low-pressure storage tank the compressor draws from; below 50 there is nothing left to pump.)

<figure>
<style>
.pl-r {--r: 12s;}
/* Both rungs are cybICS.st:47-53 verbatim. Rung A starts the compressor
   below 60; rung B seals it in up to 90. Which rung conducts is the whole
   of the plant's hysteresis, and it is the one thing ladder shows better
   than the IF it compiles from. */
.pl-r .seg {stroke-dasharray:6 8; animation: r-flow 1.2s linear infinite;}
.pl-r .a1 {animation: r-a1 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .a2 {animation: r-a2 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .a3 {animation: r-a3 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .b1 {animation: r-b1 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .b2 {animation: r-b2 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .b3 {animation: r-b3 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .wa2 {animation: r-wa2 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wa3 {animation: r-wa3 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wa4 {animation: r-wa4 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wb2 {animation: r-wb2 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wb3 {animation: r-wb3 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wb4 {animation: r-wb4 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .ca > * {animation: r-ca var(--r) steps(1,end) infinite;}
.pl-r .cb > * {animation: r-cb var(--r) steps(1,end) infinite;}
.pl-r .rd1 {opacity:0; animation: r-rd1 var(--r) steps(1,end) infinite;}
.pl-r .rd2 {opacity:0; animation: r-rd2 var(--r) steps(1,end) infinite;}
.pl-r .rd3 {opacity:0; animation: r-rd3 var(--r) steps(1,end) infinite;}
@keyframes r-a1{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(0px)} 66.67%,99.99%{transform:translateX(0px)}}
@keyframes r-a2{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(0px)} 66.67%,99.99%{transform:translateX(0px)}}
@keyframes r-a3{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(34px)} 66.67%,99.99%{transform:translateX(34px)}}
@keyframes r-b1{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(34px)} 66.67%,99.99%{transform:translateX(0px)}}
@keyframes r-b2{0%,33.32%{transform:translateX(0px)} 33.33%,66.66%{transform:translateX(34px)} 66.67%,99.99%{transform:translateX(34px)}}
@keyframes r-b3{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(34px)} 66.67%,99.99%{transform:translateX(34px)}}
@keyframes r-wa2{0%,33.33%{stroke:#ff6b00; stroke-opacity:1} 33.33%,100%{stroke:currentColor; stroke-opacity:0.55}}
@keyframes r-wa3{0%,33.33%{stroke:#ff6b00; stroke-opacity:1} 33.33%,100%{stroke:currentColor; stroke-opacity:0.55}}
@keyframes r-wa4{0%,33.33%{stroke:#ff6b00; stroke-opacity:1} 33.33%,100%{stroke:currentColor; stroke-opacity:0.55}}
@keyframes r-wb2{0%,66.67%{stroke:#ff6b00; stroke-opacity:1} 66.67%,100%{stroke:currentColor; stroke-opacity:0.55}}
@keyframes r-wb3{0%,33.33%{stroke:currentColor; stroke-opacity:0.55} 33.33%,66.67%{stroke:#ff6b00; stroke-opacity:1} 66.67%,100%{stroke:currentColor; stroke-opacity:0.55}}
@keyframes r-wb4{0%,33.33%{stroke:currentColor; stroke-opacity:0.55} 33.33%,66.67%{stroke:#ff6b00; stroke-opacity:1} 66.67%,100%{stroke:currentColor; stroke-opacity:0.55}}
@keyframes r-ca{0%,33.33%{stroke:#ff6b00; stroke-opacity:1} 33.33%,100%{stroke:currentColor; stroke-opacity:0.55}}
@keyframes r-cb{0%,33.33%{stroke:currentColor; stroke-opacity:0.55} 33.33%,66.67%{stroke:#ff6b00; stroke-opacity:1} 66.67%,100%{stroke:currentColor; stroke-opacity:0.55}}
@keyframes r-rd1{0%,33.33%{opacity:1} 33.34%,100%{opacity:0}}
@keyframes r-rd2{0%,33.33%{opacity:0} 33.34%,66.67%{opacity:1} 66.68%,100%{opacity:0}}
@keyframes r-rd3{0%,66.67%{opacity:0} 66.68%,100%{opacity:1}}
@keyframes r-flow{to{stroke-dashoffset:-56}}
@media (prefers-reduced-motion: reduce){
  .pl-r * {animation:none !important;}
  .pl-r .a1,.pl-r .a2,.pl-r .a3 {transform:translateX(34px);}
  /* Phase 1: hpt is 55, so `hpt < 90` is closed too. Only
     `compressorState = 1` is open, which is why rung B does not conduct. */
  .pl-r .b1,.pl-r .b3 {transform:translateX(34px);}
  .pl-r .wa2,.pl-r .wa3,.pl-r .wa4,.pl-r .ca > * {stroke:#ff6b00; stroke-opacity:1;}
  .pl-r .wb2 {stroke:#ff6b00; stroke-opacity:1;}
  .pl-r .wb3,.pl-r .wb4,.pl-r .cb > * {stroke:currentColor; stroke-opacity:0.55;}
  .pl-r .rd1 {opacity:1;}
}
</style>
<svg class="pl-r" viewBox="0 0 520 220" role="img"
     aria-label="Two ladder rungs for the CybICS compressor. The first starts it when the pressure is below 60 and the compressor is currently off; the second seals it in while the pressure is below 90 and it is already on. Both also require the storage tank above 50. Watching which rung conducts as the pressure rises from 55 to 95 shows the hysteresis between 60 and 90.">
  <line x1="20" y1="20" x2="20" y2="180" stroke="currentColor" stroke-width="2"/>
  <line x1="500" y1="20" x2="500" y2="180" stroke="currentColor" stroke-width="2"/>
  <line class="seg" x1="20" y1="60" x2="90" y2="60" stroke="#ff6b00" stroke-width="2"/>
  <line class="seg" x1="20" y1="130" x2="90" y2="130" stroke="#ff6b00" stroke-width="2"/>
  <text x="26" y="90" font-size="11" opacity="0.7">rung A &mdash; start</text>
  <text x="26" y="160" font-size="11" opacity="0.7">rung B &mdash; seal-in</text>
  <line class="plate a1" x1="90" y1="44" x2="90" y2="76" stroke="currentColor" stroke-width="2"/>
  <line x1="134" y1="44" x2="134" y2="76" stroke="currentColor" stroke-width="2"/>
  <text x="112" y="36" text-anchor="middle" font-size="13">hpt &lt; 60</text>
  <line class="plate a2" x1="210" y1="44" x2="210" y2="76" stroke="currentColor" stroke-width="2"/>
  <line x1="254" y1="44" x2="254" y2="76" stroke="currentColor" stroke-width="2"/>
  <text x="232" y="36" text-anchor="middle" font-size="13">compressorState = 0</text>
  <line class="plate a3" x1="330" y1="44" x2="330" y2="76" stroke="currentColor" stroke-width="2"/>
  <line x1="374" y1="44" x2="374" y2="76" stroke="currentColor" stroke-width="2"/>
  <text x="352" y="36" text-anchor="middle" font-size="13">gst &gt; 50</text>
  <line class="plate b1" x1="90" y1="114" x2="90" y2="146" stroke="currentColor" stroke-width="2"/>
  <line x1="134" y1="114" x2="134" y2="146" stroke="currentColor" stroke-width="2"/>
  <text x="112" y="106" text-anchor="middle" font-size="13">hpt &lt; 90</text>
  <line class="plate b2" x1="210" y1="114" x2="210" y2="146" stroke="currentColor" stroke-width="2"/>
  <line x1="254" y1="114" x2="254" y2="146" stroke="currentColor" stroke-width="2"/>
  <text x="232" y="106" text-anchor="middle" font-size="13">compressorState = 1</text>
  <line class="plate b3" x1="330" y1="114" x2="330" y2="146" stroke="currentColor" stroke-width="2"/>
  <line x1="374" y1="114" x2="374" y2="146" stroke="currentColor" stroke-width="2"/>
  <text x="352" y="106" text-anchor="middle" font-size="13">gst &gt; 50</text>
  <line class="seg wa2" x1="134" y1="60" x2="210" y2="60" stroke="#ff6b00" stroke-width="2"/>
  <line class="seg wa3" x1="254" y1="60" x2="330" y2="60" stroke="#ff6b00" stroke-width="2"/>
  <line class="seg wa4" x1="374" y1="60" x2="420" y2="60" stroke="#ff6b00" stroke-width="2"/>
  <line class="seg wb2" x1="134" y1="130" x2="210" y2="130" stroke="#ff6b00" stroke-width="2"/>
  <line class="seg wb3" x1="254" y1="130" x2="330" y2="130" stroke="#ff6b00" stroke-width="2"/>
  <line class="seg wb4" x1="374" y1="130" x2="420" y2="130" stroke="#ff6b00" stroke-width="2"/>
  <g class="ca">
    <path d="M420 44 A18 16 0 0 0 420 76" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <path d="M452 44 A18 16 0 0 1 452 76" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <line x1="452" y1="60" x2="500" y2="60" stroke="#ff6b00" stroke-width="2"/>
  </g>
  <g class="cb">
    <path d="M420 114 A18 16 0 0 0 420 146" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <path d="M452 114 A18 16 0 0 1 452 146" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <line x1="452" y1="130" x2="500" y2="130" stroke="#ff6b00" stroke-width="2"/>
  </g>
  <text x="436" y="36" text-anchor="middle" font-size="13" fill="#ff6b00">compressorState</text>
  <text x="436" y="106" text-anchor="middle" font-size="13" fill="#ff6b00">compressorState</text>

  <g font-size="12" font-weight="bold">
    <text class="rd1" x="26" y="204" fill="#ff6b00">HPT 55, already off &mdash; rung A starts it</text>
    <text class="rd2" x="26" y="204" fill="#ff6b00">HPT 75, already on &mdash; rung B holds it</text>
    <text class="rd3" x="26" y="204" fill="#ff6b00">HPT 95 &mdash; neither conducts, it stops</text>
  </g>
</svg>
<figcaption>The compressor rule as two rungs, which is what <code>cybICS.st</code> lines 47 to 52 actually say. Rung A can only start the compressor while it is off; rung B can only hold it while it is on. Between 60 and 90 neither condition changes, so the compressor simply stays as it is &mdash; that gap is the hysteresis, and it is why the pressure saws instead of chattering. A third rung at line 62 copies <code>compressorState</code> to the real output coil <code>compressor</code>.</figcaption>
</figure>

## How the outside world reaches the PLC

The program's variables are bound to memory addresses in their declarations: `%QX0.1` for the compressor output, `%MW102` for the HPT reading. OpenPLC exposes those over industrial protocols, with `%QX0.0`&ndash;`%QX0.3` appearing as Modbus coils 0&ndash;3 and each `%MW`*n* as holding register 1024 + *n*. That is why HPT, declared `%MW102`, is register **1126** &mdash; the same arithmetic gives 1124 for GST, and 1132 and 1134 for `systemSen` and `boSen` &mdash; system-operational and blow-out.

OpenPLC publishes the same memory over Modbus, S7comm, DNP3 and EtherNet/IP simultaneously, which is convenient for integration and equally convenient for an attacker: as deployed here, none of them authenticate. Blocking one port does not close the door, because the same address is reachable through the next protocol along &mdash; and neither defence module closes it either. *Modbus Firewall Rules* filters port 502; *Network Segmentation* checks 8080, 502 and 4840. Pass both and register 1126 is still writable over S7comm on port 102.

Uploading a **new program** to a running controller is one of the most impactful actions in ICS: it changes how the process behaves, permanently, and no amount of watching register values will reveal it. That is exactly the *PLC Programming* challenge, and it maps to MITRE ATT&CK for ICS **T0843 Program Download**.
