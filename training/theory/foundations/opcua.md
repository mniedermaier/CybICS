# OPC-UA

**OPC Unified Architecture (OPC-UA)** is the modern, vendor-neutral standard for industrial
data exchange, on port **4840**. Unlike Modbus and classic S7comm, OPC-UA was designed with
security in mind: it has sessions, authentication, and optional signing and encryption. It
is the protocol you *can* secure &mdash; if it is configured correctly.

## Address space and sessions

OPC-UA models a device as an **address space** of nodes (objects, variables, methods) that
a client browses. To read or write, a client opens a **secure channel**, then a
**session**, authenticating as an anonymous, username, or certificate user.

<figure>
<svg viewBox="0 0 520 200" role="img" aria-label="OPC-UA session establishment">
  <rect x="20" y="20" width="110" height="44" rx="6" fill="#ff6b00" opacity="0.85"/>
  <text x="75" y="47" text-anchor="middle" font-size="12" fill="#1a1a1a">Client</text>
  <rect x="390" y="20" width="110" height="44" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="445" y="42" text-anchor="middle" font-size="12">Server</text>
  <text x="445" y="56" text-anchor="middle" font-size="10">:4840</text>
  <defs><marker id="o" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <g font-size="11">
    <line x1="130" y1="36" x2="388" y2="36" stroke="#ff6b00" stroke-width="2" marker-end="url(#o)"/>
    <text x="259" y="30" text-anchor="middle">1. OpenSecureChannel (sign / encrypt)</text>
    <line x1="130" y1="72" x2="388" y2="72" stroke="#ff6b00" stroke-width="2" marker-end="url(#o)"/>
    <text x="259" y="66" text-anchor="middle">2. CreateSession + ActivateSession (auth)</text>
    <line x1="130" y1="108" x2="388" y2="108" stroke="#ff6b00" stroke-width="2" marker-end="url(#o)"/>
    <text x="259" y="102" text-anchor="middle">3. Read / Write / Call on nodes</text>
  </g>
  <text x="20" y="150" font-size="11" opacity="0.85">The security level depends on step 1's policy and step 2's identity.</text>
  <text x="20" y="168" font-size="11" opacity="0.85">"None" policy + anonymous user = an unauthenticated free-for-all.</text>
</svg>
<figcaption>OPC-UA establishes a secure channel and an authenticated session before data access. Its safety hinges entirely on which security policy and user token the server accepts.</figcaption>
</figure>

## Where it goes wrong

OPC-UA can be strong, but defaults and convenience often weaken it:

- **SecurityPolicy None** &mdash; the channel is neither signed nor encrypted, so traffic
  can be read and forged like Modbus.
- **Anonymous access** &mdash; no user token required.
- **Weak or shared passwords**, or certificates trusted too broadly.

The CybICS OPC-UA server exposes both a user-tier and an admin-tier value. The challenge is
to authenticate well enough to reach the admin flag, illustrating how much rides on the
identity model.

## Security relevance

OPC-UA shifts the question from "can anyone talk to it" (Modbus) to "who is allowed, and how
strongly are they proven". Detection focuses on unexpected clients and on sessions using the
weakest policies. In CybICS, OPC-UA activity from any host that is not a known client raises
an IDS alert.
