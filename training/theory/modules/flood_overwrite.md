# Flood and overwrite

Modbus accepts any write from anyone, so an attacker can write the same register over and over. The interesting part is not that the write lands &mdash; the *Modbus* topic covers why nothing stops it &mdash; but what happens next. The flood does not break the plant. It lies to the controller, and the controller does the damage.

## Winning a race, not defeating a check

Register 1126 is the high pressure reading. The PLC program only ever reads it; what keeps it truthful is `hwio`, the process bridge, which writes the real measurement back nominally every 20 ms. A single forged write survives about ten milliseconds on average and is gone.

`flooding_hpt.py` writes 1126 in a loop with `time.sleep(0.001)`, so roughly twenty of its writes land between one `hwio` write and the next. The register spends almost all of its time holding the attacker's value.

<figure>
<style>
.fo-r {--d: 12s;}
/* Two clocks against one register. The point is the ratio: the attacker's
   writes are not stronger, only more frequent. */
.fo-r .head {animation: r-head var(--d) linear 3 forwards;}
.fo-r .lane {clip-path: inset(0 100% 0 0); animation: r-wipe var(--d) linear 3 forwards;}
@keyframes r-head{0%{transform:translateX(0)} 90%,100%{transform:translateX(360px)}}
@keyframes r-wipe{0%{clip-path:inset(0 100% 0 0)} 90%,100%{clip-path:inset(0 0 0 0)}}
@media (prefers-reduced-motion: reduce){
  .fo-r .head{animation:none; transform:translateX(360px)}
  .fo-r .lane{animation:none; clip-path:none}
}
</style>
<svg class="fo-r" viewBox="0 0 460 196" role="img"
     aria-label="A hundred-millisecond timeline. The attacker writes register 1126 about once every millisecond; hwio writes the true value back every twenty milliseconds. The register therefore holds the forged value for roughly nineteen milliseconds out of every twenty.">
  <text x="8" y="40" font-size="13" opacity="0.85">attacker</text>
  <text x="8" y="54" font-size="12" opacity="0.7">every 1 ms</text>
  <g class="lane"><rect x="60.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="63.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="67.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="70.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="74.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="78.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="81.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="85.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="88.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="92.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="96.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="99.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="103.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="106.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="110.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="114.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="117.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="121.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="124.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="128.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="132.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="135.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="139.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="142.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="146.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="150.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="153.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="157.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="160.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="164.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="168.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="171.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="175.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="178.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="182.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="186.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="189.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="193.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="196.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="200.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="204.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="207.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="211.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="214.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="218.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="222.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="225.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="229.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="232.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="236.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="240.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="243.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="247.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="250.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="254.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="258.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="261.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="265.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="268.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="272.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="276.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="279.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="283.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="286.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="290.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="294.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="297.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="301.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="304.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="308.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="312.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="315.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="319.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="322.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="326.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="330.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="333.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="337.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="340.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="344.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="348.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="351.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="355.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="358.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="362.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="366.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="369.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="373.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="376.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="380.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="384.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="387.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="391.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="394.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="398.4" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="402.0" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="405.6" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="409.2" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="412.8" y="42" width="1.6" height="16" fill="#ff6b00"/><rect x="416.4" y="42" width="1.6" height="16" fill="#ff6b00"/></g>
  <text x="8" y="90" font-size="13" opacity="0.85">hwio</text>
  <text x="8" y="104" font-size="12" opacity="0.7">every 20 ms</text>
  <g class="lane"><rect x="60.0" y="92" width="2.4" height="16" fill="currentColor" opacity="0.75"/><rect x="132.0" y="92" width="2.4" height="16" fill="currentColor" opacity="0.75"/><rect x="204.0" y="92" width="2.4" height="16" fill="currentColor" opacity="0.75"/><rect x="276.0" y="92" width="2.4" height="16" fill="currentColor" opacity="0.75"/><rect x="348.0" y="92" width="2.4" height="16" fill="currentColor" opacity="0.75"/><rect x="420.0" y="92" width="2.4" height="16" fill="currentColor" opacity="0.75"/></g>
  <text x="8" y="140" font-size="13" opacity="0.85">reg 1126</text>
  <text x="8" y="154" font-size="12" opacity="0.7">holds</text>
  <g class="lane">
    <rect x="60" y="142" width="360" height="16" fill="#ff6b00"/>
    <rect x="60.0" y="142" width="3.6" height="16" fill="currentColor" opacity="0.5"/><rect x="132.0" y="142" width="3.6" height="16" fill="currentColor" opacity="0.5"/><rect x="204.0" y="142" width="3.6" height="16" fill="currentColor" opacity="0.5"/><rect x="276.0" y="142" width="3.6" height="16" fill="currentColor" opacity="0.5"/><rect x="348.0" y="142" width="3.6" height="16" fill="currentColor" opacity="0.5"/><rect x="420.0" y="142" width="3.6" height="16" fill="currentColor" opacity="0.5"/>
  </g>
  <line class="head" x1="60" y1="34" x2="60" y2="166" stroke="currentColor" stroke-width="2"/>
  <g font-size="12" opacity="0.7">
    <text x="60" y="182" text-anchor="middle">0 ms</text>
    <text x="240" y="182" text-anchor="middle">50</text>
    <text x="420" y="182" text-anchor="middle">100</text>
  </g>
