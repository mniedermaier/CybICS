# TRITON/TRISIS (2017)

A Safety Instrumented System (SIS) is the last automatic line of defence in a plant. When pressure or temperature leaves the safe range, it shuts the process down, whatever the normal control system is doing. In 2017 attackers tried to reprogram one. It is the first known malware built to switch off the part of a plant that exists to keep people alive, and it was only found because it made a mistake.

## What happened

In 2017 a petrochemical plant, widely reported to be in Saudi Arabia, shut down unexpectedly. Its safety controllers, Triconex Tricon units made by Schneider Electric, had stopped the process and gone into their fail-safe state. While investigating, the plant's staff and later the security company FireEye (now Mandiant) found malware on the engineering workstation used to program those safety controllers.

On 14 December 2017 FireEye and Dragos published their analyses on the same day. FireEye called the malware **TRITON**, Dragos called it **TRISIS**; both names are in use. The United States Cybersecurity and Infrastructure Security Agency (CISA, then still the ICS-CERT) and Schneider Electric issued advisories as well.

<figure class="wide">
<svg viewBox="0 0 560 150" role="img" aria-label="Timeline of TRITON. 2017: attackers reach the safety engineering workstation of a petrochemical plant. 2017: the safety controllers trip and shut the plant down, prompting an investigation. December 2017: FireEye and Dragos publish their analyses. October 2018: FireEye links the tools to a Russian research institute. 2020 and 2022: the United States sanctions the institute and charges one of its employees.">
  <line x1="20" y1="70" x2="540" y2="70" stroke="currentColor" stroke-width="2"/>
  <g fill="#ff6b00"><circle cx="50" cy="70" r="6"/><circle cx="165" cy="70" r="6"/><circle cx="280" cy="70" r="6"/><circle cx="395" cy="70" r="6"/><circle cx="510" cy="70" r="6"/></g>
  <g font-size="12" fill="currentColor" text-anchor="middle">
    <text x="50" y="50" font-weight="bold">2017</text><text x="50" y="95">safety engineering</text><text x="50" y="111">PC compromised</text>
    <text x="165" y="50" font-weight="bold">2017</text><text x="165" y="95">controllers trip,</text><text x="165" y="111">plant shuts down</text>
    <text x="280" y="50" font-weight="bold">Dec 2017</text><text x="280" y="95">FireEye and</text><text x="280" y="111">Dragos publish</text>
    <text x="395" y="50" font-weight="bold">Oct 2018</text><text x="395" y="95">link to Russian</text><text x="395" y="111">institute</text>
    <text x="510" y="50" font-weight="bold">2020 / 2022</text><text x="510" y="95">US sanctions</text><text x="510" y="111">and indictment</text>
  </g>
</svg>
<figcaption>The attack was noticed because the safety system did what it was designed to do: when something went wrong inside it, it shut the plant down.</figcaption>
</figure>

**Who was behind it.** In October 2018 FireEye linked the tools to the Central Scientific Research Institute of Chemistry and Mechanics (TsNIIKhM), a Russian state research institute. The US Treasury sanctioned that institute in 2020, and in 2022 the US Department of Justice charged one of its employees. Dragos tracks the group as XENOTIME and reported in 2019 that it had started probing electric utilities in North America. These are the findings of companies and one government; they have not been tested in court.

## How the attack worked

An SIS is like the circuit breaker in your home's fuse box: it does nothing for years, then cuts the power the moment something is dangerous. The TRITON attackers wanted to control that breaker. The MITRE ATT&CK for ICS catalogue maps their steps.

