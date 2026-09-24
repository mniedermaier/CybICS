# Man in the middle

A man-in-the-middle on an ICS network is rarely about reading the traffic. Modbus carries nothing worth stealing &mdash; the interesting move is to lie in *both* directions at once: pass the operator's command through untouched so the plant really does what they asked, and rewrite the readings coming back so the screen says everything is fine.

## The two-sided lie

`training/mitm/mitm.py` is a Modbus TCP proxy. Requests go through it byte for byte &mdash; `manipulate_request` returns its input unchanged. Responses do not. It rewrites four holding registers on their way back (GST to 200, HPT to 95, the system sensor to 1, manual mode to 0) and two coils (compressor and system valve, both to 1).

Those choices hang together. 95 sits inside the 50-to-100 band, and `sysSen` is only set when the pressure is in that band *and* the system valve is open &mdash; so forging the sensor without also forging the valve coil would give the operator a reading that contradicts itself. GST 200 does not read "normal"; the plant's own classifier calls anything above 150 **Full**, which is the point: a well-stocked supply is one fewer thing to wonder about. And `manual` back to 0 hides the mode switch that made the rest of it possible.

<figure>
<style>
.mm-p {--d: 12s; --on:#ff6b00; --onink:#1a1a1a;}
html.light-mode .mm-p {--on:#b34700; --onink:#ffffff;}
/* Request and response are separate lanes because the attack is asymmetric:
   one direction is relayed, the other is rewritten. The handover from the
   true value to the forged one happens inside the proxy rect, which is the
   only place it can honestly be drawn. */
.mm-p .req  {opacity:0; animation: p-req var(--d) linear 20 forwards;}
.mm-p .rsp1 {transform:translateX(-92px); animation: p-r1 var(--d) linear 20 forwards;}
.mm-p .rsp2 {transform:translateX(-84px); animation: p-r2 var(--d) linear 20 forwards;}
.mm-p .truth{animation: p-show var(--d) steps(1,end) 20 forwards;}
@keyframes p-req {0%{transform:translateX(0); opacity:1} 30%{transform:translateX(244px); opacity:1}
                  33%,100%{transform:translateX(244px); opacity:0}}
@keyframes p-r1  {0%,36%{transform:translateX(0); opacity:0} 38%{opacity:1}
                  58%,100%{transform:translateX(-92px); opacity:1}}
@keyframes p-r2  {0%,58%{transform:translateX(0); opacity:0} 60%{opacity:1}
                  82%,100%{transform:translateX(-84px); opacity:1}}
@keyframes p-show{0%,58%{opacity:0} 60%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .mm-p *{animation:none !important}
  .mm-p .req{opacity:0}
  .mm-p .rsp1{transform:translateX(-92px)} .mm-p .rsp2{transform:translateX(-84px)}
}
</style>
<svg class="mm-p" viewBox="0 0 460 206" role="img"
     aria-label="A Modbus read passes from FUXA through the attacker's proxy to OpenPLC unchanged. OpenPLC answers with the true pressure, 240. The proxy replaces it with 95 inside itself before forwarding, so the operator's screen reads 95 while the tank holds 240.">
  <rect x="14" y="60" width="92" height="44" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="60" y="80" text-anchor="middle" font-size="14" font-weight="bold">FUXA</text>
  <text x="60" y="96" text-anchor="middle" font-size="13" opacity="0.75">.0.4</text>
  <rect x="184" y="60" width="92" height="44" rx="6" fill="var(--on)"/>
  <text x="230" y="80" text-anchor="middle" font-size="14" style="fill:var(--onink)" font-weight="bold">proxy</text>
  <text x="230" y="96" text-anchor="middle" font-size="13" style="fill:var(--onink)">.0.100</text>
  <rect x="354" y="60" width="92" height="44" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="400" y="80" text-anchor="middle" font-size="14" font-weight="bold">OpenPLC</text>
  <text x="400" y="96" text-anchor="middle" font-size="13" opacity="0.75">.0.3</text>

  <text x="230" y="34" text-anchor="middle" font-size="13" opacity="0.7">request &mdash; relayed byte for byte</text>
  <g class="req">
    <rect x="112" y="40" width="66" height="18" rx="3" fill="var(--on)"/>
    <text x="145" y="53" text-anchor="middle" font-size="13" style="fill:var(--onink)">read 1126</text>
  </g>

  <text x="230" y="128" text-anchor="middle" font-size="13" opacity="0.7">response &mdash; rewritten inside the proxy</text>
  <g class="rsp1">
    <rect x="282" y="134" width="62" height="18" rx="3" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-opacity="0.6"/>
    <text x="313" y="147" text-anchor="middle" font-size="13">240</text>
  </g>
  <g class="rsp2">
    <rect x="196" y="134" width="62" height="18" rx="3" fill="var(--on)"/>
    <text x="227" y="147" text-anchor="middle" font-size="13" style="fill:var(--onink)">95</text>
  </g>
  <g class="truth" font-size="13">
    <text x="60" y="176" text-anchor="middle" fill="var(--on)" font-weight="bold">screen: 95</text>
    <text x="400" y="176" text-anchor="middle" opacity="0.85">tank: 240</text>
    <text x="230" y="196" text-anchor="middle" opacity="0.8">healthy band is 50 to 100</text>
  </g>
</svg>
<figcaption>The true answer reaches the proxy and the forged one leaves it; the substitution happens in the middle, which is the whole of the attack. Note the precondition, though: the proxy never touches <code>hwio</code>, and in automatic mode the compressor stops at 90. A tank at 240 means somebody has already driven the plant out of band by hand &mdash; the proxy's job is to hide that, which is exactly why its table puts <code>manual</code> back to 0.</figcaption>
</figure>

## Two ways in, and they win different things

The module gives two ways to reach the middle. It presents the second as a prerequisite, but it is a complete alternative, and the two are not equivalent.

**ARP poisoning.** `arpspoof` or `ettercap` tells FUXA that the PLC's address belongs to the attacker's MAC, and tells the PLC the same about FUXA. Nothing in ARP asks for proof, so both caches simply believe the last thing they heard. Traffic now crosses the attacker's machine &mdash; but with forwarding enabled and no redirection rule it is routed straight on to OpenPLC. `mitm.py` listens on port 5020, and there is no `iptables ... REDIRECT --to-port 5020` anywhere in the repository. On this route the proxy is a bystander: the poisoning is real, the interception is not.

**Repointing FUXA.** Log in as an administrator and edit the device: point its PLC connection at the proxy's address and port. No ARP is touched; the traffic arrives at the attacker because the operator's own configuration sends it there. This is the route that actually feeds the proxy.

<figure>
<style>
.mm-a {--d: 11s; --on:#ff6b00;}
html.light-mode .mm-a {--on:#b34700;}
/* The resting state is the detected one, because that is what the caption
   under the figure describes. The keyframes replay the "before" at the start
   of each cycle rather than the other way round. */
.mm-a .old,.mm-a .m1 {opacity:0; animation: a-old var(--d) steps(1,end) 20 forwards;}
.mm-a .new,.mm-a .m2 {animation: a-new var(--d) steps(1,end) 20 forwards;}
.mm-a .fire{animation: a-fire var(--d) steps(1,end) 20 forwards;}
@keyframes a-old {0%,34%{opacity:1} 35%,100%{opacity:0}}
@keyframes a-new {0%,34%{opacity:0} 35%,100%{opacity:1}}
@keyframes a-fire{0%,44%{opacity:0} 45%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .mm-a *{animation:none !important}
  .mm-a .old,.mm-a .m1{opacity:0}
  .mm-a .new,.mm-a .m2,.mm-a .fire{opacity:1}
}
</style>
<svg class="mm-a" viewBox="0 0 460 128" role="img"
     aria-label="FUXA's ARP cache entry for the PLC's address is overwritten with the attacker's MAC. The IDS keeps a set of MACs per address; when the set for that address reaches two, rule 8 raises arp_spoof.">
  <text x="14" y="28" font-size="13" opacity="0.8">FUXA's ARP cache for .0.3</text>
  <rect x="14" y="36" width="238" height="30" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.6"/>
  <text class="old" x="26" y="56" font-size="13" font-family="monospace" opacity="0.85">d6:10:7c:61:8a:64</text>
  <text class="new" x="26" y="56" font-size="13" font-family="monospace" fill="var(--on)" font-weight="bold">c6:76:2b:3f:44:40</text>
  <text x="166" y="56" font-size="13" opacity="0.6">last heard</text>

  <text x="276" y="28" font-size="13" opacity="0.8">the IDS remembers</text>
  <rect x="276" y="36" width="170" height="30" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.6"/>
  <text class="m1" x="288" y="56" font-size="13" font-family="monospace">1 MAC</text>
  <text class="m2" x="288" y="56" font-size="13" font-family="monospace" fill="var(--on)" font-weight="bold">2 MACs</text>

  <text class="fire" x="14" y="92" font-size="14" fill="var(--on)" font-weight="bold">arp_spoof &mdash; one address, two MACs</text>
  <text x="14" y="116" font-size="13" opacity="0.8">Nothing in the cache is verified; nothing in the set is ever removed.</text>
</svg>
<figcaption>Rule 8 does not detect interception &mdash; it detects an address that has been seen with more than one MAC. That is why the configuration route is invisible to it, nobody having lied about a MAC, and why a plain container restart raises the same alert: Docker hands out a fresh random MAC each time, and the set is never emptied, so the alert outlives both the attack and the container.</figcaption>
</figure>

That split matters for the challenge, because `check_mitm_attack.py` asks the IDS one question: did `arp_spoof` fire? Its docstring claims either route leaves a trace. The proxy route leaves none it looks for &mdash; and in fact none at all, because the proxy's upstream is on the `172.17.0.0/16` docker0 network while the IDS captures `172.18.0.0/24`. So the ARP route wins the flag without deceiving anyone, and the configuration route deceives the operator without winning the flag. Joining them takes the redirection rule the module never gives you.

Why ARP accepts anyone's word for it is worth a sentence of its own: the protocol dates from 1982, when the machines that could answer were the ones you had cabled up yourself. There was no threat model in which a reply might be a lie, so no field was reserved for proving it was not &mdash; and by the time that mattered, every stack on earth had shipped.

## The skill

Poison the two ARP tables and the IDS will see it; that is what the flag is scored on. To see the deception itself you need the traffic to actually enter the proxy, which means either repointing FUXA or adding the redirection rule yourself. The flag and the lesson are not in the same place here, which is worth knowing before you spend an hour wondering why nothing on the screen changed.

> **MITRE ATT&CK for ICS:** T0830 Adversary-in-the-Middle, and for the forged readings **T1692.002 Reporting Message** (Evasion / Impair Process Control). The module still cites T0856 Spoof Reporting Message, which the catalogue has since superseded &mdash; that page now serves only a redirect. Defence: static ARP entries, segmentation so the attacker is never on the same broadcast domain, and protocols that authenticate the endpoint rather than trusting the address.
