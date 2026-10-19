# Colonial Pipeline (2021)

Colonial Pipeline is the largest pipeline for refined fuel in the United States. In May 2021 a ransomware gang encrypted computers in its office network. As far as is publicly known, the attackers never touched the systems that control the pipeline. The pipeline still stopped for five days, and parts of the US East Coast ran short of fuel. This case is about why an IT attack can stop OT, the Operational Technology that runs physical processes.

## What happened

On 7 May 2021 an employee found a ransom note on an IT computer. The same morning Colonial shut the whole pipeline down as a precaution, for the first time in its history. It paid the ransom that evening and began restarting on 12 May.

<figure class="wide">
<svg viewBox="0 0 560 150" role="img" aria-label="Timeline of the Colonial Pipeline incident in 2021. 7 May: ransom note found, pipeline shut down as a precaution. 7 May, evening: ransom of 75 bitcoin paid. 10 May: FBI names DarkSide. 12 May: restart begins. 7 June: Department of Justice recovers 63.7 bitcoin. 8 June: CEO testifies to the Senate.">
  <line x1="20" y1="70" x2="540" y2="70" stroke="currentColor" stroke-width="2"/>
  <g fill="#ff6b00"><circle cx="40" cy="70" r="6"/><circle cx="135" cy="70" r="6"/><circle cx="230" cy="70" r="6"/><circle cx="325" cy="70" r="6"/><circle cx="420" cy="70" r="6"/><circle cx="515" cy="70" r="6"/></g>
  <g font-size="12" fill="currentColor" text-anchor="middle">
    <text x="40" y="50" font-weight="bold">7 May</text><text x="40" y="95">note found,</text><text x="40" y="111">pipeline off</text>
    <text x="135" y="50" font-weight="bold">7 May</text><text x="135" y="95">ransom</text><text x="135" y="111">paid</text>
    <text x="230" y="50" font-weight="bold">10 May</text><text x="230" y="95">FBI names</text><text x="230" y="111">DarkSide</text>
    <text x="325" y="50" font-weight="bold">12 May</text><text x="325" y="95">restart</text><text x="325" y="111">begins</text>
    <text x="420" y="50" font-weight="bold">7 Jun</text><text x="420" y="95">most bitcoin</text><text x="420" y="111">recovered</text>
    <text x="515" y="50" font-weight="bold">8 Jun</text><text x="515" y="95">Senate</text><text x="515" y="111">hearing</text>
  </g>
</svg>
<figcaption>The pipeline was off for about five days, although the attack was confined to the office IT network.</figcaption>
</figure>

During those days, many petrol stations in the south-eastern United States ran dry, partly because people rushed to fill up.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the full timeline and the scale of the outage</summary>

Colonial's pipeline runs about 5,500 miles from Texas to the New York area and, by the company's own figures, carries around 45 per cent of the fuel used on the East Coast. During the outage several states declared emergencies, and federal agencies temporarily relaxed rules on fuel transport by road.

| Date (2021) | Event |
|---|---|
| 7 May, early morning | An employee finds a ransom note on an IT computer. The same morning Colonial decides to shut the whole pipeline down as a precaution, for the first time in its history. |
| 7 May, evening | According to Chief Executive Joseph Blount, Colonial pays the attackers 75 bitcoin, about 4.4 million US dollars at the time, for a decryption tool. |
| 10 May | The Federal Bureau of Investigation (FBI) names the DarkSide ransomware group as responsible. |
| 12 May, evening | Colonial starts restarting the pipeline. Deliveries return to normal over the following days. |
| 7 June | The US Department of Justice announces it has recovered 63.7 of the bitcoin. |
| 8 and 9 June | Blount testifies before the US Senate and House of Representatives. |

</details>

## How the attack worked

Ransomware is malware that encrypts files so their owner cannot use them, and demands money for the key. DarkSide, the group the FBI named, ran "ransomware as a service": it wrote the ransomware and rented it to others, who broke in and shared the ransom. The table uses MITRE ATT&CK for Enterprise, the IT catalogue, for the IT steps and ATT&CK for ICS for the effect on operations.

