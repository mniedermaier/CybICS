# Defense in depth

No single control secures an ICS. The strategy is **defense in depth**: layered controls, so that getting past one still leaves an attacker facing the next. Two standards frame this for OT &mdash; **IEC 62443**, which groups assets into **zones** and controls the **conduits** between them, and **NIST SP 800-82**.

The usual picture is concentric rings: an attacker has to defeat each one in turn. That is a good picture of a building and a poor picture of a network, and this platform will show you why in about two minutes.

## A conduit is a list of ports, and lists have gaps

The *Network Segmentation* challenge asks you to stop the attack machine reaching the controllers. Its Solution gives you three rules.

<figure>
<style>
.article figure svg.dh-p {min-width: 360px;}
.dh-p {--p: 16s;}
/* One prober tries four doors in turn. Three are shut and one was never
   listed, so the animation is a sequence with an ending -- which is the whole
   argument and the thing a row of four static gates cannot make. */
.dh-p .prb {animation: dp-prb var(--p) cubic-bezier(.4,0,.2,1) infinite;}
.dh-p .g1 {animation: dp-g1 var(--p) steps(1,end) infinite;}
.dh-p .g2 {animation: dp-g2 var(--p) steps(1,end) infinite;}
.dh-p .g3 {animation: dp-g3 var(--p) steps(1,end) infinite;}
.dh-p .g4 {animation: dp-g4 var(--p) steps(1,end) infinite;}
/* The base state is the fourth door, the one that is open. */
.dh-p .prb {transform: translateY(129px);}
.dh-p .g1,.dh-p .g2,.dh-p .g3 {opacity:0;}
.dh-p .g4 {opacity:1;}
@keyframes dp-prb {0%,20%{transform:translateY(0)}      25%,45%{transform:translateY(43px)}
                   50%,70%{transform:translateY(86px)}  75%,100%{transform:translateY(129px)}}
