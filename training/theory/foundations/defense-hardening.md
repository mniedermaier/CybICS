# Defense in depth

No single control secures an ICS. The strategy is **defense in depth**: layered controls so
that getting past one still leaves an attacker facing the next. Two standards frame this for
OT: **IEC 62443** and **NIST SP 800-82**.

## Zones and conduits

IEC 62443 groups assets into **zones** with similar security needs and controls the
**conduits** (the connections) between them. The attack machine belongs in a different zone
from the PLC, and the conduit between them should be tightly restricted.

<figure>
<svg viewBox="0 0 520 210" role="img" aria-label="Zones and conduits">
  <g font-size="11" text-anchor="middle">
    <rect x="20" y="30" width="150" height="150" rx="8" fill="currentColor" opacity="0.10" stroke="currentColor"/>
    <text x="95" y="24" font-size="11">IT / attacker zone</text>
    <rect x="45" y="70" width="100" height="40" rx="6" fill="#ff6b00" opacity="0.35"/>
    <text x="95" y="94">Attack box</text>

    <rect x="350" y="30" width="150" height="150" rx="8" fill="#ff6b00" opacity="0.10" stroke="#ff6b00"/>
    <text x="425" y="24" font-size="11">Control zone</text>
    <rect x="375" y="60" width="100" height="36" rx="6" fill="#ff6b00" opacity="0.7"/>
    <text x="425" y="83" fill="#1a1a1a">PLC</text>
    <rect x="375" y="110" width="100" height="36" rx="6" fill="#ff6b00" opacity="0.5"/>
    <text x="425" y="133" fill="#1a1a1a">HMI / OPC-UA</text>
  </g>
  <!-- conduit with firewall -->
  <line x1="170" y1="105" x2="350" y2="105" stroke="currentColor" stroke-width="2"/>
  <rect x="240" y="88" width="40" height="34" rx="4" fill="#ff6b00"/>
  <text x="260" y="110" text-anchor="middle" font-size="10" fill="#1a1a1a">FW</text>
  <text x="260" y="140" text-anchor="middle" font-size="10" opacity="0.8">conduit: only what is needed</text>
</svg>
<figcaption>Segmentation puts the attacker and the controllers in different zones, with a firewalled conduit between them. The segmentation and firewall challenges build exactly this boundary.</figcaption>
</figure>

## Practical hardening in CybICS

The defense challenges implement concrete, verifiable controls:

| Control | What you do | Standard |
|---|---|---|
| Remove default credentials | change OpenPLC and FUXA passwords | IEC 62443 SR 1.1; NIST IA-5 |
| Restrict Modbus | iptables so only the HMI reaches port 502 | SR 5.1; NIST SC-7 |
| Network segmentation | block the attack host from the controllers | SR 5.1; NIST SC-7 |
| Keep the IDS effective | detection stays active and tuned | NIST SI-4 |

## Layering the controls

Each control is modest alone; together they compound. Change the passwords and a stolen
default is worthless. Segment the network and a scan never reaches the PLC. Keep the IDS
tuned and whatever slips through still raises an alarm.

<figure>
<svg viewBox="0 0 420 150" role="img" aria-label="Layers of defense">
  <g text-anchor="middle" font-size="11">
    <ellipse cx="210" cy="75" rx="200" ry="65" fill="#ff6b00" opacity="0.10" stroke="currentColor"/>
    <text x="210" y="22">Monitoring / IDS</text>
    <ellipse cx="210" cy="80" rx="150" ry="50" fill="#ff6b00" opacity="0.14" stroke="currentColor"/>
    <text x="210" y="46">Segmentation</text>
    <ellipse cx="210" cy="88" rx="95" ry="34" fill="#ff6b00" opacity="0.25" stroke="#ff6b00"/>
    <text x="210" y="70">Host firewall</text>
    <text x="210" y="95" font-weight="bold">Strong auth</text>
  </g>
</svg>
<figcaption>Defense in depth: an attacker must defeat every ring, and the outer ring (monitoring) still reports the attempt.</figcaption>
</figure>

## The mindset

Assume any single control can fail. Design so that a failure is contained and observed. In
OT this must be balanced against availability &mdash; a lockout or a dropped packet must
never endanger the process &mdash; which is why segmentation and monitoring, not intrusive
blocking, are the workhorses of ICS defense.
