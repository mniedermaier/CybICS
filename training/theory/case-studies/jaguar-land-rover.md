# Jaguar Land Rover (2025)

Jaguar Land Rover (JLR) is the UK's largest carmaker. At the end of August 2025 attackers broke into its Information Technology (IT) network, the office and business computers. JLR switched its systems off to contain them, and its factories in the UK and Slovakia stood still for about five weeks. This case is about what happens when a just-in-time factory loses its IT, even though its Operational Technology (OT), the machines on the factory floor, is not known to have been attacked, and how far the damage spreads beyond the company that was hit.

## What happened

The attack began around 31 August 2025. On 1 September JLR shut down its IT systems as a precaution, and production stopped at its UK plants in Solihull, Halewood and Wolverhampton and abroad, including Slovakia. Dealers' sales were disrupted, and suppliers could no longer deliver.

As suppliers ran out of money, the UK government guaranteed a £1.5 billion loan on 28 September to keep them afloat. The restart was pushed back several times; a phased restart began on 8 October, with the engine and battery plants first. An independent estimate made it the costliest cyber incident in UK history.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the full timeline and the cost estimates</summary>

<figure class="wide">
<svg viewBox="0 0 560 150" role="img" aria-label="Timeline of the Jaguar Land Rover incident. 31 August 2025: attack begins. 1 September: IT shut down, production stops. 10 September: JLR confirms some data was affected. 28 September: UK government guarantees a 1.5 billion pound loan. 8 October: phased restart begins with the engine and battery plants. 22 October: the Cyber Monitoring Centre estimates the UK cost at 1.9 billion pounds.">
  <line x1="20" y1="70" x2="540" y2="70" stroke="currentColor" stroke-width="2"/>
  <g fill="#ff6b00"><circle cx="40" cy="70" r="6"/><circle cx="135" cy="70" r="6"/><circle cx="230" cy="70" r="6"/><circle cx="325" cy="70" r="6"/><circle cx="420" cy="70" r="6"/><circle cx="515" cy="70" r="6"/></g>
  <g font-size="12" fill="currentColor" text-anchor="middle">
    <text x="40" y="50" font-weight="bold">31 Aug</text><text x="40" y="95">attack</text><text x="40" y="111">begins</text>
    <text x="135" y="50" font-weight="bold">1 Sep</text><text x="135" y="95">IT off,</text><text x="135" y="111">plants stop</text>
    <text x="230" y="50" font-weight="bold">10 Sep</text><text x="230" y="95">data</text><text x="230" y="111">affected</text>
    <text x="325" y="50" font-weight="bold">28 Sep</text><text x="325" y="95">£1.5bn loan</text><text x="325" y="111">guarantee</text>
    <text x="420" y="50" font-weight="bold">8 Oct</text><text x="420" y="95">phased</text><text x="420" y="111">restart</text>
    <text x="515" y="50" font-weight="bold">22 Oct</text><text x="515" y="95">£1.9bn UK</text><text x="515" y="111">estimate</text>
  </g>
</svg>
<figcaption>The plants stood still for about five weeks; getting back to normal output took several more.</figcaption>
</figure>

| Date | Event |
|---|---|
| 31 Aug 2025 | The attack begins, according to the BBC. |
| 1 to 2 Sep | JLR shuts down its systems "to mitigate" the attack. Production and retail are "severely disrupted". A group calling itself Scattered Lapsus$ Hunters claims the attack on Telegram. |
| 10 Sep | JLR says that "some data" has been affected, after first reporting no evidence of that. |
| 23 Sep | The production pause is extended to 1 October. Unions have been reporting since mid-September that supplier staff are being laid off. |
| 28 Sep | The UK government guarantees a commercial loan of up to £1.5 billion to protect JLR's supply chain. |
| 8 Oct | The phased restart begins at the Wolverhampton engine plant and the battery assembly centre in the West Midlands, with stamping, body and paint shops; Range Rover production in Solihull follows later that week. |
| 22 Oct | The Cyber Monitoring Centre (CMC), an independent body, rates the incident a Category 3 systemic event: about £1.9 billion of UK losses (range £1.6 to 2.1 billion) and more than 5,000 UK organisations affected. |
| Nov 2025 | JLR reports £196 million of direct "cyber related" costs for its July to September quarter. |
| Jun 2026 | The New York Times reports, citing people close to the investigation, that Russian hackers were behind the attack and that Microsoft had alerted JLR. The group that claimed it on Telegram is no longer seen as the main culprit. Whether a state directed it is not established. |
| Oct 2026 | The Telegraph reports that Al Carns, a former defence minister, said at a Chatham House event in July: "We know the Jaguar Land Rover attack was state-sponsored." He named no state and said this was not an official Ministry of Defence assessment. The government does not comment on the investigation. |