@keyframes dp-g1 {0%,24.9%{opacity:1} 25%,100%{opacity:0}}
@keyframes dp-g2 {0%,24.9%{opacity:0} 25%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes dp-g3 {0%,49.9%{opacity:0} 50%,74.9%{opacity:1} 75%,100%{opacity:0}}
@keyframes dp-g4 {0%,74.9%{opacity:0} 75%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dh-p * {animation:none !important;} }
</style>
<svg class="dh-p" viewBox="0 0 360 238" role="img"
     aria-label="The attack machine probes four ports on the control zone in turn. Port 8080, the OpenPLC web interface, is dropped by rule. Port 502, Modbus, is dropped by rule. Port 4840, OPC-UA, is dropped by rule. Port 102, the S7 server, has no rule at all, because the challenge's own solution lists only the first three, and the probe goes straight through to the same memory word Modbus would have reached.">
  <text x="8" y="18" font-size="12" font-weight="bold">the attack machine tries four doors</text>
  <g class="prb"><rect x="8" y="28" width="78" height="26" rx="4" fill="#ff6b00"/>
    <text x="47" y="45" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">172.18.0.100</text></g>
  <g font-size="12">
    <text x="96" y="45">:8080 &rarr; OpenPLC web</text>
    <text x="96" y="88">:502 &rarr; Modbus</text>
    <text x="96" y="131">:4840 &rarr; OPC-UA</text>
    <text x="96" y="174">:102 &rarr; S7comm</text>
  </g>
  <g font-size="12" font-weight="bold">
    <text class="g1" x="352" y="45" text-anchor="end">DROP</text>
    <text class="g2" x="352" y="88" text-anchor="end">DROP</text>
    <text class="g3" x="352" y="131" text-anchor="end">DROP</text>
    <text class="g4" x="352" y="174" text-anchor="end" fill="#ff6b00">no rule &mdash; through</text>
  </g>
  <g stroke="currentColor" stroke-opacity="0.45" stroke-dasharray="3 3">
    <line x1="90" y1="41" x2="352" y2="41"/><line x1="90" y1="84" x2="352" y2="84"/>
    <line x1="90" y1="127" x2="352" y2="127"/><line x1="90" y1="170" x2="352" y2="170"/>
  </g>
  <text x="8" y="206" font-size="11" opacity="0.85">Three rules written. The plant answers on four ports,</text>
  <text x="8" y="222" font-size="11" opacity="0.85">and S7 reaches the same memory word Modbus would have.</text>
</svg>
<figcaption>The Solution in <code>training/defense_network/README.md</code> writes one rule per port: 8080 and 502 on OpenPLC, 4840 on OPC-UA. OpenPLC also answers S7comm on 102, where the same pressure register is <code>DB1002.DBW204</code> &mdash; verified against the running stack, it returns the same value as Modbus register 1126. Follow the Solution exactly and the challenge passes with the controller still writable.</figcaption>
</figure>

The challenge's *Steps* do not have this problem: they tell you to write `iptables -A INPUT -s 172.18.0.100 -j DROP`, with no port at all, which closes everything. Two routes through the same exercise, one of which leaves a door open, and both of which are marked correct.

## Which is a statement about the check, not about you

<figure>
<style>
.article figure svg.dh-v {min-width: 360px;}
.dh-v {--v: 14s;}
/* The scanner walks the rule table line by line and stops on the first line
   that satisfies it. Running it over two different tables, one after the
   other, is the point: the stop happens at the same moment in both. */
.dh-v .scan {animation: dv-scan var(--v) steps(1,end) infinite;}
.dh-v .tblA {animation: dv-a var(--v) steps(1,end) infinite;}
.dh-v .tblB {animation: dv-b var(--v) steps(1,end) infinite;}
.dh-v .ok   {animation: dv-ok var(--v) steps(1,end) infinite;}
.dh-v .scan {transform: translateY(26px);}
.dh-v .tblA {opacity:0;}
.dh-v .tblB {opacity:1;}
.dh-v .ok   {opacity:1;}
@keyframes dv-scan {0%,7%{transform:translateY(0)}   10%,20%{transform:translateY(13px)}
                    23%,43%{transform:translateY(26px)}
                    50%,57%{transform:translateY(0)}  60%,70%{transform:translateY(13px)}
                    73%,100%{transform:translateY(26px)}}
@keyframes dv-a {0%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes dv-b {0%,49.9%{opacity:0} 50%,100%{opacity:1}}
@keyframes dv-ok {0%,22.9%{opacity:0} 23%,49.9%{opacity:1}
                  50%,72.9%{opacity:0} 73%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dh-v * {animation:none !important;} }
</style>
<svg class="dh-v" viewBox="0 0 360 202" role="img"
     aria-label="The segmentation verifier reads the output of iptables -L INPUT -n and stops at the first line that contains the attack machine's address together with DROP. It is shown running over two different rule tables. The first is a single blanket DROP, which closes every port. The second is three per-port rules, which leaves port 102 open. The verifier stops on the third line in both cases and reports the same pass, because it is matching text, not testing reachability.">
  <text x="8" y="18" font-size="12" font-weight="bold">what the segmentation check reads</text>
  <text x="8" y="36" font-size="11" opacity="0.85" font-family="monospace">iptables -L INPUT -n</text>
  <rect class="scan" x="8" y="48" width="280" height="14" rx="3" fill="#ff6b00" fill-opacity="0.30" stroke="#ff6b00"/>
  <g font-family="monospace" font-size="11">
    <g class="tblA">
      <text x="12" y="59">Chain INPUT (policy ACCEPT)</text>
      <text x="12" y="72">target prot source</text>
      <text x="12" y="85">DROP   all  172.18.0.100</text>
    </g>
    <g class="tblB">
      <text x="12" y="59">DROP  tcp  172.18.0.100  dpt:8080</text>
      <text x="12" y="72">DROP  tcp  172.18.0.100  dpt:502</text>
      <text x="12" y="85">DROP  tcp  172.18.0.100  dpt:4840</text>
    </g>
  </g>
  <text class="ok" x="8" y="112" font-size="12" font-weight="bold" fill="#ff6b00">line contains the address and DROP &rarr; pass</text>

  <text x="8" y="142" font-size="11" opacity="0.85">Both tables pass. One of them closes port 102 and the other</text>
  <text x="8" y="158" font-size="11" opacity="0.85">does not. The check never opens a socket, so it cannot tell.</text>
  <text x="8" y="184" font-size="11" opacity="0.85">The password check does open one, and fails you if the old</text>
  <text x="8" y="198" font-size="11" opacity="0.85">credential still works.</text>
</svg>
<figcaption><code>_check_iptables_rule</code> runs <code>iptables -L INPUT -n</code> in each target container and returns true for the first line containing the attack machine&rsquo;s address and either DROP or REJECT. No port is compared, and nothing is connected to. <code>check_openplc_password.py</code> is the opposite: it posts the default credential to the login form and passes only when that attempt fails. Same word, &ldquo;verified&rdquo;, two very different promises.</figcaption>
</figure>

## The four controls, and what each check actually proves

| Control | What you do | What the check proves | Standard |
|---|---|---|---|
| Remove default credentials | change the OpenPLC and FUXA passwords | that the old credential no longer works &mdash; it tries it | IEC 62443 SR 1.1; NIST IA-5 |
| Restrict Modbus | iptables so only `hwio` and FUXA reach port 502 | that a DROP rule exists **and** that port 502 refuses a connection from an unauthorised host | SR 5.1; NIST SC-7 |
| Network segmentation | block the attack host from the controllers | only that some rule mentioning the attack host exists | SR 5.1; NIST SC-7 |
| Keep the IDS effective | detection stays running and tuned | that the IDS process is up | NIST SI-4 |

Two of the four test an outcome and two test a configuration. That is not a criticism of the exercises &mdash; testing an outcome is often expensive, and a configuration check is what most real audits are &mdash; but it is the difference between knowing a door is shut and reading a note that says it should be.

## Rings are the wrong picture

The concentric-ring drawing implies that an attacker must defeat every layer in turn. On a network they rarely have to. Each control guards a *path*, and an attacker needs one path, not all of them. The Modbus firewall does not help if S7 is open; strong OpenPLC passwords do not help if the register is writable without logging in at all, which is exactly what *Flood &amp; Overwrite* demonstrates.

What survives from the ring picture, and it is the important half: **monitoring is the one layer that does not have to stop anything.** Whatever path an attacker takes, if it is watched, the attempt is recorded. That is why the *Detect Modbus Flooding* and *IDS Evasion* challenges sit where they do, and why the ICS answer to "which control matters most" is usually the one that sees rather than the one that blocks.

## The mindset

Assume any single control can fail, and assume your evidence that it works is weaker than it looks. Design so a failure is contained and observed. In OT this is balanced against availability &mdash; a lockout or a dropped packet must never endanger the process &mdash; which is why segmentation and monitoring, rather than intrusive blocking, are the workhorses of ICS defense.

And when a check passes, ask what it looked at. On this platform you can answer that question by reading forty lines of Python, which is a luxury you will not usually have.
