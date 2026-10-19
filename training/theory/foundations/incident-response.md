# Incident response in OT

Sooner or later an alarm turns out to be real. What you do in the next hour decides whether a security incident stays a security incident or becomes a safety incident. This article covers the response phases, why "unplug it" can be the worst move in a plant, and where you find evidence in CybICS.

## The six phases

Most incident response plans follow the same six-phase cycle. The names matter less than the order.

<figure>
<svg viewBox="0 0 520 220" role="img" aria-label="The incident response cycle as six boxes in a loop: preparation, identification, containment, eradication, recovery and lessons learned. An arrow leads from lessons learned back to preparation, showing that each incident improves the preparation for the next.">
  <g font-size="12" text-anchor="middle" fill="currentColor">
    <g fill="none" stroke="currentColor" stroke-width="1.5">
      <rect x="20" y="30" width="140" height="44" rx="8"/>
      <rect x="190" y="30" width="140" height="44" rx="8"/>
      <rect x="360" y="30" width="140" height="44" rx="8" stroke="#ff6b00" stroke-width="2.5"/>
      <rect x="360" y="146" width="140" height="44" rx="8"/>
      <rect x="190" y="146" width="140" height="44" rx="8"/>
      <rect x="20" y="146" width="140" height="44" rx="8"/>
      <path d="M160 52 H186 M330 52 H356 M430 74 V142 M360 168 H334 M190 168 H164 M90 146 V78"/>
    </g>
    <text x="90" y="57">1 Preparation</text>
    <text x="260" y="57">2 Identification</text>
    <text x="430" y="57" font-weight="bold">3 Containment</text>
    <text x="430" y="173">4 Eradication</text>
    <text x="260" y="173">5 Recovery</text>
    <text x="90" y="173">6 Lessons learned</text>
    <text x="260" y="118" font-size="11" opacity="0.8">containment is where OT differs most</text>
  </g>
</svg>
<figcaption>The incident response cycle. Lessons learned feed back into preparation, so each incident makes the next response better.</figcaption>
</figure>

1. **Preparation.** Before anything happens: a written plan, known-good backups of PLC programs, agreed safe actions, monitoring that records evidence, and practice.
2. **Identification.** Is the alert real, and what is affected? Compare what the alarm says with what the plant is actually doing.
3. **Containment.** Stop the attacker from doing more damage, without making the plant less safe.
4. **Eradication.** Remove what the attacker left behind: changed programs, new accounts, malware, stolen passwords.
5. **Recovery.** Bring the plant back to normal automatic operation, step by step, and watch closely.
6. **Lessons learned.** What worked, what did not, and what changes now: a firewall rule, an IDS threshold, a password policy.

## Why OT is different: you cannot just pull the plug

In an office, you disconnect an infected laptop and lose a few hours of work. In a plant, every device you switch off was doing something, and the process does not pause while you investigate.

<div class="callout analogy" markdown="1">
**Analogy:** if a pilot suspects a problem with the autopilot, they do not switch off the engines. They take manual control first, keep the plane flying, and only then work out what went wrong.
</div>

Three things shape every decision in OT incident response:

- **Safety comes first.** The first question is not "how do we stop the attacker?" but "is the process safe now, and will it stay safe after what we do next?" Operations and safety staff belong in the room from the start.
- **Containment has side effects.** Stopping a PLC drops its outputs to a default state; cutting the HMI off from the PLC blinds the operators. Both can be worse than the attack, so the plan says in advance which actions are safe.
- **Manual operation is a real option.** After the 2015 attack on the Ukrainian grid, operators restored power by switching substations by hand (see [the Ukraine case study](/theory/ukraine-grid)).

The reverse also happens. In 2021 Colonial Pipeline shut its pipeline down as a precaution after ransomware hit its business IT network, because it could not be sure the operational side was unaffected (see [the Colonial Pipeline case study](/theory/colonial-pipeline)). Containment can mean stopping the process on purpose, in a controlled way.

