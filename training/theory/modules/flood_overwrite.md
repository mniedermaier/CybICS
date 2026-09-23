# Flood and overwrite

Modbus accepts any write from anyone, so an attacker can write the same register over and over. The interesting part is not that the write lands &mdash; the *Modbus* topic covers why nothing stops it &mdash; but what happens next. The flood does not break the plant. It lies to the controller, and the controller does the damage.

## Winning a race, not defeating a check

Register 1126 is the high pressure reading. The PLC program only ever reads it; what keeps it truthful is `hwio`, the process bridge, whose loop does a coil read and five register writes and then sleeps 20 ms. A single forged write survives about ten milliseconds on average and is gone.

`flooding_hpt.py` writes 1126 in a loop with `time.sleep(0.001)`, but that sleep is not the period: each pass also waits for a synchronous Modbus response. Measured against this stack it manages **between about 700 and 830 writes a second** depending on where you run it, so something like fifteen to eighteen of its writes land between one `hwio` write and the next. The register spends almost all of its time holding the attacker's value.

<figure>
<style>
.fo-r {--d: 12s;}
/* Two clocks against one register. The point is the ratio: the attacker's
   writes are not stronger, only more frequent. */
.fo-r .head {animation: r-head var(--d) linear 3 forwards;}
.fo-r .lane {animation: r-wipe var(--d) linear 3 forwards;}
@keyframes r-head{0%{transform:translateX(0)} 90%,100%{transform:translateX(340px)}}
@keyframes r-wipe{0%{clip-path:inset(0 100% 0 0)} 90%,100%{clip-path:inset(0 0 0 0)}}
@media (prefers-reduced-motion: reduce){
  .fo-r .head{animation:none; transform:translateX(340px)}
  .fo-r .lane{animation:none}
}
</style>
<svg class="fo-r" viewBox="0 0 460 196" role="img"
     aria-label="A hundred-millisecond timeline. The attacker writes register 1126 about every 1.2 milliseconds; hwio writes the true value back about every 20 milliseconds. The register therefore holds the forged value for all but roughly one millisecond in twenty.">
  <text x="8" y="46" font-size="13" opacity="0.85">attacker</text>
  <text x="8" y="60" font-size="12" opacity="0.7">~1.2 ms</text>
  <g class="lane"><rect x="80.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="84.1" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="88.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="92.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="96.3" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="100.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="104.5" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="108.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="112.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="116.7" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="120.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="124.9" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="129.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="133.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="137.1" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="141.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="145.3" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="149.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="153.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="157.5" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="161.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="165.7" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="169.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="173.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="177.9" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="182.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="186.1" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="190.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="194.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="198.3" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="202.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="206.5" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="210.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="214.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="218.7" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="222.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="226.9" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="231.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="235.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="239.1" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="243.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="247.3" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="251.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="255.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="259.5" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="263.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="267.7" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="271.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="275.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="279.9" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="284.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="288.1" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="292.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="296.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="300.3" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="304.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="308.5" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="312.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="316.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="320.7" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="324.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="328.9" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="333.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="337.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="341.1" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="345.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="349.3" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="353.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="357.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="361.5" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="365.6" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="369.7" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="373.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="377.8" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="381.9" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="386.0" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="390.1" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="394.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="398.2" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="402.3" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="406.4" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="410.5" y="42" width="1.8" height="16" fill="#ff6b00"/><rect x="414.6" y="42" width="1.8" height="16" fill="#ff6b00"/></g>
  <text x="8" y="96" font-size="13" opacity="0.85">hwio</text>
  <text x="8" y="110" font-size="12" opacity="0.7">~20 ms</text>
  <g class="lane"><rect x="80.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="148.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="216.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="284.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="352.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="420.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/></g>
  <text x="8" y="146" font-size="13" opacity="0.85">reg 1126</text>
  <text x="8" y="160" font-size="12" opacity="0.7">holds</text>
  <g class="lane">
    <rect x="80" y="142" width="340" height="16" fill="#ff6b00"/>
    <rect x="80.0" y="142" width="4" height="16" fill="#141414"/><rect x="148.0" y="142" width="4" height="16" fill="#141414"/><rect x="216.0" y="142" width="4" height="16" fill="#141414"/><rect x="284.0" y="142" width="4" height="16" fill="#141414"/><rect x="352.0" y="142" width="4" height="16" fill="#141414"/>
  </g>
  <line class="head" x1="80" y1="34" x2="80" y2="166" stroke="currentColor" stroke-width="2"/>
  <g font-size="12" opacity="0.7">
    <text x="80" y="182" text-anchor="middle">0 ms</text>
    <text x="250" y="182" text-anchor="middle">50</text>
    <text x="420" y="182" text-anchor="middle">100</text>
  </g>
