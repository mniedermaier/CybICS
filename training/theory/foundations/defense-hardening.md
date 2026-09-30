# Defense in depth

No single control secures an ICS. The strategy is **defense in depth**: layered controls, so that getting past one still leaves an attacker facing the next. Two standards frame this for OT &mdash; **IEC 62443**, which groups assets into **zones** and controls the **conduits** between them, and **NIST SP 800-82**.

The usual picture is concentric rings: an attacker has to defeat each one in turn. That is a good picture of a building and a poor picture of a network, and this platform will show you why in about two minutes.

## A conduit is a list of ports, and lists have gaps

The *Network Segmentation* challenge asks you to stop the attack machine reaching the controllers. Its Solution gives you three rules.

<figure>
<style>
.article figure svg.dh-p {min-width: 388px;}
.dh-p {--p: 18s;}
/* The verdicts accumulate rather than replacing each other, so the figure
   ends on the whole comparison -- which is also what a reader gets when the
   animation is switched off. Replacing them meant the still showed one
   verdict and five dashed leaders pointing at nothing. */
.dh-p .prb {animation: dp-prb var(--p) cubic-bezier(.4,0,.2,1) infinite;}
.dh-p .g1 {animation: dp-g1 var(--p) steps(1,end) infinite;}
.dh-p .g2 {animation: dp-g2 var(--p) steps(1,end) infinite;}
.dh-p .g3 {animation: dp-g3 var(--p) steps(1,end) infinite;}
.dh-p .g4 {animation: dp-g4 var(--p) steps(1,end) infinite;}
.dh-p .g5 {animation: dp-g5 var(--p) steps(1,end) infinite;}
.dh-p .g6 {animation: dp-g6 var(--p) steps(1,end) infinite;}
.dh-p .prb {transform: translateY(175px);}
/* The leader lines are the only thing tying a port to its verdict across the
   gap, so they are graphics that carry meaning: at 0.45 they measured 2.69:1
   on white. */
.dh-p .ldr {stroke:currentColor; stroke-opacity:0.7; stroke-dasharray:3 3;}
@keyframes dp-prb {0%,13%{transform:translateY(0)}     16.7%,30%{transform:translateY(35px)}
                   33.3%,46%{transform:translateY(70px)}  50%,63%{transform:translateY(105px)}
                   66.7%,80%{transform:translateY(140px)} 83.3%,100%{transform:translateY(175px)}}
@keyframes dp-g1 {0%,13%{opacity:0} 13.1%,100%{opacity:1}}
@keyframes dp-g2 {0%,29.9%{opacity:0} 30%,100%{opacity:1}}
@keyframes dp-g3 {0%,46.5%{opacity:0} 46.6%,100%{opacity:1}}
@keyframes dp-g4 {0%,63.2%{opacity:0} 63.3%,100%{opacity:1}}
@keyframes dp-g5 {0%,79.9%{opacity:0} 80%,100%{opacity:1}}
@keyframes dp-g6 {0%,96.5%{opacity:0} 96.6%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dh-p * {animation:none !important;} }
</style>
<svg class="dh-p" viewBox="0 0 360 280" role="img"
     aria-label="The attack machine probes six service ports in turn. Port 8080, the OpenPLC web interface, and port 502, Modbus, are dropped by the solution's rules on the OpenPLC container, and port 4840 is dropped on the OPC-UA container. Ports 102 for S7comm, 20000 for DNP3 and 44818 for EtherNet slash IP have no rule at all, because the solution lists only the first three. All six verdicts stay on screen once reached, so the figure ends showing three doors shut and three open.">
  <text x="8" y="18" font-size="12" font-weight="bold">the attack machine tries every listening port</text>
  <g class="prb"><rect x="8" y="32" width="78" height="26" rx="4" fill="#ff6b00"/>
    <text x="47" y="49" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">172.18.0.100</text></g>
  <g font-size="12">
    <text x="96" y="45">:8080 &rarr; web UI</text>
    <text x="96" y="80">:502 &rarr; Modbus</text>
    <text x="96" y="115">:4840 &rarr; OPC-UA</text>
    <text x="96" y="150">:102 &rarr; S7comm</text>
    <text x="96" y="185">:20000 &rarr; DNP3</text>
    <text x="96" y="220">:44818 &rarr; EtherNet/IP</text>
  </g>
  <g class="ldr">
    <line x1="90" y1="53" x2="344" y2="53"/><line x1="90" y1="88" x2="344" y2="88"/>
    <line x1="90" y1="123" x2="344" y2="123"/><line x1="90" y1="158" x2="344" y2="158"/>
    <line x1="90" y1="193" x2="344" y2="193"/><line x1="90" y1="228" x2="344" y2="228"/>
  </g>
  <g font-size="12" font-weight="bold" text-anchor="end">
    <text class="g1" x="344" y="45">DROP</text>
    <text class="g2" x="344" y="80">DROP</text>
    <text class="g3" x="344" y="115">DROP</text>
    <text class="g4" x="344" y="150" fill="#ff6b00">open</text>
    <text class="g5" x="344" y="185" fill="#ff6b00">open</text>
    <text class="g6" x="344" y="220" fill="#ff6b00">open</text>
  </g>
  <text x="8" y="252" font-size="11" opacity="0.85">Three rules written. Six ports answering. The three left open</text>
  <text x="8" y="268" font-size="11" opacity="0.85">all reach the same controller memory.</text>
