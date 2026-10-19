# PLCs and the scan cycle

Every decision in the CybICS plant, from "start the compressor" to "open the valve", is made by one small computer: the PLC. Once you know how it thinks, you can tell when a forged value survives and when the controller simply overwrites it.

## What a PLC is

A **Programmable Logic Controller (PLC)** is a rugged little computer built to control machines. It reads sensors, runs a control program and switches actuators such as motors and valves, for years without a reboot.

In CybICS the PLC is **OpenPLC**, an open-source PLC in the container at `172.18.0.3`. Its plant program decides when the compressor runs and when the valves open.

<div class="callout analogy" markdown="1">
**Analogy:** picture a very strict cook who works in rounds. At the start of each round they read every order slip at once, then cook from that list without looking up, then hand out all the plates together. Slips that arrive mid-round wait for the next round. That is a PLC.
</div>

## The scan cycle

An ordinary program starts, does its work and exits. A PLC never exits. It runs a **scan cycle**: an endless loop of three phases.

1. **Read inputs.** Copy every input value into memory, once.
2. **Run the program.** Execute the whole control logic on that snapshot.
3. **Write outputs.** Send every computed output to the actuators, all at once.

Then it starts again. The CybICS PLC scans **every 50 milliseconds, twenty times a second**. Change the HPT pressure below and step through one scan to watch the PLC decide whether the compressor should run.

<div data-widget="scan-cycle"></div>

<figure class="wide">
<style>
/* The base state is the end of the story (phase 2 recomputing the coil), so a
   browser that drops animations still shows a meaningful frame. */