</svg>
<figcaption>The orange band is the forged value; the dark notches are the moments <code>hwio</code> gets its measurement in before the next attacker write buries it. Seventeen-ish attacker writes per <code>hwio</code> write means the register reads 10 almost continuously &mdash; not because the attacker defeated anything, but because nothing was arbitrating.</figcaption>
</figure>

## What the controller does with a lie

Now read `cybICS.st` with `hpt` pinned at 10. Both of the rules that fire are the program working exactly as designed.

- `IF hpt < 60 AND compressorState = 0 AND gst > 50` is the start condition, and with the reading stuck at 10 its pressure test is permanently true. Whenever the compressor is off, the next scan turns it back on. (The seal-in `ELSIF hpt < 90 AND compressorState = 1 AND gst > 50` barely matters here; the start branch is doing the work.) The compressor does still drop out, but only in the moments the storage tank falls to 50 and fails the `gst > 50` guard &mdash; simulated against the plant model, that is a duty cycle around 97%, not 100%.
- `IF hpt > 50 AND hpt < 100 THEN systemValve := TRUE` is false at 10, so the system valve shuts and the downstream process stops drawing.

A compressor running 97% of the time, feeding a tank with no outlet. The attacker never touched the compressor coil or the valve coil; the controller drove both, correctly, from a reading it had no way to doubt.

<figure>
<style>
.fo-d {--d: 14s;}
/* Two traces from one register: what the controller believes, and what the
   tank actually holds. pathLength normalises both paths to 1000 units so the
   dash offset and the playhead advance together -- without it the traces
   finish in a quarter of the sweep. */
.fo-d .trace {stroke-dasharray:1000; animation: d-draw var(--d) linear 3 forwards;}
.fo-d .head  {animation: d-head var(--d) linear 3 forwards;}
@keyframes d-draw{0%{stroke-dashoffset:1000} 88%,100%{stroke-dashoffset:0}}
@keyframes d-head{0%{transform:translateX(0)} 88%,100%{transform:translateX(280px)}}
@media (prefers-reduced-motion: reduce){
  .fo-d .trace{animation:none; stroke-dashoffset:0}
  .fo-d .head {animation:none; transform:translateX(280px)}
}
</style>
<svg class="fo-d" viewBox="0 0 460 210" role="img"
     aria-label="Two traces over about four minutes. The value OpenPLC reads from register 1126 stays flat at 10. The pressure actually in the tank climbs from 75 past 220, where the relief valve opens and halves the rate of rise, and on to the 255 ceiling. The compressor runs almost the whole time with the system valve shut.">
  <line x1="60" y1="30" x2="60" y2="150" stroke="currentColor" stroke-opacity="0.4"/>
  <line x1="60" y1="150" x2="340" y2="150" stroke="currentColor" stroke-opacity="0.4"/>
  <g font-size="12" opacity="0.7">
    <text x="54" y="34" text-anchor="end">255</text>
    <text x="54" y="51" text-anchor="end">220</text>
    <text x="54" y="154" text-anchor="end">10</text>
    <text x="60" y="170" text-anchor="middle">0</text>
    <text x="200" y="170" text-anchor="middle">2 min</text>
    <text x="340" y="170" text-anchor="middle">4 min</text>
  </g>
  <line x1="60" y1="47" x2="340" y2="47" stroke="#ff6b00" stroke-dasharray="4 3"/>
  <text x="346" y="51" font-size="12" fill="#ff6b00">relief valve</text>

  <polyline class="trace" pathLength="1000" points="60,150 340,150" fill="none" stroke="currentColor" stroke-width="2.5" stroke-opacity="0.75"/>
  <text x="346" y="154" font-size="12" opacity="0.75">OpenPLC reads 10</text>
  <polyline class="trace" pathLength="1000" points="60,118 130,92 200,66 245,47 340,31" fill="none" stroke="#ff6b00" stroke-width="2.5"/>
  <text x="346" y="34" font-size="12" fill="#ff6b00">the tank</text>

  <rect x="60" y="182" width="280" height="14" rx="3" fill="#ff6b00"/>
  <text x="200" y="193" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">compressor on, system valve shut</text>
  <line class="head" x1="60" y1="26" x2="60" y2="156" stroke="currentColor" stroke-width="2"/>
</svg>
<figcaption>The physics advances one tick per pass of <code>hwio</code>'s outer loop, so the climb from the normal band to the relief valve takes on the order of two and a half minutes and the ceiling about four &mdash; a millisecond-scale race with a minute-scale consequence. Above the dashed line the valve halves the rate of rise and no more: it vents half a unit per tick against a steady +1. Neither trace is wrong from where it is measured; what the attack removed is the correspondence between them.</figcaption>
</figure>

Watching this from the HMI has a catch worth knowing. FUXA's HPT trend reads the same register the flood is pinning, so it shows a flat 10 and has nothing to diverge from. What it *does* show is `boSen`, the blow-out flag, which `hwio` sets from the true pressure: the trend sits at 10 while the alarm goes high. The real pressure is only visible on `hwio`'s own dashboard.