</svg>
<figcaption>The Solution in <code>training/defense_network/README.md</code> writes one rule per port: 8080 and 502 on OpenPLC, 4840 on OPC-UA. That container is also listening on 102, 20000 and 44818 &mdash; S7comm, DNP3 and EtherNet/IP &mdash; and OpenPLC publishes the same memory through all of them. The pressure register is <code>DB1002.DBW204</code> over S7, and on the running stack it returns what Modbus register 1126 returns. Follow the Solution exactly and the challenge passes with the controller still writable three ways.</figcaption>
</figure>

The challenge's *Steps* do not have this problem: they tell you to write `iptables -A INPUT -s 172.18.0.100 -j DROP`, with no port at all, which closes everything. Two routes through the same exercise, one of which leaves a door open, and both of which are marked correct.

## Which is a statement about the check, not about you

<figure>
<style>
.article figure svg.dh-v {min-width: 388px;}
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
     aria-label="The segmentation verifier reads the output of iptables -L INPUT -n and stops at the first line that contains the attack machine's address together with DROP. It is shown running over the OpenPLC container's rule table twice. The first version is a single blanket DROP, which closes every port. The second is the solution's per-port rule, which closes only the port it names. The verifier stops on the same line in both cases and reports the same pass, because it is matching text rather than testing reachability.">
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
      <text x="12" y="59">Chain INPUT (policy ACCEPT)</text>
      <text x="12" y="72">target prot source</text>
      <text x="12" y="85">DROP   6    172.18.0.100  dpt:8080</text>
    </g>
  </g>
  <text class="ok" x="8" y="112" font-size="12" font-weight="bold" fill="#ff6b00">line contains the address and DROP &rarr; pass</text>

  <text x="8" y="142" font-size="11" opacity="0.85">Both pass. One closes every port, the other closes one.</text>
  <text x="8" y="158" font-size="11" opacity="0.85">The check never opens a socket, so it cannot tell them apart.</text>
  <text x="8" y="184" font-size="11" opacity="0.85">The password check does open one, and fails you if the old</text>
  <text x="8" y="198" font-size="11" opacity="0.85">credential still works.</text>
</svg>
<figcaption><code>_check_iptables_rule</code> runs <code>iptables -L INPUT -n</code> in each target container and returns true for the first line containing the attack machine&rsquo;s address and either DROP or REJECT. No port is compared, and nothing is connected to. The check also runs per container, so the OPC-UA rule never appears in this listing at all. <code>check_openplc_password.py</code> is the opposite kind of test: it posts the default credential to the login form and passes only when that attempt fails. Same word, &ldquo;verified&rdquo;, two very different promises.</figcaption>
</figure>

## Four controls, five checks, and what each one actually proves

| Control | What you do | What the check proves | Standard |
|---|---|---|---|
| Remove default credentials | change the OpenPLC and FUXA passwords | that the old credential no longer works &mdash; it tries it | IEC 62443 SR 1.5; NIST IA-5 |
| Restrict Modbus | iptables so only `hwio` and FUXA reach port 502 | that a DROP rule exists **and** that port 502 refuses a connection from an unauthorised host | SR 5.2; NIST SC-7 |
| Network segmentation | block the attack host from the controllers | only that some rule mentioning the attack host exists | SR 5.1; NIST SC-7 |
| Keep the IDS effective | detection stays running and tuned | that the IDS answers `/health`, reports itself active, **and** that at least three distinct rules have non-zero hit counts | NIST SI-4 |

Three of the four test an outcome and one tests a configuration &mdash; and the one that tests a configuration is the same exercise whose Steps and Solution disagree. That is not a criticism of the exercises: testing an outcome is often expensive, and a configuration check is what most real audits are. There is even a reason for it here. `docker exec … iptables -L` is cheap and works from anywhere, while a socket test can only probe from wherever the checker happens to be &mdash; which is why the Modbus row's socket test runs from the host-networked landing container and would not notice a rule that blocks only the attack machine.

## Rings are the wrong picture

The concentric-ring drawing implies that an attacker must defeat every layer in turn. On a network they rarely have to. Each control guards a *path*, and an attacker needs one path, not all of them. The Modbus firewall does not help if S7 is open; strong OpenPLC passwords do not help if the register is writable without logging in at all, which is exactly what *Flood &amp; Overwrite* demonstrates.

What survives from the ring picture, and it is the important half: **monitoring is the one layer that does not have to stop anything.** Whatever path an attacker takes, if it is watched, the attempt is recorded. That is why the *Detect Modbus Flooding* and *IDS Evasion* challenges sit where they do, and why the ICS answer to "which control matters most" is usually the one that sees rather than the one that blocks.

## The mindset

Assume any single control can fail, and assume your evidence that it works is weaker than it looks. Design so a failure is contained and observed. In OT this is balanced against availability &mdash; a lockout or a dropped packet must never endanger the process &mdash; which is why segmentation and monitoring, rather than intrusive blocking, are the workhorses of ICS defense.

And when a check passes, ask what it looked at. On this platform you can answer it by reading thirteen lines of Python &mdash; `_check_iptables_rule` is that short &mdash; which is a luxury you will not usually have.
