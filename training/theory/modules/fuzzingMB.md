# Modbus fuzzing

Fuzzing sends malformed and non-standard messages to see whether a device mishandles them:
crashes, hangs, or misbehaves. It tests robustness &mdash; and fragile field devices often
fail badly on input their firmware never expected.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Fuzzing malformed frames">
  <defs><marker id="fz" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="38" width="90" height="44" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="65" y="64" text-anchor="middle" font-size="11" fill="#1a1a1a">fuzzer</text>
  <g font-size="9" text-anchor="middle" fill="currentColor">
    <line x1="110" y1="48" x2="380" y2="48" stroke="#ff6b00" stroke-width="1.4" marker-end="url(#fz)"/>
    <line x1="110" y1="60" x2="380" y2="60" stroke="#ff6b00" stroke-width="1.4" marker-end="url(#fz)"/>
    <line x1="110" y1="72" x2="380" y2="72" stroke="#ff6b00" stroke-width="1.4" marker-end="url(#fz)"/>
    <text x="245" y="40">FC 8 diagnostics, FC 67/68 non-standard, bad lengths</text>
  </g>
  <rect x="382" y="38" width="118" height="44" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="441" y="64" text-anchor="middle" font-size="11">Modbus server</text>
</svg>
<figcaption>A fuzzer sweeps function codes and field values, including odd and diagnostic codes, watching for a device that copes badly.</figcaption>
</figure>

## The skill

Run a Modbus fuzzer against port 502, including the diagnostic function codes. In CybICS the
run is confirmed by the IDS `modbus_diagnostic` signature, which reveals the flag.

> **MITRE ATT&CK for ICS:** exploitation via malformed protocol input. Robust field devices
> and protocol-aware monitoring are the defence.
