# Detecting a scan

The scan you ran in reconnaissance is noisy: one host touching many ports in a short time.
A simple rule engine catches exactly that pattern. This module flips you from attacker to
defender.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Port scan detection window">
  <text x="20" y="24" font-size="11">one source, unique ports in a sliding window</text>
  <g>
    <rect x="20" y="40" width="360" height="30" rx="4" fill="currentColor" opacity="0.12" stroke="currentColor"/>
    <g fill="#ff6b00">
      <rect x="30" y="46" width="10" height="18"/><rect x="55" y="46" width="10" height="18"/>
      <rect x="80" y="46" width="10" height="18"/><rect x="110" y="46" width="10" height="18"/>
      <rect x="140" y="46" width="10" height="18"/><rect x="175" y="46" width="10" height="18"/>
      <rect x="210" y="46" width="10" height="18"/><rect x="250" y="46" width="10" height="18"/>
    </g>
    <text x="200" y="64" text-anchor="middle" font-size="9" fill="#1a1a1a"> </text>
  </g>
  <text x="400" y="60" font-size="11">&ge; threshold &rarr;</text>
  <rect x="400" y="70" width="110" height="28" rx="4" fill="#ff6b00" opacity="0.6"/>
  <text x="455" y="89" text-anchor="middle" font-size="10" fill="#1a1a1a">port_scan alert</text>
  <text x="20" y="112" font-size="10" opacity="0.7">Counting unique destination ports per source over a time window.</text>
</svg>
<figcaption>The port-scan rule counts how many distinct ports a single source probes in a window. Past the threshold, it alerts.</figcaption>
</figure>

## The skill

Run a scan, open the IDS dashboard, and find the `port_scan` alert. The rule revealing the
flag proves the detection fired.

> **MITRE D3FEND:** Network Traffic Analysis. Maps to the attacker's T0846 Discovery.
