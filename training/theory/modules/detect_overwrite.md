# Detecting a flood

A Modbus write flood is even louder than a scan. The IDS counts write function codes per
source in a short window and alerts when the rate crosses a threshold.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Flood detection rate">
  <polyline points="20,90 60,88 100,85 140,84 180,50 220,30 260,25 300,24" fill="none" stroke="#ff6b00" stroke-width="2"/>
  <line x1="20" y1="45" x2="320" y2="45" stroke="currentColor" stroke-dasharray="5 4" opacity="0.5"/>
  <text x="324" y="48" font-size="10">threshold</text>
  <text x="20" y="110" font-size="10" opacity="0.7">writes per second from one host over time</text>
  <rect x="360" y="30" width="150" height="30" rx="4" fill="#ff6b00" opacity="0.6"/>
  <text x="435" y="49" text-anchor="middle" font-size="10" fill="#1a1a1a">modbus_flood alert</text>
</svg>
<figcaption>When the write rate from a single host spikes past the threshold, the flood rule fires.</figcaption>
</figure>

## The skill

Launch the flood, then read the IDS alert stream for the `modbus_flood` detection that
carries the flag. Note the rule inspects *write* function codes, so a read flood raises
nothing &mdash; detections are specific by design.

> **MITRE D3FEND:** Protocol Metadata Anomaly Detection. Maps to T0814 / T0836.
