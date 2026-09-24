# Programming the controller

The PLC runs a program, and the program can be replaced from a web form. Downloading modified logic to a running controller is one of the highest-impact actions in ICS, because nothing about the process *looks* different afterwards &mdash; the registers still read plausibly, the HMI still draws its trends, and the plant now does something else. It is the technique behind Stuxnet, and on this platform it is four clicks.

## What the check actually looks at, and why

Most CTF flags are a string you find. This one is not: `check_plc_program.py` asks the controller which program it is running.

<figure>
<style>
.article figure svg.pg-f {min-width: 388px;}
.pg-f {--f: 18s;}
/* Three states, because the check is a conjunction and the interesting frame
   is the one in the middle: a new file that was never started. A two-state
   crossfade would be a before-and-after still with a seven-second wait. The
   rest state is the first, which is what this stack reports right now and
   what the figcaption quotes. */
.pg-f .s1 {opacity:1; animation: pf-s1 var(--f) steps(1,end) infinite;}
.pg-f .s2 {opacity:0; animation: pf-s2 var(--f) steps(1,end) infinite;}
.pg-f .s3 {opacity:0; animation: pf-s3 var(--f) steps(1,end) infinite;}
@keyframes pf-s1 {0%,33.2%{opacity:1} 33.3%,100%{opacity:0}}
@keyframes pf-s2 {0%,33.2%{opacity:0} 33.3%,66.5%{opacity:1} 66.6%,100%{opacity:0}}
@keyframes pf-s3 {0%,66.5%{opacity:0} 66.6%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pg-f * {animation:none !important;} }
</style>
<svg class="pg-f" viewBox="0 0 360 244" role="img"
     aria-label="The OpenPLC dashboard reports two things and the check needs both. In the first state the file is 424345.st, one of the three shipped with the image, and the status is Running: the check fails because the program is not yours. In the second the file is 831742.st, which is new, but the status is Stopped: the check fails because you uploaded without starting it. Only in the third, a new file and Running, does it pass. The file name is a fingerprint the wire cannot forge; the status is the half people forget.">
  <text x="8" y="18" font-size="12" font-weight="bold">the check needs both fields</text>
  <rect x="8" y="30" width="216" height="52" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="20" y="51" font-size="12" opacity="0.85">File:</text>
  <g font-family="monospace" font-size="12" font-weight="bold">
    <text class="s1" x="66" y="51">424345.st</text>
    <text class="s2" x="66" y="51">831742.st</text>
    <text class="s3" x="66" y="51">831742.st</text>
  </g>
  <text x="20" y="72" font-size="12" opacity="0.85">Status:</text>
  <g font-size="12" font-weight="bold">
    <text class="s1" x="76" y="72">Running</text>
    <text class="s2" x="76" y="72">Stopped</text>
    <text class="s3" x="76" y="72">Running</text>
  </g>

  <text x="8" y="106" font-size="11" opacity="0.85">the three files shipped in the seeded image:</text>
  <g font-family="monospace" font-size="11">
    <text x="8" y="124">424345.st</text>
    <text x="90" y="124">4968.st</text>
    <text x="160" y="124">blank_program.st</text>
  </g>

  <g font-size="12" font-weight="bold">
    <text class="s1" x="8" y="156">in the set &rarr; not your program</text>
    <text class="s2" x="8" y="156">new file, but never started</text>
    <text class="s3" x="8" y="156" fill="#ff6b00">new file and running &rarr; pass</text>
  </g>
  <text x="8" y="190" font-size="11" opacity="0.85">A coil can be written back over Modbus in fifty milliseconds.</text>
  <text x="8" y="206" font-size="11" opacity="0.85">A file name in the controller&rsquo;s own database cannot be written</text>
  <text x="8" y="222" font-size="11" opacity="0.85">at all. That is why this check asks the runtime, not the wire.</text>
  <text x="8" y="240" font-size="11" opacity="0.85">And why it also asks whether you remembered to press Start.</text>
</svg>
<figcaption>OpenPLC names every uploaded file <code>str(random.randint(1, 1000000)) + ".st"</code>, so the dashboard&rsquo;s <code>File:</code> field identifies what is loaded. <code>check_plc_program.py</code> logs in, parses that field and the status, and passes only when the name is outside <code>{424345.st, 4968.st, blank_program.st}</code> <strong>and</strong> the controller reports <code>Running</code> &mdash; a conjunction, which is why uploading without starting fails. Read live from this stack while writing: <code>424345.st</code>, <code>Running</code>, the first of the three states above. Worth reading critically, though: the id is assigned at <em>upload</em>, not at compile, so re-uploading a byte-identical copy of the shipped program also passes. The check proves a file outside that set is loaded and running. It does not prove you changed anything.</figcaption>
</figure>

## Two challenges that want opposite things

There is a trap in the order, and it is worth meeting on a page rather than in a verifier.