## Why this one is loud

Rule 3 in `software/ids/rules.py` counts writes per source: fifty inside a five-second window, from anything that is not `hwio`, `fuxa` or `openplc`, raises `modbus_flood`. At the measured rate the flood crosses that line in roughly sixty to seventy milliseconds, and the challenge's verifier simply asks the IDS whether the rule fired.

That is the trade the attack makes: completely effective and completely obvious. The *IDS Evasion* challenge is the same kind of write from the same host &mdash; three of them, five seconds apart &mdash; aimed at register 1124, the GST reading, which `hwio` owns just as tightly. Under rule 3's fifty-in-five and rule 4's ten-in-thirty, it is silent. It also pins nothing, because `hwio` wins every race it is not being out-written in.

<figure>
<style>
.fo-c {--d: 7s;}
.fo-c .fill {transform-box: fill-box; transform-origin: left;
             animation: c-fill var(--d) linear 3 forwards;}
.fo-c .tick {transform-box: fill-box; transform-origin: left;
             animation-duration:var(--d); animation-timing-function:steps(1,end);
             animation-iteration-count:3; animation-fill-mode:forwards;}
.fo-c .t1{animation-name:c-t1} .fo-c .t2{animation-name:c-t2} .fo-c .t3{animation-name:c-t3}
.fo-c .alarm{animation: c-alarm var(--d) steps(1,end) 3 forwards;}
.fo-c .slow {animation: c-slow var(--d) steps(1,end) 3 forwards;}
/* Both rows share one clock, so the flood's instant fill and the evasion's
   three widely spaced ticks are directly comparable. */
@keyframes c-fill {0%{transform:scaleX(0)} 8%,100%{transform:scaleX(1)}}
@keyframes c-alarm{0%,8%{opacity:0} 9%,100%{opacity:1}}
@keyframes c-t1{0%{transform:scaleX(0)} 0.1%,100%{transform:scaleX(1)}}
@keyframes c-t2{0%,33%{transform:scaleX(0)} 33.1%,100%{transform:scaleX(1)}}
@keyframes c-t3{0%,66%{transform:scaleX(0)} 66.1%,100%{transform:scaleX(1)}}
@keyframes c-slow {0%,66%{opacity:0} 67%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .fo-c *{animation:none !important}
  .fo-c .fill,.fo-c .tick{transform:scaleX(1)}
}
</style>
<svg class="fo-c" viewBox="0 0 460 140" role="img"
     aria-label="Rule 3 alerts at fifty writes in five seconds. The flood reaches that almost immediately. The IDS Evasion challenge sends three writes five seconds apart, so its counter never rises above one or two in any five-second window and no alert is raised.">
  <text x="8" y="36" font-size="13" opacity="0.85">flood</text>
  <rect x="120" y="24" width="220" height="18" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
  <rect class="fill" x="121" y="25" width="218" height="16" rx="2" fill="#ff6b00"/>
  <text x="348" y="38" font-size="12" opacity="0.7">50 writes / 5 s</text>
  <text class="alarm" x="8" y="60" font-size="13" fill="#ff6b00" font-weight="bold">modbus_flood after about 60 ms</text>

  <text x="8" y="100" font-size="13" opacity="0.85">evasion</text>
  <rect x="120" y="88" width="220" height="18" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
  <rect class="tick t1" x="121" y="89" width="5" height="16" rx="2" fill="currentColor" opacity="0.65"/>
  <rect class="tick t2" x="194" y="89" width="5" height="16" rx="2" fill="currentColor" opacity="0.65"/>
  <rect class="tick t3" x="267" y="89" width="5" height="16" rx="2" fill="currentColor" opacity="0.65"/>
  <text x="348" y="102" font-size="12" opacity="0.7">3 writes, 5 s apart</text>
  <text class="slow" x="8" y="124" font-size="13" opacity="0.8">no rule fires, and nothing stays pinned either</text>
</svg>
<figcaption>Both rows run on one clock. The only difference between the two challenges is the interval: one crosses a counter and pins a value, the other crosses neither and changes nothing. A rate rule cannot tell an attacker from an engineer &mdash; it can only tell a hurried one from a patient one.</figcaption>
</figure>

## The skill

Run `flooding_hpt.py` against the PLC, watch FUXA's blow-out flag go high while its HPT trend still reads 10, and click Verify. The flag comes from the IDS having seen `modbus_flood` on the wire, not from the plant reaching any particular state.

> **MITRE ATT&CK for ICS:** T0836 Modify Parameter, T0855 Unauthorized Command Message, T0806 Brute Force I/O. Detection: the *Detect Modbus Flooding* module. The quiet counterpart is *IDS Evasion*.
