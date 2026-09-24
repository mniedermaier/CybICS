# The gas pressure process

Every CybICS attack ends in a physical effect, so it pays to know the process before attacking it. The plant moves gas from an external supply into a **Gas Storage Tank (GST)**, compresses it into a **High Pressure Tank (HPT)**, and protects itself with a mechanical **blowout** valve if the pressure climbs too far.

The challenge asks you to trigger that blowout from the HMI's manual mode. Doing it is three clicks. Understanding why those three and not two is most of what this page is for.

## One tick, and the exchange rate

The simulation advances in ticks. A tick is one pass of the `if delay > 50` gate in `physical_process_thread`, which is fifty-one turns of a loop that sleeps 20 ms &mdash; measured on the running stack, about 1.06 seconds. Every rate below is per tick, and the first one is the one that decides the challenge.

<figure>
<style>
.article figure svg.pp-b {min-width: 360px;}
.pp-b {--b: 16s;}
/* The two levels move on one clock over 103 transfers, which is the whole
   contents of a full storage tank. The 220 line stays where it is, and the
   pressure stops visibly short of it -- an ending a still can only assert. */
.pp-b .lvl {transform-box: fill-box; transform-origin: bottom;}
.pp-b .gst {transform: scaleY(0.192); animation: pb-gst var(--b) linear infinite;}
.pp-b .hpt {transform: scaleY(0.757); animation: pb-hpt var(--b) linear infinite;}
.pp-b .beat{animation: pb-beat 1.06s ease-in-out infinite;}
.pp-b .done{opacity:1; animation: pb-done var(--b) steps(1,end) infinite;}
@keyframes pb-gst {0%,4%{transform:scaleY(1)} 86%,100%{transform:scaleY(0.192)}}
@keyframes pb-hpt {0%,4%{transform:scaleY(0.353)} 86%,100%{transform:scaleY(0.757)}}
@keyframes pb-beat{0%,100%{opacity:0.35} 50%{opacity:1}}
@keyframes pb-done{0%,85.9%{opacity:0} 86%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pp-b * {animation:none !important;} }
</style>
<svg class="pp-b" viewBox="0 0 360 250" role="img"
     aria-label="A full gas storage tank emptying into the high pressure tank. Each tick the compressor takes two units out of storage and puts one into pressure, so a full tank of 255 units buys 103 units of pressure before the guard at 50 stops the transfer. Starting from the top of the normal band at 90, the pressure reaches 193 and stops, which is below the blowout threshold of 220. The storage tank alone cannot cause a blowout.">
  <text x="8" y="18" font-size="12" font-weight="bold">empty a full storage tank into the pressure tank</text>

  <rect x="24" y="40" width="56" height="150" rx="4" fill="none" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="lvl gst" x="26" y="42" width="52" height="146" fill="currentColor" fill-opacity="0.55"/>
  <text x="52" y="208" text-anchor="middle" font-size="12" font-weight="bold">GST</text>
  <text x="52" y="224" text-anchor="middle" font-size="11" opacity="0.85">255 &rarr; 49</text>

  <rect x="150" y="96" width="76" height="34" rx="4" fill="#ff6b00"/>
  <text x="188" y="110" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">compressor</text>
  <text class="beat" x="188" y="124" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">&minus;2 &rarr; +1</text>
  <text x="188" y="150" text-anchor="middle" font-size="11" opacity="0.85">one tick &asymp; 1.06 s</text>

  <rect x="280" y="40" width="56" height="150" rx="4" fill="none" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="lvl hpt" x="282" y="42" width="52" height="146" fill="#ff6b00"/>
  <text x="308" y="208" text-anchor="middle" font-size="12" font-weight="bold">HPT</text>
  <text x="308" y="224" text-anchor="middle" font-size="11" opacity="0.85">90 &rarr; 193</text>

  <line x1="272" y1="62" x2="344" y2="62" stroke="#ff6b00" stroke-width="2" stroke-dasharray="5 4"/>
  <text x="266" y="58" text-anchor="end" font-size="11" fill="#ff6b00" font-weight="bold">220 &mdash; blowout</text>
  <text class="done" x="266" y="96" text-anchor="end" font-size="12" font-weight="bold">103 transfers, then</text>
  <text class="done" x="266" y="110" text-anchor="end" font-size="12" font-weight="bold">the guard stops it</text>
  <text x="8" y="244" font-size="11" opacity="0.85">The level stops below the line. Storage alone is not enough.</text>
</svg>
<figcaption>The compressor moves two units out of storage for every one it delivers, and only while <code>gst &gt;= 50</code>. From a completely full tank that is 103 transfers &mdash; 255, 253, and so on down to 51, with the next pass blocked at 49. So the pressure can gain 103 and no more: from the top of the normal band at 90 it reaches 193, and from the bottom at 60 it reaches 163. The blowout needs 220. This is why the manual panel has three buttons and not two: without opening the supply valve as well, the attack simply runs out of gas.</figcaption>
</figure>

The other rates matter less but are worth having. The supply valve adds a random 0 to 3 units to storage each tick, averaging 1.5, and stops at 251. When the compressor is off and the system valve is open, the downstream process draws a random 0 to 2 units out of the pressure tank. And the relief valve, once open, vents a random 0 or 1 &mdash; half a unit a tick on average, against the compressor's steady one.