</svg>
<figcaption>The orange band is the forged value, the grey slivers are the moments <code>hwio</code> gets its measurement in. Twenty attacker writes per <code>hwio</code> write means the register reads 10 about nineteen milliseconds out of every twenty &mdash; not because the attacker defeated anything, but because nothing was arbitrating.</figcaption>
</figure>

## What the controller does with a lie

Now read `cybICS.st` with `hpt` pinned at 10. Two independent rules fire, and both of them are the program working exactly as designed.

- `IF hpt < 60 AND compressorState = 0 AND gst > 50` starts the compressor, and `ELSIF hpt < 90 AND compressorState = 1` keeps it running. At 10 the second condition never stops holding, so the compressor never switches off.
- `IF hpt > 50 AND hpt < 100 THEN systemValve := TRUE` is false at 10, so the system valve shuts and the downstream process stops drawing.

A compressor that never stops, feeding a tank with no outlet. The attacker never touched the compressor coil or the valve coil; the controller drove both, correctly, from a reading it had no way to doubt.

<figure>
<style>
.fo-d {--d: 14s;}
/* Two traces from one register: what the controller believes, and what the
   tank actually holds. The gap between them is the attack. */
.fo-d .trace {stroke-dasharray:1000; stroke-dashoffset:1000;
              animation: d-draw var(--d) linear 3 forwards;}
.fo-d .head  {animation: d-head var(--d) linear 3 forwards;}
@keyframes d-draw{0%{stroke-dashoffset:1000} 88%,100%{stroke-dashoffset:0}}
@keyframes d-head{0%{transform:translateX(0)} 88%,100%{transform:translateX(280px)}}
@media (prefers-reduced-motion: reduce){
  .fo-d .trace{animation:none; stroke-dashoffset:0}
  .fo-d .head {animation:none; transform:translateX(340px)}
}
</style>
<svg class="fo-d" viewBox="0 0 460 196" role="img"
     aria-label="Two traces over the course of the attack. The value OpenPLC reads from register 1126 stays flat at 10. The pressure actually in the tank climbs from 75 past 220, where the relief valve opens, and on towards 255. The compressor runs the whole time.">
  <line x1="60" y1="30" x2="60" y2="150" stroke="currentColor" stroke-opacity="0.4"/>
  <line x1="60" y1="150" x2="340" y2="150" stroke="currentColor" stroke-opacity="0.4"/>
  <g font-size="12" opacity="0.7">
    <text x="54" y="34" text-anchor="end">255</text>
    <text x="54" y="58" text-anchor="end">220</text>
    <text x="54" y="146" text-anchor="end">10</text>
  </g>
  <line x1="60" y1="54" x2="340" y2="54" stroke="#ff6b00" stroke-dasharray="4 3" stroke-opacity="0.6"/>
  <text x="346" y="58" font-size="12" fill="#ff6b00">relief valve</text>

  <polyline class="trace" points="60,146 340,146" fill="none" stroke="currentColor" stroke-width="2.5" stroke-opacity="0.75"/>
  <text x="346" y="150" font-size="12" opacity="0.75">OpenPLC reads 10</text>
  <polyline class="trace" points="60,118 130,96 200,70 270,50 340,36" fill="none" stroke="#ff6b00" stroke-width="2.5"/>
  <text x="346" y="34" font-size="12" fill="#ff6b00">the tank</text>

  <rect x="60" y="168" width="340" height="14" rx="3" fill="#ff6b00"/>
  <text x="230" y="179" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">compressor on, system valve shut &mdash; the whole time</text>
  <line class="head" x1="60" y1="26" x2="60" y2="156" stroke="currentColor" stroke-width="2"/>
