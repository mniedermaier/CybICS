# Man in the middle

A man-in-the-middle on an ICS network is rarely about reading the traffic. Modbus has nothing worth stealing &mdash; the interesting move is to lie in *both* directions at once: pass the operator's command through untouched so the plant really does what they asked, and rewrite the readings coming back so the screen says everything is fine.

## The two-sided lie

`training/mitm/mitm.py` is a Modbus TCP proxy. Requests go through it unchanged. Responses do not: it rewrites the register values on their way back, to a fixed table &mdash; GST to 200, HPT to 95, the system sensor to 1, manual mode to 0. Those are not random numbers. 95 sits inside the 50-to-100 band in which the plant reports itself healthy, and a system sensor reading 1 is the "operational" flag. The proxy is not hiding the process, it is painting a normal one.

<figure>
<style>
.mm-p {--d: 12s; --on:#ff6b00;}
html.light-mode .mm-p {--on:#b34700;}
/* Request and response are separate lanes because the attack is asymmetric:
   one direction is relayed, the other is rewritten. A still cannot show the
   value changing as it passes the middle. */
.mm-p .req  {animation: p-req var(--d) linear 20 forwards;}
.mm-p .rsp1 {animation: p-r1 var(--d) linear 20 forwards;}
.mm-p .rsp2 {opacity:1; animation: p-r2 var(--d) linear 20 forwards;}
.mm-p .truth{opacity:1; animation: p-show var(--d) steps(1,end) 20 forwards;}
@keyframes p-req {0%{transform:translateX(0); opacity:0} 4%{opacity:1}
                  30%{transform:translateX(320px); opacity:1}
                  33%,100%{transform:translateX(320px); opacity:0}}
@keyframes p-r1  {0%,38%{transform:translateX(0); opacity:0} 41%{opacity:1}
                  58%{transform:translateX(-165px); opacity:1}
                  60%,100%{transform:translateX(-165px); opacity:0}}
@keyframes p-r2  {0%,60%{transform:translateX(0); opacity:0} 62%{opacity:1}
                  82%{transform:translateX(-155px); opacity:1}
                  85%,100%{transform:translateX(-155px); opacity:0}}
@keyframes p-show{0%,84%{opacity:0} 85%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .mm-p *{animation:none !important}
  .mm-p .req,.mm-p .rsp1,.mm-p .rsp2{opacity:0}
  .mm-p .truth{opacity:1}
}
</style>
<svg class="mm-p" viewBox="0 0 460 210" role="img"
     aria-label="A Modbus read passes from the HMI through the attacker's proxy to the PLC unchanged. The PLC answers with the true pressure, 240. The proxy replaces it with 95 before forwarding, so the operator's screen reads 95 while the tank holds 240.">
  <rect x="14" y="60" width="92" height="44" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="60" y="80" text-anchor="middle" font-size="14" font-weight="bold">FUXA</text>
  <text x="60" y="96" text-anchor="middle" font-size="13" opacity="0.75">.0.4</text>
  <rect x="184" y="60" width="92" height="44" rx="6" fill="var(--on)"/>
  <text x="230" y="80" text-anchor="middle" font-size="14" style="fill:#1a1a1a" font-weight="bold">proxy</text>
  <text x="230" y="96" text-anchor="middle" font-size="13" style="fill:#1a1a1a">.0.100</text>
  <rect x="354" y="60" width="92" height="44" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="400" y="80" text-anchor="middle" font-size="14" font-weight="bold">OpenPLC</text>
  <text x="400" y="96" text-anchor="middle" font-size="13" opacity="0.75">.0.3</text>

  <text x="230" y="36" text-anchor="middle" font-size="13" opacity="0.7">request &mdash; relayed untouched</text>
  <g class="req">
    <rect x="112" y="40" width="66" height="18" rx="3" fill="var(--on)"/>
    <text x="145" y="53" text-anchor="middle" font-size="13" style="fill:#1a1a1a">read 1126</text>
  </g>

  <text x="230" y="130" text-anchor="middle" font-size="13" opacity="0.7">response &mdash; rewritten in the middle</text>
  <g class="rsp1">
    <rect x="282" y="136" width="62" height="18" rx="3" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-opacity="0.6"/>
    <text x="313" y="149" text-anchor="middle" font-size="13">240</text>
  </g>
  <g class="rsp2">
    <rect x="112" y="136" width="62" height="18" rx="3" fill="var(--on)"/>
    <text x="143" y="149" text-anchor="middle" font-size="13" style="fill:#1a1a1a">95</text>
  </g>
  <g class="truth" font-size="13">
    <text x="60" y="180" text-anchor="middle" fill="var(--on)" font-weight="bold">screen: 95</text>
    <text x="400" y="180" text-anchor="middle" opacity="0.85">tank: 240</text>
    <text x="230" y="200" text-anchor="middle" opacity="0.8">healthy band is 50 to 100</text>
  </g>
</svg>
<figcaption>The command the operator sends is honoured; only the answer is forged. That is what makes this different from a flood &mdash; the plant is not being driven anywhere by the attacker, it is being driven by an operator who has been given a false picture of where it already is.</figcaption>
</figure>

## Two ways in, and only one of them counts

The module gives two routes to the middle, and they are not equivalent.

The first is **ARP poisoning**: `arpspoof` or `ettercap` tells FUXA that the PLC's IP belongs to the attacker's MAC, and tells the PLC the same about FUXA. Traffic then goes through the attacker's machine without either endpoint noticing, because nothing in ARP asks for proof.

The second needs no poisoning at all. Log into FUXA as an administrator and edit the device: point its PLC connection at the proxy's address and port. The traffic arrives at the attacker because the operator's own configuration sends it there.

<figure>
<style>
.mm-a {--d: 10s; --on:#ff6b00;}
html.light-mode .mm-a {--on:#b34700;}
/* The cache entry is overwritten in place and the IDS's set only grows -- one
   address remembered with two MACs is the entire signature. */
.mm-a .old {animation: a-old var(--d) steps(1,end) 20 forwards;}
.mm-a .new {opacity:0; animation: a-new var(--d) steps(1,end) 20 forwards;}
.mm-a .m2  {opacity:0; animation: a-new var(--d) steps(1,end) 20 forwards;}
.mm-a .fire{opacity:0; animation: a-fire var(--d) steps(1,end) 20 forwards;}
@keyframes a-old {0%,34%{opacity:1} 35%,100%{opacity:0}}
@keyframes a-new {0%,34%{opacity:0} 35%,100%{opacity:1}}
@keyframes a-fire{0%,44%{opacity:0} 45%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .mm-a *{animation:none !important}
  .mm-a .old{opacity:0} .mm-a .new,.mm-a .m2,.mm-a .fire{opacity:1}
}
</style>
<svg class="mm-a" viewBox="0 0 460 136" role="img"
     aria-label="FUXA's ARP cache entry for the PLC's address is overwritten with the attacker's MAC. The IDS keeps a set of MACs per address; when the set for that address reaches two, rule 8 raises arp_spoof.">
  <text x="14" y="28" font-size="13" opacity="0.8">FUXA's ARP cache</text>
  <rect x="14" y="36" width="200" height="30" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="24" y="56" font-size="13" font-family="monospace">172.18.0.3</text>
  <text class="old" x="120" y="56" font-size="13" font-family="monospace" opacity="0.85">02:42:ac:12:00:03</text>
  <text class="new" x="120" y="56" font-size="13" font-family="monospace" fill="var(--on)" font-weight="bold">e6:44:65:dc:d5:ef</text>

  <text x="246" y="28" font-size="13" opacity="0.8">what the IDS remembers</text>
  <rect x="246" y="36" width="200" height="30" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="256" y="56" font-size="13" font-family="monospace">.0.3 &rarr; 1 MAC</text>
  <text class="m2" x="256" y="56" font-size="13" font-family="monospace" fill="var(--on)" font-weight="bold">.0.3 &rarr; 2 MACs</text>

  <text class="fire" x="14" y="96" font-size="14" fill="var(--on)" font-weight="bold">arp_spoof &mdash; one address, two MACs</text>
  <text x="14" y="124" font-size="13" opacity="0.8">No reply is verified, so the cache simply takes the last one it heard.</text>
</svg>
<figcaption>Rule 8 does not detect interception; it detects an address that has been seen with more than one MAC. It never removes a MAC from that set either, so the alert outlives the attack. That is why the configuration route is invisible to it &mdash; nobody lied about a MAC &mdash; and why a plain container restart, which also hands an address a new MAC, raises the same alert.</figcaption>
</figure>

That difference matters for the challenge, because `check_mitm_attack.py` asks the IDS one question: did `arp_spoof` fire? Its own docstring claims either route leaves a trace, but the proxy route leaves none it looks for. Take the configuration path and the attack works perfectly while the Verify button keeps telling you nothing was detected.

## The skill

Poison the two ARP tables, enable forwarding, run the proxy, and watch FUXA report a healthy plant while the tank climbs past it. The flag comes from the IDS having seen the poisoning, not from the deception succeeding &mdash; which is worth noticing, because the deception is the part that would matter.

> **MITRE ATT&CK for ICS:** T0830 Adversary-in-the-Middle and T0856 Spoof Reporting Message. The second is the one this attack is really about. Defence: static ARP entries, segmentation so the attacker is never on the same broadcast domain, and protocols that authenticate the endpoint rather than trusting the address.
