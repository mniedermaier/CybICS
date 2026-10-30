# Tuning the IDS

In this challenge you make sure the Intrusion Detection System (IDS) is actually doing its job: running, listening to the network, and raising alerts for real attacks. An IDS that is switched off, or watching the wrong network, gives a false sense of safety that is worse than knowing you have none.

## The idea

A smoke detector on the ceiling only protects you if it has a battery, hangs in the right room, and goes off when there is smoke. Each of those can fail on its own, and the detector still looks fine from below. That is why you press its test button.

An IDS has the same three links in its chain:

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Three stages in a row. Running: the service answers its health check. Capturing: packet capture is active. Detecting: at least three different rules have produced alerts. Only when all three hold is detection proven end to end.">
  <defs><marker id="dids" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="currentColor"/></marker></defs>
  <g fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-width="2">
    <rect x="15" y="30" width="140" height="56" rx="6"/>
    <rect x="190" y="30" width="140" height="56" rx="6"/>
    <rect x="365" y="30" width="140" height="56" rx="6"/>
  </g>
  <g fill="#ff6b00"><rect x="15" y="30" width="6" height="56"/><rect x="190" y="30" width="6" height="56"/><rect x="365" y="30" width="6" height="56"/></g>
  <g font-size="13" text-anchor="middle" fill="currentColor">
    <text x="88" y="54" font-weight="bold">1. running</text><text x="88" y="73" opacity="0.85">/health answers</text>
    <text x="263" y="54" font-weight="bold">2. capturing</text><text x="263" y="73" opacity="0.85">status: active</text>
    <text x="438" y="54" font-weight="bold">3. detecting</text><text x="438" y="73" opacity="0.85">3 or more rules hit</text>
  </g>
  <g stroke="currentColor" stroke-width="2"><line x1="155" y1="58" x2="186" y2="58" marker-end="url(#dids)"/><line x1="330" y1="58" x2="361" y2="58" marker-end="url(#dids)"/></g>
  <text x="260" y="110" font-size="13" text-anchor="middle" fill="currentColor" opacity="0.85">all three must hold: a break anywhere means no detection</text>
</svg>
<figcaption>A healthy IDS: the service is up, it is capturing traffic, and several different rules have fired, which proves the whole pipeline from packet to alert.</figcaption>
</figure>

## How it looks on CybICS

The CybICS IDS runs with host networking, so it can listen to the Docker bridge that carries all lab traffic in `172.18.0.0/24`. Its dashboard and API are on port 8443 of the CybICS host. It normally starts capturing on boot, but it can be stopped and started:

| Endpoint | Shows or does |
|---|---|
| `/health` | answers when the service is up |
| `/api/status` | `active: true` while packets are being captured |
| `/api/start`, `/api/stop` | start or stop capturing |
| `/api/rules/stats` | how many alerts each rule has produced |

There are twelve rules. Each one watches for a different kind of activity: port scans, connection floods, Modbus write floods, unauthorised Modbus writes, Modbus diagnostic requests, S7comm access, S7comm writes, S7comm CPU mode changes, DNP3 control commands, login brute force, ARP spoofing and OPC-UA access from unknown hosts. The Rules tab shows each rule's threshold and window.

The **Verify Defense** check tests the three links from the figure in order. The rule counts come from the alert buffer, so emptying the buffer also resets them.

## How to approach it

1. **Check the first two links.** Open the dashboard or call `/health` and `/api/status`. If capture is not active, start it.
2. **Start before you attack.** The IDS only sees traffic while it captures. Attacks run earlier leave no trace.
3. **Pick three different behaviours.** Choose three attacks you learned in earlier modules that map to three different rules. Repeating the same attack does not add new rules.
4. **Watch the alerts arrive** on the dashboard, then verify.

Then think about tuning. Every threshold is a trade-off between missing attacks and drowning in false alarms. Try it here: the stream mixes legitimate writes from the engineering workstation, which is not an expected writer, with an attacker's.

<div data-widget="ids-threshold"></div>

<div data-widget="checkpoint" data-id="tradeoff"></div>

## Detect and defend

Keeping detection healthy is itself a defense, and it needs routine:

- **Monitor the monitor.** Alert when the IDS stops capturing or stops producing any events, not only when it sees an attack.
- **Test regularly.** A short, known test (a small scan from an authorised host) proves the pipeline end to end, like the smoke detector's test button.
- **Tune with care.** Lower thresholds catch slower attacks but raise false alarms. Exemptions, such as the trust CybICS gives `hwio` and `fuxa` for Modbus writes, remove noise but create a blind spot if that host is ever taken over. The [IDS evasion](/theory/ids_evasion) module shows what slips under a threshold.
- **Someone must read it.** Alerts nobody reviews protect nothing.

NIST SP 800-82 calls this System Monitoring (SI-4). D3FEND lists Network Traffic Analysis (D3-NTA).

## Before you start

- [Detection and monitoring](/theory/detection-monitoring): how an IDS works and what false positives are
- [Intrusion detection](/theory/ids_challenge): the CybICS IDS and its rules in detail
- [Network scanning](/theory/scanning) and [Flood & Overwrite](/theory/flood_overwrite): attacks the rules recognise
