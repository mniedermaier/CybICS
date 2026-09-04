# Host firewalling

Not every host needs to talk Modbus to the PLC &mdash; only the HMI does. A host firewall on
the controller drops Modbus from everyone else, so an attacker on the network cannot reach
port 502 at all.

<figure>
<svg viewBox="0 0 520 130" role="img" aria-label="iptables allowing only the HMI">
  <defs><marker id="df" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="20" width="90" height="34" rx="6" fill="#ff6b00" opacity="0.55"/><text x="65" y="42" text-anchor="middle" font-size="10" fill="#1a1a1a">HMI (allow)</text>
  <rect x="20" y="76" width="90" height="34" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/><text x="65" y="98" text-anchor="middle" font-size="10">attacker (deny)</text>
  <rect x="230" y="45" width="46" height="40" rx="4" fill="#ff6b00"/><text x="253" y="70" text-anchor="middle" font-size="10" fill="#1a1a1a">FW</text>
  <rect x="380" y="45" width="110" height="40" rx="6" fill="#ff6b00" opacity="0.6"/><text x="435" y="70" text-anchor="middle" font-size="11" fill="#1a1a1a">PLC :502</text>
  <line x1="110" y1="37" x2="230" y2="55" stroke="#ff6b00" stroke-width="2" marker-end="url(#df)"/>
  <line x1="110" y1="93" x2="228" y2="75" stroke="currentColor" stroke-width="2" opacity="0.4"/>
  <line x1="215" y1="60" x2="245" y2="90" stroke="#ff6b00" stroke-width="2"/>
  <line x1="276" y1="65" x2="380" y2="65" stroke="#ff6b00" stroke-width="2" marker-end="url(#df)"/>
</svg>
<figcaption>An iptables rule permits Modbus only from the HMI and drops it from the attack host, shrinking the attack surface to what the process needs.</figcaption>
</figure>

## The skill

Add iptables rules on the OpenPLC container so only the HMI reaches port 502. The check
confirms a DROP/REJECT rule for the attack host and that 502 is no longer reachable from
elsewhere.

> **IEC 62443** SR 5.1; **NIST SP 800-82 / 800-53** SC-7 Boundary Protection.
