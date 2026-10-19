# Programming the controller

In this challenge you change the program that runs on the CybICS PLC, compile it and load it onto the running controller. Downloading new logic is one of the most powerful things anyone can do in a control system, because afterwards nothing *looks* different: the screens still draw their trends, and the plant quietly follows new rules.

## The idea

A Programmable Logic Controller (PLC) is a small, rugged computer that runs one program in an endless loop: read the sensors, decide, switch the outputs. The program is written by a control engineer on an **engineering workstation**, compiled, and then *downloaded* to the controller. Think of a washing machine whose wash programme can be replaced over the network. The buttons and the display stay the same, but the drum may now spin at a different speed.

Engineers download programs all the time, for good reasons: fixing a bug, tuning a limit, adding a sensor. Attackers use the very same path. Stuxnet did it in 2010: it replaced code on Siemens PLCs so that centrifuges were driven at damaging speeds while the operators' screens showed normal values. MITRE ATT&CK for ICS lists the two steps as *Modify Program* (T0889) and *Program Download* (T0843).

<div data-widget="scan-cycle"></div>

## How it looks on CybICS

The CybICS controller is **OpenPLC** in the `openplc` container (172.18.0.3). Its web interface on port 8080 lets you upload, compile and start programs. Its program, `cybICS.st`, is written in Structured Text (ST), one of the IEC 61131-3 PLC languages, and it reads much like simple Pascal. It holds a few rules:

- Refill the gas storage tank (GST) when it falls below 60, and stop at 240.
- Run the compressor when the high-pressure tank (HPT) is below 60, and keep it on until 90, but only while the GST holds more than 50.
- Open the system valve only while the HPT is between 50 and 100.
- Blink a heartbeat output so you can see the PLC is alive.

The editor is on the **engineering workstation** (`engineeringws`, 172.18.0.10), a desktop in your browser at port 6080 (noVNC), with the OpenPLC Editor and the CybICS project already on the desktop. It is only part of the Docker stack and starts in the `full` and `withoutai` modes.

The challenge does not hand you a string. When you click **Verify**, the landing page logs into OpenPLC and reads its dashboard: which program file is loaded, and whether the controller is running.

<figure class="wide">
<style>
.pg-f {--f: 18s;}
.pg-f .s1 {opacity:1; animation: pf-s1 var(--f) steps(1,end) infinite;}
.pg-f .s2 {opacity:0; animation: pf-s2 var(--f) steps(1,end) infinite;}
.pg-f .s3 {opacity:0; animation: pf-s3 var(--f) steps(1,end) infinite;}
@keyframes pf-s1 {0%,33.2%{opacity:1} 33.3%,100%{opacity:0}}
@keyframes pf-s2 {0%,33.2%{opacity:0} 33.3%,66.5%{opacity:1} 66.6%,100%{opacity:0}}
@keyframes pf-s3 {0%,66.5%{opacity:0} 66.6%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .pg-f * {animation:none !important;} }
</style>
<svg class="pg-f" viewBox="0 0 360 244" role="img"
     aria-label="The OpenPLC dashboard reports two things and the check needs both. In the first state the file is 424345.st, one of the three shipped with the image, and the status is Running: the check fails because the program is not yours. In the second the file is 831742.st, which is new, but the status is Stopped: the check fails because the program was uploaded but never started. Only in the third, a new file and Running, does it pass.">
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
<figcaption>OpenPLC gives every uploaded program a new random file name, so the name on the dashboard shows which program is loaded. The check passes only when that name is not one of the three shipped with the lab <strong>and</strong> the controller reports <code>Running</code>. Uploading without starting is not enough.</figcaption>
</figure>

## How to approach it

1. Open the engineering workstation in your browser and start the OpenPLC Editor from the desktop. Open the CybICS project.
2. Read the program first. Find the rules listed above and work out which variable is which sensor or actuator.
3. Make a change. It can be harmless, such as a comment, or a change to a limit. If you change a limit, predict what the plant will do before you load it.
4. Compile the project in the editor. The result is a `.st` file.
5. In the OpenPLC web interface on port 8080, upload the file under **Programs**, let it compile, and start the PLC.
6. Watch the plant on the HMI, then click **Verify** on the challenge page.

<div data-widget="checkpoint" data-id="start"></div>

<div class="callout warning" markdown="1">
**Warning:** The verifier logs into OpenPLC with its default credentials. Do this challenge *before* the challenge that asks you to harden the OpenPLC password, or restore the default for a moment.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: how a small edit can stall the plant</summary>

The compressor band (60 to 90) and the system-valve band (50 to 100) are separate rules, but they depend on each other. Raise the compressor's upper limit to 99 and the plant still cycles. Raise it to 120 and something surprising happens.

Once the pressure passes 100, the PLC shuts the system valve, so the only consumer of gas disappears. The compressor runs on until it reaches its new limit or storage runs low, then stops. Now the pressure is above 100, nothing draws gas out, and the compressor would only restart below 60. The plant freezes. No alarm sounds, because the blowout needs 220. The only sign is that the "system running" indicator stays off.

That is why program changes are dangerous even without bad intent: a controller program encodes couplings that nobody wrote down.

</details>

## Detect and defend

A program download is ordinary engineering traffic. It uses the vendor's own tools and protocols, here a web upload to port 8080, so a network sensor cannot tell a legitimate change from a malicious one by looking at it. The CybICS IDS has no rule for program uploads; its web rule only counts login attempts.

Defenders therefore rely on process and integrity controls:

- **Change control.** Every program change is requested, reviewed and recorded. An unplanned download is then an incident by definition.
- **Integrity checks.** Compare the loaded program with a known-good copy, for example by its hash or file name. The challenge verifier does exactly this.
- **Access control.** Change the default OpenPLC login and restrict who can reach port 8080. See [Hardening credentials](/theory/defense_password) and [Host firewalling](/theory/defense_firewall).
- **Process monitoring.** A plant that behaves differently after a change, such as a valve that never opens, is a clue even when the screens look normal.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The plc_programming verifier needs the default `openplc` login to read the dashboard, and the OpenPLC credential-hardening challenge passes only once that login no longer works. Students who harden first will see "Cannot log into OpenPLC to verify the loaded program."

<figure class="wide">
<style>
.pg-o {--o: 16s;}
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
     aria-label="Two orderings of the same two tasks. Doing the program download first and hardening the OpenPLC password afterwards leaves both checks able to pass. Hardening the password first means the program check can no longer log into the controller, so it cannot read which program is loaded.">
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
<figcaption>The order matters: download first, harden afterwards. The coupling mirrors real change audits, where the evidence that a change happened often depends on the access the change was meant to remove.</figcaption>
</figure>

The file name is assigned at upload, so re-uploading an unchanged copy of the shipped program also passes. The check proves that a new upload is loaded and running, not that the logic differs. A good discussion question: how would you prove that it does?

</details>

## Before you start

- [PLCs and the scan cycle](/theory/plc-fundamentals) for how the controller runs its program.
- [The gas pressure process](/theory/physical_process) for what the program controls.
- [Stuxnet (2010)](/theory/stuxnet) for the real-world version of this attack.
