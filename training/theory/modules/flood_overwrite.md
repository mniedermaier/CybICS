# Flood and overwrite

Modbus accepts any write from anyone, so an attacker can write the same register over and over. The interesting part is not that the write lands &mdash; the *Modbus* topic covers why nothing stops it &mdash; but what happens next. The flood does not break the plant. It lies to the controller, and the controller does the damage.

## Why there is a register to fight over at all

OpenPLC maps each `%MW`*n* in the program onto holding register 1024 + *n*. `hpt AT %MW102` is therefore register 1126, and a holding register is a single address space with no notion of who owns the word. The sensor path and the attacker's write path are not two channels that happen to meet &mdash; they are literally the same sixteen bits, and the protocol has no field in which to disagree about that.

## Winning a race, not defeating a check

The PLC program only ever reads 1126; what keeps it truthful is `hwio`, whose loop does a coil read and five register writes and then sleeps 20 ms &mdash; 20.7 ms a pass, measured on this stack from the period of the physics tick, which is fifty-one passes and came out at 1.06 s. A single forged write survives roughly ten milliseconds and is gone.

`flooding_hpt.py` writes in a loop with `time.sleep(0.001)`, but the sleep is not the period: each pass also waits for a Modbus response. Measured against this stack it manages **about eight hundred writes a second** from either the attack machine or the landing container, so seventeen or eighteen of its writes land between one `hwio` write and the next.