<figure>
<style>
.article figure svg.pg-o {min-width: 388px;}
.pg-o {--o: 16s;}
/* One marker walks two orderings of the same two tasks. The rest state shows
   both rows and both verdicts, because the figure's whole content is the
   comparison -- resting on one row showed a reader the broken ordering and
   nothing to compare it against. The two verdicts also get equal time; the
   first used to hold for 1.6 s against the second's 5.6. */
.pg-o .mk  {animation: po-mk var(--o) cubic-bezier(.4,0,.2,1) infinite;}
.pg-o .rA  {animation: po-a var(--o) steps(1,end) infinite;}
.pg-o .rB  {animation: po-b var(--o) steps(1,end) infinite;}
.pg-o .okA {opacity:1; animation: po-oka var(--o) steps(1,end) infinite;}
.pg-o .okB {opacity:1; animation: po-okb var(--o) steps(1,end) infinite;}
.pg-o .mk  {transform: translate(160px,86px);}
.pg-o .rA,.pg-o .rB {stroke-width:3;}
@keyframes po-mk {0%,10%{transform:translate(0,0)}      20%,42%{transform:translate(160px,0)}
                  52%,60%{transform:translate(0,86px)}   70%,100%{transform:translate(160px,86px)}}
@keyframes po-a  {0%,49.9%{stroke-width:3} 50%,100%{stroke-width:0}}
@keyframes po-b  {0%,49.9%{stroke-width:0} 50%,100%{stroke-width:3}}
@keyframes po-oka{0%,19.9%{opacity:0} 20%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes po-okb{0%,69.9%{opacity:0} 70%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pg-o * {animation:none !important;} }
</style>
<svg class="pg-o" viewBox="0 0 360 226" role="img"
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

  <g class="mk"><path d="M 150 46 L 168 53 L 150 60 Z" fill="#ff6b00" stroke="currentColor" stroke-width="1.5"/></g>
  <text x="8" y="202" font-size="11" opacity="0.85">One verifier needs the default credential to work.</text>
  <text x="8" y="218" font-size="11" opacity="0.85">The other passes only when it has stopped working.</text>
</svg>
<figcaption><code>check_plc_program.py</code> logs into OpenPLC as <code>openplc</code>/<code>openplc</code> to read the dashboard, and <code>check_openplc_password.py</code> passes only when that exact credential no longer works. The two are in direct opposition, and the program check says so in its own failure text: &ldquo;Do this challenge before hardening the OpenPLC password, or restore it temporarily.&rdquo; That is a fair design &mdash; there is no other way for an outside checker to read the loaded program &mdash; but it is the kind of coupling that makes real change-control audits difficult, where the evidence that a change happened often depends on the access the change was meant to remove.</figcaption>
</figure>

## Doing it

The editor is on the Engineering Workstation: `http://localhost:6080/vnc.html`, password `cybics`, and the project is `beremiz.xml` on the desktop. Change something in `cybICS.st`, compile it, then upload and start the result through OpenPLC's web UI on port 8080. The flag is `CybICS(ladder_logic_modified)`.

What to change is up to you, and the two obvious edits behave very differently. Widening the compressor band from 60&ndash;90 to 60&ndash;99 leaves the plant cycling exactly as before &mdash; simulated over 6000 ticks, the pressure still swings between 58 and its new ceiling and the system valve is open the whole time. Widen it to 60&ndash;120 and the plant stops dead.

The reason is a coupling the program never states. `cybICS.st` opens the system valve only while `hpt > 50 AND hpt < 100`, so the moment the pressure passes 100 the only consumer disappears. The compressor keeps running until storage falls to its own guard, storage then refills to 240 and parks, and the pressure freezes above 100 for good &mdash; restarting the cycle would need it to fall below 60, and nothing can take it down. Simulated: at 60&ndash;99 the valve is open 100 per cent of ticks; at 60&ndash;100 and beyond, 0.9 per cent.

No alarm sounds, because the blowout needs 220 and the pressure never gets there. What does happen is that `systemSen` flatlines at zero on the HMI's own trend and stays there. That is the better parallel to draw with *Flood &amp; Overwrite*: the flood is loud and transient, and a program download can brick a process permanently without tripping a single designed alarm &mdash; using a coupling between two bands that no one wrote down.

## Detecting it

You cannot, on this platform. The IDS dispatches on destination port, and port 8080 reaches only the brute-force rule, which counts POSTs whose first 200 bytes contain `login` or `auth`. A program upload matches neither, so no port rule fires. The two rules that run before the dispatch see it &mdash; they see every SYN packet on every port &mdash; but one needs five distinct ports in ten seconds and the other a hundred SYNs, and an upload is neither.

That is not a gap peculiar to CybICS. Program downloads are ordinary engineering traffic, they use the vendor's own protocol, and telling a legitimate change from a malicious one means knowing which changes were authorised &mdash; which is change control, not network detection.

> **MITRE ATT&CK for ICS:** T0843 Program Download, T0889 Modify Program. Defence: configuration management and change control (NIST CM-3), and integrity verification of the loaded program &mdash; which is exactly what this challenge&rsquo;s own verifier does, and the only reason it can tell.
