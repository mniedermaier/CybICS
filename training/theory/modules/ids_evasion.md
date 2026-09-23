# IDS evasion

A rate rule does not watch a level. It keeps a **count inside a sliding window**, and alerts when that count crosses a threshold. Getting this wrong is the usual reason people think a detector saw something it could not have seen &mdash; and getting it right is the whole of this challenge.

Rule 4 in `software/ids/rules.py` is ten writes in thirty seconds from a source that is not `hwio` or `fuxa`. Rule 3 is fifty in five. Neither cares how large the value is or which register it lands in; both care only how many writes are inside the window right now.

<figure>
<style>
.ev-w {--d: 15s;}
/* The window is the lesson: it slides, and writes leave it from the left.
   A still can show three ticks under a line; it cannot show a count that
   rises and then falls again without anything else happening. */
.ev-w .win {animation: w-slide var(--d) linear 3 forwards;}
.ev-w .c0{opacity:0; animation: w-c0 var(--d) steps(1,end) 3 forwards;}
.ev-w .c1{opacity:0; animation: w-c1 var(--d) steps(1,end) 3 forwards;}
.ev-w .c2{opacity:0; animation: w-c2 var(--d) steps(1,end) 3 forwards;}
.ev-w .c3{opacity:0; animation: w-c3 var(--d) steps(1,end) 3 forwards;}
.ev-w .c4{opacity:0; animation: w-c4 var(--d) steps(1,end) 3 forwards;}
.ev-w .c5{opacity:0; animation: w-c5 var(--d) steps(1,end) 3 forwards;}
@keyframes w-slide{0%{transform:translateX(0)} 80%,100%{transform:translateX(350px)}}
@keyframes w-c0{0%,0%{opacity:0} 0.01%,8.889%{opacity:1} 8.899%,100%{opacity:0}}
@keyframes w-c1{0%,8.889%{opacity:0} 8.899%,17.78%{opacity:1} 17.79%,100%{opacity:0}}
@keyframes w-c2{0%,17.78%{opacity:0} 17.79%,53.33%{opacity:1} 53.34%,100%{opacity:0}}
@keyframes w-c3{0%,53.33%{opacity:0} 53.34%,62.22%{opacity:1} 62.23%,100%{opacity:0}}
@keyframes w-c4{0%,62.22%{opacity:0} 62.23%,71.11%{opacity:1} 71.12%,100%{opacity:0}}
@keyframes w-c5{0%,71.11%{opacity:0} 71.12%,80%{opacity:1} 100%}
@media (prefers-reduced-motion: reduce){
  .ev-w *{animation:none !important}
  .ev-w .win{transform:translateX(140px)}
  .ev-w .c2{opacity:1}
}
</style>
<svg class="ev-w" viewBox="0 0 460 190" role="img"
     aria-label="A forty-five second timeline with three Modbus writes at zero, five and ten seconds. A thirty-second window slides across it. The count inside the window rises to three, holds while all three writes are inside it, and then falls back to zero as each write ages out of the left edge. It never approaches rule 4's threshold of ten.">
  <defs><clipPath id="evclip"><rect x="70" y="86" width="350" height="54"/></clipPath></defs>
  <g clip-path="url(#evclip)">
    <g class="win">
      <rect x="-163.4" y="88" width="233.4" height="50" rx="3" fill="currentColor" opacity="0.16"/>
      <line x1="70" y1="86" x2="70" y2="140" stroke="#ff6b00" stroke-width="2"/>
    </g>
  </g>
  <line x1="70" y1="120" x2="420" y2="120" stroke="currentColor" stroke-opacity="0.45"/>
<rect x="68.5" y="100" width="3" height="20" rx="1" fill="#ff6b00"/><rect x="107.4" y="100" width="3" height="20" rx="1" fill="#ff6b00"/><rect x="146.3" y="100" width="3" height="20" rx="1" fill="#ff6b00"/>
  <g class="win">
    <text class="c0" x="52" y="78" text-anchor="middle" font-size="15" font-weight="bold" fill="#ff6b00">1</text>
    <text class="c1" x="52" y="78" text-anchor="middle" font-size="15" font-weight="bold" fill="#ff6b00">2</text>
    <text class="c2" x="52" y="78" text-anchor="middle" font-size="15" font-weight="bold" fill="#ff6b00">3</text>
    <text class="c3" x="52" y="78" text-anchor="middle" font-size="15" font-weight="bold" fill="#ff6b00">2</text>
    <text class="c4" x="52" y="78" text-anchor="middle" font-size="15" font-weight="bold" fill="#ff6b00">1</text>
    <text class="c5" x="52" y="78" text-anchor="middle" font-size="15" font-weight="bold" fill="#ff6b00">0</text>
    <text x="52" y="60" text-anchor="middle" font-size="12" opacity="0.7">in window</text>
  </g>
  <text x="70" y="158" font-size="12" opacity="0.7" text-anchor="middle">0 s</text>
  <text x="245" y="158" font-size="12" opacity="0.7" text-anchor="middle">22</text>
  <text x="420" y="158" font-size="12" opacity="0.7" text-anchor="middle">45</text>
  <text x="70" y="178" font-size="13" opacity="0.85">three writes, five seconds apart &mdash; rule 4 wants ten in thirty</text>