<figure>
<style>
.fo-r {--d: 12s; --on:#ff6b00; --notch:#141414;}
html.light-mode .fo-r {--on:#b34700; --notch:#ffffff;}
/* Two clocks against one register. The point is the ratio: the attacker's
   writes are not stronger, only more frequent. The loop runs long enough that
   it is still moving when a reader gets here. */
.fo-r .head {animation: r-head var(--d) linear 20 forwards;}
.fo-r .lane {animation: r-wipe var(--d) linear 20 forwards;}
@keyframes r-head{0%{transform:translateX(0)} 90%,100%{transform:translateX(340px)}}
@keyframes r-wipe{0%{clip-path:inset(0 100% 0 0)} 90%,100%{clip-path:inset(0 0 0 0)}}
@media (prefers-reduced-motion: reduce){
  .fo-r .head{animation:none; transform:translateX(340px)}
  .fo-r .lane{animation:none}
}
</style>
<svg class="fo-r" viewBox="0 0 460 196" role="img"
     aria-label="A hundred-millisecond timeline. The attacker writes register 1126 about every 1.3 milliseconds; hwio writes the true value back every 20.7 milliseconds. The register therefore holds the forged value for all but about 0.65 milliseconds in every 20.7.">
  <text x="8" y="46" font-size="14" opacity="0.85">attacker</text>
  <text x="8" y="60" font-size="13" opacity="0.7">~1.2 ms</text>
  <g class="lane"><rect x="80.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="84.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="88.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="92.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="96.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="100.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="104.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="108.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="112.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="116.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="120.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="124.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="129.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="133.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="137.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="141.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="145.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="149.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="153.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="157.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="161.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="165.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="169.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="173.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="177.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="182.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="186.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="190.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="194.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="198.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="202.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="206.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="210.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="214.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="218.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="222.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="226.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="231.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="235.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="239.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="243.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="247.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="251.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="255.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="259.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="263.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="267.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="271.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="275.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="279.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="284.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="288.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="292.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="296.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="300.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="304.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="308.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="312.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="316.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="320.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="324.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="328.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="333.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="337.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="341.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="345.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="349.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="353.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="357.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="361.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="365.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="369.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="373.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="377.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="381.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="386.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="390.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="394.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="398.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="402.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="406.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="410.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="414.6" y="42" width="1.8" height="16" fill="var(--on)"/></g>
  <text x="8" y="96" font-size="14" opacity="0.85">hwio</text>
  <text x="8" y="110" font-size="13" opacity="0.7">20.7 ms</text>
  <g class="lane"><rect x="80.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="148.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="216.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="284.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="352.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="420.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/></g>
  <text x="8" y="146" font-size="14" opacity="0.85">reg 1126</text>
  <text x="8" y="160" font-size="13" opacity="0.7">holds</text>
  <g class="lane">
    <rect x="80" y="142" width="340" height="16" fill="var(--on)"/>
    <rect x="80.0" y="142" width="2.1" height="16" fill="var(--notch)"/><rect x="148.0" y="142" width="2.1" height="16" fill="var(--notch)"/><rect x="216.0" y="142" width="2.1" height="16" fill="var(--notch)"/><rect x="284.0" y="142" width="2.1" height="16" fill="var(--notch)"/><rect x="352.0" y="142" width="2.1" height="16" fill="var(--notch)"/>
  </g>
  <line class="head" x1="80" y1="34" x2="80" y2="166" stroke="currentColor" stroke-width="2"/>
  <g font-size="13" opacity="0.7">
    <text x="80" y="182" text-anchor="middle">0 ms</text>
    <text x="250" y="182" text-anchor="middle">50</text>
    <text x="420" y="182" text-anchor="middle">100</text>
  </g>
</svg>
<figcaption>The orange band is the forged value; the dark notches are the moments <code>hwio</code> gets its measurement in before the next attacker write buries it. <code>hwio</code> owns the word about <strong>3%</strong> of the time. Note it is not the ratio of the two periods: <code>hwio</code>'s write lands at a random point inside an attacker interval, so what survives is the <em>residual</em> of that interval, which averages half of it. 0.65 ms out of 20.7 is the number, and halving is what a race does.</figcaption>
</figure>

## What the controller does with a lie

Read `cybICS.st` with `hpt` reading 10. Two rules fire, and both are the program working as designed.

- `IF hpt < 60 AND compressorState = 0 AND gst > 50` starts the compressor, and `ELSIF hpt < 90 AND compressorState = 1 AND gst > 50` holds it on. Scan to scan it is the seal-in doing the work; the start branch is what brings the compressor back after each drop-out.
- `IF hpt > 50 AND hpt < 100 THEN systemValve := TRUE` is false at 10, so the system valve shuts and the downstream process stops drawing.

So the compressor runs and nothing draws. The attacker never touched the compressor coil or the valve coil.

The compressor does drop out, and there are two reasons for it on two very different scales.

The first is the race in the figure above, and it turns out to be almost nothing. A scan that happens to sample the true pressure only breaks the hold once that pressure is above 90 &mdash; below it the seal-in branch is still satisfied and the compressor stays on. Past 90, a true read fails both conditions at once, the `ELSE` fires, and the compressor stops for exactly one scan: fifty milliseconds. Measured across a flood while the storage tank still had gas in it, the compressor was on **99.1%** of the time. The blink is real and it is over before anything mechanical could notice.

The second is far larger, and the attacker has no hand in it. The compressor moves two units of storage for every one unit of pressure, and the program refills the storage tank on its own hysteresis: `IF gst < 60 AND gstState = 0` opens the supply and `gst < 240` keeps it open. Under a compressor that never switches off, the tank drains faster than the supply refills it and walks down to the `gst > 50` guard &mdash; which is a condition in *both* branches of the compressor rule, reading register **1124**, which the attacker is not flooding.

Measured over a hundred and fifty seconds of flood, starting from a storage tank at 112: the compressor was on 72.5% of the time overall, and **99% of the lost time fell in samples where the tank was at or below 52**. Above 52 it ran 99.1%. The duty cycle is not a property of the attack at all. It is a property of how much gas was in the tank when the attack started.

That is worth sitting with. The forgery is perfect &mdash; the controller has no way to doubt register 1126 &mdash; and what limits the damage is a second register the attacker never touched, enforced by a condition written for an entirely unrelated reason: to stop the compressor grinding against an empty tank. The plant's own material balance is the last line of defence here, and nobody wrote it as a safety function.

<figure>
<style>
.fo-d {--d: 14s; --on:#ff6b00;}
html.light-mode .fo-d {--on:#b34700;}
/* pathLength normalises both paths to 1000 units so the dash offset and the
   playhead advance together -- without it the traces finish in a quarter of
   the sweep. */
.fo-d .trace {stroke-dasharray:1000; animation: d-draw var(--d) linear 18 forwards;}
/* The flat trace runs parallel to the axis and both are currentColor, so at
   figure scale they merged into one heavy rule and the "reads 10" label
   annotated the wrong line. The axis moved down and this one carries a round
   cap and a wider stroke, so it reads as data. */
.fo-d .flat {stroke-linecap:round;}
.fo-d .head  {animation: d-head var(--d) linear 18 forwards;}
@keyframes d-draw{0%{stroke-dashoffset:1000} 88%,100%{stroke-dashoffset:0}}
@keyframes d-head{0%{transform:translateX(0)} 88%,100%{transform:translateX(280px)}}
@media (prefers-reduced-motion: reduce){
  .fo-d .trace{animation:none; stroke-dashoffset:0}
  .fo-d .head {animation:none; transform:translateX(280px)}
}
</style>
<svg class="fo-d" viewBox="0 0 460 210" role="img"
     aria-label="Two traces over about five minutes. The value OpenPLC reads from register 1126 stays flat at 10. The pressure actually in the tank climbs from 75, reaching the relief valve at about three minutes and the 255 ceiling at about five. The compressor runs almost continuously with the system valve shut, until the storage tank runs down.">
  <line x1="60" y1="30" x2="60" y2="164" stroke="currentColor" stroke-opacity="0.6"/>
  <line x1="60" y1="164" x2="340" y2="164" stroke="currentColor" stroke-opacity="0.6"/>
  <g font-size="13" opacity="0.7">
    <text x="54" y="34" text-anchor="end">255</text>
    <text x="54" y="51" text-anchor="end">220</text>
    <text x="54" y="154" text-anchor="end">10</text>
    <text x="60" y="180" text-anchor="middle">0</text>
    <text x="200" y="180" text-anchor="middle">2.5 min</text>
    <text x="340" y="180" text-anchor="middle">5 min</text>
  </g>
  <line x1="60" y1="47" x2="340" y2="47" stroke="var(--on)" stroke-dasharray="4 3"/>
  <text x="346" y="51" font-size="13" fill="var(--on)">relief valve</text>

  <polyline class="trace flat" pathLength="1000" points="60,150 340,150" fill="none" stroke="currentColor" stroke-width="3" stroke-opacity="0.85"/>
  <text x="346" y="154" font-size="13" opacity="0.75">reads 10</text>
  <polyline class="trace" pathLength="1000" points="60,118 150,80 228,47 312,30 340,30" fill="none" stroke="var(--on)" stroke-width="2.5"/>
  <text x="346" y="34" font-size="13" fill="var(--on)">the tank</text>

  <rect x="60" y="186" width="280" height="14" rx="3" fill="#ff6b00"/>
  <text x="200" y="197" text-anchor="middle" font-size="13" style="fill:#1a1a1a" font-weight="bold">compressor on, valve shut</text>
  <line class="head" x1="60" y1="26" x2="60" y2="170" stroke="currentColor" stroke-width="2"/>
</svg>
<figcaption>The physics advances one tick per <em>fifty-one</em> passes of <code>hwio</code>'s outer loop &mdash; the <code>if delay &gt; 50</code> gate &mdash; so a tick is about 1.06 seconds, not 21 milliseconds. That is why a millisecond-scale race has a minute-scale consequence: roughly three minutes to the relief valve and about five to the ceiling. Above the dashed line the rise falls to about 0.29 units per second against 0.83 below it &mdash; not half but nearer a third, because by then the relief valve is not the only thing pushing back: the storage tank is running down as well.</figcaption>
</figure>

Watching this from the HMI has a catch. FUXA's HPT trend reads the same register the flood is pinning, so it shows a flat 10 with nothing to diverge from. What it *does* show is `boSen`, the blow-out flag, which `hwio` sets from the true pressure: the trend sits at 10 while the alarm goes high.

## Why this one is loud

Rule 3 counts fifty writes inside a five-second window from anything that is not `hwio`, `fuxa` or `openplc`. At eight hundred a second the fiftieth write lands about sixty milliseconds after the first, and the challenge's verifier simply asks the IDS whether the rule fired.

The *IDS Evasion* challenge is the same kind of write from the same host &mdash; three of them, five seconds apart, aimed at register 1124 &mdash; and trips nothing. The two sit at opposite ends of one axis, and the gap between them is larger than any single picture can hold.

<figure>
<style>
.fo-c {--d: 7s; --on:#ff6b00;}
html.light-mode .fo-c {--on:#b34700;}
.fo-c .fill {transform-box: fill-box; transform-origin: left;
             animation: c-fill var(--d) linear 40 forwards;}
.fo-c .tick {transform-box: fill-box; transform-origin: bottom;
             animation-duration:var(--d); animation-timing-function:steps(1,end);
             animation-iteration-count:40; animation-fill-mode:forwards;}
.fo-c .t1{animation-name:c-t1} .fo-c .t2{animation-name:c-t2} .fo-c .t3{animation-name:c-t3}
.fo-c .alarm{animation: c-alarm var(--d) steps(1,end) 40 forwards;}
.fo-c .slow {animation: c-slow var(--d) steps(1,end) 40 forwards;}
/* The two rows are NOT one clock, and cannot be: 1.2 ms against 5 s is four
   thousand to one. Each row carries its own span label, and the caption says
   why no single axis holds both. */
@keyframes c-fill {0%{transform:scaleX(0)} 8%,100%{transform:scaleX(1)}}
@keyframes c-alarm{0%,8%{opacity:0} 9%,100%{opacity:1}}
@keyframes c-t1{0%,3%{transform:scaleY(0)} 4%,100%{transform:scaleY(1)}}
@keyframes c-t2{0%,33%{transform:scaleY(0)} 34%,100%{transform:scaleY(1)}}
@keyframes c-t3{0%,66%{transform:scaleY(0)} 67%,100%{transform:scaleY(1)}}
@keyframes c-slow {0%,66%{opacity:0} 67%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .fo-c *{animation:none !important}
  .fo-c .fill,.fo-c .tick{transform:scaleX(1) scaleY(1)}
}
</style>
<svg class="fo-c" viewBox="0 0 460 150" role="img"
     aria-label="Two rows drawn on different time scales. The flood row spans sixty milliseconds and fills rule 3's counter of fifty. The evasion row spans fifteen seconds and places three writes, so its counter never rises above one or two in any five-second window and no alert is raised.">
  <text x="8" y="36" font-size="14" opacity="0.85">flood</text>
  <text x="8" y="52" font-size="13" opacity="0.7">first 60 ms</text>
  <rect x="120" y="24" width="220" height="18" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
  <rect class="fill" x="121" y="25" width="218" height="16" rx="2" fill="var(--on)"/>
  <text x="348" y="38" font-size="13" opacity="0.7">50 writes / 5 s</text>
  <text class="alarm" x="120" y="62" font-size="13" fill="var(--on)" font-weight="bold">modbus_flood fires</text>

  <text x="8" y="104" font-size="14" opacity="0.85">evasion</text>
  <text x="8" y="120" font-size="13" opacity="0.7">first 15 s</text>
  <rect x="120" y="92" width="220" height="18" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
  <rect class="tick t1" x="121" y="93" width="5" height="16" rx="2" fill="currentColor" opacity="0.65"/>
  <rect class="tick t2" x="194" y="93" width="5" height="16" rx="2" fill="currentColor" opacity="0.65"/>
  <rect class="tick t3" x="267" y="93" width="5" height="16" rx="2" fill="currentColor" opacity="0.65"/>
  <text x="348" y="106" font-size="13" opacity="0.7">3 writes / 5 s</text>
  <text class="slow" x="120" y="130" font-size="13" opacity="0.8">nothing fires, and nothing stays pinned</text>
</svg>
<figcaption>The two rows are drawn on different scales &mdash; sixty milliseconds against fifteen seconds &mdash; because no single axis holds both. One write every 1.2 ms against one every five seconds is a ratio of about four thousand to one, and that gap is the whole content of the comparison. A rate rule cannot tell an attacker from an engineer; it can only tell a hurried one from a patient one.</figcaption>
</figure>

## The skill

Run `flooding_hpt.py` against the PLC, watch FUXA's blow-out flag go high while its HPT trend still reads 10, and click Verify. The flag comes from the IDS having seen `modbus_flood` on the wire, not from the plant reaching any particular state. Do not wait to verify: `boSen` is transient. Once the flood stops, the mechanical relief valve keeps venting &mdash; it latches open above 220 and stays open until the pressure is back to 200, independently of the system valve &mdash; and then clears the flag. That is the recovery and its limit in one. The spring bleeds off everything above its latch and then stops, and below the latch nothing drains the tank at all, because the valve the controller shut is still shut. Measured after one flood on this stack, the plant came to rest at 192 with `boSen` back to 0, and sat there unchanged for the next two minutes: the compressor off, the valve shut, and no path in either direction.

> **MITRE ATT&CK for ICS:** T0836 Modify Parameter, T0855 Unauthorized Command Message, T0806 Brute Force I/O. Detection: the *Detect Modbus Flooding* module. The quiet counterpart is *IDS Evasion*.
