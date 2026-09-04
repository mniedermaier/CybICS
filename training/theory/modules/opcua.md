# Attacking OPC-UA

OPC-UA can be secure, but weak configurations undo it: an anonymous or weakly authenticated
session may read and write nodes it should not. The challenge is to authenticate well enough
to reach an admin-tier value.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="OPC-UA node access by tier">
  <rect x="20" y="30" width="110" height="44" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="75" y="57" text-anchor="middle" font-size="11" fill="#1a1a1a">client</text>
  <defs><marker id="ou" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <line x1="130" y1="45" x2="360" y2="45" stroke="#ff6b00" stroke-width="2" marker-end="url(#ou)"/>
  <text x="245" y="39" text-anchor="middle" font-size="10">session as user / admin</text>
  <g font-size="10" text-anchor="middle">
    <rect x="362" y="24" width="140" height="26" rx="4" fill="currentColor" opacity="0.2" stroke="currentColor"/>
    <text x="432" y="41">userFLAG (user tier)</text>
    <rect x="362" y="58" width="140" height="26" rx="4" fill="#ff6b00" opacity="0.5"/>
    <text x="432" y="75" fill="#1a1a1a">adminFLAG (admin tier)</text>
  </g>
  <text x="20" y="108" font-size="10" opacity="0.7">The tier you reach depends on how you authenticate.</text>
</svg>
<figcaption>Different nodes require different privilege. Reaching the admin value shows why the identity model, not the protocol, is what protects OPC-UA.</figcaption>
</figure>

## The skill

Connect with an OPC-UA client, browse the address space, and authenticate to write the value
that unlocks the admin flag. Contrast this with Modbus: here there *is* a security model to
get past.

> **MITRE ATT&CK for ICS:** T0855 Unauthorized Command Message. Background: the OPC-UA
> foundation topic.
