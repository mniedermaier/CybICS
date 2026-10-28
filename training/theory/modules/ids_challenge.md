# Intrusion detection

In this challenge you look at the CybICS intrusion detection system (IDS) as a whole. You run several different attacks you already know, watch which of them the IDS recognises, and collect the flag once it has seen enough. Along the way you build a map of which attack leaves which trace, which is exactly what a defender needs to know.

## The idea

An **intrusion detection system** is the security camera of a network. It does not lock any doors. It watches the traffic, compares it with a set of **rules**, and raises an **alert** when something matches. Each rule describes one kind of suspicious behaviour, such as "one host trying many ports" or "an unknown host writing to the PLC".

A single rule only covers a single behaviour. Real attacks have several stages: first discovery, then access, then manipulation. A useful IDS therefore has rules for each stage, so that an attacker who slips past one is caught by the next. This idea is called **defence in depth**.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="A bar chart of alerts accumulating over time in the IDS buffer. When the bars pass a dashed threshold line, the IDS reports an intrusion and the flag is unlocked.">
  <g fill="#ff6b00" opacity="0.8">
    <rect x="30" y="70" width="24" height="20"/><rect x="64" y="60" width="24" height="30"/>
    <rect x="98" y="52" width="24" height="38"/><rect x="132" y="40" width="24" height="50"/>
  </g>
  <line x1="20" y1="50" x2="300" y2="50" stroke="currentColor" stroke-dasharray="5 4" opacity="0.5"/>
  <text x="304" y="53" font-size="11">alert threshold</text>
  <text x="20" y="108" font-size="11" opacity="0.7">alerts accumulating in the buffer</text>
  <rect x="360" y="45" width="150" height="30" rx="4" fill="#ff6b00" opacity="0.6"/>
  <text x="435" y="64" text-anchor="middle" font-size="11" fill="#1a1a1a">flag unlocked</text>
</svg>
<figcaption>Once enough alerts have accumulated, the IDS confirms an intrusion and releases the flag.</figcaption>
</figure>

## How it looks on CybICS

The IDS runs on the CybICS host and listens to all traffic on the plant network `172.18.0.0/24`. Its dashboard is on port **8443**. It has twelve rules:

| Rule | What sets it off | Severity |
|---|---|---|
| `port_scan` | one source tries 5 or more ports on one target within 10 s | medium |
| `syn_flood` | 100 or more connection attempts (SYN) from one source within 10 s | high |
| `modbus_flood` | 50 or more Modbus writes in 5 s from a host that is not a known writer | critical |
| `modbus_unauth_write` | 10 or more Modbus writes in 30 s from a host other than hwio or FUXA | high |
| `modbus_diagnostic` | Modbus function code 8 or 43 | medium |
| `s7_enumeration` | any S7comm traffic to port 102 or 1102 | medium |
| `http_brute_force` | 5 or more POSTs in 30 s to port 8080 or 1881 that mention `login` or `auth` (OpenPLC's login does, FUXA's `/api/signin` does not) | high |
| `arp_spoof` | one IP address seen with two different MAC addresses | critical |
| `opcua_access` | OPC-UA traffic to port 4840 from a host that is not a plant service | low |
| `s7_write` | an S7comm write request to port 102 or 1102; the alert names the address and value written | high |
| `dnp3_operate` | a DNP3 control request (operate, select or write) to port 20000 with correct CRCs; the alert names the points and values | high |
| `s7_cpu_control` | an S7comm request that changes the CPU's operating mode: PLC STOP or a warm or cold restart | critical (STOP), high (restart) |

Every alert records the rule, the source and target, a severity and a MITRE ATT&CK for ICS technique. The dashboard shows them live; the API at `/api/alerts`, `/api/summary` and `/api/rules/stats` returns the same data for scripts.

<div class="callout cybics" markdown="1">
**On CybICS:** the IDS raises at most one alert per rule and source every 30 seconds (for `s7_write` and `s7_cpu_control`, only an exact repeat of the previous request is folded). Repeating the same scan ten times in a row therefore gives you one alert, not ten. Different attacks are the faster way to more alerts.
</div>

<div data-widget="checkpoint" data-id="cooldown"></div>

Click a host in the network map below to see which IDS rules watch it.

<div data-widget="purdue-explorer"></div>

## How to approach it

1. **Open the dashboard** and make sure the IDS is running. Keep it visible while you work.
2. **Pick three attacks from different stages.** The challenge asks you to set off at least three different rules. Good candidates are a port scan, a handful of Modbus writes from the attack machine, and an S7comm or OPC-UA connection. You have done all of them in earlier modules.
3. **Run them one at a time** and watch which alert each one produces. Write down the rule name, severity and source.
4. **Note what stays silent.** Did any attack raise nothing? Why not, judging by the table above?
5. **Ask the IDS for the flag** at its `/api/flag` endpoint. It tells you how many alerts it has counted so far if you are not there yet.

## Detect and defend

The value of this exercise is the map you just built: attack on one side, the alert it causes on the other. Real security teams keep the same map, often against the MITRE ATT&CK matrix, to see where they are blind.

- **Coverage.** Every stage of an attack should have at least one rule. Gaps are where an attacker will go.
- **Tuning.** Thresholds trade missed attacks against false alarms. The [IDS evasion](/theory/ids_evasion) module shows how an attacker uses that trade-off.
- **Triage.** Severity helps an analyst look at the critical alerts first; the [IDS forensics](/theory/ids_forensics) module practises reading the alert stream like an investigator.
- **Response.** An IDS only detects. Alerts must reach a person or a system that can act, for example by blocking a host at the firewall.

The CybICS IDS is a **signature- and threshold-based** IDS: it recognises behaviour that someone described in advance. That makes it predictable and easy to explain, but it cannot see an attack nobody wrote a rule for.

<details class="deep-dive" markdown="1">
<summary>Deep dive: signature, threshold and anomaly detection</summary>

A **signature** rule matches a specific pattern, such as "function code 8". It has almost no false alarms but only catches what it describes. A **threshold** rule counts events and compares them with a limit, such as "50 writes in 5 seconds". An **anomaly** detector first learns what normal traffic looks like and then flags anything that deviates, which can catch new attacks but needs careful training to avoid false alarms.

Industrial networks suit all three well, because their normal traffic is so regular. Commercial OT monitoring products usually combine them with an inventory of every device and every connection it has ever seen.

</details>

## Before you start

- [Detection and monitoring](/theory/detection-monitoring): how an IDS works.
- [Detecting a scan](/theory/detect_basic): your first IDS alert, step by step.
- [The ICS attack lifecycle](/theory/attack-lifecycle): the stages the rules cover.
