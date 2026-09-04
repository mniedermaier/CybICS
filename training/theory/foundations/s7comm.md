# S7comm

**S7comm** is the proprietary protocol Siemens PLCs use for programming and data exchange.
It rides on the ISO-on-TCP (RFC 1006) transport on port **102**. CybICS ships a small
S7comm server so you can practise enumeration without a real Siemens PLC.

## The layered stack

S7comm is not a flat protocol; it is wrapped in two lower layers. Understanding the layers
explains why a connection needs a setup handshake before any data flows.

<figure>
<svg viewBox="0 0 360 210" role="img" aria-label="S7comm protocol stack">
  <g font-size="12" text-anchor="middle">
    <rect x="80" y="10" width="200" height="34" rx="4" fill="#ff6b00" opacity="0.8"/>
    <text x="180" y="32" fill="#1a1a1a" font-weight="bold">S7comm (function, data)</text>
    <rect x="80" y="52" width="200" height="34" rx="4" fill="currentColor" opacity="0.22" stroke="currentColor"/>
    <text x="180" y="74">COTP (ISO 8073)</text>
    <rect x="80" y="94" width="200" height="34" rx="4" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="180" y="116">TPKT / ISO-on-TCP (RFC 1006)</text>
    <rect x="80" y="136" width="200" height="34" rx="4" fill="currentColor" opacity="0.14" stroke="currentColor"/>
    <text x="180" y="158">TCP : 102</text>
  </g>
  <text x="180" y="192" font-size="10" opacity="0.7">Each layer wraps the one above; a COTP connection request</text>
  <text x="180" y="205" font-size="10" opacity="0.7">opens the session before any S7 function is sent.</text>
</svg>
<figcaption>The S7comm stack. A client first completes a COTP connection request, then negotiates S7 parameters, then can read data or identity.</figcaption>
</figure>

## Reading device identity

A useful, low-noise reconnaissance step is the **Read SZL** (System Status List) function.
It returns identity records: module type, serial number, firmware, plant designation. No
authentication is needed, so a scanner can fingerprint a Siemens device before touching the
process. In CybICS the module-type field is where the *scanning2* challenge hides its flag.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="SZL identity query">
  <rect x="20" y="30" width="110" height="44" rx="6" fill="#ff6b00" opacity="0.85"/>
  <text x="75" y="57" text-anchor="middle" font-size="12" fill="#1a1a1a">scanner</text>
  <rect x="390" y="30" width="110" height="44" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="445" y="52" text-anchor="middle" font-size="12">S7 server</text>
  <text x="445" y="66" text-anchor="middle" font-size="10">:102</text>
  <defs><marker id="s" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <line x1="130" y1="45" x2="388" y2="45" stroke="#ff6b00" stroke-width="2" marker-end="url(#s)"/>
  <text x="259" y="39" text-anchor="middle" font-size="11">Read SZL (module identification)</text>
  <line x1="390" y1="62" x2="132" y2="62" stroke="currentColor" stroke-width="2" opacity="0.6" marker-end="url(#s)"/>
  <text x="259" y="80" text-anchor="middle" font-size="11" opacity="0.85">Module type, serial, firmware &hellip;</text>
  <text x="20" y="108" font-size="10" opacity="0.7">Enumeration maps to MITRE ATT&amp;CK for ICS T0846 Remote System Discovery.</text>
</svg>
<figcaption>An SZL read returns device identity with no login &mdash; ideal for the attacker's discovery phase, and the basis of the S7comm scanning challenge.</figcaption>
</figure>

## Security relevance

Classic S7comm (S7-300/400) has no authentication. Newer S7-1200/1500 added S7comm-Plus
with anti-replay and integrity, but huge installed bases still speak the old protocol.
Enumeration is quiet and hard to distinguish from legitimate engineering traffic, which is
why detecting it relies on *where* the request comes from, not *what* it is.