.pl-c {--c: 6s;}
.pl-c:where(.light-mode *) .dot {fill:#b34700;}
.pl-c .dot {animation: c-run var(--c) linear infinite;}
.pl-c .ph1 {animation: c-p1 var(--c) steps(1,end) infinite;}
.pl-c .car1,.pl-c .car3 {opacity:0;}
.pl-c .car2 {opacity:1;}
.pl-c .ph1,.pl-c .ph3 {stroke-width:0;}
.pl-c .ph2 {stroke-width:3;}
.pl-c .dot {transform: translate(-65.8px,114px);}
.pl-c .car1{animation: c-p1t var(--c) steps(1,end) infinite;}
.pl-c .car2{animation: c-p2t var(--c) steps(1,end) infinite;}
.pl-c .car3{animation: c-p3t var(--c) steps(1,end) infinite;}
.pl-c .atk {opacity:0; animation: c-atk var(--c) steps(1,end) infinite;}
.pl-c .gone{opacity:1; animation: c-gone var(--c) steps(1,end) infinite;}
.pl-c .lamp{fill-opacity:1; animation: c-lamp var(--c) steps(1,end) infinite;}
.pl-c .ph2 {animation: c-p2 var(--c) steps(1,end) infinite;}
.pl-c .ph3 {animation: c-p3 var(--c) steps(1,end) infinite;}
@keyframes c-run{0%{transform:translate(0px,0px)} 8.333%{transform:translate(-38px,10.2px)} 16.67%{transform:translate(-65.8px,38px)} 25%{transform:translate(-76px,76px)} 33.33%{transform:translate(-65.8px,114px)} 41.67%{transform:translate(-38px,141.8px)} 50%{transform:translate(0px,152px)} 58.33%{transform:translate(38px,141.8px)} 66.67%{transform:translate(65.8px,114px)} 75%{transform:translate(76px,76px)} 83.33%{transform:translate(65.8px,38px)} 91.67%{transform:translate(38px,10.2px)} 100%{transform:translate(0px,0px)}}
@keyframes c-p1{0%,16.7%{stroke-width:3} 16.71%,83.2%{stroke-width:0} 83.3%,100%{stroke-width:3}}
@keyframes c-p2{0%,16.7%{stroke-width:0} 16.71%,50%{stroke-width:3} 50.01%,100%{stroke-width:0}}
@keyframes c-p3{0%,50%{stroke-width:0} 50.01%,83.2%{stroke-width:3} 83.3%,100%{stroke-width:0}}
@keyframes c-p1t{0%,16.7%{opacity:1} 16.71%,83.2%{opacity:0} 83.3%,100%{opacity:1}}
@keyframes c-p2t{0%,16.7%{opacity:0} 16.71%,50%{opacity:1} 50.01%,100%{opacity:0}}
@keyframes c-p3t{0%,50%{opacity:0} 50.01%,83.2%{opacity:1} 83.3%,100%{opacity:0}}
@keyframes c-atk{0%,16.7%{opacity:1} 16.71%,83.2%{opacity:0} 83.3%,100%{opacity:1}}
@keyframes c-gone{0%,16.7%{opacity:0} 16.71%,50%{opacity:1} 50.01%,100%{opacity:0}}
@keyframes c-lamp{0%,16.7%{fill-opacity:0.15} 16.71%,83.2%{fill-opacity:1} 83.3%,100%{fill-opacity:0.15}}
@media (prefers-reduced-motion: reduce){
  .pl-c * {animation:none !important;}
}
</style>
<svg class="pl-c" viewBox="0 0 440 244" role="img"
     aria-label="The PLC scan cycle as a ring. A marker travels clockwise past three boxes in turn: read inputs, run program, write outputs, and back to the start. Meanwhile an attacker writes coil 1 off with Modbus function code 5. The write lands between two scans; then the program phase recomputes the coil from the logic and the attacker's value is gone.">
  <defs>
    <marker id="ah" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/>
    </marker>
  </defs>
  <circle cx="220" cy="140" r="76" fill="none" stroke="currentColor" stroke-opacity="0.65" stroke-width="2"/>
  <path d="M 200.3 66.6 A76 76 0 0 0 146.6 159.7" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M 166.3 193.7 A76 76 0 0 0 273.7 193.7" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M 293.4 159.7 A76 76 0 0 0 239.7 66.6" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>

  <g font-size="12" text-anchor="middle">
    <rect class="ph1" x="152" y="10" width="136" height="44" rx="6" fill="#ff6b00" stroke="currentColor" stroke-width="0"/>
    <text x="220" y="31" style="fill:#1a1a1a" font-weight="bold">1. Read inputs</text>
    <text x="220" y="46" style="fill:#1a1a1a" font-size="11">sensors &rarr; memory</text>
    <rect class="ph2" x="4" y="176" width="136" height="44" rx="6" fill="#ff6b00" stroke="currentColor" stroke-width="0"/>
    <text x="72" y="197" style="fill:#1a1a1a" font-weight="bold">2. Run program</text>
    <text x="72" y="212" style="fill:#1a1a1a" font-size="11">logic on the values</text>
    <rect class="ph3" x="300" y="176" width="136" height="44" rx="6" fill="#ff6b00" stroke="currentColor" stroke-width="0"/>
    <text x="368" y="197" style="fill:#1a1a1a" font-weight="bold">3. Write outputs</text>
    <text x="368" y="212" style="fill:#1a1a1a" font-size="11">memory &rarr; actuators</text>
  </g>

  <circle class="dot" cx="220" cy="64" r="7" fill="#ff6b00" stroke="#1a1a1a" stroke-width="1"/>
  <circle class="lamp" cx="192" cy="108" r="8" fill="#ff6b00" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="208" y="113" font-size="12" opacity="0.85">coil 1</text>
  <g text-anchor="middle" font-size="12">
    <text class="car1" x="220" y="136" fill="#ff6b00" font-weight="bold">hpt = 75, put there by hwio</text>
    <text class="car2" x="220" y="136" fill="#ff6b00" font-weight="bold">decides: keep it on</text>
    <text class="car3" x="220" y="136" fill="#ff6b00" font-weight="bold">writes coil 1 = on</text>
    <text x="220" y="156" opacity="0.7" font-size="11">one scan, 50 ms</text>
  </g>
  <g font-size="11">
    <text class="atk" x="4" y="236" fill="#ff6b00" font-weight="bold">attacker: FC 05 sets coil 1 = off, between scans</text>
    <text class="gone" x="4" y="236" opacity="0.75">&hellip; and phase 2 recomputes the coil, here</text>
  </g>
</svg>
<figcaption>One scan: read all inputs, run the program on that snapshot, write all outputs, repeat 50 ms later. The lamp is coil 1, the compressor: an attacker switches it off between two scans, and phase 2 switches it straight back on.</figcaption>
</figure>

<div data-widget="checkpoint" data-id="scan"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: why a loop, where the 50 ms come from and when a write lands</summary>

Why a loop instead of reacting to events? A machine that can hurt someone needs a worst case you can state. With a fixed scan, every input is acted on within one period, on a consistent snapshot. Engineers call this **determinism**: the same inputs always give the same outputs, on time.

The program sets its own rhythm in its configuration, `TASK TaskMain(INTERVAL := T#50ms, ...)` in `software/OpenPLC/cybICS.st`.

Inside OpenPLC, every phase of the scan, and every Modbus request, takes the same lock (`bufferLock`) on the shared memory. A Modbus write therefore cannot land in the middle of the program; it waits for the gap between scans. That is why the figure above shows the attacker's write arriving between two scans.

</details>

## The compressor rule

PLC programs are written in the languages of the standard **IEC 61131-3**. CybICS uses **Structured Text (ST)**, which reads a lot like Python or Pascal. Here is the heart of the plant program:

```
IF hpt < 60 AND compressorState = 0 AND gst > 50 THEN
  compressorState := 1;        (* start *)
ELSIF hpt < 90 AND compressorState = 1 AND gst > 50 THEN
  compressorState := 1;        (* keep running *)
ELSE
  compressorState := 0;        (* stop *)
END_IF;
```

In words: start the compressor when the high-pressure tank (HPT) drops below 60, keep it running until 90, and never run it when the gas storage tank (GST) holds 50 or less, because there is nothing left to pump. A later line copies `compressorState` to the real output, `compressor`.

Why two thresholds? With a single limit of 75, the compressor would flick on and off as the pressure wobbled around it. The gap between 60 and 90 is called **hysteresis**; your home thermostat uses the same trick.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the other rules and the two guards</summary>

The program has three more rules:

| Output | Rule in automatic mode |
|---|---|
| System valve | Open while the HPT is between 50 and 100 |
| GST refill (`gstSig`) | Start refilling when the GST drops below 60, stop at 240 |
| Heartbeat | Blinks about once per two seconds, whatever the mode |

Two guards sit around the plant outputs. If `stop` is set, the program forces the compressor, the system valve and the refill off. If `manual` is set, it stops assigning those three outputs at all, and the operator's HMI buttons take over.

</details>

<details class="deep-dive" markdown="1">
<summary>Deep dive: the same rule as a ladder diagram, and the other languages</summary>

Engineers outside CybICS often draw the same logic as a **Ladder Diagram (LD)**, which looks like an electrical wiring plan. Here is the compressor rule as one rung:

<figure class="wide">
<style>
.pl-r {--r: 12s; --w:#ff6b00;}
.pl-r:where(.light-mode *) {--w:#b34700;}
/* Marching dashes mean current; a dead segment drops its dashes entirely. */
.pl-r .seg {animation: r-flow 1.2s linear infinite;}
.pl-r .live {stroke:var(--w); stroke-dasharray:6 4;}
.pl-r .a1 {animation: r-a1 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .a2 {animation: r-a2 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .b1 {animation: r-b1 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .b2 {animation: r-b2 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .c3 {animation: r-c3 var(--r) cubic-bezier(.4,0,.2,1) infinite;}
.pl-r .wa1 {animation: r-wa1 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wa2 {animation: r-wa2 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wb1 {animation: r-wb1 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wb2 {animation: r-wb2 var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wt {animation: r-wt var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .wc {animation: r-wc var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .coil > * {animation: r-coil var(--r) steps(1,end) infinite, r-flow 1.2s linear infinite;}
.pl-r .a1,.pl-r .a2,.pl-r .b1,.pl-r .c3 {transform: translateX(34px);}
.pl-r .wa1,.pl-r .wa2,.pl-r .wb1,.pl-r .wt,.pl-r .wc,
.pl-r .coil > * {stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4;}
.pl-r .wb2 {stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none;}
.pl-r .rd1 {opacity:1; animation: r-rd1 var(--r) steps(1,end) infinite;}
.pl-r .rd2 {opacity:0; animation: r-rd2 var(--r) steps(1,end) infinite;}
.pl-r .rd3 {opacity:0; animation: r-rd3 var(--r) steps(1,end) infinite;}
@keyframes r-flow{to{stroke-dashoffset:-56}}
@keyframes r-a1{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(0px)} 66.67%,99.99%{transform:translateX(0px)}}
@keyframes r-a2{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(0px)} 66.67%,99.99%{transform:translateX(0px)}}
@keyframes r-b1{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(34px)} 66.67%,99.99%{transform:translateX(0px)}}
@keyframes r-b2{0%,33.32%{transform:translateX(0px)} 33.33%,66.66%{transform:translateX(34px)} 66.67%,99.99%{transform:translateX(34px)}}
@keyframes r-c3{0%,33.32%{transform:translateX(34px)} 33.33%,66.66%{transform:translateX(34px)} 66.67%,99.99%{transform:translateX(34px)}}
@keyframes r-wa1{0%,33.32%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 33.33%,66.66%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none} 66.67%,99.99%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none}}
@keyframes r-wa2{0%,33.32%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 33.33%,66.66%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none} 66.67%,99.99%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none}}
@keyframes r-wb1{0%,33.32%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 33.33%,66.66%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 66.67%,99.99%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none}}
@keyframes r-wb2{0%,33.32%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none} 33.33%,66.66%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 66.67%,99.99%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none}}
@keyframes r-wt{0%,33.32%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 33.33%,66.66%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 66.67%,99.99%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none}}
@keyframes r-wc{0%,33.32%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 33.33%,66.66%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 66.67%,99.99%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none}}
@keyframes r-coil{0%,33.32%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 33.33%,66.66%{stroke:var(--w); stroke-opacity:1; stroke-dasharray:6 4} 66.67%,99.99%{stroke:currentColor; stroke-opacity:0.55; stroke-dasharray:none}}
@keyframes r-rd1{0%,33.32%{opacity:1} 33.33%,66.66%{opacity:0} 66.67%,99.99%{opacity:0}}
@keyframes r-rd2{0%,33.32%{opacity:0} 33.33%,66.66%{opacity:1} 66.67%,99.99%{opacity:0}}
@keyframes r-rd3{0%,33.32%{opacity:0} 33.33%,66.66%{opacity:0} 66.67%,99.99%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .pl-r * {animation:none !important;}
}
</style>
<svg class="pl-r" viewBox="0 0 520 214" role="img"
     aria-label="One ladder rung for the CybICS compressor. Two branches run in parallel from the left rail: the upper one closes when the pressure is below 60 and the compressor is currently off, the lower one when the pressure is below 90 and it is already on. They rejoin, pass through a contact requiring the storage tank above 50, and drive a single compressorState coil. As the pressure rises from 55 to 75 to 95, the upper branch conducts, then only the lower one, then neither.">
  <line x1="20" y1="40" x2="20" y2="160" stroke="currentColor" stroke-width="2"/>
  <line x1="500" y1="40" x2="500" y2="160" stroke="currentColor" stroke-width="2"/>
  <line class="seg live" x1="20" y1="100" x2="70" y2="100" stroke-width="2"/>
  <line class="seg live" x1="70" y1="70" x2="70" y2="130" stroke-width="2"/>
  <line class="seg live" x1="70" y1="70" x2="100" y2="70" stroke-width="2"/>
  <line class="seg live" x1="70" y1="130" x2="100" y2="130" stroke-width="2"/>
  <line class="seg wt" x1="330" y1="70" x2="330" y2="130" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
  <line class="a1" x1="100" y1="54" x2="100" y2="86" stroke="currentColor" stroke-width="2"/>
  <line x1="144" y1="54" x2="144" y2="86" stroke="currentColor" stroke-width="2"/>
  <text x="122" y="48" text-anchor="middle" font-size="13">hpt &lt; 60</text>
  <line class="a2" x1="210" y1="54" x2="210" y2="86" stroke="currentColor" stroke-width="2"/>
  <line x1="254" y1="54" x2="254" y2="86" stroke="currentColor" stroke-width="2"/>
  <text x="232" y="48" text-anchor="middle" font-size="13">compressorState = 0</text>
  <line class="b1" x1="100" y1="114" x2="100" y2="146" stroke="currentColor" stroke-width="2"/>
  <line x1="144" y1="114" x2="144" y2="146" stroke="currentColor" stroke-width="2"/>
  <text x="122" y="162" text-anchor="middle" font-size="13">hpt &lt; 90</text>
  <line class="b2" x1="210" y1="114" x2="210" y2="146" stroke="currentColor" stroke-width="2"/>
  <line x1="254" y1="114" x2="254" y2="146" stroke="currentColor" stroke-width="2"/>
  <text x="232" y="162" text-anchor="middle" font-size="13">compressorState = 1</text>
  <line class="c3" x1="360" y1="84" x2="360" y2="116" stroke="currentColor" stroke-width="2"/>
  <line x1="404" y1="84" x2="404" y2="116" stroke="currentColor" stroke-width="2"/>
  <text x="382" y="78" text-anchor="middle" font-size="13">gst &gt; 50</text>
  <line class="seg wa1" x1="144" y1="70" x2="210" y2="70" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
  <line class="seg wa2" x1="254" y1="70" x2="330" y2="70" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
  <line class="seg wb1" x1="144" y1="130" x2="210" y2="130" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
  <line class="seg wb2" x1="254" y1="130" x2="330" y2="130" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
  <line class="seg wt" x1="330" y1="100" x2="360" y2="100" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
  <line class="seg wc" x1="404" y1="100" x2="412" y2="100" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
  <g class="coil">
    <path d="M430 84 A18 16 0 0 0 430 116" fill="none" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
    <path d="M462 84 A18 16 0 0 1 462 116" fill="none" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
    <line x1="480" y1="100" x2="500" y2="100" stroke="currentColor" stroke-opacity="0.55" stroke-width="2"/>
  </g>
  <text x="446" y="60" text-anchor="middle" font-size="13" fill="#ff6b00">compressorState</text>
  <text x="26" y="36" font-size="12" opacity="0.7">start branch</text>
  <text x="26" y="176" font-size="12" opacity="0.7">seal-in branch</text>

  <g font-size="13" font-weight="bold">
    <text class="rd1" x="26" y="204" fill="#ff6b00">HPT 55, compressor off &mdash; the start branch conducts</text>
    <text class="rd2" x="26" y="204" fill="#ff6b00">HPT 75, compressor on &mdash; only the seal-in branch does</text>
    <text class="rd3" x="26" y="204" fill="#ff6b00">HPT 95 &mdash; neither branch conducts, it stops</text>
  </g>
</svg>
<figcaption>Read a rung like an electric circuit: "current" flows from the left rail to the coil on the right only if a path of closed contacts connects them. The upper branch can only start the compressor while it is off; the lower one, the "seal-in", can only keep it running while it is on. Between 60 and 90 neither changes the state, and that is the hysteresis. For clarity, the storage-tank check that the ST repeats in both branches is drawn once.</figcaption>
</figure>

IEC 61131-3 defines Ladder Diagram (LD), Function Block Diagram (FBD), Structured Text (ST), Sequential Function Chart (SFC) and Instruction List (IL, now deprecated). OpenPLC compiles them all to C; CybICS only uses ST.

</details>

## Who owns a value?

An attacker on the network can write values into the PLC over [Modbus](/theory/modbus). Whether the forged value *sticks* depends on one question: **who writes that address next?**

- **Coil 1 is the compressor.** The program computes it on every scan. Force it off and, in automatic mode, the next scan puts back whatever the logic says, within 50 ms.
- **Register 1126 is the HPT pressure.** The program only *reads* it. `hwio`, the plant simulation, pushes the current value in over Modbus about every 20 ms, so a forged pressure lasts only until `hwio` writes again.

<figure class="wide">
<style>
.pl-t {--t: 8s;}
.pl-t:where(.light-mode *) .barA, .pl-t:where(.light-mode *) .barB {fill:#b34700;}
.pl-t .head {animation: t-head var(--t) linear infinite;}
.pl-t .barA, .pl-t .barB {transform-box: fill-box; transform-origin: left;}
.pl-t .barA {animation: t-barA var(--t) linear infinite;}
.pl-t .barB {animation: t-barB var(--t) linear infinite;}
.pl-t .head {transform: translateX(410px);}
.pl-t .barA, .pl-t .barB {transform: scaleX(1);}
.pl-t .fixA {opacity:1; animation: t-fixA var(--t) steps(1,end) infinite;}
.pl-t .fixB {opacity:1; animation: t-fixB var(--t) steps(1,end) infinite;}
.pl-t .shot {opacity:1; animation: t-shot var(--t) steps(1,end) infinite;}
@keyframes t-head{0%{transform:translateX(0)} 70%,100%{transform:translateX(410px)}}
@keyframes t-shot{0%,10.4%{opacity:0} 10.5%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes t-barA{0%,10.5%{transform:scaleX(0)} 17.5%,96%{transform:scaleX(1)} 96.01%,100%{transform:scaleX(0)}}
@keyframes t-barB{0%,10.5%{transform:scaleX(0)} 14%,96%{transform:scaleX(1)} 96.01%,100%{transform:scaleX(0)}}
@keyframes t-fixA{0%,17.4%{opacity:0} 17.5%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes t-fixB{0%,13.9%{opacity:0} 14%,96%{opacity:1} 96.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .pl-t * {animation:none !important;}
}
</style>
<svg class="pl-t" viewBox="0 0 520 210" role="img"
     aria-label="A timeline over 200 milliseconds. An attacker writes at 30 milliseconds. Coil 1 is restored by the PLC scan at 50 milliseconds; register 1126 is restored by hwio at 40 milliseconds. The two are owned by different writers running at different rates.">
  <g font-size="13" opacity="0.7">
    <line x1="90" y1="182" x2="500" y2="182" stroke="currentColor"/>
    <text x="90"    y="198" text-anchor="middle">0 ms</text>
    <text x="192.5" y="198" text-anchor="middle">50</text>
    <text x="295"   y="198" text-anchor="middle">100</text>
    <text x="397.5" y="198" text-anchor="middle">150</text>
    <text x="500"   y="198" text-anchor="middle">200</text>
  </g>

  <g class="head">
    <line x1="90" y1="24" x2="90" y2="178" stroke="currentColor" stroke-width="2.5"/>
    <path d="M 84 178 L 96 178 L 90 188 Z" fill="currentColor"/>
  </g>
  <text x="10" y="52" font-size="13" font-weight="bold">coil 1</text>
  <text x="10" y="66" font-size="13" opacity="0.75">the scan</text>
  <text x="10" y="79" font-size="13" opacity="0.75">owns it</text>
  <line x1="90" y1="40" x2="500" y2="40" stroke="currentColor" stroke-opacity="0.45"/>
  <g stroke="currentColor" stroke-opacity="0.65">
    <line x1="90"    y1="34" x2="90"    y2="74"/><line x1="192.5" y1="34" x2="192.5" y2="74"/>
    <line x1="295"   y1="34" x2="295"   y2="74"/><line x1="397.5" y1="34" x2="397.5" y2="74"/>
    <line x1="500"   y1="34" x2="500"   y2="74"/>
  </g>
  <rect class="barA" x="151.5" y="44" width="41" height="22" rx="3" fill="#ff6b00"/>
  <g class="fixA"><path d="M 192.5 44 L 188 36 L 197 36 Z" fill="#ff6b00"/><text x="210" y="24" font-size="13" fill="#ff6b00" font-weight="bold">the scan puts it back</text></g>

  <text x="10" y="122" font-size="13" font-weight="bold">reg 1126</text>
  <text x="10" y="136" font-size="13" opacity="0.75">hwio &ge;20 ms</text>
  <text x="10" y="149" font-size="13" opacity="0.75">owns it</text>
  <line x1="90" y1="110" x2="500" y2="110" stroke="currentColor" stroke-opacity="0.45"/>
  <g stroke="currentColor" stroke-opacity="0.65">
    <line x1="90"  y1="104" x2="90"  y2="144"/><line x1="131" y1="104" x2="131" y2="144"/>
    <line x1="172" y1="104" x2="172" y2="144"/><line x1="213" y1="104" x2="213" y2="144"/>
    <line x1="254" y1="104" x2="254" y2="144"/><line x1="295" y1="104" x2="295" y2="144"/>
    <line x1="336" y1="104" x2="336" y2="144"/><line x1="377" y1="104" x2="377" y2="144"/>
    <line x1="418" y1="104" x2="418" y2="144"/><line x1="459" y1="104" x2="459" y2="144"/>
    <line x1="500" y1="104" x2="500" y2="144"/>
  </g>
  <rect class="barB" x="151.5" y="114" width="20.5" height="22" rx="3" fill="#ff6b00"/>
  <g class="fixB"><path d="M 172 114 L 167.5 106 L 176.5 106 Z" fill="#ff6b00"/><text x="180" y="100" font-size="13" fill="#ff6b00" font-weight="bold">hwio puts it back</text></g>

  <g class="shot">
    <line x1="151.5" y1="26" x2="151.5" y2="160" stroke="#ff6b00" stroke-width="2" stroke-dasharray="4 3"/>
    <text x="90" y="20" font-size="13" fill="#ff6b00" font-weight="bold">one write, t = 30 ms</text>
  </g>
</svg>
<figcaption>Two addresses, two owners, two clocks. One forged write lands in both rows at once. The PLC's next scan restores the coil; <code>hwio</code>'s next write restores the register. The orange bars show how long the forged value lasted.</figcaption>
</figure>

To keep a forged value in place, you have to write it *faster than its owner*: that is the [Flood & Overwrite](/theory/flood_overwrite) challenge, and it is noisy for exactly that reason. The quieter alternative is to change the *program*, so the PLC computes the attacker's values itself: the [PLC Programming](/theory/plc_programming) challenge.

In **manual** mode the program stops assigning the compressor, the system valve and the refill, so a forced coil simply stays where it was put; only the heartbeat on coil 0 keeps blinking. (The `stop` register is different: it forces those three outputs off.) A mode that does nothing can be more dangerous than one that shouts.

## Reaching the PLC from outside

Each variable in the program is bound to a PLC memory address, such as `compressor AT %QX0.1` or `hpt AT %MW102`. OpenPLC publishes that memory over Modbus with a simple rule: output bit `%QX0.`*n* becomes **coil *n***, and memory word `%MW`*n* becomes **holding register 1024 + *n***. So `hpt AT %MW102` is register 1126.

Modbus is not the only door: S7comm, DNP3 and EtherNet/IP reach the same memory, and none of them asks for a password. The most powerful action is uploading a **new program**: it changes the plant's behaviour permanently, and watching register values never reveals it. MITRE ATT&CK for ICS calls this **T0843 Program Download**.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the full address map, the other ports and how the outputs reach the plant</summary>

| Variable | PLC address | Modbus address |
|---|---|---|
| `heartbeat`, `compressor`, `systemValve`, `gstSig` | `%QX0.0` to `%QX0.3` | coils 0 to 3 |
| `gst` (storage tank) | `%MW100` | register 1124 |
| `hpt` (high-pressure tank) | `%MW102` | register 1126 |
| `systemSen` (plant healthy) | `%MW108` | register 1132 |
| `boSen` (blow-out active) | `%MW110` | register 1134 |

The OpenPLC container exposes its S7comm server on port 102, DNP3 on 20000 and EtherNet/IP on 44818, next to Modbus on 502. Blocking one port does not close the door when the same memory is reachable through the next one.

`cybICS.st` declares no `%I` input addresses at all: every located variable is a `%QX` output or a `%MW` memory word. In the Docker testbed OpenPLC also runs a "blank" hardware layer, so phase 3 drives no physical pins. The plant only sees the outputs because `hwio` reads the coils back over Modbus. On real hardware, `hwio-raspberry` plays the same bridge role between OpenPLC and the STM32 that runs the process.

</details>
