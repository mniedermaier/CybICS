# The gas pressure process

In this challenge you take the controls of the CybICS plant yourself. You switch the Human-Machine Interface (HMI) to manual mode and drive the process into its safety blowout. Every later attack on CybICS ends in a physical effect like this one, so knowing how the plant behaves is the best preparation you can get.

## The idea

Think of a bicycle pump connected to a bottle. Every stroke takes air from the room and squeezes it into the bottle, and the pressure in the bottle rises. If you keep pumping and nothing lets the air out, something has to give. Real pressure vessels therefore carry a spring-loaded relief valve that opens on its own when the pressure gets too high.

An industrial plant works the same way, only automated. A Programmable Logic Controller (PLC) reads the sensors many times a second and switches pumps and valves to keep the pressure inside a safe band. The operator watches all of this on the HMI, a screen that shows the tanks and offers buttons.

Most HMIs also have a **manual mode**. In manual mode the PLC stops deciding, and the operator's buttons switch the equipment directly. That is useful for maintenance, and it is exactly the kind of power an attacker wants: whoever controls the buttons controls the physics. MITRE ATT&CK for ICS calls this *Manipulation of Control* (T0831).

## How it looks on CybICS

The plant has two tanks and four actuators:

| Part | What it does |
|---|---|
| Gas storage tank (GST) | Low-pressure supply, holding register 1124 |
| High-pressure tank (HPT) | The tank that is protected, holding register 1126 |
| Compressor (coil 1) | Moves gas from the GST into the HPT |
| System valve (coil 2) | Lets the downstream process draw gas out of the HPT |
| GST supply signal (coil 3) | Refills the GST from an outside supply |
| Blowout valve | Mechanical relief valve on the HPT; its state is register 1134 |

In the Docker version the plant is simulated by the `hwio` container (172.18.0.2). It advances in steps of about one second, called ticks. In automatic mode the PLC program refills the GST when it falls below 60, runs the compressor when the HPT falls below 60 until it reaches 90, and opens the system valve only while the HPT is between 50 and 100.

You can watch those values live here:

<div data-widget="plant-live" data-fields="gst,hpt,compressor,systemValve,gstSig,boSen"></div>

Now use what you see. From the compressor and the system valve alone you can tell where the pressure is heading:

<div data-widget="plant-predict"></div>

The compressor has an exchange rate, and it matters. Each tick it takes two bar out of the GST and adds one to the HPT, and only while the GST still holds at least 50.

