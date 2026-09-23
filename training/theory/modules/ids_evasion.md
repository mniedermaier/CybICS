# IDS evasion

A rate rule does not watch a level. It keeps a **count inside a sliding window** and alerts when that count crosses a threshold. Getting this wrong is the usual reason people think a detector saw something it could not have seen &mdash; and getting it right is the whole of this challenge.

Two rules in `software/ids/rules.py` guard Modbus writes. `modbus_unauth_write` (rule 4) fires on ten writes in thirty seconds from a source that is not `hwio` or `fuxa`. `modbus_flood` (rule 3) fires on fifty in five, and forgives one host more: `openplc` is on its exemption list too. Neither rule looks at the value or the register &mdash; `_check_modbus` reads one byte, the function code, and nothing else.

<figure>
<style>
.ev-w {--d: 15s; --on:#ff6b00;}
html.light-mode .ev-w {--on:#b34700;}
/* The window is the lesson: it slides, and writes leave it from the left.
   A still can show three ticks under a line; it cannot show a count that
   rises and then falls again without anything else happening.
   The resting state is the animation's most informative frame, so it is also
   the default for anyone who gets no animation at all. */
.ev-w .win {transform: translateX(233.4px); animation: w-slide var(--d) linear 20 forwards;}
.ev-w .c0{opacity:0; animation: w-c0 var(--d) steps(1,end) 20 forwards;}
.ev-w .c1{opacity:0; animation: w-c1 var(--d) steps(1,end) 20 forwards;}
.ev-w .c2{opacity:0; animation: w-c2 var(--d) steps(1,end) 20 forwards;}
.ev-w .c3{opacity:0; animation: w-c3 var(--d) steps(1,end) 20 forwards;}
.ev-w .c4{opacity:0; animation: w-c4 var(--d) steps(1,end) 20 forwards;}
.ev-w .c5{opacity:0; animation: w-c5 var(--d) steps(1,end) 20 forwards;}
.ev-w .c2 {opacity: 1;}
@keyframes w-slide{0%{transform:translateX(0)} 80%,100%{transform:translateX(350px)}}
@keyframes w-c0{0%,0%{opacity:0} 0.01%,8.889%{opacity:1} 8.899%,100%{opacity:0}}
@keyframes w-c1{0%,8.889%{opacity:0} 8.899%,17.78%{opacity:1} 17.79%,100%{opacity:0}}
@keyframes w-c2{0%,17.78%{opacity:0} 17.79%,53.33%{opacity:1} 53.34%,100%{opacity:0}}
@keyframes w-c3{0%,53.33%{opacity:0} 53.34%,62.22%{opacity:1} 62.23%,100%{opacity:0}}
@keyframes w-c4{0%,62.22%{opacity:0} 62.23%,71.11%{opacity:1} 71.12%,100%{opacity:0}}
@keyframes w-c5{0%,71.11%{opacity:0} 71.12%,80%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .ev-w *{animation:none !important}
  .ev-w .win{transform:translateX(233.4px)}
  .ev-w .c0,.ev-w .c1,.ev-w .c3,.ev-w .c4,.ev-w .c5{opacity:0}
  .ev-w .c2{opacity:1}
}
</style>
<svg class="ev-w" viewBox="0 0 460 176" role="img"
     aria-label="A forty-five second timeline with three Modbus writes at zero, five and ten seconds. A thirty-second window slides across it. The count inside the window rises to three, holds while all three writes are inside it, and then falls back to zero as each write ages out of the left edge. It never approaches rule 4's threshold of ten.">
  <defs><clipPath id="evclip"><rect x="70" y="86" width="350" height="54"/></clipPath></defs>
  <g clip-path="url(#evclip)">
    <g class="win">
      <rect x="-163.4" y="88" width="233.4" height="50" rx="3" fill="currentColor" fill-opacity="0.16"
            stroke="currentColor" stroke-opacity="0.5"/>
      <line x1="70" y1="86" x2="70" y2="140" stroke="var(--on)" stroke-width="2"/>
    </g>
  </g>
  <line x1="70" y1="120" x2="420" y2="120" stroke="currentColor" stroke-opacity="0.45"/>
<line x1="70.0" y1="100" x2="70.0" y2="120" stroke="var(--on)" stroke-width="3"/><line x1="108.9" y1="100" x2="108.9" y2="120" stroke="var(--on)" stroke-width="3"/><line x1="147.8" y1="100" x2="147.8" y2="120" stroke="var(--on)" stroke-width="3"/>
  <g class="win">
    <text class="c0" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold" fill="var(--on)">1</text>
    <text class="c1" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold" fill="var(--on)">2</text>
    <text class="c2" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold" fill="var(--on)">3</text>
    <text class="c3" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold" fill="var(--on)">2</text>
    <text class="c4" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold" fill="var(--on)">1</text>
    <text class="c5" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold" fill="var(--on)">0</text>
    <text x="52" y="60" text-anchor="middle" font-size="13" opacity="0.7">in window</text>
  </g>
  <g font-size="13" opacity="0.7">
    <text x="70" y="158" text-anchor="middle">0 s</text>
    <text x="245" y="158" text-anchor="middle">22.5</text>
    <text x="420" y="158" text-anchor="middle">45</text>
  </g>
</svg>
<figcaption>Three writes, five seconds apart, against a rule that wants ten in thirty. The count peaks at three and then falls again without the attacker doing anything, purely because the window moved on. That is why low-and-slow works: the detector has no memory beyond its window, so patience is not evasion of a check &mdash; it is arranging for there never to be a check to evade.</figcaption>
</figure>

## What the challenge actually asks

`solve_ids_evasion.py` sends three writes to register 1124, five seconds apart, over a single TCP connection. The timing is the whole of it, and two of the other choices are not what they look like.

- Three writes across **ten** seconds never brings rule 4's thirty-second count above three, or rule 3's five-second count above two &mdash; in practice one, because a `sleep(5)` plus a send and a receive always overshoots the window edge.
- The script's comment credits its single connection with dodging `syn_flood`. It does not: three connections would be three SYNs against a threshold of a hundred. And `port_scan` counts *distinct destination ports* per source-destination pair, so a thousand connections to 502 still count as one port. Staying on one port does matter, because that is what rule 1 counts; the number of connections to it does not. The single connection is tidy, not stealthy.
- Register 1124 is the GST reading, which `hwio` rewrites every cycle. The write is therefore invisible to the process as well as to the detector &mdash; which is exactly why the loud counterpart has to flood to have any effect at all.

The scoring is unusual, and there is no Verify button: the IDS keeps its own score. You arm a two-minute window at `/api/evasion/start`, which records the current alert id, and `/api/evasion/check` awards the flag as soon as it has seen three Modbus writes with zero new alerts since. It is winnable about twelve seconds in &mdash; and if you let the window run out instead, `check_evasion` returns `expired` and no flag, however many writes it counted.

<figure>
<style>
.ev-c {--d: 12s; --on:#ff6b00;}
html.light-mode .ev-c {--on:#b34700;}
.ev-c .run {transform-box: fill-box; transform-origin: left; transform: scaleX(0.12);
            animation: c-run var(--d) linear 20 forwards;}
.ev-c .w {transform-box: fill-box; transform-origin: bottom;
          animation-duration:var(--d); animation-timing-function:steps(1,end);
          animation-iteration-count:20; animation-fill-mode:forwards;}
.ev-c .w1{animation-name:c-w1} .ev-c .w2{animation-name:c-w2} .ev-c .w3{animation-name:c-w3}
.ev-c .flag{animation: c-flag var(--d) steps(1,end) 20 forwards;}
.ev-c .gone{opacity:0; animation: c-gone var(--d) steps(1,end) 20 forwards;}
/* The bar is 120 s at 2.5 units per second, so the three write marks and the
   keyframes that light them agree: 0, 5 and 10 s of window time. */
@keyframes c-run {0%{transform:scaleX(0)} 92%,100%{transform:scaleX(1)}}
@keyframes c-w1 {0%{transform:scaleY(0)} 0.5%,100%{transform:scaleY(1)}}
@keyframes c-w2 {0%,3.83%{transform:scaleY(0)} 4.3%,100%{transform:scaleY(1)}}
@keyframes c-w3 {0%,7.67%{transform:scaleY(0)} 8.1%,100%{transform:scaleY(1)}}
@keyframes c-flag{0%,9.2%{opacity:0} 9.7%,92%{opacity:1} 92.01%,100%{opacity:0}}
@keyframes c-gone{0%,92%{opacity:0} 92.01%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .ev-c *{animation:none !important}
  .ev-c .run{transform:scaleX(0.12)} .ev-c .w{transform:scaleY(1)}
  .ev-c .flag{opacity:1} .ev-c .gone{opacity:0}
}
</style>
<svg class="ev-c" viewBox="0 0 460 150" role="img"
     aria-label="A two-minute evasion window. Three Modbus writes land in its first ten seconds, and the flag becomes available about twelve seconds in, while a hundred and eight seconds of the window remain. When the bar runs out the window expires and the flag is gone, however many writes were counted.">
  <text x="8" y="42" font-size="14" opacity="0.85">window</text>
  <rect x="96" y="30" width="300" height="16" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="run" x="97" y="31" width="298" height="14" rx="2" fill="currentColor" opacity="0.55"/>
  <text x="402" y="43" font-size="13" opacity="0.7">120 s</text>

  <text x="8" y="92" font-size="14" opacity="0.85">writes</text>
  <line x1="96" y1="92" x2="396" y2="92" stroke="currentColor" stroke-opacity="0.45"/>
  <line class="w w1" x1="96" y1="72" x2="96" y2="92" stroke="var(--on)" stroke-width="4"/>
  <line class="w w2" x1="108.5" y1="72" x2="108.5" y2="92" stroke="var(--on)" stroke-width="4"/>
  <line class="w w3" x1="121" y1="72" x2="121" y2="92" stroke="var(--on)" stroke-width="4"/>
  <text x="140" y="88" font-size="13" opacity="0.7">0, 5 and 10 s</text>

  <text x="8" y="126" font-size="14" opacity="0.85">alerts</text>
  <line x1="96" y1="126" x2="396" y2="126" stroke="currentColor" stroke-opacity="0.45"/>
  <text x="140" y="122" font-size="13" opacity="0.8">0 &mdash; nothing to draw</text>
  <text class="flag" x="8" y="146" font-size="13" fill="var(--on)" font-weight="bold">CybICS(&hellip;) &mdash; available now</text>
  <text class="gone" x="8" y="146" font-size="13" opacity="0.8">window expired &mdash; no flag, whatever it counted</text>
</svg>
<figcaption>Three writes are all the check requires. The flag arrives long before the bar does, and leaves when it does. The row being scored is the one with nothing in it, together with the write count &mdash; and an absence is exactly what a rate rule cannot distinguish from an empty network.</figcaption>
</figure>

One detail in the scoring is a bug wearing a comment. `check_evasion` skips any alert whose rule is `arp_spoof`, called "background noise" in the source. It is not noise, it is memory: the four rate trackers drop stale timestamps on every event inside `_track_event`, but `arp_tracker` holds a *set* of MACs per address and nothing anywhere removes one. Restart a container, Docker hands the same IP a fresh MAC, and that address is permanently on record as having had two &mdash; so the rule re-fires whenever it next ARPs, which on a settled bridge is a couple of times a day, indefinitely. Rather than let the set forget, the scoring learned to look away.

Three lines further on there is a second bug with no comment at all, and it is the one a learner will actually trip over. `get_status` reports the evasion window's alert count as `alerts_total - evasion_start_alert_count`, but `evasion_start_alert_count` is initialised to zero and never assigned again &mdash; `start_evasion` sets `evasion_start_alert_id` instead, which is what `check_evasion` correctly uses. So the dashboard shows the IDS's *lifetime* alert total while the scoring endpoint, reading the same window, returns zero. You can be told you have triggered a hundred and seventy-seven alerts and win anyway.

## The skill

Arm the window, send three writes at a human pace, and ask the IDS whether it noticed. Then read `rules.py` and work out what rate you would have had to exceed. That number, not the flag, is the thing worth taking away.

> **MITRE ATT&CK for ICS:** the module maps to T0820 Exploitation for Evasion and T0855 Unauthorized Command Message. Take T0820 with a pinch of salt &mdash; MITRE defines it as exploiting a *vulnerability* in a security feature, and staying under a documented threshold is not that; `training/README.md` maps this module differently again. The loud counterpart is *Flood &amp; Overwrite*.
