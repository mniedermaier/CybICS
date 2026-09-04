# IDS forensics

Detection produces an alert buffer; forensics reads it to answer **who, what, and when**.
An analyst reconstructs the incident from the recorded alerts rather than the live process.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Alert record fields">
  <rect x="20" y="30" width="480" height="60" rx="6" fill="currentColor" opacity="0.12" stroke="currentColor"/>
  <g font-size="10" text-anchor="middle">
    <text x="90" y="52" font-weight="bold" fill="#ff6b00">timestamp</text><text x="90" y="70">when</text>
    <text x="210" y="52" font-weight="bold" fill="#ff6b00">source IP</text><text x="210" y="70">who</text>
    <text x="330" y="52" font-weight="bold" fill="#ff6b00">rule</text><text x="330" y="70">what</text>
    <text x="450" y="52" font-weight="bold" fill="#ff6b00">target</text><text x="450" y="70">where</text>
  </g>
</svg>
<figcaption>Each alert records the facts an investigator needs. Reading them answers the forensic questions without touching the process.</figcaption>
</figure>

## The skill

Query the IDS for its alert history and answer questions computed from the buffer: which host
was most active, which rule fired most, when it started. Correct answers unlock the
forensics flag.

> **MITRE D3FEND:** Network Traffic Analysis and incident reconstruction. This is the
> analyst's counterpart to the attacker's noise.
