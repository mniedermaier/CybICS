# IDS evasion

In this challenge you write to the PLC over Modbus while the Intrusion Detection System (IDS) watches, and the goal is that it never raises an alarm. Real attackers study a detector before they act. Doing the same shows you where a simple rule-based IDS is blind, which is what a defender needs to know to close the gap.

## The idea

Picture a speed camera that only flashes when a car passes more than ten times in thirty seconds. A driver who knows the rule passes three times, slowly, and is never photographed. The camera works perfectly; it just measures the wrong thing.

Many IDS rules are **rate rules** like that camera. They keep a count of events inside a **sliding window**, a stretch of time that moves forward with the clock, and alert only when the count reaches a **threshold**. Old events drop out of the left edge of the window as time passes, so the count can fall again without the attacker doing anything.

<style>
.ev-w {--d: 15s; --on: #ff6b00;}
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

<figure class="wide">
<svg class="ev-w" viewBox="0 0 460 176" role="img"
     aria-label="A forty-five second timeline with three Modbus writes early on. A thirty-second window slides across it. The count inside the window rises to three, holds while all three writes are inside it, and then falls back to zero as each write ages out of the left edge. It never approaches a threshold of ten.">
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
  <g class="win" fill="currentColor">
    <text class="c0" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold">1</text>
    <text class="c1" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold">2</text>
    <text class="c2" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold">3</text>
    <text class="c3" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold">2</text>
    <text class="c4" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold">1</text>
    <text class="c5" x="52" y="78" text-anchor="middle" font-size="16" font-weight="bold">0</text>
    <text x="52" y="60" text-anchor="middle" font-size="13" opacity="0.7">in window</text>
  </g>
  <g font-size="13" opacity="0.7" fill="currentColor">
    <text x="70" y="158" text-anchor="middle">0 s</text>
    <text x="245" y="158" text-anchor="middle">22.5</text>
    <text x="420" y="158" text-anchor="middle">45</text>
  </g>
</svg>
<figcaption>Three writes against a rule that wants ten in thirty seconds. The count peaks at three and then falls again purely because the window moved on. The detector has no memory beyond its window.</figcaption>
</figure>

<div data-widget="checkpoint" data-id="window"></div>

## How it looks on CybICS

You work from the attack machine (`172.18.0.100`) and talk Modbus TCP to OpenPLC at `172.18.0.3`, port 502. The IDS dashboard on port 8443 lists every rule and its threshold on the Rules tab. Four of them matter to you:

| Rule | Fires when one source sends... |
|---|---|
| `modbus_unauth_write` | 10 Modbus writes within 30 seconds |
| `modbus_flood` | 50 Modbus writes within 5 seconds |
| `port_scan` | connection attempts to 5 different ports of one host within 10 seconds |
| `syn_flood` | 100 connection attempts within 10 seconds |

The Modbus rules read just one byte of each request: the function code, which says whether it is a read or a write. They ignore the register and the value. Writes from `hwio` and `fuxa` are trusted and never counted.

The challenge keeps its own score. You open a two-minute **evasion window** on the IDS, act, and then ask it how you did.

<details class="deep-dive" markdown="1">
<summary>Deep dive: how the evasion window is scored</summary>

The IDS opens the window at `/api/evasion/start` and reports on it at `/api/evasion/check`.

<style>
.ev-c {--d: 12s; --on: #ff6b00;}
.ev-c .run {transform-box: fill-box; transform-origin: left; transform: scaleX(0.12);
            animation: c-run var(--d) linear 20 forwards;}
.ev-c .wbar {transform-box: fill-box; transform-origin: bottom;
          animation-duration:var(--d); animation-timing-function:steps(1,end);
          animation-iteration-count:20; animation-fill-mode:forwards;}
.ev-c .w1{animation-name:c-w1} .ev-c .w2{animation-name:c-w2} .ev-c .w3{animation-name:c-w3}
.ev-c .ok{animation: c-ok var(--d) steps(1,end) 20 forwards;}
.ev-c .gone{opacity:0; animation: c-gone var(--d) steps(1,end) 20 forwards;}
@keyframes c-run {0%{transform:scaleX(0)} 92%,100%{transform:scaleX(1)}}
@keyframes c-w1 {0%{transform:scaleY(0)} 0.5%,100%{transform:scaleY(1)}}
@keyframes c-w2 {0%,3.83%{transform:scaleY(0)} 4.3%,100%{transform:scaleY(1)}}
@keyframes c-w3 {0%,7.67%{transform:scaleY(0)} 8.1%,100%{transform:scaleY(1)}}
@keyframes c-ok{0%,9.2%{opacity:0} 9.7%,92%{opacity:1} 92.01%,100%{opacity:0}}
@keyframes c-gone{0%,92%{opacity:0} 92.01%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .ev-c *{animation:none !important}
  .ev-c .run{transform:scaleX(0.12)} .ev-c .wbar{transform:scaleY(1)}
  .ev-c .ok{opacity:1} .ev-c .gone{opacity:0}
}
</style>

<figure class="wide">
<svg class="ev-c" viewBox="0 0 460 150" role="img"
     aria-label="A two-minute evasion window. A few Modbus writes land early in it with no alerts, and the check reports success while most of the window remains. When the bar runs out the window expires and a new attempt is needed, however many writes were counted.">
  <g fill="currentColor">
  <text x="8" y="42" font-size="14" opacity="0.85">window</text>
  <rect x="96" y="30" width="300" height="16" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="run" x="97" y="31" width="298" height="14" rx="2" opacity="0.55"/>
  <text x="402" y="43" font-size="13" opacity="0.7">120 s</text>
  <text x="8" y="92" font-size="14" opacity="0.85">writes</text>
  <text x="140" y="88" font-size="13" opacity="0.7">counted by the check</text>
  <text x="8" y="126" font-size="14" opacity="0.85">alerts</text>
  <text x="140" y="122" font-size="13" opacity="0.8">0 &mdash; nothing to draw</text>
  <text class="ok" x="8" y="146" font-size="13" font-weight="bold">success: the check is satisfied</text>
  <text class="gone" x="8" y="146" font-size="13" opacity="0.8">window expired &mdash; start a new attempt</text>
  </g>
  <line x1="96" y1="92" x2="396" y2="92" stroke="currentColor" stroke-opacity="0.45"/>
  <line class="wbar w1" x1="96" y1="72" x2="96" y2="92" stroke="var(--on)" stroke-width="4"/>
  <line class="wbar w2" x1="108.5" y1="72" x2="108.5" y2="92" stroke="var(--on)" stroke-width="4"/>
  <line class="wbar w3" x1="121" y1="72" x2="121" y2="92" stroke="var(--on)" stroke-width="4"/>
  <line x1="96" y1="126" x2="396" y2="126" stroke="currentColor" stroke-opacity="0.45"/>
</svg>
<figcaption>The check wants a small number of writes and zero new alerts while the window is open. The row being scored is the empty one: an absence of alerts, which a rate rule cannot tell apart from a quiet network.</figcaption>
</figure>

</details>

Try a plan before you try the network. The planner uses the two Modbus write rules of the CybICS IDS and the challenge's two-minute window.

<div data-widget="rate-planner"></div>

## How to approach it

1. **Read the rules first.** On the Rules tab, note the threshold and window of every rule your traffic could touch, not only the Modbus ones.
2. **Plan your rate.** Work out how many writes fit into any 30-second and any 5-second stretch without reaching a threshold. Leave a safety margin: a pause in a script is never perfectly exact.
3. **Keep the rest of your traffic quiet.** Use one target port. A quick `nmap` "just to check" during the window is the classic way to fail.
4. **Use a script.** A few lines of Python with `pymodbus` and `time.sleep()` give you exact control over timing. The [Flood & Overwrite](/theory/flood_overwrite) module shows how to open a client and write a register.
5. **Open the window, act, then check.** The check counts Modbus writes from any host that is not one of the plant's own services, and every new alert since the window opened, whoever caused it.

<div class="callout warning" markdown="1">
**Watch out:** The window lasts two minutes. If it expires before you check, the attempt is lost and you start a new one.
</div>

## Detect and defend

Low-and-slow traffic beats rate rules, so a defender adds checks that do not depend on speed:

- **Allow-listing.** Only the plant's own writers, the HMI and the plant I/O (hwio), should ever write to the PLC. A rule that alerts on the very first write from any other address has no threshold to hide under.
- **Longer memory.** Count writes per source over hours, not seconds, and compare against a normal baseline.
- **Process awareness.** Check whether a written value makes sense for the plant, not only how often writes arrive.
- **Prevention.** A firewall that drops Modbus from unknown hosts stops the write entirely. See [Host firewalling](/theory/defense_firewall).

The technique you practise is Unauthorized Message: Command Message (T1692.001) in MITRE ATT&CK for ICS.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

- The evasion check ignores `arp_spoof` alerts, because ARP alerts can reappear after container restarts and would otherwise spoil attempts.
- The `evasion.new_alerts` value in `/api/status` subtracts from a counter that is never set, so the dashboard can show the lifetime alert total while `/api/evasion/check` correctly reports zero. Point students to the check endpoint.
- Alerts from other students' traffic during the window count too; run this one in a quiet lab.

</details>

## Before you start

- [Intrusion detection](/theory/ids_challenge): the CybICS IDS and how its rules are built
- [Detection and monitoring](/theory/detection-monitoring): thresholds, windows and false alarms
- [Modbus TCP](/theory/modbus): function codes and register writes
- [Flood & Overwrite](/theory/flood_overwrite): the loud version of the same attack
