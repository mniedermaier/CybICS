# Man in the middle

If the HMI-to-PLC traffic can be intercepted, an attacker can read and alter it: show the
operator a normal reading while sending the PLC a different command. On a switched LAN this
is done with **ARP poisoning**, which redirects traffic through the attacker.

<figure>
<svg viewBox="0 0 520 150" role="img" aria-label="ARP poisoning MITM">
  <defs><marker id="mm" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <g text-anchor="middle" font-size="11">
    <rect x="20" y="55" width="80" height="40" rx="6" fill="#ff6b00" opacity="0.7"/><text x="60" y="79" fill="#1a1a1a">HMI</text>
    <rect x="420" y="55" width="80" height="40" rx="6" fill="#ff6b00" opacity="0.55"/><text x="460" y="79" fill="#1a1a1a">PLC</text>
    <rect x="215" y="10" width="90" height="38" rx="6" fill="currentColor" opacity="0.25" stroke="#ff6b00"/>
    <text x="260" y="33">attacker</text>
  </g>
  <line x1="100" y1="70" x2="215" y2="35" stroke="#ff6b00" stroke-width="2" marker-end="url(#mm)"/>
  <line x1="305" y1="35" x2="420" y2="70" stroke="#ff6b00" stroke-width="2" marker-end="url(#mm)"/>
  <line x1="100" y1="85" x2="420" y2="85" stroke="currentColor" stroke-dasharray="5 4" opacity="0.4"/>
  <text x="260" y="105" text-anchor="middle" font-size="10" opacity="0.7">traffic now flows through the attacker, who can alter it</text>
  <text x="260" y="130" text-anchor="middle" font-size="10" opacity="0.8">one IP appearing with two MAC addresses = the arp_spoof signature</text>
</svg>
<figcaption>ARP poisoning inserts the attacker between HMI and PLC. The tell-tale is one IP claimed by two MAC addresses, which the IDS flags.</figcaption>
</figure>

## The skill

Use `arpspoof` to poison the ARP tables of the HMI and PLC, enable forwarding, and relay (or
alter) the Modbus traffic. CybICS confirms the attack via the IDS `arp_spoof` signature.

> **MITRE ATT&CK for ICS:** T0830 Adversary-in-the-Middle. Defence: static ARP, segmentation,
> and integrity-protected protocols.