<div data-widget="checkpoint" data-id="plug"></div>

## Evidence: collect it before it disappears

Evidence answers who did what, when and how. In OT much of it is **volatile**: it lives in memory and is gone after a restart. Rebooting a controller "to be safe" can wipe what shows the attacker's changes. Collect first, then act, unless safety demands otherwise.

- Write down what you do and when; your own actions become part of the record.
- Copy logs and captures off the affected system before changing it.
- Compare the running PLC program with a known-good backup.

## Evidence sources in CybICS

CybICS gives you four places to look.

| Source | Where | What it tells you | What it misses |
|---|---|---|---|
| **IDS alerts** | The IDS API on port 8443 (`/api/alerts`, `/api/summary`) | Which rule fired, the severity, the source and destination address, the MITRE technique and the time | Anything no rule looks for, such as DNP3 commands |
| **Packet captures** | Wireshark or `tshark` on the attack machine; `tcpdump` on the board | Every byte of the traffic you captured, including the exact register and value written | Traffic you did not capture, and only from when you started |
| **PLC logs** | The runtime log on the OpenPLC dashboard (port 8080), and the container logs via `./cybics.sh logs` | When protocol servers started and when clients connected and disconnected | The clients' addresses and what they wrote |
| **Process data** | The FUXA HMI and the registers, for example HPT in holding register 1126 | What the plant actually did | Why it did it |

The IDS keeps only its 500 most recent alerts, and only in memory: a restart or a call to its clear endpoint erases them, so export them early. And no single source is enough: the alert names the sender, the capture shows which coil was written, the process data shows whether the HPT pressure rose.

<div data-widget="checkpoint" data-id="volatile"></div>

## A response on CybICS, step by step

Imagine the IDS raises `modbus_unauth_write` from `172.18.0.100`, the attack machine.

1. **Identification.** Is the HPT pressure on the HMI still between 60 and 90 bar? Pull the alert details from the IDS and start a capture.
2. **Containment.** Keep the PLC running: it holds the pressure in range. Instead, drop traffic from `172.18.0.100` at the PLC with a firewall rule. If the pressure is already rising, an operator can switch the HMI to manual and stop the compressor.
3. **Eradication.** Check that the PLC program still matches the known-good backup, and change any password the attacker could have seen.
4. **Recovery.** Return to automatic mode and watch the pressure and the IDS for a while.
5. **Lessons learned.** Should the IDS threshold be lower, the firewall rule permanent? Write it down.

The *IDS forensics* challenge trains identification; read [Detection and monitoring](/theory/detection-monitoring) first. Now a different alarm: sort the response into the six phases.

<div data-widget="sequence" data-id="response"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: plans, playbooks and the OT-specific guidance</summary>

The six-phase version of the cycle is the one taught by SANS; NIST SP 800-61 groups the same work into fewer, larger phases. A full Preparation phase also includes a contact list and an up-to-date asset inventory. In the CybICS walk-through, the known-good program is `cybICS.st`, and eradication also checks that no PLC settings changed. The *IDS forensics* challenge has you query the IDS for its alert history and work out who was most active, which rule fired most and when the activity started.

NIST SP 800-61 is the general US guide to incident handling. Its 2024 revision (Rev. 3) aligns the response activities with the NIST Cybersecurity Framework 2.0 functions rather than presenting a separate lifecycle. For OT, NIST SP 800-82 Rev. 3 adds the points this article stresses: involve operations and safety staff, plan containment actions per system in advance, and prefer manual or degraded operation over abrupt shutdown where it is safe.

A practical plan contains **playbooks**: one page per likely scenario ("unauthorised writes to the PLC", "ransomware on the HMI", "lost engineering laptop") that lists who decides, which actions are safe, which evidence to collect and in what order. Exercising them in a tabletop session, where the team talks through a scenario without touching the plant, finds most gaps at almost no cost. A training platform such as CybICS is a natural place to run such an exercise against live, harmless traffic.

</details>
