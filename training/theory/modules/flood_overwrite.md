# Flood and overwrite

In this challenge you overwrite the pressure reading of the CybICS plant hundreds of times a second, so that the PLC believes the high-pressure tank is almost empty. You never touch the compressor or the valves. The controller does the damage itself, because it acts faithfully on a lie.

## The idea

Picture a thermostat whose temperature sensor you hold an ice cube against. The room is warm, but the thermostat sees cold and keeps the heating on. Nothing is broken; the thermostat does exactly what it should with the information it has.

A PLC is in the same position. It never sees the tank, only a number in a **holding register**: a numbered 16-bit memory slot, like a mailbox, that the PLC reads every cycle. Modbus TCP lets any client on the network write to that mailbox, with no login and no check of who sent the value. If the attacker writes a false value more often than the real sensor writes the true one, the PLC almost always reads the false one.

MITRE ATT&CK for ICS calls repeated writes to an I/O value *Brute Force I/O* (T0806), sent as *Unauthorized Messages: Command Message* (T1692.001). Because the HMI shows the same forged number, the operator's view is manipulated too (*Manipulation of View*, T0832).

## How it looks on CybICS

The HPT pressure lives in holding register **1126** on OpenPLC (172.18.0.3, port 502). Two writers compete for it:

- The `hwio` container (172.18.0.2), which simulates the plant, writes the true pressure about every 20 milliseconds.
- The challenge script `flooding_hpt.py` from `training/flood_overwrite/` writes the value 10, as fast as the PLC answers, several hundred times a second.

