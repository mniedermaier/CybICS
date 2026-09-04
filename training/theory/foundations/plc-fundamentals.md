# PLCs and the scan cycle

A **Programmable Logic Controller (PLC)** is the small, rugged computer at the heart of a
control system. It reads sensors, runs a control program, and drives actuators &mdash; over
and over, thousands of times a minute. In CybICS the PLC role is played by **OpenPLC**.

## The scan cycle

A PLC does not run like a normal program that starts, does work, and exits. It runs a
**cyclic scan**: an endless loop of three phases repeated every few milliseconds.

<figure>
<svg viewBox="0 0 420 260" role="img" aria-label="PLC scan cycle">
  <defs>
    <marker id="ah" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/>
    </marker>
  </defs>
  <circle cx="210" cy="130" r="95" fill="none" stroke="currentColor" stroke-opacity="0.25" stroke-width="2"/>
  <!-- three phases -->
  <g font-size="12" text-anchor="middle">
    <rect x="150" y="10" width="120" height="42" rx="6" fill="#ff6b00" opacity="0.85"/>
    <text x="210" y="30" fill="#1a1a1a" font-weight="bold">1. Read inputs</text>
    <text x="210" y="45" fill="#1a1a1a" font-size="10">sensors &rarr; memory</text>

    <rect x="300" y="150" width="120" height="42" rx="6" fill="#ff6b00" opacity="0.6"/>
    <text x="360" y="170" fill="#1a1a1a" font-weight="bold">2. Run program</text>
    <text x="360" y="185" fill="#1a1a1a" font-size="10">logic on the values</text>

    <rect x="0" y="150" width="120" height="42" rx="6" fill="#ff6b00" opacity="0.6"/>
    <text x="60" y="170" fill="#1a1a1a" font-weight="bold">3. Write outputs</text>
    <text x="60" y="185" fill="#1a1a1a" font-size="10">memory &rarr; actuators</text>
  </g>
  <!-- arrows around -->
  <path d="M270 40 A95 95 0 0 1 350 150" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M300 185 A95 95 0 0 1 120 185" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M70 150 A95 95 0 0 1 150 40" fill="none" stroke="#ff6b00" stroke-width="2" marker-end="url(#ah)"/>
  <text x="210" y="135" text-anchor="middle" font-size="12" opacity="0.7">scan cycle</text>
  <text x="210" y="152" text-anchor="middle" font-size="11" opacity="0.7">(every few ms)</text>
</svg>
<figcaption>One scan: read all inputs into memory, run the whole program on that snapshot, then write all outputs at once. Then repeat.</figcaption>
</figure>

A consequence worth remembering: the program works on a **snapshot** taken at the start of
the scan. An output you set is only applied at the end of the cycle. This is why forcing an
output value from outside (over Modbus, say) is fought by the program: the next scan
overwrites it with whatever the logic computes.

## IEC 61131-3 languages

PLC programs are written in the languages standardised by **IEC 61131-3**. The two you meet
in CybICS are:

- **Ladder Diagram (LD)** &mdash; a graphical notation that looks like a relay wiring
  diagram. Power flows left to right through contacts and coils.
- **Structured Text (ST)** &mdash; a Pascal-like textual language. The CybICS plant program
  `cybICS.st` is written in ST.

<figure>
<svg viewBox="0 0 460 90" role="img" aria-label="A ladder rung">
  <line x1="20" y1="10" x2="20" y2="80" stroke="currentColor" stroke-width="2"/>
  <line x1="440" y1="10" x2="440" y2="80" stroke="currentColor" stroke-width="2"/>
  <line x1="20" y1="45" x2="120" y2="45" stroke="currentColor"/>
  <!-- normally open contact -->
  <line x1="120" y1="30" x2="120" y2="60" stroke="currentColor" stroke-width="2"/>
  <line x1="150" y1="30" x2="150" y2="60" stroke="currentColor" stroke-width="2"/>
  <text x="112" y="24" font-size="11">start</text>
  <line x1="150" y1="45" x2="360" y2="45" stroke="currentColor"/>
  <!-- coil -->
  <path d="M360 30 A18 15 0 0 0 360 60" fill="none" stroke="#ff6b00" stroke-width="2"/>
  <path d="M392 30 A18 15 0 0 1 392 60" fill="none" stroke="#ff6b00" stroke-width="2"/>
  <text x="360" y="24" font-size="11" fill="#ff6b00">motor</text>
  <line x1="392" y1="45" x2="440" y2="45" stroke="currentColor"/>
  <text x="20" y="80" font-size="10" opacity="0.7">left rail (power)</text>
  <text x="392" y="80" font-size="10" opacity="0.7" text-anchor="end">right rail</text>
</svg>
<figcaption>A single ladder rung: when the "start" contact is closed, power reaches the "motor" coil and energises it. The CybICS program expresses the same logic in Structured Text.</figcaption>
</figure>

## How the outside world reaches the PLC

The program's variables are mapped to memory addresses (`%IX`, `%QX`, `%MW` &hellip;) that are
exposed over industrial protocols. OpenPLC publishes them over Modbus, S7comm, DNP3 and
EtherNet/IP at the same time. That is convenient for integration &mdash; and, because those
protocols do not authenticate, convenient for an attacker.

Uploading a **new program** to a running controller is one of the most impactful actions in
ICS: it changes how the process behaves. That is exactly the *PLC Programming* challenge,
and it maps to MITRE ATT&CK for ICS **T0843 Program Download**.