</svg>
<figcaption>The relief valve opens where the dashed line is and cannot keep up &mdash; it vents half a unit per tick against a steady +1. Neither trace is wrong from where it is measured. The controller is reading its sensor register and acting on it; the tank is doing what a running compressor makes it do. Everything between them &mdash; the part where a reading is supposed to correspond to a pressure &mdash; is what the attack removed.</figcaption>
</figure>

## Why this one is loud

Rule 3 in `software/ids/rules.py` counts writes per source: fifty inside a five-second window, from anything that is not `hwio`, `fuxa` or `openplc`, raises `modbus_flood`. At roughly a thousand writes a second the flood crosses that line in about fifty milliseconds, and the challenge's own verifier simply asks the IDS whether the rule fired.

That is the trade the attack makes: it is completely effective and completely obvious. The *IDS Evasion* challenge is the same write against the same register from the same host, sent three times with five-second gaps &mdash; under rule 3's fifty, under rule 4's ten-in-thirty-seconds, and therefore silent. It also does not pin anything, because `hwio` wins every race it is not being out-written in.

<figure>
<style>
.fo-c {--d: 10s;}
.fo-c .fill {transform-box: fill-box; transform-origin: left; transform: scaleX(0);
             animation: c-fill var(--d) linear 3 forwards;}
.fo-c .alarm{opacity:0; animation: c-alarm var(--d) steps(1,end) 3 forwards;}
.fo-c .slow {opacity:0; animation: c-slow var(--d) steps(1,end) 3 forwards;}
@keyframes c-fill {0%{transform:scaleX(0)} 6%,100%{transform:scaleX(1)}}
@keyframes c-alarm{0%,6%{opacity:0} 7%,100%{opacity:1}}
@keyframes c-slow {0%,20%{opacity:0} 21%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .fo-c .fill {animation:none; transform:scaleX(1)}
  .fo-c .alarm,.fo-c .slow{animation:none; opacity:1}
}
</style>
<svg class="fo-c" viewBox="0 0 460 150" role="img"
     aria-label="Rule 3 alerts at fifty writes in five seconds. The flood reaches that in about fifty milliseconds. The IDS Evasion challenge sends three writes with five-second gaps, so its counter never rises above three and no alert is raised.">
  <text x="8" y="34" font-size="13" opacity="0.85">flood</text>
  <rect x="120" y="22" width="220" height="18" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
  <rect class="fill" x="121" y="23" width="218" height="16" rx="2" fill="#ff6b00"/>
  <text x="346" y="36" font-size="12" opacity="0.7">50 writes / 5 s</text>
  <text class="alarm" x="8" y="56" font-size="13" fill="#ff6b00" font-weight="bold">modbus_flood after about 50 ms</text>

  <text x="8" y="96" font-size="13" opacity="0.85">evasion</text>
  <rect x="120" y="84" width="220" height="18" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
  <rect x="121" y="85" width="13" height="16" rx="2" fill="currentColor" opacity="0.5"/>
  <text x="346" y="98" font-size="12" opacity="0.7">3 writes / 15 s</text>
  <text class="slow" x="8" y="118" font-size="13" opacity="0.8">no rule fires, and nothing stays pinned either</text>
  <text x="8" y="142" font-size="12" opacity="0.7">Both are the same write, to the same register, from the same host.</text>
</svg>
<figcaption>The only difference between the two challenges is the interval. One crosses a counter and pins a value; the other crosses neither and changes nothing. A rate rule cannot tell an attacker from an engineer &mdash; it can only tell a hurried one from a patient one.</figcaption>
</figure>

## The skill

Run `flooding_hpt.py` against the PLC, watch the FUXA trend diverge from the tank, and click Verify. The flag comes from the IDS having seen `modbus_flood` on the wire, not from the plant reaching any particular state.

> **MITRE ATT&CK for ICS:** T0836 Modify Parameter, T0855 Unauthorized Command Message, T0806 Brute Force I/O. Detection: the *Detect Modbus Flooding* module. The quiet counterpart is *IDS Evasion*.