</details>

## How an IT attack stopped the factories

A car factory works **just in time**: parts arrive hours before they are fitted, not weeks. Thousands of parts from hundreds of suppliers are ordered, scheduled and tracked by IT systems. Planning, ordering and the systems that tell each station which car comes next all live there.

When JLR switched that IT off, the robots and conveyors were, as far as is known, not broken. But nobody could tell them what to build, and no parts were coming.

<div class="callout analogy" markdown="1">
**Analogy:** a restaurant kitchen with working stoves, but no order tickets and no deliveries. The cooks are there; they just have nothing to cook and no idea what was ordered.
</div>

The suppliers had built their whole business around JLR's schedule. With no orders and no payments, many had to send workers home within days. That is how one company's IT incident became a UK-wide economic event.

| Effect | ATT&CK for ICS |
|---|---|
| Five weeks without production | T0828 Loss of Productivity and Revenue |
| Plants unable to run while IT was off | T0826 Loss of Availability |

<details class="deep-dive" markdown="1">
<summary>Deep dive: what is not known about the attack itself</summary>

The technical chain is largely not public. Press reports said the attackers phoned staff and pretended to be colleagues to get passwords ("vishing", voice phishing); JLR's chief information security officer at the time said no social engineering was involved. The New York Times reported that the attackers used new ransomware but, according to Al Carns, a former armed forces minister it quoted, never demanded a ransom; several experts read that as sabotage rather than extortion. Treat all of this as unconfirmed: a claim on Telegram, anonymous sources and a former minister's remark are not an official attribution, and no government has published one.

That is a lesson in itself: in the first weeks of an incident you usually do not know who is behind it or how they got in, and you have to decide what to switch off anyway.

</details>

Now put the cascade in order, from the break-in to the restart.

<div data-widget="sequence" data-id="cascade"></div>

## Why it hurt so much

**IT was part of production.** Like Colonial Pipeline, JLR stopped operations by switching off IT; there is no public evidence that the attackers reached the machines. The difference is that a car plant cannot run at all without its scheduling and ordering systems, so systems that look like IT were really part of production.

**One company, a whole supply chain.** Most of the CMC's estimated loss came from lost output at JLR and its suppliers, not from JLR's own repair costs. Small suppliers with thin margins had no reserves for weeks without orders.

**Restarting is a project of its own.** Systems had to be checked and restored before they could be trusted again, and the plants restarted in order: engines and batteries first, because the vehicle lines depend on them.

<div data-widget="checkpoint" data-id="stopped"></div>

## What it means for CybICS

In the virtual CybICS testbed, two containers run the plant: the Programmable Logic Controller (PLC) decides, and the hwio container plays the sensors and actuators of the gas plant. Together they keep the pressures in range without any other host; on the board, the STM32 microcontroller plays the plant instead. Operators see and steer it through the FUXA Human-Machine Interface (HMI), and the OPC-UA server passes the values on to other systems.

Ask the JLR question about each host: if you had to switch it off tomorrow to contain an attacker, would the plant keep running, and would anyone still know what it was doing?

<div data-widget="purdue-explorer"></div>

The [Network Segmentation challenge](/ctf/challenge/defense_network_segmentation) asks you to build the boundary that lets you contain an attacker without stopping the plant. The [Incident PCAP challenge](/ctf/challenge/incident_pcap) puts you in the position of the responder who has to work out what happened from the evidence.

## Lessons for defenders

- **Know which IT systems production needs.** Map them before an incident, and plan how to run, even slowly, without them. See [Risk assessment](/theory/risk-assessment).
- **Segment so you can contain without stopping.** If you can isolate the business network and prove the plant is not affected, you have a choice besides switching everything off. See [Network segmentation](/theory/defense_network).
- **Plan the restart, not just the shutdown.** Clean backups, a tested restore order and the critical-first sequence decide how long the outage lasts. See [Incident response](/theory/incident-response).
- **Think beyond your own walls.** Suppliers depend on your systems, and you depend on theirs. Include them in exercises and in your continuity plans.

Which defence fits each moment of the incident?

<div data-widget="sequence" data-id="defend"></div>
