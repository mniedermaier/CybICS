# Ukraine power grid (2015, 2016, 2022)

On a winter afternoon in 2015, control room operators in western Ukraine watched the mouse pointer on their screens move by itself and switch off substation after substation. It was the first publicly confirmed cyberattack that cut electricity to customers. The same group came back in 2016 with malware that did the job automatically, and again in 2022. Together, the three attacks show how an attacker moves from "logging in like an operator" to "speaking the grid's protocols directly".

## What happened

**23 December 2015.** Attackers opened circuit breakers at substations of three regional electricity distribution companies. According to the joint analysis by the Electricity Information Sharing and Analysis Center (E-ISAC) and the SANS Institute, about 225,000 customers lost power for between one and six hours. Staff restored power by driving to the substations and switching them back on by hand.

**17 December 2016.** Just before midnight, a transmission substation near Kyiv operated by the national grid company Ukrenergo was switched off, and part of the city lost power for about an hour. In June 2017 the security companies ESET and Dragos published the malware behind it, which ESET named **Industroyer** and Dragos **CrashOverride**.

**8 April 2022.** During the Russian invasion, attackers planned to switch off high-voltage substations of a Ukrainian energy company with a new version, **Industroyer2**. The Ukrainian Computer Emergency Response Team (CERT-UA), working with ESET, found and stopped it before it caused an outage; they published it on 12 April 2022.

<figure class="wide">
<svg viewBox="0 0 560 160" role="img" aria-label="Timeline of the Ukrainian grid attacks. Spring 2015: phishing e-mails deliver BlackEnergy 3 into the companies' office networks. 23 December 2015: operators' HMIs are used to open breakers, about 225,000 customers lose power. 17 December 2016: Industroyer switches off a Kyiv transmission substation for about an hour. 8 April 2022: Industroyer2 is planned against high-voltage substations and stopped before it causes an outage.">
  <line x1="20" y1="70" x2="540" y2="70" stroke="currentColor" stroke-width="2"/>
  <g fill="#ff6b00"><circle cx="60" cy="70" r="6"/><circle cx="200" cy="70" r="6"/><circle cx="350" cy="70" r="6"/><circle cx="500" cy="70" r="6"/></g>
  <g font-size="12" fill="currentColor" text-anchor="middle">
    <text x="60" y="50" font-weight="bold">2015</text><text x="60" y="95">phishing,</text><text x="60" y="111">BlackEnergy 3</text>
    <text x="200" y="50" font-weight="bold">23 Dec 2015</text><text x="200" y="95">HMIs hijacked,</text><text x="200" y="111">~225,000 customers</text><text x="200" y="127">without power</text>
    <text x="350" y="50" font-weight="bold">17 Dec 2016</text><text x="350" y="95">Industroyer:</text><text x="350" y="111">Kyiv substation</text><text x="350" y="127">off for ~1 hour</text>
    <text x="500" y="50" font-weight="bold">8 Apr 2022</text><text x="500" y="95">Industroyer2</text><text x="500" y="111">planned,</text><text x="500" y="127">stopped in time</text>
  </g>
</svg>
<figcaption>Three attacks, one direction: each one needed fewer people at the keyboard than the one before.</figcaption>
</figure>

Ukraine's government blamed Russia. In October 2020 the United States Department of Justice charged six officers of the Russian military intelligence unit 74455, a group the security industry calls **Sandworm**, with crimes that include the 2015 and 2016 attacks. ESET also attributes Industroyer2 to Sandworm. These are the conclusions of governments and companies; Russia denies them.

## How the attack worked

### 2015: logging in like an operator

The 2015 attack was mostly done by hand, using the companies' own tools. The MITRE ATT&CK for ICS catalogue describes the steps.

| Step | What happened | ATT&CK for ICS |
|---|---|---|
| Getting in | Office documents with malicious macros installed BlackEnergy 3 in the office networks, months before the outage | T0865 Spearphishing Attachment |
| Becoming an operator | Stolen user names and passwords, then the companies' own Virtual Private Network (VPN) into the control network | T0859 Valid Accounts, T0822 External Remote Services |
| Switching off power | Remote control of the operators' HMIs; clicks on the screen opened the breakers | T0823 Graphical User Interface, T0831 Manipulation of Control |
| Slowing the repair | New firmware that broke the serial-to-Ethernet converters linking control centres to substations; KillDisk wiped computers | T1693.001 Modify Firmware: System Firmware, T0809 Data Destruction |
| Leaving operators blind | Control centre backup power reconfigured, and the customer call centre flooded with calls | T0814 Denial of Service, T0813 Denial of Control |

