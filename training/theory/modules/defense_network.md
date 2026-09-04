# Network segmentation

Segmentation is firewalling raised to the network level: the attacker's zone is cut off from
the control zone across every service, not just one port. In CybICS you block the attack
host from both the PLC and the OPC-UA server.

<figure>
<svg viewBox="0 0 520 150" role="img" aria-label="Segmenting attacker from control zone">
  <rect x="20" y="30" width="150" height="90" rx="8" fill="currentColor" opacity="0.1" stroke="currentColor"/>
  <text x="95" y="24" text-anchor="middle" font-size="10">attacker zone</text>
  <rect x="45" y="60" width="100" height="34" rx="6" fill="#ff6b00" opacity="0.3"/><text x="95" y="82" text-anchor="middle" font-size="10">attack box</text>
  <rect x="350" y="30" width="150" height="90" rx="8" fill="#ff6b00" opacity="0.1" stroke="#ff6b00"/>
  <text x="425" y="24" text-anchor="middle" font-size="10">control zone</text>
  <rect x="370" y="48" width="110" height="28" rx="5" fill="#ff6b00" opacity="0.6"/><text x="425" y="67" text-anchor="middle" font-size="10" fill="#1a1a1a">PLC</text>
  <rect x="370" y="82" width="110" height="28" rx="5" fill="#ff6b00" opacity="0.5"/><text x="425" y="101" text-anchor="middle" font-size="10" fill="#1a1a1a">OPC-UA</text>
  <line x1="170" y1="75" x2="350" y2="75" stroke="currentColor" stroke-width="2"/>
  <line x1="250" y1="55" x2="270" y2="95" stroke="#ff6b00" stroke-width="3"/>
  <text x="260" y="120" text-anchor="middle" font-size="10" opacity="0.8">no path from the attacker to the controllers</text>
</svg>
<figcaption>Segmentation removes the attacker's route to the whole control zone, the boundary the Purdue model and IEC 62443 call for.</figcaption>
</figure>

## The skill

Apply DROP rules on both the OpenPLC and OPC-UA containers for the attack host, then verify.
This builds the zone boundary between the attacker and the controllers.

> **IEC 62443** zones and conduits (SR 5.1); **NIST SP 800-82 / 800-53** SC-7.
