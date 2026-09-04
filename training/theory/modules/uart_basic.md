# UART and hardware access

Physical access changes everything. Many embedded controllers expose a **UART** serial
console on the board for debugging. Anyone who can attach to those pins may get a shell, a
boot log, or a login prompt &mdash; below every network control.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="UART serial console">
  <rect x="30" y="40" width="150" height="46" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="105" y="60" text-anchor="middle" font-size="11">STM32 board</text>
  <text x="105" y="76" text-anchor="middle" font-size="9">TX / RX / GND pins</text>
  <g stroke="#ff6b00" stroke-width="2">
    <line x1="180" y1="55" x2="330" y2="55"/>
    <line x1="180" y1="63" x2="330" y2="63"/>
    <line x1="180" y1="71" x2="330" y2="71"/>
  </g>
  <text x="255" y="46" text-anchor="middle" font-size="9">3 wires</text>
  <rect x="332" y="40" width="160" height="46" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="412" y="60" text-anchor="middle" font-size="11" fill="#1a1a1a">USB-serial + terminal</text>
  <text x="412" y="76" text-anchor="middle" font-size="9" fill="#1a1a1a">115200 8N1</text>
</svg>
<figcaption>A serial console needs only three wires. It sits beneath the network stack, so it bypasses every network control.</figcaption>
</figure>

## The skill

Connect to the board's serial console, reach the menu, and get past its simple login. The
UART flag `CybICS(U#RT)` is printed by the firmware behind that gate. This module is
hardware-only.

> **MITRE ATT&CK for ICS:** physical/hardware access. Defence: disable or protect debug
> interfaces, and control physical access to the equipment.