### 2016 and 2022: speaking the protocol directly

Industroyer did not need an HMI. It had modules that spoke four industrial protocols used in power grids: IEC 60870-5-101 (serial), IEC 60870-5-104 (over TCP/IP), IEC 61850 and OLE for Process Control Data Access (OPC DA). It sent commands straight to the substation equipment (**T1692.001 Unauthorized Message: Command Message**), switched breakers on and off repeatedly (**T0806 Brute Force I/O**) and then wiped its own tracks (**T0809 Data Destruction**). A separate tool tried to crash Siemens SIPROTEC protection relays with a known flaw (**T0837 Loss of Protection**).

Industroyer2 was smaller. It spoke only IEC 104 and carried a hard-coded list of the devices it should switch, which suggests the attackers had studied that exact substation in advance. It came with wiper malware for Windows and Linux computers.

<details class="deep-dive" markdown="1">
<summary>Deep dive: was 2016 meant to destroy equipment?</summary>

A 2019 Dragos reassessment by Joe Slowik argued that the 2016 attack aimed at more than a short blackout. Opening breakers while the protection relays were disabled could, when operators switched the power back on, have damaged equipment that was no longer protected. The relay attack failed, so this stayed a possibility. Treat it as an expert assessment, not an established fact.

</details>

Check that you can tell the three attacks apart and retell them in order.

<div data-widget="sequence" data-id="attack"></div>

## Why it worked

**The attackers had legitimate access.** In 2015 they did not break the control system; they logged in to it with real accounts over a VPN that had no second factor. To the system, they *were* the operators.

**Grid protocols trust every message.** IEC 104, like Modbus, has no built-in check of who sent a command. Once Industroyer could reach the equipment, a command from it looked exactly like a command from the control centre.

**Preparation was long and quiet.** BlackEnergy sat in the networks for months. The attackers studied the control systems before they touched them.

**Recovery was the real target.** Breaking the converters and wiping computers turned a few hours of outage into a long period in which substations had to be run by hand.

## What it means for CybICS

CybICS uses Modbus TCP instead of IEC 104, but the lessons map directly.

- **Stolen or guessed passwords.** In 2015 the HMI itself was the weapon. In the [FUXA password challenge](/ctf/challenge/password_attack) you get into the FUXA HMI at `172.18.0.4` by guessing the password, and the [OpenPLC password challenge](/ctf/challenge/password_openplc) does the same for the PLC's web interface. Once in, you are "an operator".
- **Commands without the HMI.** Industroyer skipped the HMI and talked to the equipment. On CybICS, any host that can reach port 502 on the PLC at `172.18.0.3` can write coils and registers, because Modbus has no authentication. The [Flood & Overwrite challenge](/ctf/challenge/flood_overwrite) shows what that does to the plant. Read [Modbus TCP](/theory/modbus) to understand why.
- **Sitting in the middle.** The [Man-in-the-Middle challenge](/ctf/challenge/mitm) places you between the HMI and the PLC, where you can watch and change every message, much as an attacker inside a grid control network can.

<div data-widget="checkpoint" data-id="protocol"></div>

## Lessons for defenders

- **Make remote access hard to abuse.** Use multi-factor authentication on every VPN or remote login into the control network, and log who uses it and when.
- **Assume the protocol will not protect you.** Limit which hosts may send commands to controllers, and watch for commands from anywhere else. See [Defence and hardening](/theory/defense-hardening).
- **Watch for the quiet phase.** Months of preparation leave traces: new accounts, unusual logins, scans. See [Detection and monitoring](/theory/detection-monitoring).
- **Plan to run by hand.** Ukraine recovered because staff could still operate substations manually. Practise that, and keep spare firmware and backups offline. See [Incident response](/theory/incident-response).
- **Look at the whole campaign.** Each attack followed the stages of the [ICS attack lifecycle](/theory/attack-lifecycle), and each stage was a chance to notice it.
