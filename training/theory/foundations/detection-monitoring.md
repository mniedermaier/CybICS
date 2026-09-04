# Detection and monitoring

Because ICS protocols do not authenticate, defenders cannot ask "is this client allowed?".
Instead they **watch the network** and reason about behaviour. An **Intrusion Detection
System (IDS)** observes traffic passively and raises alerts when it sees patterns that
should not occur. CybICS ships a lightweight rule-based IDS.

## Passive monitoring

The IDS sits on a mirror/span of the control network. It never injects packets, so it
cannot disturb the process &mdash; a hard requirement in OT, where availability is
paramount.

<figure>
<svg viewBox="0 0 520 170" role="img" aria-label="Passive IDS on a network tap">
  <g font-size="11" text-anchor="middle">
    <rect x="30" y="30" width="90" height="40" rx="6" fill="#ff6b00" opacity="0.7"/>
    <text x="75" y="54" fill="#1a1a1a">HMI</text>
    <rect x="400" y="30" width="90" height="40" rx="6" fill="#ff6b00" opacity="0.55"/>
    <text x="445" y="54" fill="#1a1a1a">PLC</text>
    <line x1="120" y1="50" x2="400" y2="50" stroke="currentColor" stroke-width="2"/>
    <text x="260" y="42" font-size="10">Modbus / S7 / OPC-UA traffic</text>
    <!-- tap -->
    <line x1="260" y1="50" x2="260" y2="110" stroke="#ff6b00" stroke-dasharray="5 3"/>
    <rect x="205" y="110" width="110" height="42" rx="6" fill="currentColor" opacity="0.2" stroke="#ff6b00"/>
    <text x="260" y="130">IDS (passive)</text>
    <text x="260" y="145" font-size="9">read-only copy</text>
  </g>
  <text x="30" y="168" font-size="10" opacity="0.7">The IDS receives a copy of the traffic and never writes to the wire.</text>
</svg>
<figcaption>A passive IDS reads a copy of the traffic. It can alert but cannot block, matching OT's availability-first priorities.</figcaption>
</figure>

## What the rules look for

The CybICS rule engine keeps small sliding-window counters per source and fires named
rules. Each maps to a MITRE technique:

| Rule | Fires on | ATT&CK for ICS |
|---|---|---|
| `port_scan` | many ports probed from one host | T0846 Discovery |
| `modbus_flood` | burst of Modbus writes | T0814 Denial of Service |
| `modbus_unauth_write` | writes from an unexpected host | T0855 Unauthorized Command |
| `modbus_diagnostic` | diagnostic / odd function codes | fuzzing, misuse |
| `s7_enumeration` | S7comm access | T0846 Discovery |
| `arp_spoof` | one IP with two MACs | T0830 Adversary-in-the-Middle |
| `opcua_access` | OPC-UA from a non-client host | unexpected access |

## Detection is not prevention

An alert is only useful if someone acts on it. Defense maps detections to responses. MITRE
**D3FEND** catalogues the countermeasures: network traffic analysis, protocol-metadata
anomaly detection, and so on. The detection challenges have you *cause* an attack and then
*find* it in the alert stream; the tuning challenge keeps the IDS effective.

> **Rule of thumb:** a good ICS detection is specific (few false alarms on normal plant
> traffic) and tied to a real technique, so an analyst knows what it means and what to do.
