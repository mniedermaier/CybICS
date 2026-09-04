# S7comm enumeration

Beyond open ports, an attacker wants device identity: make, model, firmware. S7comm exposes
this through its System Status List (SZL) with no authentication, letting a scanner
fingerprint a Siemens-style PLC before touching the process.

<figure>
<svg viewBox="0 0 520 110" role="img" aria-label="S7 identity enumeration">
  <defs><marker id="se" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="34" width="100" height="44" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="70" y="60" text-anchor="middle" font-size="11" fill="#1a1a1a">enumerator</text>
  <line x1="120" y1="48" x2="390" y2="48" stroke="#ff6b00" stroke-width="2" marker-end="url(#se)"/>
  <text x="255" y="42" text-anchor="middle" font-size="10">Read SZL (module id)</text>
  <line x1="390" y1="66" x2="122" y2="66" stroke="currentColor" stroke-width="2" opacity="0.6" marker-end="url(#se)"/>
  <text x="255" y="84" text-anchor="middle" font-size="10" opacity="0.85">Module type, serial, firmware</text>
  <rect x="392" y="34" width="108" height="44" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="446" y="55" text-anchor="middle" font-size="11">S7 server :102</text>
</svg>
<figcaption>An SZL read returns identity records. The CybICS S7 server hides the scanning flag in the module-type field.</figcaption>
</figure>

## The skill

Point an S7 enumeration tool (or nmap S7 script) at port 102 and read the identity records.
The device fingerprint tells an attacker what exploits and defaults might apply.

> **MITRE ATT&CK for ICS:** T0846 Remote System Discovery. Background: see the S7comm
> foundation topic.