## The relief valve is a latch, not a limit

That last comparison is the one people get wrong. The valve does not hold the pressure at 220; it bleeds more slowly than the compressor fills, so a compressor that never stops wins. What the valve does do is latch.

<figure>
<style>
.article figure svg.pp-l {min-width: 360px;}
.pp-l {--l: 14s;}
/* The trace and the latch state share one clock, because the whole point is
   which one changes first: the latch opens the tick after 220 is passed and
   closes the tick 200 is reached, and between those two the pressure only
   falls. The flat tail is not decoration -- it is the fixed point. */
.pp-l .trc {stroke-dasharray:1000; animation: pl-trc var(--l) linear infinite;}
.pp-l .shut{opacity:0; animation: pl-shut var(--l) steps(1,end) infinite;}
.pp-l .open{opacity:0; animation: pl-open var(--l) steps(1,end) infinite;}
.pp-l .rest{opacity:1; animation: pl-rest var(--l) steps(1,end) infinite;}
@keyframes pl-trc {0%{stroke-dashoffset:1000} 90%,100%{stroke-dashoffset:0}}
@keyframes pl-shut{0%,35.9%{opacity:1} 36%,100%{opacity:0}}
@keyframes pl-open{0%,35.9%{opacity:0} 36%,63.9%{opacity:1} 64%,100%{opacity:0}}
@keyframes pl-rest{0%,63.9%{opacity:0} 64%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pp-l * {animation:none !important;} }
</style>
<svg class="pp-l" viewBox="0 0 360 208" role="img"
     aria-label="The pressure climbs past 220, where the relief valve latches open. It then vents until the pressure is back to 200, where the latch releases. Below 200 nothing drains the tank at all while the system valve is shut, so the pressure rests at 200 and stays there. The valve removes the excess and nothing removes the rest.">
  <text x="8" y="18" font-size="12" font-weight="bold">what the relief valve actually does</text>
  <line x1="44" y1="150" x2="344" y2="150" stroke="currentColor" stroke-opacity="0.6"/>
  <line x1="44" y1="36" x2="44" y2="150" stroke="currentColor" stroke-opacity="0.6"/>
  <line x1="44" y1="48" x2="306" y2="48" stroke="#ff6b00" stroke-width="2" stroke-dasharray="5 4"/>
  <text x="312" y="52" font-size="11" fill="#ff6b00" font-weight="bold">220</text>
  <line x1="44" y1="76" x2="306" y2="76" stroke="currentColor" stroke-opacity="0.55" stroke-dasharray="4 4"/>
  <text x="312" y="80" font-size="11" opacity="0.85">200</text>

  <polyline class="trc" pathLength="1000" points="44,142 160,44 232,76 300,76" fill="none" stroke="#ff6b00" stroke-width="2.5" stroke-linejoin="round"/>

  <g font-size="12" font-weight="bold">
    <text class="shut" x="60" y="112">latch shut &mdash; pressure rising</text>
    <text class="open" x="60" y="112" fill="#ff6b00">latch open &mdash; venting to 200</text>
    <text class="rest" x="60" y="112">latch shut again &mdash; nothing drains</text>
  </g>
  <text x="8" y="176" font-size="11" opacity="0.85">It opens above 220, closes at 200, removes the excess</text>
  <text x="8" y="192" font-size="11" opacity="0.85">and nothing removes the rest. 200 is where the plant stops.</text>
</svg>
<figcaption>The condition is <code>hpt &gt; 220 or (boSen &gt; 0 and hpt &gt; 200)</code>, so the valve latches open above 220 and stays open until 200, whatever the system valve is doing. Below 200 the only drain is the downstream process, and the PLC opens the system valve only between 50 and 100 &mdash; so after a blowout the plant comes to rest around 200 and sits there. Measured after one flood on this stack: it settled at 192 and did not move for the next two minutes.</figcaption>
</figure>

## Doing the challenge

Log into FUXA as `operator`, switch to **Manual**, and three buttons appear: **Comp.**, **SV** and **GST**. They write coils 1, 2 and 3 directly.

- **SV off** removes the only drain on the pressure tank.
- **Comp. on** starts the 2-for-1 transfer.
- **GST on** keeps the storage tank refilling, which is what carries you past the 103-unit ceiling the figure above stops at.

The flag is `CybICS(Bl0w0ut)` &mdash; zeros, not letters, which is worth noticing before you retype it.

## Why it matters

Knowing which register is which turns a blind write into a targeted one, and knowing the rates tells you how long an attack takes before you run it. *Flood &amp; Overwrite* forges the pressure reading and lets the PLC's own logic do all of this for you, which takes about three minutes from the normal band. The difference between the two challenges is only who presses the buttons.

> The plant model exists twice: `thread_physical` in `software/stm32/src/main.c` is the reference, and `physical_process_thread` in `software/hwio-virtual/hardwareAbstraction.py` mirrors it for Docker. `tests/test_plant_model_parity.py` parses both and fails on drift, which is why the numbers on this page hold for the board as well as the container.
