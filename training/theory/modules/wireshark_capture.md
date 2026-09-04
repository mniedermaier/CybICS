# Capturing Modbus traffic

Modbus is plaintext. Anyone who can see the traffic can read every value the HMI and PLC
exchange &mdash; setpoints, readings, and anything an application writes into registers.
Traffic capture turns a network position into data.

<figure>
<svg viewBox="0 0 520 130" role="img" aria-label="Sniffing Modbus writes">
  <g font-size="10" text-anchor="middle">
    <rect x="30" y="30" width="80" height="36" rx="6" fill="#ff6b00" opacity="0.7"/><text x="70" y="52" fill="#1a1a1a">HMI</text>
    <rect x="410" y="30" width="80" height="36" rx="6" fill="#ff6b00" opacity="0.55"/><text x="450" y="52" fill="#1a1a1a">PLC</text>
    <line x1="110" y1="48" x2="410" y2="48" stroke="currentColor" stroke-width="2"/>
    <text x="260" y="40">FC16 write regs 1200.. = 43 79 62 49 43 53</text>
    <line x1="260" y1="48" x2="260" y2="95" stroke="#ff6b00" stroke-dasharray="4 3"/>
    <rect x="205" y="95" width="110" height="30" rx="5" fill="currentColor" opacity="0.2" stroke="#ff6b00"/>
    <text x="260" y="114">Wireshark</text>
  </g>
  <text x="30" y="125" font-size="10" opacity="0.7">Register bytes decode straight to ASCII: "CybICS(...)".</text>
</svg>
<figcaption>Register writes carry bytes that decode to ASCII. Capturing the write packets recovers a flag hidden in holding registers 1200 onward.</figcaption>
</figure>

## The skill

Capture traffic with Wireshark or tshark, filter for Modbus write function codes, and decode
the register payloads. The plaintext nature of Modbus is the whole point.

> **MITRE ATT&CK for ICS:** T0802 Automated Collection. Defence: encrypt or segment the
> control network so capture is not possible from arbitrary hosts.