<figure class="wide">
<style>
.pp-b {--b: 16s;}
.pp-b .lvl {transform-box: fill-box; transform-origin: bottom;}
.pp-b .gst {transform: scaleY(0.188); animation: pb-gst var(--b) linear infinite;}
.pp-b .hpt {transform: scaleY(0.733); animation: pb-hpt var(--b) linear infinite;}
.pp-b .beat{animation: pb-beat 1.06s ease-in-out infinite;}
.pp-b .done{opacity:1; animation: pb-done var(--b) steps(1,end) infinite;}
@keyframes pb-gst {0%,4%{transform:scaleY(0.949)} 86%,100%{transform:scaleY(0.188)}}
@keyframes pb-hpt {0%,4%{transform:scaleY(0.353)} 86%,100%{transform:scaleY(0.733)}}
@keyframes pb-beat{0%,100%{opacity:0.85} 50%{opacity:1}}
@keyframes pb-done{0%,85.9%{opacity:0} 86%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pp-b * {animation:none !important;} }
</style>
<svg class="pp-b" viewBox="0 0 360 250" role="img"
     aria-label="A full gas storage tank emptying into the high-pressure tank. Each tick the compressor takes two units out of storage and puts one into the pressure tank. Storage holds about 242 when full, so it buys 97 units of pressure before the guard at 50 blocks the next transfer. Starting at 90, the pressure reaches 187 and stops, below the blowout threshold of 221.">
  <text x="8" y="18" font-size="12" font-weight="bold">empty a full storage tank into the pressure tank</text>

  <rect x="24" y="40" width="56" height="150" rx="4" fill="none" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="lvl gst" x="26" y="42" width="52" height="146" fill="currentColor" fill-opacity="0.55"/>
  <text x="52" y="208" text-anchor="middle" font-size="12" font-weight="bold">GST</text>
  <text x="52" y="224" text-anchor="middle" font-size="11" opacity="0.85">242 &rarr; 48</text>

  <rect x="150" y="96" width="76" height="34" rx="4" fill="#ff6b00"/>
  <text x="188" y="110" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">compressor</text>
  <text class="beat" x="188" y="124" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">&minus;2 &rarr; +1</text>
  <text x="188" y="150" text-anchor="middle" font-size="11" opacity="0.85">one tick &asymp; 1 s</text>

  <rect x="280" y="40" width="56" height="150" rx="4" fill="none" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="lvl hpt" x="282" y="42" width="52" height="146" fill="#ff6b00" stroke="currentColor" stroke-width="1.5"/>
  <text x="308" y="208" text-anchor="middle" font-size="12" font-weight="bold">HPT</text>
  <text x="308" y="224" text-anchor="middle" font-size="11" opacity="0.85">90 &rarr; 187</text>

  <line x1="272" y1="62" x2="344" y2="62" stroke="#ff6b00" stroke-width="2" stroke-dasharray="5 4"/>
  <text x="266" y="58" text-anchor="end" font-size="11" fill="#ff6b00" font-weight="bold">221 &mdash; blowout</text>
  <text class="done" x="266" y="170" text-anchor="end" font-size="12" font-weight="bold">97 transfers, then</text>
  <text class="done" x="266" y="184" text-anchor="end" font-size="12" font-weight="bold">the guard stops it</text>
  <text x="8" y="244" font-size="11" opacity="0.85">The level stops below the line. One tank of storage is not enough.</text>
</svg>
<figcaption>Two units out, one unit in, and only while the storage tank holds at least 50. The PLC stops refilling storage at 240, so a full tank holds about 242 and buys 97 units of pressure. From the top of the normal band at 90 that reaches 187, short of the 221 the blowout needs. Keep this mass balance in mind when you plan.</figcaption>
</figure>

<div data-widget="checkpoint" data-id="balance"></div>

## How to approach it

1. Open FUXA on port 1881 and log in with the operator account given in the challenge material.
2. Open the system view and switch from automatic to manual. Three buttons appear: compressor, system valve and GST supply. Each one writes its coil directly.
3. Before you press anything, ask three questions. What adds gas to the HPT? What takes gas out of it? What can stop the thing that adds gas?
4. Make your changes and watch the HPT, the GST and the blowout indicator over a few minutes. The plant changes by about one bar a second, so be patient.
5. When the blowout valve opens, the HMI rewards you. Switch back to automatic afterwards.

The blowout valve itself is worth understanding, because it does not behave like a ceiling.

