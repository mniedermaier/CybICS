# Programming the controller

The PLC runs a program you can change. Downloading modified logic to a running controller is
one of the highest-impact actions in ICS, because it silently changes how the process
behaves &mdash; the technique behind Stuxnet.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Program download to PLC">
  <defs><marker id="pd" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="40" width="140" height="46" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="90" y="62" text-anchor="middle" font-size="11" fill="#1a1a1a">Engineering WS</text>
  <text x="90" y="77" text-anchor="middle" font-size="9" fill="#1a1a1a">OpenPLC Editor</text>
  <line x1="160" y1="63" x2="340" y2="63" stroke="#ff6b00" stroke-width="2" marker-end="url(#pd)"/>
  <text x="250" y="56" text-anchor="middle" font-size="10">compile + download (T0843)</text>
  <rect x="342" y="40" width="150" height="46" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="417" y="62" text-anchor="middle" font-size="11">OpenPLC runtime</text>
  <text x="417" y="77" text-anchor="middle" font-size="9">now runs your logic</text>
</svg>
<figcaption>Editing the ladder/ST program, compiling it, and downloading it changes the controller's behaviour. The challenge verifies your program is actually running.</figcaption>
</figure>

## The skill

Open the CybICS project in OpenPLC Editor, modify and compile it, then upload and launch it
through the web UI. The controller then runs a program that is no longer the shipped one
&mdash; proof you exercised the program-download workflow.

> **MITRE ATT&CK for ICS:** T0843 Program Download, T0889 Modify Program. Defence:
> configuration management and change control (NIST CM-3), and integrity verification.
