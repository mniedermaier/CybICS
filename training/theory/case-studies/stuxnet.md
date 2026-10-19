# Stuxnet (2010)

Stuxnet was the first widely known malware built to damage physical machines. It changed the program inside industrial controllers so that uranium centrifuges spun at harmful speeds, while the operators saw readings that looked perfectly normal. Almost every idea in it can be tried, in small, on the CybICS gas plant.

## What happened

Stuxnet was found in June 2010 by VirusBlokAda, a small antivirus company in Belarus, after a customer's Windows computers kept rebooting. Researchers at Symantec, Langner Communications and elsewhere then took it apart.

The Windows part of the worm was only a carrier. The real payload was code for Siemens Step 7, the software engineers use to program Siemens S7 Programmable Logic Controllers (PLCs). It only became active on a very specific setup: S7 controllers driving frequency converters (the electronics that set how fast a motor spins) from two particular vendors.

That setup matched the uranium enrichment plant at Natanz in Iran. Reports by the International Atomic Energy Agency (IAEA) show that Iran removed a large number of centrifuges at Natanz in late 2009 and early 2010. Most researchers link this to Stuxnet, although Iran never published its own account.

Nobody has officially claimed Stuxnet. Journalists, most prominently David Sanger in the New York Times in 2012, reported that it was a joint United States and Israeli operation. Treat that as well-sourced reporting, not as a confirmed fact.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the timeline and the sources</summary>

<figure class="wide">
<svg viewBox="0 0 560 150" role="img" aria-label="Timeline of Stuxnet. Around 2007: an early version that attacked valves is already in circulation. 2009: newer versions spread and attack centrifuge drives. Late 2009 to early 2010: Iran replaces many centrifuges at Natanz. June 2010: VirusBlokAda discovers the worm. February 2011: Symantec publishes the final version of its dossier.">
  <line x1="20" y1="70" x2="540" y2="70" stroke="currentColor" stroke-width="2"/>
  <g fill="#ff6b00"><circle cx="40" cy="70" r="6"/><circle cx="150" cy="70" r="6"/><circle cx="270" cy="70" r="6"/><circle cx="390" cy="70" r="6"/><circle cx="510" cy="70" r="6"/></g>
  <g font-size="12" fill="currentColor" text-anchor="middle">
    <text x="40" y="50" font-weight="bold">~2007</text><text x="40" y="95">early version</text><text x="40" y="111">attacks valves</text>
    <text x="150" y="50" font-weight="bold">2009</text><text x="150" y="95">new versions</text><text x="150" y="111">attack drives</text>
    <text x="270" y="50" font-weight="bold">2009&#8211;10</text><text x="270" y="95">centrifuges</text><text x="270" y="111">replaced at Natanz</text>
    <text x="390" y="50" font-weight="bold">Jun 2010</text><text x="390" y="95">worm found</text><text x="390" y="111">in Belarus</text>
    <text x="510" y="50" font-weight="bold">Feb 2011</text><text x="510" y="95">Symantec</text><text x="510" y="111">dossier final</text>
  </g>
</svg>
<figcaption>The attack ran for years before anyone noticed. The early valve-attacking version was described by Symantec in 2013 ("Stuxnet 0.5"); exact start dates are not public.</figcaption>
</figure>

Symantec's "W32.Stuxnet Dossier" (final version February 2011) and Ralph Langner's analysis are still the main public sources. The IAEA figures on the removed centrifuges were analysed by the Institute for Science and International Security.

</details>

## How the attack worked

Think of Stuxnet as a burglar who also replaces the security camera feed with a recording of an empty room. The MITRE ATT&CK for ICS knowledge base, a catalogue of attacker techniques against Industrial Control Systems (ICS), lists the steps.

| Step | What Stuxnet did | ATT&CK for ICS |
|---|---|---|
| Getting in | Spread on USB sticks, because the plant was not connected to the internet | T0847 Replication Through Removable Media |
| Spreading | Used Windows flaws, among them four that were unknown at the time ("zero-days"), to move between computers | T0866 Exploitation of Remote Services |
| Reaching the PLC | Infected Step 7 project files, so an engineer opening a project spread it further | T0873 Project File Infection |
| Hiding on the engineering PC | Replaced a Step 7 library so that the engineer could not see the malicious code blocks | T0874 Hooking, T0851 Rootkit |
| Changing the logic | Wrote its own code blocks into the PLC | T0843 Program Download, T0889 Modify Program |
| Changing the process | Ordered the drives to unusual speeds, far above and far below normal | T0836 Modify Parameter, T0831 Manipulation of Control |
| Fooling the operators | Recorded normal sensor values and played them back to the monitoring systems | T0835 Manipulate I/O Image, T0832 Manipulation of View |

