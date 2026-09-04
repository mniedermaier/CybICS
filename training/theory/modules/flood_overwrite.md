# Flood and overwrite

Because Modbus accepts any write, an attacker can hammer a register faster than the process
logic can correct it, pinning a value or driving the plant into an unsafe state. This is a
denial-of-control against the process itself.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Write flood">
  <defs><marker id="fo" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="40" width="90" height="40" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="65" y="64" text-anchor="middle" font-size="11" fill="#1a1a1a">attacker</text>
  <g stroke="#ff6b00" stroke-width="1.5">
    <line x1="110" y1="46" x2="392" y2="46" marker-end="url(#fo)"/>
    <line x1="110" y1="54" x2="392" y2="54" marker-end="url(#fo)"/>
    <line x1="110" y1="62" x2="392" y2="62" marker-end="url(#fo)"/>
    <line x1="110" y1="70" x2="392" y2="70" marker-end="url(#fo)"/>
  </g>
  <text x="250" y="38" text-anchor="middle" font-size="10">hundreds of writes/second to HPT</text>
  <rect x="394" y="40" width="100" height="40" rx="6" fill="#ff6b00" opacity="0.6"/>
  <text x="444" y="64" text-anchor="middle" font-size="11" fill="#1a1a1a">PLC / HPT</text>
  <text x="20" y="110" font-size="10" opacity="0.7">The flood outruns the control loop, so the register no longer reflects reality.</text>
</svg>
<figcaption>A write flood overwhelms the register faster than the scan cycle can restore it, an impairment of process control.</figcaption>
</figure>

## The skill

Run rapid Modbus writes at the HPT register and watch the process react. In CybICS the flood
is confirmed by the IDS `modbus_flood` signature, which reveals the flag once the attack is
observed on the wire.

> **MITRE ATT&CK for ICS:** T0836 Modify Parameter, T0814 Denial of Service. Detection: the
> *detect a flood* module.