| Step | What happened | ATT&CK |
|---|---|---|
| Getting in | The password of an old Virtual Private Network (VPN) account. The CEO testified that it was a "legacy" profile no longer meant to be in use, with no multi-factor authentication. | Enterprise T1133 External Remote Services, T1078 Valid Accounts |
| Stealing data | According to press reports, about 100 gigabytes of data were copied out before encrypting, to add pressure. | Exfiltration (the exact method is not public) |
| Encrypting | Ransomware encrypted IT systems. | Enterprise T1486 Data Encrypted for Impact |
| Impact on operations | Fuel stopped flowing although the control systems were not attacked. | ICS T0828 Loss of Productivity and Revenue, T0826 Loss of Availability |

MITRE's own description of T0828 uses Colonial as its example.

<details class="deep-dive" markdown="1">
<summary>Deep dive: what is not known about the break-in</summary>

How exactly the attackers obtained the password is not public. Investigators told reporters that it may have been reused and leaked elsewhere; treat that as unconfirmed. MITRE's T0828 description puts the effect at roughly 2.5 million barrels of fuel a day that the pipeline could not move.

</details>

Now retell the incident, from the forgotten VPN account to the stopped pipeline.

<div data-widget="sequence" data-id="attack"></div>

## Why it worked

**One password was enough.** The forgotten VPN account had no second factor, and nobody was watching an account nobody thought was in use.

**Nobody could be sure where the attack stopped.** Colonial said it shut down to contain the attack. If you do not know whether the attacker can reach your control systems, stopping the process is the safe choice. The separation between IT and OT could not be proven when it mattered.

**The business depended on IT.** A pipeline also has to track whose fuel it carries and bill for it. CNN reported, citing people briefed on the matter, that the billing system was hit and that this kept the pipeline off; Colonial did not confirm that. Either way: if a process cannot run without an IT system, that IT system is part of the process.

<div class="callout analogy" markdown="1">
**Analogy:** a bakery's ovens work fine, but the till and the order system are down. You could bake, but you would not know who ordered what or how to get paid. Many bakeries would close for the day.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: what changed afterwards</summary>

Within weeks, the US Transportation Security Administration, which regulates pipeline security, issued its first mandatory cybersecurity directives for pipeline operators. They required, among other things, reporting incidents to CISA, the US Cybersecurity and Infrastructure Security Agency, and later specific measures such as network segmentation between IT and OT. The incident also sped up US government action against ransomware groups.

</details>

## What it means for CybICS

On CybICS every container sits in one flat network, `172.18.0.0/24`. The attack machine at `172.18.0.100` reaches the PLC on `172.18.0.3` and the OPC-UA server on `172.18.0.5` directly. In the terms of this case, there is no line between IT and OT at all.

The [Network Segmentation challenge](/ctf/challenge/defense_network_segmentation) asks you to block the attack machine from the critical services while the plant keeps running. That is the kind of boundary that lets an operator say "the attack is in IT, OT is safe, keep the pipeline running".

<div data-widget="purdue-explorer"></div>

The explorer places the CybICS hosts on the Purdue levels, the usual model for separating plant and business networks. For each host, ask: which hosts must it reach to do its job, and if it were encrypted tomorrow, would the plant have to stop?

<details class="deep-dive" markdown="1">
<summary>Deep dive: the CybICS host that plays the billing system</summary>

The OPC-UA server reads the tank pressures from the PLC and offers them to other systems, much like the data feeds a billing or planning system would rely on. Ask whether the plant itself would notice if it went away.

</details>

<div data-widget="checkpoint" data-id="shutdown"></div>

## Lessons for defenders

- **Find and close forgotten access.** Inventory every remote access path and account, remove what is unused, and require multi-factor authentication on the rest. See [Defence and hardening](/theory/defense-hardening).
- **Segment, and be able to prove it.** A boundary between IT and OT only helps if you can show, in the middle of an incident, that the attacker cannot cross it. See [Network segmentation](/theory/defense_network).
- **Map business dependencies.** List the IT systems operations cannot run without, such as billing, and plan how to work without them. See [Risk assessment](/theory/risk-assessment).
- **Decide in advance when to stop.** A precautionary shutdown is a valid choice, but it should be a planned one, with criteria and a restart plan. See [Incident response](/theory/incident-response).
- **Prepare for ransomware.** Offline backups and practised restores shorten an outage more than any payment does.