<details class="deep-dive" markdown="1">
<summary>Deep dive: stolen certificates and the speed attack in numbers</summary>

The driver files were signed with certificates stolen from two Taiwanese hardware companies, so Windows trusted them. Stuxnet also used a hard-coded database password in Siemens' WinCC supervisory software.

According to Symantec, the drive attack waited for the motors to run between 807 Hz and 1210 Hz, then pushed them to 1410 Hz, back to 1064 Hz, later down to 2 Hz, and back again, with weeks of quiet in between. Running a centrifuge rotor through these speeds stresses it mechanically. The long pauses kept the failures looking like ordinary bad luck rather than an attack.

The targeted setup was S7-300 controllers driving the frequency converters, plus S7-417 controllers in a matching cascade layout. The older S7-417 attack targeted the valves that protect a cascade of centrifuges, raising the pressure inside them. Langner describes this as the more aggressive of the two attacks.

</details>

Check that you can retell the attack, from the USB stick to the damaged centrifuges.

<div data-widget="sequence" data-id="attack"></div>

## Why it worked

**The PLC trusted whoever programmed it.** An S7 controller of that time accepted new code from any Step 7 installation that could reach it, with no check of who wrote it.

**The engineers trusted their tools.** If Step 7 says the program is unchanged, people believe it. Stuxnet attacked exactly that tool.

**The operators trusted their screens.** Operators watch the process through a Human-Machine Interface (HMI). When its values are a recording, they see a calm plant while the machines are damaged.

**An air gap is not a wall.** The plant was isolated from the internet, but people carried data in on USB sticks. Isolation slowed the attack; it did not stop it.

## What it means for CybICS

You can recreate the two halves of Stuxnet on the CybICS gas plant. Read [PLCs and the scan cycle](/theory/plc-fundamentals) first.

**Changing the PLC logic.** The CybICS OpenPLC program decides when the compressor runs, from the pressures in the high-pressure tank (HPT) and the gas storage tank (GST). In the [PLC programming challenge](/ctf/challenge/plc_programming) you change that program and upload it through the OpenPLC web interface on port 8080 of `172.18.0.3`. The engineering workstation at `172.18.0.10` plays the role of Natanz's Step 7 computers.

**Lying to the operators.** The FUXA HMI at `172.18.0.4` reads the plant values from the PLC over Modbus TCP, which has no authentication and no integrity check. In the [Flood & Overwrite challenge](/ctf/challenge/flood_overwrite) you overwrite the HPT pressure value in holding register 1126. The [Man-in-the-Middle challenge](/ctf/challenge/mitm) lets you change the values on their way between the PLC and the HMI.

<div class="callout cybics" markdown="1">
**On the plant:** when you overwrite the HPT value, look at the FUXA screen. What would an operator conclude, and which independent measurement could have told them the truth? That question is the lesson of Natanz.
</div>

<div data-widget="checkpoint" data-id="view"></div>

## Lessons for defenders

- **Control removable media.** Scan or block USB sticks; the air gap only helps if people do not bridge it.
- **Protect the engineering workstation.** It holds the keys to every controller. Limit who uses it, what is plugged into it and which networks it reaches.
- **Watch for programming traffic.** Program downloads to a PLC are rare in normal operation, so each one is worth an alert. See [Detection and monitoring](/theory/detection-monitoring) and the [ICS attack lifecycle](/theory/attack-lifecycle).
- **Know what program your PLC is running.** Keep a known-good copy of every controller program and compare it regularly, with a tool you trust. A change nobody planned is an incident. See [Defence in depth](/theory/defense-hardening).
- **Do not rely on one view of the process.** An independent measurement, such as a separate speed or pressure gauge that does not go through the PLC, shows what a fooled HMI hides.

Each of these defences fits one moment of the attack; match them up.

<div data-widget="sequence" data-id="defend"></div>
