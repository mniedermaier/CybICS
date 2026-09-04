# What is an Industrial Control System?

An **Industrial Control System (ICS)** is the combination of hardware and software that
monitors and controls a physical process: a gas plant, a water works, a power grid, a
production line. Unlike ordinary IT, an ICS acts on the real world. A wrong value does not
corrupt a spreadsheet, it opens a valve.

This is why the priorities are inverted compared to IT. In IT the order is usually
**confidentiality, integrity, availability**. In operational technology (OT) it is the
reverse: keeping the process running safely comes first.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="IT versus OT priorities">
  <text x="10" y="24" font-size="13" font-weight="bold">IT priorities</text>
  <rect x="10" y="34" width="150" height="26" rx="4" fill="#ff6b00" opacity="0.85"/>
  <text x="20" y="51" font-size="12" fill="#1a1a1a">1. Confidentiality</text>
  <rect x="170" y="34" width="120" height="26" rx="4" fill="currentColor" opacity="0.25"/>
  <text x="180" y="51" font-size="12">2. Integrity</text>
  <rect x="300" y="34" width="120" height="26" rx="4" fill="currentColor" opacity="0.15"/>
  <text x="310" y="51" font-size="12">3. Availability</text>
  <text x="10" y="88" font-size="13" font-weight="bold">OT priorities</text>
  <rect x="10" y="94" width="150" height="26" rx="4" fill="#ff6b00" opacity="0.85"/>
  <text x="20" y="111" font-size="12" fill="#1a1a1a">1. Safety &amp; Availability</text>
  <rect x="170" y="94" width="120" height="26" rx="4" fill="currentColor" opacity="0.25"/>
  <text x="180" y="111" font-size="12">2. Integrity</text>
  <rect x="300" y="94" width="120" height="26" rx="4" fill="currentColor" opacity="0.15"/>
  <text x="310" y="111" font-size="12">3. Confidentiality</text>
</svg>
<figcaption>The same three goals, ordered differently. In OT, a stopped process can be dangerous and expensive, so availability and safety lead.</figcaption>
</figure>

## The Purdue model

ICS networks are traditionally described with the **Purdue Enterprise Reference
Architecture**, a layered model that separates the office from the plant floor. Each level
talks mostly to its neighbours, and a well-designed plant places security boundaries
between the levels.

<figure>
<svg viewBox="0 0 520 320" role="img" aria-label="Purdue model levels">
  <!-- levels -->
  <g font-size="12">
    <rect x="60" y="10" width="400" height="40" rx="5" fill="currentColor" opacity="0.10" stroke="currentColor"/>
    <text x="72" y="35">Level 4/5 &mdash; Enterprise / IT (ERP, email, internet)</text>
    <rect x="60" y="60" width="400" height="40" rx="5" fill="currentColor" opacity="0.14" stroke="currentColor"/>
    <text x="72" y="85">Level 3 &mdash; Operations (historian, engineering workstation)</text>
    <rect x="60" y="110" width="400" height="40" rx="5" fill="#ff6b00" opacity="0.30" stroke="#ff6b00"/>
    <text x="72" y="135">Level 2 &mdash; Supervisory (SCADA, HMI)</text>
    <rect x="60" y="160" width="400" height="40" rx="5" fill="#ff6b00" opacity="0.45" stroke="#ff6b00"/>
    <text x="72" y="185">Level 1 &mdash; Control (PLCs, controllers)</text>
    <rect x="60" y="210" width="400" height="40" rx="5" fill="#ff6b00" opacity="0.60" stroke="#ff6b00"/>
    <text x="72" y="235" fill="#1a1a1a">Level 0 &mdash; Process (sensors, actuators, motors)</text>
  </g>
  <!-- DMZ marker -->
  <line x1="60" y1="105" x2="460" y2="105" stroke="#ff6b00" stroke-dasharray="6 4"/>
  <text x="60" y="272" font-size="11" opacity="0.8">A security boundary (often an OT DMZ) belongs on the dashed line,</text>
  <text x="60" y="288" font-size="11" opacity="0.8">between IT above and the control network below.</text>
</svg>
<figcaption>The Purdue model. CybICS lives at Levels 0&ndash;2: the physical process, the PLC that controls it, and the HMI that supervises it.</figcaption>
</figure>

## Where CybICS fits

CybICS is a small but complete ICS. The mapping to the Purdue levels is:

| Purdue level | CybICS component |
|---|---|
| Level 2 (Supervisory) | FUXA HMI, and the landing dashboard |
| Level 1 (Control) | OpenPLC runtime executing the plant program |
| Level 0 (Process) | The gas pressure process (real on the STM32 board, or simulated) |

The office levels (3&ndash;5) are represented by the engineering workstation and the
attack machine that sit on the same network for training.

## Why it matters for security

Because these systems were built for reliability, not for hostile networks, most ICS
protocols have **no authentication and no encryption**. Any host that can reach a PLC can
usually read and write its values. The rest of the Theory Path shows exactly how each
protocol works, how that trust is abused, and how to detect and contain it.

> **Key idea:** in ICS security you are protecting a physical process. Every attack in the
> later modules ends in a real-world effect &mdash; a frozen reading, a forced valve, a
> blown-out tank.
