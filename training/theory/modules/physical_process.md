# The gas pressure process

Every CybICS attack ends in a physical effect, so it pays to know the process. The plant
moves gas from an external supply into a **Gas Storage Tank (GST)**, compresses it into a
**High Pressure Tank (HPT)**, and protects itself with a mechanical **blowout** if pressure
climbs too high.

<figure>
<svg viewBox="0 0 520 150" role="img" aria-label="Gas pressure process">
  <defs><marker id="p" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <g text-anchor="middle" font-size="11">
    <text x="40" y="70" font-size="10">supply</text>
    <line x1="60" y1="80" x2="110" y2="80" stroke="#ff6b00" stroke-width="2" marker-end="url(#p)"/>
    <rect x="112" y="55" width="90" height="50" rx="6" fill="#ff6b00" opacity="0.4"/>
    <text x="157" y="78">GST</text><text x="157" y="93" font-size="9">storage</text>
    <rect x="235" y="60" width="60" height="40" rx="6" fill="#ff6b00" opacity="0.6"/>
    <text x="265" y="84" fill="#1a1a1a" font-size="10">compressor</text>
    <line x1="202" y1="80" x2="233" y2="80" stroke="#ff6b00" stroke-width="2" marker-end="url(#p)"/>
    <line x1="295" y1="80" x2="326" y2="80" stroke="#ff6b00" stroke-width="2" marker-end="url(#p)"/>
    <rect x="328" y="55" width="90" height="50" rx="6" fill="#ff6b00" opacity="0.75"/>
    <text x="373" y="78" fill="#1a1a1a">HPT</text><text x="373" y="93" font-size="9" fill="#1a1a1a">high pressure</text>
    <line x1="418" y1="70" x2="470" y2="45" stroke="currentColor" stroke-dasharray="4 3" marker-end="url(#p)"/>
    <text x="470" y="38" font-size="10">blowout</text>
  </g>
  <text x="20" y="135" font-size="10" opacity="0.7">The PLC keeps HPT in a safe band; forcing it past critical triggers the blowout.</text>
</svg>
<figcaption>The CybICS process. Registers expose GST, HPT, the compressor and the valves &mdash; the same values every protocol attack reads and writes.</figcaption>
</figure>

## Why it matters

The control logic keeps the HPT within a safe pressure band by running the compressor and
opening valves. An attacker who overwrites those registers, or the setpoints, can drive the
tank past its limit &mdash; the `CybICS(Bl0w0ut)` outcome shown on the HMI. Knowing which
register is which turns a blind write into a targeted one.

> Related: the plant model exists identically in the STM32 firmware and the virtual
> `hardwareAbstraction.py`, kept in sync by a parity test.
