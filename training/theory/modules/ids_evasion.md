# IDS evasion

A rate-based rule only fires above a threshold. An attacker who stays **under** the rate, or
spreads activity out, can act while raising no alert. Evasion teaches the limits of simple
detection.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Low and slow under the threshold">
  <line x1="20" y1="45" x2="420" y2="45" stroke="currentColor" stroke-dasharray="5 4" opacity="0.5"/>
  <text x="424" y="48" font-size="10">threshold</text>
  <g fill="#ff6b00" opacity="0.8">
    <rect x="40" y="70" width="12" height="16"/><rect x="120" y="72" width="12" height="14"/>
    <rect x="210" y="70" width="12" height="16"/><rect x="300" y="73" width="12" height="13"/>
    <rect x="380" y="71" width="12" height="15"/>
  </g>
  <text x="20" y="108" font-size="10" opacity="0.7">a few writes, well spaced &mdash; each window stays below the line</text>
</svg>
<figcaption>Low-and-slow activity keeps every window under the threshold, so the rule never fires even though the attack succeeds.</figcaption>
</figure>

## The skill

Perform Modbus writes slowly enough that the flood rule never triggers, yet the writes take
effect. CybICS checks that writes occurred with no new alerts to award the evasion flag.

> **MITRE ATT&CK for ICS:** T0851 and evasion of monitoring. Defence: combine rate rules
> with anomaly and allow-list detection so "quiet" is not the same as "safe".