<figure class="wide">
<style>
.fo-r {--d: 12s; --on:#e65c00;}
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
     aria-label="A hundred-millisecond timeline. The attacker writes register 1126 a little more than once per millisecond; hwio writes the true value back every 20 milliseconds. The register holds the forged value almost all the time, and the true value only for a fraction of a millisecond after each hwio write.">
  <text x="8" y="46" font-size="14" opacity="0.85">attacker</text>
  <text x="8" y="60" font-size="13" opacity="0.7">~1.2 ms</text>
  <g class="lane"><rect x="80.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="84.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="88.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="92.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="96.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="100.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="104.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="108.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="112.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="116.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="120.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="124.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="129.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="133.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="137.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="141.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="145.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="149.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="153.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="157.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="161.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="165.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="169.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="173.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="177.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="182.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="186.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="190.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="194.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="198.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="202.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="206.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="210.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="214.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="218.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="222.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="226.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="231.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="235.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="239.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="243.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="247.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="251.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="255.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="259.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="263.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="267.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="271.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="275.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="279.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="284.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="288.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="292.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="296.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="300.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="304.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="308.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="312.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="316.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="320.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="324.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="328.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="333.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="337.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="341.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="345.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="349.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="353.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="357.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="361.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="365.6" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="369.7" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="373.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="377.8" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="381.9" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="386.0" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="390.1" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="394.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="398.2" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="402.3" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="406.4" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="410.5" y="42" width="1.8" height="16" fill="var(--on)"/><rect x="414.6" y="42" width="1.8" height="16" fill="var(--on)"/></g>
  <text x="8" y="96" font-size="14" opacity="0.85">hwio</text>
  <text x="8" y="110" font-size="13" opacity="0.7">~20 ms</text>
  <g class="lane"><rect x="80.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="148.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="216.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="284.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="352.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/><rect x="420.0" y="92" width="2.6" height="16" fill="currentColor" opacity="0.75"/></g>
  <text x="8" y="146" font-size="14" opacity="0.85">reg 1126</text>
  <text x="8" y="160" font-size="13" opacity="0.7">holds</text>
  <g class="lane">
    <rect x="80" y="142" width="340" height="16" fill="var(--on)"/>
    <rect x="80.0" y="142" width="2.1" height="16" fill="currentColor"/><rect x="148.0" y="142" width="2.1" height="16" fill="currentColor"/><rect x="216.0" y="142" width="2.1" height="16" fill="currentColor"/><rect x="284.0" y="142" width="2.1" height="16" fill="currentColor"/><rect x="352.0" y="142" width="2.1" height="16" fill="currentColor"/>
  </g>
  <line class="head" x1="80" y1="34" x2="80" y2="166" stroke="currentColor" stroke-width="2"/>
  <g font-size="13" opacity="0.7">
    <text x="80" y="182" text-anchor="middle">0 ms</text>
    <text x="250" y="182" text-anchor="middle">50</text>
    <text x="420" y="182" text-anchor="middle">100</text>
  </g>
</svg>
<figcaption>The orange band is the forged value; the thin notches are the moments after each <code>hwio</code> write, before the next attacker write buries it. The true value survives only a fraction of a millisecond, so the PLC, which reads the register every 50 ms, almost always sees the lie. The attacker's writes are not stronger, only more frequent.</figcaption>
</figure>

With the HPT reading 10, two rules in the PLC program fire, both exactly as designed. The compressor rule sees a pressure below 60 and switches the compressor on. The system-valve rule opens the valve only between 50 and 100, so at 10 it shuts the valve and nothing draws gas from the tank. The real pressure climbs by about one unit per second.

<figure class="wide">
<style>
.fo-d {--d: 14s; --on:#e65c00;}
.fo-d .trace {stroke-dasharray:1000; animation: d-draw var(--d) linear 18 forwards;}
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
     aria-label="Two traces over about five minutes. The value OpenPLC reads from register 1126 stays flat at 10. The pressure actually in the tank climbs from 75, reaching the relief valve at about three minutes and the 255 ceiling at about five. The compressor runs almost continuously with the system valve shut.">
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
<figcaption>The race is decided in milliseconds, but the plant moves in steps of about one second. That is why it takes minutes, not seconds, to reach the relief valve. Above it the rise slows, because the valve vents a little and the storage tank is running low, but it does not stop.</figcaption>
</figure>

On the FUXA HMI the HPT display shows the forged 10, because it reads the same register. The blowout indicator is different: `hwio` sets it from the *true* pressure in register 1134, so it goes high while the pressure display still says 10.

<div data-widget="plant-live" data-fields="hpt,boSen,compressor,systemValve"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: what limits the attack</summary>

The compressor needs gas to push. It takes two units out of the gas storage tank (GST, register 1124) for every unit it adds to the HPT, and the PLC only runs it while the GST holds more than 50. Under a flood the GST drains faster than the supply refills it, so the compressor runs in bursts once storage is low. The attacker cannot speed this up, because the flood does not touch register 1124. A rule written to protect the compressor from an empty tank ends up limiting the attack.

After the flood stops, the PLC sees the true, very high pressure, switches the compressor off and keeps the system valve shut. The relief valve vents down to about 200 and closes, and then nothing drains the tank. The plant does not recover on its own.

</details>

## How to approach it

1. Read `flooding_hpt.py` before you run it. Find the register it writes, the value and the loop. Predict what the PLC will do.
2. Open FUXA on port 1881 in another window and note the normal values first.
3. Run the script from the attack machine against OpenPLC. It runs until you stop it or for a set `--duration`.
4. Watch the HMI. Compare the pressure display with the blowout indicator over a few minutes.
5. Click **Verify** on the challenge page. It does not look at the plant; it asks the IDS whether its flood rule has fired.
6. Stop the script and watch how the plant does, or does not, recover.

<div data-widget="checkpoint" data-id="race"></div>

## Detect and defend

This attack is loud. The CybICS IDS counts Modbus write requests per source: fifty within five seconds from any host other than `hwio`, `fuxa` or `openplc` raises a critical `modbus_flood` alert. A second rule flags ten writes within thirty seconds from any unexpected writer. Try the trade-off between catching attackers and bothering operators yourself:

<div data-widget="ids-threshold"></div>

The [Detecting a flood](/theory/detect_overwrite) challenge asks you to find this alert. The patient opposite is [IDS evasion](/theory/ids_evasion): a few writes, seconds apart, stay below every threshold.

Defences that stop or limit the attack:

- **Allow-list Modbus writers.** Only the plant I/O and the HMI need to write. A firewall in front of port 502 can drop everything else. See [Host firewalling](/theory/defense_firewall).
- **Plausibility checks in the PLC.** A real pressure cannot fall from 75 to 10 in one cycle. A program can reject impossible jumps or compare redundant sensors.
- **Independent safety.** The relief valve works on the real pressure, not on a register, which is why the tank does not burst.
- **Segmentation**, so the attack machine cannot reach port 502 at all.

## Before you start

- [Modbus TCP](/theory/modbus) for registers and write function codes.
- [The gas pressure process](/theory/physical_process) for how the plant reacts.
- [Detection and monitoring](/theory/detection-monitoring) for how rate rules work.