| Step | What happened | ATT&CK for ICS |
|---|---|---|
| Reaching the safety network | Using remote desktop jump hosts and poorly configured firewalls, the attackers moved from the office network to the engineering workstation for the safety controllers | T0886 Remote Services |
| Blending in | The tool was named `trilog.exe`, like a genuine Triconex log viewer | T0849 Masquerading |
| Talking to the controller | It spoke TriStation, Schneider's own engineering protocol, over the network | T0869 Standard Application Layer Protocol |
| Checking first | It read which state the controller was in before acting | T0868 Detect Operating Mode, T0845 Program Upload |
| Gaining full control | A previously unknown flaw in the Tricon firmware gave it the highest privileges | T0890 Exploitation for Privilege Escalation |
| Planting a backdoor | It wrote its own code into the controller's memory, so the attackers could later read and change it at will | T0843 Program Download, T1693.001 Modify Firmware: System Firmware |
| Covering tracks | It tried to restore the original state afterwards | T0872 Indicator Removal on Host |

The intended impact is **T0880 Loss of Safety**: a safety system that no longer responds when it must.

<details class="deep-dive" markdown="1">
<summary>Deep dive: what was the plan?</summary>

The public analyses agree that the attackers were installing a hidden, persistent backdoor in the safety controllers. They do not agree on, and cannot know, exactly what the final step would have been. One possibility is to disable the safety function and then cause a dangerous condition through the normal control system; another is to trigger shutdowns at will. FireEye's view was that the attackers were preparing the ability to cause physical damage. Avoid stating the final goal as fact.

Reports also indicate that the controllers' physical key switch had been left in a position that allowed them to be programmed over the network. Tricon controllers have such a switch precisely so that remote programming can be locked out during normal operation.

</details>

## Why it worked

**The safety system was reachable.** Good practice keeps the SIS on its own isolated network. Here the attackers could get from the engineering workstation to the safety controllers over the network.

**The engineering workstation was the gateway.** Whoever controls the computer that programs the SIS controls the SIS. Its security mattered as much as the controller's.

**A lock was left open.** The controller's mode switch is a physical barrier against exactly this kind of attack, and it only works if it is in the locked position.

**It failed safe.** The good news is in the mistake: when the injected code misbehaved, the controllers detected a fault and stopped the plant. A safe shutdown is expensive, but nobody was hurt.

## What it means for CybICS

CybICS has no separate SIS. Its last line of defence is the **blow-out valve** on the high-pressure tank (HPT), and it is built very differently from a programmable safety controller. The valve is part of the physical process simulation, not of the OpenPLC program: it opens when the HPT goes above 220 bar and stays open until the pressure falls below 200. No Modbus write and no PLC program change can disable it, just as a real spring-loaded relief valve does not care what the software says.

The valve has a limit, though. It vents more slowly than the compressor fills, so a compressor that keeps running drives the tank into a state the valve cannot recover. In the [physical process challenge](/ctf/challenge/physical_process) you work out what triggers the blow-out and how the HMI reports it. Read [Safety systems](/theory/safety-systems) first to see where an SIS would sit in this plant.

Other parts of TRITON map onto the lab as well:

- The engineering workstation at `172.18.0.10` runs the OpenPLC Editor. Like the Triconex workstation, whoever controls it can produce new controller code.
- OpenPLC's web interface on port 8080 can stop and start the PLC program, a software version of the Tricon's mode switch (T0858 Change Operating Mode). There is no physical key to lock it.

<div data-widget="checkpoint" data-id="barrier"></div>

## Lessons for defenders

- **Keep the safety system separate.** Put the SIS and its engineering workstation on their own network, with no path from the office network. See [Defence and hardening](/theory/defense-hardening).
- **Use the physical locks.** Keep controller mode switches in the run position and remove the key. A physical barrier cannot be hacked from the network.
- **Treat every unexpected trip as a possible attack.** The plant investigated a shutdown and found TRITON. Shutdowns without a process reason deserve a security look. See [Incident response](/theory/incident-response).
- **Layer your protection.** Keep at least one safety barrier, such as a mechanical relief valve, that no software can switch off. See [Risk assessment](/theory/risk-assessment).
- **Watch engineering traffic.** Programming a safety controller is rare. Any TriStation-style programming session outside a planned change is worth an alert. See [Detection and monitoring](/theory/detection-monitoring).
