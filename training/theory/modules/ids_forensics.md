# IDS forensics

In this challenge you play the analyst who arrives after the attack. You do not watch packets live; you read what the Intrusion Detection System (IDS) wrote down and answer three questions about the incident. This is the everyday work of a Security Operations Centre (SOC): turning a pile of alerts into a short, correct story of who did what, and when.

## The idea

Think of a building's visitor log. You were not at the front desk yesterday, but the log tells you who signed in, at what time, and which room they asked for. Reconstructing an incident from such a record, instead of from memory or from the live building, is what forensics means.

An IDS keeps the same kind of log. Every time one of its rules matches, it writes an **alert**: a small record with a fixed set of fields. Each field answers one of the questions an investigator always asks.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="An alert record with four fields: timestamp answers when, source IP answers who, rule answers what, and target answers where.">
  <rect x="20" y="30" width="480" height="60" rx="6" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.6"/>
  <g stroke="#ff6b00" stroke-width="2"><line x1="150" y1="38" x2="150" y2="82"/><line x1="270" y1="38" x2="270" y2="82"/><line x1="390" y1="38" x2="390" y2="82"/></g>
  <g font-size="13" text-anchor="middle" fill="currentColor">
    <text x="90" y="54" font-weight="bold">timestamp</text><text x="90" y="74" opacity="0.8">when</text>
    <text x="210" y="54" font-weight="bold">source IP</text><text x="210" y="74" opacity="0.8">who</text>
    <text x="330" y="54" font-weight="bold">rule</text><text x="330" y="74" opacity="0.8">what</text>
    <text x="445" y="54" font-weight="bold">target</text><text x="445" y="74" opacity="0.8">where</text>
  </g>
</svg>
<figcaption>Each alert records the facts an investigator needs. Reading many of them together answers the forensic questions without touching the process.</figcaption>
</figure>

One alert is a clue. Many alerts become a pattern: one address that appears again and again, a burst of the same rule, a jump in severity. Your job is to count and group them carefully.

## How it looks on CybICS

The CybICS IDS listens to all traffic on the lab network `172.18.0.0/24` and offers a dashboard and a small web API on port 8443 of the CybICS host. The API speaks JSON, a plain text format for structured data that both people and scripts can read.

| Endpoint | What it gives you |
|---|---|
| `/api/alerts` | Every stored alert with `id`, `timestamp`, `severity`, `rule`, `src`, `dst`, `message` and `mitre` |
| `/api/summary` | Totals already grouped by severity, by rule and by source address |
| `/api/forensics` | Whether there is enough evidence yet, and the three questions |
| `/api/forensics/submit` | Where you send your answers |

The investigation opens once the buffer holds at least five alerts from at least three different rules. If it does not, run a few of the attacks from earlier modules first, such as a port scan or a burst of Modbus writes.

Severity is one of `low`, `medium`, `high` or `critical`. Each rule always uses the same severity, which you can look up on the dashboard's Rules tab.

<div data-widget="checkpoint" data-id="field"></div>

Before you query the real IDS, practise on a made-up morning of alerts. The questions are different from the challenge's, but the moves are the same: filter, count, and read the fields carefully.

<div data-widget="alert-log"></div>

## How to approach it

1. **Check readiness.** Ask `/api/forensics` whether the evidence threshold is met.
2. **Freeze the scene.** The answers are computed from the alert buffer at the moment you submit. Stop running attacks while you investigate, or your counts will drift.
3. **Start with the summary.** `/api/summary` has already grouped the alerts for you. Read it with `curl` and `python3 -m json.tool`, or with a few lines of Python using `requests`.
4. **Cross-check with the raw alerts.** Open `/api/alerts` and confirm that the grouped numbers match what you see in the individual records.
5. **Submit** a JSON body with your three answers. A wrong answer tells you which field was wrong, so you can look again.

<div class="callout tip" markdown="1">
**Tip:** An analyst writes down how each answer was found, not only the answer. If a colleague cannot repeat your count from the same data, the count is not evidence yet.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: why an alert count is not a packet count</summary>

The CybICS rule engine raises at most one alert per rule and source address every 30 seconds. A flood of thousands of packets can therefore appear as a handful of alerts. The buffer also keeps only the most recent 500 alerts, and anyone can empty it through `/api/alerts/clear`.

The `src` field also deserves a second look. For most rules it is the sender of the packet, but for `arp_spoof` it is the IP address that was claimed in the ARP message, which may be the victim rather than the attacker. The "top source" of alerts is a lead, not a verdict.

</details>

## Detect and defend

Forensics is the defender's side of every attack module. It only works if the evidence survives, so real sites take care of three things:

- **Retention.** Alerts are copied off the sensor to central storage, such as a Security Information and Event Management (SIEM) system, before a small in-memory buffer overwrites them.
- **Integrity.** Only the analysts can delete alerts. An attacker who can clear the log can erase their own trail.
- **Time.** All devices share a synchronised clock, so a timeline built from several sources lines up.

In the MITRE D3FEND catalogue of defensive techniques this work falls under Network Traffic Analysis (D3-NTA). The alerts you analyse here point to ATT&CK for ICS techniques such as Remote System Discovery (T0846) and Unauthorized Message: Command Message (T1692.001).

## Before you start

- [Detection and monitoring](/theory/detection-monitoring): what an IDS is and how its rules work
- [Intrusion detection](/theory/ids_challenge): the CybICS IDS and its nine rules

Later on the path:

- [Incident response in OT](/theory/incident-response): what happens with your findings next