<figure class="wide">
<style>
.pp-l {--l: 14s;}
.pp-l .trc {stroke-dasharray:1000; animation: pl-trc var(--l) linear infinite;}
.pp-l .shut{opacity:0; animation: pl-shut var(--l) steps(1,end) infinite;}
.pp-l .open{opacity:0; animation: pl-open var(--l) steps(1,end) infinite;}
.pp-l .rest{opacity:1; animation: pl-rest var(--l) steps(1,end) infinite;}
@keyframes pl-trc {0%{stroke-dashoffset:1000} 90%,100%{stroke-dashoffset:0}}
@keyframes pl-shut{0%,43.8%{opacity:1} 43.9%,100%{opacity:0}}
@keyframes pl-open{0%,43.8%{opacity:0} 43.9%,69.4%{opacity:1} 69.5%,100%{opacity:0}}
@keyframes pl-rest{0%,69.4%{opacity:0} 69.5%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pp-l * {animation:none !important;} }
</style>
<svg class="pp-l" viewBox="0 0 360 208" role="img"
     aria-label="The pressure climbs past 220, where the relief valve latches open. It vents until the pressure is back to 200, where the latch releases. Below 200 nothing drains the tank while the system valve is shut, so the pressure rests at 200.">
  <text x="8" y="18" font-size="12" font-weight="bold">what the relief valve actually does</text>
  <line x1="44" y1="150" x2="344" y2="150" stroke="currentColor" stroke-opacity="0.6"/>
  <line x1="44" y1="36" x2="44" y2="150" stroke="currentColor" stroke-opacity="0.6"/>
  <line x1="44" y1="48" x2="306" y2="48" stroke="#ff6b00" stroke-width="2" stroke-dasharray="5 4"/>
  <text x="312" y="52" font-size="11" fill="#ff6b00" font-weight="bold">220</text>
  <line x1="44" y1="76" x2="306" y2="76" stroke="currentColor" stroke-opacity="0.55" stroke-dasharray="4 4"/>
  <text x="312" y="80" font-size="11" opacity="0.85">200</text>

  <polyline class="trc" pathLength="1000" points="44,142 160,44 232,76 300,76" fill="none" stroke="#ff6b00" stroke-width="2.5" stroke-linejoin="round"/>

  <g font-size="12" font-weight="bold">
    <text class="shut" x="140" y="128">latch shut &mdash; pressure rising</text>
    <text class="open" x="140" y="128" fill="#ff6b00">latch open &mdash; venting to 200</text>
    <text class="rest" x="140" y="128">latch shut &mdash; nothing drains</text>
  </g>
  <text x="8" y="176" font-size="11" opacity="0.85">It opens above 220, closes at 200, removes the excess</text>
  <text x="8" y="192" font-size="11" opacity="0.85">and nothing removes the rest. 200 is where the plant stops.</text>
</svg>
<figcaption>The relief valve latches open above 220 and stays open until the pressure is back at 200. It vents about half a bar per tick, more slowly than a running compressor fills, so it cannot win against a compressor that never stops. Once it closes, the tank stays near 200 until something else drains it.</figcaption>
</figure>

<details class="deep-dive" markdown="1">
<summary>Deep dive: the rates per tick</summary>

These come from `physical_process_thread` in `software/hwio-virtual/hardwareAbstraction.py`, which mirrors `thread_physical` in the STM32 firmware.

- Compressor on, GST at least 50 and HPT below 255: GST minus 2, HPT plus 1.
- Compressor off and system valve open: the downstream process draws a random 0 to 2 from the HPT.
- GST supply on and GST below 251: GST plus a random 0 to 3.
- HPT above 220, or blowout already open and HPT above 200: the blowout is open and vents a random 0 or 1.

Notice that the downstream draw only happens while the compressor is off. A tick is 51 passes of a 20 ms loop in the container, so a little over one second.

</details>

## Detect and defend

A defender sees this attack in two places. The process itself is the first: an HPT climbing out of its 60 to 90 band with the system valve shut is abnormal no matter who caused it, and process monitoring that alarms on it catches operators and attackers alike. The second is the HMI: switching to manual mode is a rare, meaningful event that should be logged with the user who did it.

The defences follow from that:

- **Independent safety functions.** The blowout valve works without the PLC or the HMI. That is the idea behind a Safety Instrumented System (SIS): a last line of defence that the control system cannot switch off.
- **Least privilege on the HMI.** Not every account needs manual mode. FUXA supports separate user roles, so a viewer cannot press buttons.
- **Strong credentials.** The operator login is a weak, well-known password here on purpose. See the [password attack briefing](/theory/password_attack).
- **Interlocks in the PLC.** A program can refuse to run the compressor with the valve shut above a limit, even in manual mode.

## Before you start

- [What is an ICS?](/theory/ics-basics) for the parts of a control system.
- [PLCs and the scan cycle](/theory/plc-fundamentals) for how the controller decides.
- [HMI and SCADA](/theory/hmi-scada) for what the operator screen does.
- [Safety systems](/theory/safety-systems) for why the blowout valve is independent.
