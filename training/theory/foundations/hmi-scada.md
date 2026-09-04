# HMI and SCADA

The **Human-Machine Interface (HMI)** is the screen an operator watches: tank levels,
pressures, pumps, alarms, and the buttons to start and stop the process. **SCADA**
(Supervisory Control and Data Acquisition) is the wider system that gathers data from many
controllers and presents it. In CybICS the HMI is **FUXA**, a web-based SCADA/HMI.

## Where the HMI sits

The HMI does not talk to sensors directly. It reads and writes the PLC's registers over an
industrial protocol, and the PLC drives the process. The operator's "start pump" click
becomes a Modbus write.

<figure>
<svg viewBox="0 0 520 150" role="img" aria-label="Operator to process data flow">
  <defs><marker id="h" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <g text-anchor="middle" font-size="11">
    <rect x="10" y="50" width="90" height="44" rx="6" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="55" y="70">Operator</text><text x="55" y="85" font-size="10">eyes &amp; hands</text>
    <rect x="140" y="50" width="90" height="44" rx="6" fill="#ff6b00" opacity="0.8"/>
    <text x="185" y="70" fill="#1a1a1a">HMI</text><text x="185" y="85" font-size="10" fill="#1a1a1a">FUXA</text>
    <rect x="270" y="50" width="90" height="44" rx="6" fill="#ff6b00" opacity="0.6"/>
    <text x="315" y="70" fill="#1a1a1a">PLC</text><text x="315" y="85" font-size="10" fill="#1a1a1a">OpenPLC</text>
    <rect x="400" y="50" width="100" height="44" rx="6" fill="#ff6b00" opacity="0.4"/>
    <text x="450" y="70">Process</text><text x="450" y="85" font-size="10">tanks, valves</text>
  </g>
  <line x1="100" y1="72" x2="138" y2="72" stroke="#ff6b00" stroke-width="2" marker-end="url(#h)"/>
  <line x1="230" y1="72" x2="268" y2="72" stroke="#ff6b00" stroke-width="2" marker-end="url(#h)"/>
  <text x="250" y="44" text-anchor="middle" font-size="10">Modbus</text>
  <line x1="360" y1="72" x2="398" y2="72" stroke="#ff6b00" stroke-width="2" marker-end="url(#h)"/>
  <text x="55" y="120" font-size="10" opacity="0.7">Trust flows right; consequences flow left as displayed values.</text>
</svg>
<figcaption>The operator sees the process only through the HMI. Fool the HMI, or the data feeding it, and you control what the operator believes.</figcaption>
</figure>

## Why the HMI is a high-value target

- It holds **valid credentials** and network paths to the controllers.
- It can **command** the process directly.
- The operator **trusts what it shows**. The Stuxnet worm famously replayed normal readings
  to the HMI while sabotaging the centrifuges underneath &mdash; a lie in the supervisory
  layer.

In CybICS the FUXA login is a dictionary-attack target (the *password attack* challenge),
and the man-in-the-middle challenge sits on the HMI-to-PLC link to alter what each side
sees.

## Security relevance

Protecting the supervisory layer means strong HMI authentication, restricting who can reach
it, and protecting the integrity of the HMI-to-PLC traffic. When that traffic can be
altered undetected, the operator's screen becomes untrustworthy &mdash; the most dangerous
failure in a control room.