</svg>
<figcaption>The count peaks at three and then falls again, without the attacker doing anything, purely because the window moved on. That is why "low and slow" works: the detector has no memory beyond its window, so patience is not evasion of a check &mdash; it is arranging for there never to be a check to evade.</figcaption>
</figure>

## What the challenge actually asks

`solve_ids_evasion.py` sends three writes to register 1124, five seconds apart, over a **single TCP connection**. Every part of that is chosen against a rule.

- Three writes in fifteen seconds never brings rule 4's thirty-second count above three, and rule 3's five-second count above one.
- One connection means one SYN. Rule 1 alerts on five distinct ports inside ten seconds and rule 2 on a hundred SYNs; opening a fresh connection per write would still not trip either, but it is the habit that does, and the script's comment says so.
- Register 1124 is the GST reading. Nothing about the choice is stealthy in itself &mdash; the point is that stealth here is a property of *timing*, not of what you write.

The scoring is unusual and worth knowing, because there is no Verify button for this one: the IDS itself keeps the score. You arm a two-minute window at `/api/evasion/start`, which records the current alert id, and `/api/evasion/check` awards the flag when it has seen at least three Modbus writes and **zero** new alerts since then.

<figure>
<style>
.ev-c {--d: 10s;}
.ev-c .run {transform-box: fill-box; transform-origin: left;
            animation: c-run var(--d) linear 3 forwards;}
.ev-c .w {transform-box: fill-box; transform-origin: bottom;
          animation-duration:var(--d); animation-timing-function:steps(1,end);
          animation-iteration-count:3; animation-fill-mode:forwards;}
.ev-c .w1{animation-name:c-w1} .ev-c .w2{animation-name:c-w2} .ev-c .w3{animation-name:c-w3}
.ev-c .flag{opacity:0; animation: c-flag var(--d) steps(1,end) 3 forwards;}
@keyframes c-run {0%{transform:scaleX(0)} 88%,100%{transform:scaleX(1)}}
@keyframes c-w1 {0%,3%{transform:scaleY(0)} 3.1%,100%{transform:scaleY(1)}}
@keyframes c-w2 {0%,6.6%{transform:scaleY(0)} 6.7%,100%{transform:scaleY(1)}}
@keyframes c-w3 {0%,10.3%{transform:scaleY(0)} 10.4%,100%{transform:scaleY(1)}}
@keyframes c-flag{0%,88%{opacity:0} 89%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .ev-c *{animation:none !important}
  .ev-c .run{transform:scaleX(1)} .ev-c .w{transform:scaleY(1)} .ev-c .flag{opacity:1}
}
</style>
<svg class="ev-c" viewBox="0 0 460 156" role="img"
     aria-label="A two-minute evasion window. Three Modbus writes land in its first fifteen seconds. The new-alert counter stays at zero throughout, and at the end the flag is awarded.">
  <text x="8" y="42" font-size="13" opacity="0.85">window</text>
  <rect x="96" y="30" width="300" height="16" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
  <rect class="run" x="97" y="31" width="298" height="14" rx="2" fill="currentColor" opacity="0.3"/>
  <text x="402" y="43" font-size="12" opacity="0.7">120 s</text>

  <text x="8" y="92" font-size="13" opacity="0.85">writes</text>
  <line x1="96" y1="92" x2="396" y2="92" stroke="currentColor" stroke-opacity="0.45"/>
  <rect class="w w1" x="97" y="72" width="4" height="20" fill="#ff6b00"/>
  <rect class="w w2" x="109" y="72" width="4" height="20" fill="#ff6b00"/>
  <rect class="w w3" x="121" y="72" width="4" height="20" fill="#ff6b00"/>
  <text x="140" y="88" font-size="12" opacity="0.7">3 of 3 required</text>

  <text x="8" y="126" font-size="13" opacity="0.85">alerts</text>
  <line x1="96" y1="126" x2="396" y2="126" stroke="currentColor" stroke-opacity="0.45"/>
  <text x="140" y="122" font-size="13" opacity="0.8">0 &mdash; nothing to draw</text>
  <text class="flag" x="8" y="150" font-size="13" fill="#ff6b00" font-weight="bold">CybICS(st34lth_0p3r4t0r)</text>
</svg>
<figcaption>The only row with nothing in it is the one being scored. That is what makes this challenge different from every other one on the platform: it is verified by an absence, and an absence is exactly what a rate rule cannot distinguish from an empty network.</figcaption>
</figure>

One detail in the scoring is a small confession by the platform. `check_evasion` counts new alerts but skips any whose rule is `arp_spoof`, because that one fires constantly on ordinary Docker traffic. A rule noisy enough to be excluded from its own product's scoring is a rule nobody reads &mdash; which is the same failure mode as a rule tuned so tightly it never fires, approached from the other side.

## The skill

Arm the window, send three writes at a human pace, and ask the IDS whether it noticed. Then go and read `rules.py` and work out what rate you would have had to exceed &mdash; that number, not the flag, is the thing worth taking away.

> **MITRE ATT&CK for ICS:** T0820 Exploitation for Evasion, T0855 Unauthorized Command Message. The loud counterpart is *Flood &amp; Overwrite*; the defence is to pair rate rules with allow-lists and anomaly detection, so that "quiet" stops being the same as "safe".
