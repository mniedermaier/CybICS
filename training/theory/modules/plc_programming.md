# Programming the controller

The PLC runs a program, and the program can be replaced from a web form. Downloading modified logic to a running controller is one of the highest-impact actions in ICS, because nothing about the process *looks* different afterwards &mdash; the registers still read plausibly, the HMI still draws its trends, and the plant now does something else. It is the technique behind Stuxnet, and on this platform it is four clicks.

## What the check actually looks at, and why

Most CTF flags are a string you find. This one is not: `check_plc_program.py` asks the controller which program it is running.

<figure>
<style>
.article figure svg.pg-f {min-width: 360px;}
.pg-f {--f: 14s;}
/* The dashboard field and the verdict share one clock, because the point is
   that one follows from the other -- a fresh file id is the entire evidence,
   and the check is set membership over three known names. */
.pg-f .old {opacity:0; animation: pf-old var(--f) steps(1,end) infinite;}
.pg-f .new {opacity:1; animation: pf-new var(--f) steps(1,end) infinite;}
.pg-f .no  {opacity:0; animation: pf-old var(--f) steps(1,end) infinite;}
.pg-f .yes {opacity:1; animation: pf-new var(--f) steps(1,end) infinite;}
.pg-f .mark{opacity:0; animation: pf-old var(--f) steps(1,end) infinite;}
@keyframes pf-old {0%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes pf-new {0%,49.9%{opacity:0} 50%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pg-f * {animation:none !important;} }
</style>
<svg class="pg-f" viewBox="0 0 360 216" role="img"
     aria-label="The OpenPLC dashboard reports which program file it is running. Before the challenge it names 424345.st, which is one of the three files shipped in the seeded image, so the check reports that the shipped program is still running. After the player compiles and uploads their own program the field names a file id that has never been seen before, it is not in the baseline set, and the check passes. The evidence is the identity of the running program, which a Modbus write cannot forge.">
  <text x="8" y="18" font-size="12" font-weight="bold">what the OpenPLC dashboard reports</text>
  <rect x="8" y="30" width="200" height="50" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="20" y="50" font-size="12" opacity="0.85">File:</text>
  <text class="old" x="66" y="50" font-size="12" font-weight="bold" font-family="monospace">424345.st</text>
  <text class="new" x="66" y="50" font-size="12" font-weight="bold" font-family="monospace" fill="#ff6b00">5517293.st</text>
  <text x="20" y="70" font-size="12" opacity="0.85">Status:</text>
  <text x="76" y="70" font-size="12" font-weight="bold">Running</text>

  <text x="8" y="104" font-size="11" opacity="0.85">the three files shipped in the seeded image:</text>
  <g font-family="monospace" font-size="11">
    <text x="8" y="122">424345.st</text>
    <text x="90" y="122">4968.st</text>
    <text x="160" y="122">blank_program.st</text>
  </g>
  <g class="mark"><rect x="4" y="112" width="58" height="14" rx="3" fill="none" stroke="#ff6b00" stroke-width="2"/></g>

  <text class="no"  x="8" y="152" font-size="12" font-weight="bold">in the set &rarr; still the shipped program</text>
  <text class="yes" x="8" y="152" font-size="12" font-weight="bold" fill="#ff6b00">not in the set &rarr; you compiled this one</text>
  <text x="8" y="180" font-size="11" opacity="0.85">A coil can be written back over Modbus in fifty milliseconds.</text>
  <text x="8" y="196" font-size="11" opacity="0.85">The identity of the running program cannot be written at all.</text>
  <text x="8" y="212" font-size="11" opacity="0.85">That is why this check asks the controller and not the wire.</text>
</svg>
<figcaption>OpenPLC gives every compiled program a fresh file id, so the dashboard&rsquo;s <code>File:</code> field is a fingerprint of what is actually loaded. <code>check_plc_program.py</code> logs in, parses that field and the status, and passes when the name is outside the set <code>{424345.st, 4968.st, blank_program.st}</code> <em>and</em> the controller says <code>Running</code>. Read live from this stack a moment ago: <code>424345.st</code>, <code>Running</code> &mdash; the shipped program, so the check would currently report the challenge as not done. The docstring makes the design explicit: this state lives inside the runtime and cannot be faked over Modbus, unlike an output coil.</figcaption>
</figure>

## Two challenges that want opposite things

There is a trap in the order, and it is worth meeting on a page rather than in a verifier.

<figure>
<style>
.article figure svg.pg-o {min-width: 360px;}
.pg-o {--o: 16s;}
/* One marker walks two orderings of the same two tasks. The orderings differ
   only in sequence, so a figure that shows them one after the other is making
   exactly the comparison a reader has to make. */
.pg-o .mk  {animation: po-mk var(--o) cubic-bezier(.4,0,.2,1) infinite;}
.pg-o .rA  {animation: po-a var(--o) steps(1,end) infinite;}
.pg-o .rB  {animation: po-b var(--o) steps(1,end) infinite;}
.pg-o .okA {opacity:0; animation: po-oka var(--o) steps(1,end) infinite;}
.pg-o .okB {opacity:1; animation: po-okb var(--o) steps(1,end) infinite;}
.pg-o .mk  {transform: translate(160px,86px);}
.pg-o .rA  {stroke-width:0;}
.pg-o .rB  {stroke-width:3;}
@keyframes po-mk {0%,10%{transform:translate(0,0)}      20%,35%{transform:translate(160px,0)}
                  45%,55%{transform:translate(0,86px)}   65%,100%{transform:translate(160px,86px)}}
@keyframes po-a  {0%,44.9%{stroke-width:3} 45%,100%{stroke-width:0}}
@keyframes po-b  {0%,44.9%{stroke-width:0} 45%,100%{stroke-width:3}}
@keyframes po-oka{0%,34.9%{opacity:0} 35%,44.9%{opacity:1} 45%,100%{opacity:0}}
@keyframes po-okb{0%,64.9%{opacity:0} 65%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pg-o * {animation:none !important;} }
</style>
<svg class="pg-o" viewBox="0 0 360 214" role="img"
     aria-label="Two orderings of the same two tasks. Doing the program download first and hardening the OpenPLC password afterwards leaves both checks able to pass. Hardening the password first means the program check can no longer log into the controller, so it cannot read which program is loaded and reports that it cannot verify, even though the player may have done the work.">
  <text x="8" y="18" font-size="12" font-weight="bold">the same two tasks, two orders</text>

  <rect class="rA" x="4" y="30" width="352" height="64" rx="5" fill="none" stroke="#ff6b00"/>
  <rect x="16" y="40" width="130" height="26" rx="4" fill="#ff6b00"/>
  <text x="81" y="57" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">download program</text>
  <rect x="176" y="40" width="130" height="26" rx="4" fill="#ff6b00"/>
  <text x="241" y="57" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">harden password</text>
  <text class="okA" x="16" y="84" font-size="12" font-weight="bold" fill="#ff6b00">both checks can pass</text>

  <rect class="rB" x="4" y="116" width="352" height="64" rx="5" fill="none" stroke="#ff6b00"/>
  <rect x="16" y="126" width="130" height="26" rx="4" fill="#ff6b00"/>
  <text x="81" y="143" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">harden password</text>
  <rect x="176" y="126" width="130" height="26" rx="4" fill="#ff6b00"/>
  <text x="241" y="143" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">download program</text>
  <text class="okB" x="16" y="170" font-size="12" font-weight="bold">the program check can no longer log in</text>

  <g class="mk"><path d="M 146 46 L 162 53 L 146 60 Z" fill="#ff6b00"/></g>
  <text x="8" y="202" font-size="11" opacity="0.85">One verifier needs the default credential to work.</text>
  <text x="8" y="212" font-size="11" opacity="0.85">The other passes only when it has stopped working.</text>
</svg>
<figcaption><code>check_plc_program.py</code> logs into OpenPLC as <code>openplc</code>/<code>openplc</code> to read the dashboard, and <code>check_openplc_password.py</code> passes only when that exact credential no longer works. The two are in direct opposition, and the program check says so in its own failure text: &ldquo;Do this challenge before hardening the OpenPLC password, or restore it temporarily.&rdquo; That is a fair design &mdash; there is no other way for an outside checker to read the loaded program &mdash; but it is the kind of coupling that makes real change-control audits difficult, where the evidence that a change happened often depends on the access the change was meant to remove.</figcaption>
</figure>

## Doing it

Open the CybICS project in the OpenPLC Editor, change something in `cybICS.st`, compile it, then upload and start it through the web UI on port 8080. The flag is `CybICS(ladder_logic_modified)`.

What to change is up to you, but the instructive edit is one that leaves the plant looking normal. Widen the compressor band from 60&ndash;90 to 60&ndash;120 and the trends still show a tank filling and emptying on a cycle; nothing alarms, nothing reads as wrong, and the pressure now spends its time somewhere the designer never intended. That is the difference between this challenge and *Flood &amp; Overwrite*: the flood is loud and transient, a program download is quiet and permanent.

## Detecting it

You cannot, on this platform. The IDS dispatches on destination port, and port 8080 reaches only the brute-force rule, which counts POSTs whose first 200 bytes contain `login` or `auth`. A program upload matches neither, so no port rule fires. The two rules that run before the dispatch see it &mdash; they see every SYN packet on every port &mdash; but one needs five distinct ports in ten seconds and the other a hundred SYNs, and an upload is neither.

That is not a gap peculiar to CybICS. Program downloads are ordinary engineering traffic, they use the vendor's own protocol, and telling a legitimate change from a malicious one means knowing which changes were authorised &mdash; which is change control, not network detection.

> **MITRE ATT&CK for ICS:** T0843 Program Download, T0889 Modify Program. Defence: configuration management and change control (NIST CM-3), and integrity verification of the loaded program &mdash; which is exactly what this challenge&rsquo;s own verifier does, and the only reason it can tell.
