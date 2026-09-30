# Man in the middle

A man-in-the-middle on an ICS network is rarely about reading the traffic. Modbus carries nothing worth stealing &mdash; the interesting move is to lie in one direction only: let the operator's commands through so the plant really does what they asked, and rewrite the readings coming back so the screen says everything is fine.

## Relaying a request is not doing nothing

`training/mitm/mitm.py` is a Modbus TCP proxy, and its loop is strictly one request, one response, forever. The request leaves with the same bytes it arrived with: `manipulate_request` returns its input unmodified, and the two functions it hands the request to take a private copy before they touch anything. But they are not idle. They read the request and write down what they learn from it.

They have to. A Modbus read response carries no addresses at all &mdash; a byte count, then the values, in the order they were asked for. By the time the answer comes back there is nothing in it to say which of those numbers is the pressure. Only the request knew, and the request is gone. So the proxy parses it, works out which slot each target register will occupy in the coming answer, and pushes that little map onto a queue. The response pass pops the map and patches by position.

<figure>
<style>
.article figure svg.mm-q {min-width: 488px;}
.mm-q {--d: 14s; --on:#ff6b00; --onink:#1a1a1a;}
html.light-mode .mm-q {--on:#b34700; --onink:#ffffff;}
/* One poll, in order, on one clock. The point is the handover: the note is
   written while the request is passing through and spent when the answer
   passes back, so the queue is empty again before the next poll begins.
   A still can show the proxy or the queue, but not that they alternate. */
.mm-q .req  {animation: q-req var(--d) linear infinite;}
.mm-q .card {opacity:0; animation: q-card var(--d) steps(1,end) infinite;}
.mm-q .mt   {opacity:1; animation: q-mt var(--d) steps(1,end) infinite;}
.mm-q .rs1  {opacity:0; animation: q-rs1 var(--d) linear infinite;}
.mm-q .rs2  {opacity:0; animation: q-rs2 var(--d) linear infinite;}
.mm-q .scr  {opacity:0; animation: q-scr var(--d) steps(1,end) infinite;}
@keyframes q-req  {0%{transform:translateX(0); opacity:1}
                   36%{transform:translateX(236px); opacity:1}
                   40%,100%{transform:translateX(236px); opacity:0}}
/* The chip's centre starts at 160 and the proxy's is 230, so it is over the
   proxy 70/236 of the way through a 36% travel -- 10.7%, not a guess. */
@keyframes q-card {0%,10.6%{opacity:0} 10.7%,61.9%{opacity:1} 62%,100%{opacity:0}}
@keyframes q-mt   {0%,10.6%{opacity:1} 10.7%,61.9%{opacity:0} 62%,100%{opacity:1}}
@keyframes q-rs1  {0%,40%{transform:translateX(0); opacity:0}
                   42%{transform:translateX(0); opacity:1}
                   60%{transform:translateX(-102px); opacity:1}
                   62%,100%{transform:translateX(-102px); opacity:0}}
@keyframes q-rs2  {0%,60%{transform:translateX(0); opacity:0}
                   62%{transform:translateX(0); opacity:1}
                   80%,100%{transform:translateX(-160px); opacity:1}}
@keyframes q-scr  {0%,79.9%{opacity:0} 80%,100%{opacity:1}}
/* Without motion the three stages cannot follow one another, so they are
   shown at once: the request on its way out, the note it left behind, and
   both versions of the answer. The lanes do not overlap at these offsets. */
@media (prefers-reduced-motion: reduce){
  .mm-q *{animation:none !important}
  .mm-q .req{opacity:1; transform:translateX(0)}
  .mm-q .rs1{opacity:1; transform:translateX(0)}
  .mm-q .rs2{opacity:1; transform:translateX(-160px)}
  .mm-q .card{opacity:1} .mm-q .mt{opacity:0}
  .mm-q .scr{opacity:1}
}
</style>
<svg class="mm-q" viewBox="0 0 460 274" role="img"
     aria-label="One FUXA poll crossing the attacker's proxy. The request, a read of eleven holding registers from 1124, is relayed to OpenPLC unchanged, but as it passes the proxy writes a note into its queue saying that GST will arrive in slot 0, HPT in slot 2, manual in slot 6 and the system sensor in slot 8. OpenPLC answers with the true values, GST 184 and HPT 58. The proxy pops the note, patches those slots to 200 and 95, and forwards the answer. The queue is empty again before the next poll.">
  <text x="14" y="20" font-size="12" font-weight="bold">one poll: relayed one way, rewritten the other</text>

  <rect x="14" y="84" width="92" height="44" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="60" y="104" text-anchor="middle" font-size="14" font-weight="bold">FUXA</text>
  <text x="60" y="120" text-anchor="middle" font-size="12" opacity="0.8">.0.4</text>
  <rect x="184" y="84" width="92" height="44" rx="6" fill="var(--on)"/>
  <text x="230" y="104" text-anchor="middle" font-size="14" style="fill:var(--onink)" font-weight="bold">proxy</text>
  <text x="230" y="120" text-anchor="middle" font-size="12" style="fill:var(--onink)">.0.100</text>
  <rect x="354" y="84" width="92" height="44" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.6"/>
  <text x="400" y="104" text-anchor="middle" font-size="14" font-weight="bold">OpenPLC</text>
  <text x="400" y="120" text-anchor="middle" font-size="12" opacity="0.8">.0.3</text>

  <text x="230" y="40" text-anchor="middle" font-size="12" opacity="0.8">request &mdash; relayed byte for byte</text>
  <g class="req">
    <rect x="110" y="46" width="100" height="22" rx="3" fill="none" stroke="var(--on)" stroke-width="1.5"/>
    <text x="160" y="61" text-anchor="middle" font-size="12" fill="var(--on)" font-weight="bold">read 1124 &times; 11</text>
  </g>

  <text x="230" y="150" text-anchor="middle" font-size="12" opacity="0.8">response &mdash; patched by slot, inside the proxy</text>
  <g class="rs1">
    <rect x="272" y="158" width="132" height="22" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="338" y="173" text-anchor="middle" font-size="11" font-family="monospace">1124=184 1126=58</text>
  </g>
  <g class="rs2">
    <rect x="170" y="158" width="132" height="22" rx="3" fill="var(--on)"/>
    <text x="236" y="173" text-anchor="middle" font-size="11" font-family="monospace" style="fill:var(--onink)" font-weight="bold">1124=200 1126=95</text>
  </g>

  <text x="14" y="200" font-size="11" opacity="0.85">the request pass notes where each target will sit in the coming answer</text>
  <rect x="140" y="206" width="180" height="46" rx="4" fill="currentColor" fill-opacity="0.10" stroke="currentColor" stroke-opacity="0.5"/>
  <g class="card" font-family="monospace" font-size="12" text-anchor="middle" font-weight="bold">
    <text x="230" y="224" fill="var(--on)">GST&rarr;0   HPT&rarr;2</text>
    <text x="230" y="242" fill="var(--on)">manual&rarr;6  sysSen&rarr;8</text>
  </g>
  <text class="mt" x="230" y="235" text-anchor="middle" font-size="12" opacity="0.72">queue empty</text>
  <text class="scr" x="14" y="264" font-size="11" opacity="0.85">The operator's screen now reads 95. The tank still holds 58.</text>
</svg>
<figcaption>Measured on the running stack: FUXA polls once a second, one <code>read holding 1124, count 11</code> and one <code>read coils 0, count 4</code>. All four forged registers sit in that single block &mdash; GST at 1124, HPT at 1126, <code>manual</code> at 1130, the system sensor at 1132 &mdash; so one note covers the whole poll. Because the proxy's loop never has two requests in flight, the queue is a queue of at most one.</figcaption>
</figure>

The four values were chosen to hang together. 95 sits inside the 50-to-100 band, and `sysSen` is only set when the pressure is in that band *and* the system valve is open, so forging the sensor without also forging the valve coil would hand the operator a reading that contradicts itself. GST 200 does not read "normal"; the plant's own classifier calls anything above 150 **Full**, which is the point &mdash; a well-stocked supply is one fewer thing to wonder about. And `manual` back to 0 hides the mode switch that made the rest of it possible.

## The forged bytes land correctly for the wrong reason

Now the part worth stopping on. Modbus is big-endian: every register on the wire is high byte first. The proxy writes its forged value with `to_bytes(2, 'little')`. And it patches at `HOLDING_DATA_OFFSET + location*2` with `HOLDING_DATA_OFFSET = 10`, although the values in a read response start at byte 9.

Two mistakes. They cancel.

<figure>
<style>
.article figure svg.mm-b {min-width: 488px;}
.mm-b {--d: 13s; --on:#ff6b00; --onink:#1a1a1a;}
html.light-mode .mm-b {--on:#b34700; --onink:#ffffff;}
/* Both bytes are written in the same statement, so the only way to see that
   one is right and the other is one register out is to watch them land one
   after the other. The cell that ends up orange is the one that mattered. */
.mm-b .t5 {animation: b-t5 var(--d) steps(1,end) infinite;}
.mm-b .f5 {opacity:0; animation: b-f5 var(--d) steps(1,end) infinite;}
.mm-b .h6 {opacity:0; animation: b-h6 var(--d) steps(1,end) infinite;}
.mm-b .mk {opacity:0; animation: b-mk var(--d) ease-in-out infinite;}
.mm-b .c1 {animation: b-c1 var(--d) steps(1,end) infinite;}
.mm-b .c2 {opacity:0; animation: b-c2 var(--d) steps(1,end) infinite;}
.mm-b .c3 {opacity:0; animation: b-c3 var(--d) steps(1,end) infinite;}
.mm-b .c4 {opacity:0; animation: b-c4 var(--d) steps(1,end) infinite;}
@keyframes b-t5 {0%,19.9%{opacity:1} 20%,100%{opacity:0}}
@keyframes b-f5 {0%,19.9%{opacity:0} 20%,100%{opacity:1}}
@keyframes b-h6 {0%,49.9%{opacity:0} 50%,100%{opacity:1}}
@keyframes b-mk {0%,19.9%{opacity:0; transform:translateX(0)}
                 20%{opacity:1; transform:translateX(0)}
                 46%{opacity:1; transform:translateX(0)}
                 52%,100%{opacity:1; transform:translateX(46px)}}
@keyframes b-c1 {0%,19.9%{opacity:1} 20%,100%{opacity:0}}
@keyframes b-c2 {0%,19.9%{opacity:0} 20%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes b-c3 {0%,49.9%{opacity:0} 50%,74.9%{opacity:1} 75%,100%{opacity:0}}
@keyframes b-c4 {0%,74.9%{opacity:0} 75%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .mm-b *{animation:none !important}
  .mm-b .t5,.mm-b .c1,.mm-b .c2,.mm-b .c3{opacity:0}
  .mm-b .f5,.mm-b .h6,.mm-b .c4{opacity:1}
  .mm-b .mk{opacity:1; transform:translateX(46px)}
}
</style>
<svg class="mm-b" viewBox="0 0 460 250" role="img"
     aria-label="Eight bytes of a read response, covering registers 1124 to 1127, each as a high byte and a low byte. The proxy forges HPT, which is at slot 2, by writing at byte 14 and byte 15. Byte 14 is register 1126's low byte, so the low byte of 95 lands exactly where it belongs and 1126 reads 95. Byte 15 is register 1127's high byte, one register too far, but the value written there is zero and the byte was already zero. Nothing visible changes.">
  <text x="14" y="20" font-size="12" font-weight="bold">writing 95 into slot 2 of the answer</text>

  <text x="90"  y="84" text-anchor="middle" font-size="12" font-weight="bold">1124</text>
  <text x="182" y="84" text-anchor="middle" font-size="12" font-weight="bold">1125</text>
  <text x="274" y="84" text-anchor="middle" font-size="12" font-weight="bold">1126</text>
  <text x="366" y="84" text-anchor="middle" font-size="12" font-weight="bold">1127</text>

  <rect x="46"  y="92" width="42" height="38" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
  <rect x="92"  y="92" width="42" height="38" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
  <rect x="138" y="92" width="42" height="38" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
  <rect x="184" y="92" width="42" height="38" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
  <rect x="230" y="92" width="42" height="38" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
  <rect x="276" y="92" width="42" height="38" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
  <rect x="322" y="92" width="42" height="38" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
  <rect x="368" y="92" width="42" height="38" rx="3" fill="none" stroke="currentColor" stroke-opacity="0.6"/>

  <g font-family="monospace" font-size="13" text-anchor="middle">
    <text x="67"  y="117">00</text>
    <text x="113" y="117">b8</text>
    <text x="159" y="117">00</text>
    <text x="205" y="117">00</text>
    <text x="251" y="117">00</text>
    <text class="t5" x="297" y="117">3a</text>
    <text x="389" y="117">00</text>
  </g>
  <g class="f5">
    <rect x="276" y="92" width="42" height="38" rx="3" fill="var(--on)"/>
    <text x="297" y="117" text-anchor="middle" font-family="monospace" font-size="13" style="fill:var(--onink)" font-weight="bold">5f</text>
  </g>
  <g class="h6">
    <rect x="322" y="92" width="42" height="38" rx="3" fill="none" stroke="var(--on)" stroke-width="2.5"/>
  </g>
  <text x="343" y="117" text-anchor="middle" font-family="monospace" font-size="13">00</text>

  <g class="mk"><path d="M 291 146 L 297 134 L 303 146 Z" fill="var(--on)"/></g>

  <g font-size="11" text-anchor="middle" opacity="0.8">
    <text x="67"  y="164">hi</text>
    <text x="113" y="164">lo</text>
    <text x="159" y="164">hi</text>
    <text x="205" y="164">lo</text>
    <text x="251" y="164">hi</text>
    <text x="297" y="164">lo</text>
    <text x="343" y="164">hi</text>
    <text x="389" y="164">lo</text>
  </g>
  <g font-size="11" text-anchor="middle" opacity="0.7">
    <text x="67"  y="180">9</text>
    <text x="113" y="180">10</text>
    <text x="159" y="180">11</text>
    <text x="205" y="180">12</text>
    <text x="251" y="180">13</text>
    <text x="297" y="180">14</text>
    <text x="343" y="180">15</text>
    <text x="389" y="180">16</text>
  </g>
  <text x="14" y="164" font-size="11" opacity="0.8">half</text>
  <text x="14" y="180" font-size="11" opacity="0.7">byte</text>

  <g font-size="13" font-weight="bold">
    <text class="c1" x="14" y="212">the true answer &mdash; 1126 holds 58</text>
    <text class="c2" x="14" y="212" fill="var(--on)">low byte of 95 &rarr; byte 14, exactly where it belongs</text>
    <text class="c3" x="14" y="212" fill="var(--on)">high byte &rarr; byte 15, one whole register too far</text>
    <text class="c4" x="14" y="212">1126 now reads 95; byte 15 was 00 and is still 00</text>
  </g>
  <text x="14" y="236" font-size="11" opacity="0.85">Wrong byte order plus wrong offset, in a plant that never exceeds 255.</text>
</svg>
<figcaption>The low byte of a little-endian pair is written first, and <code>10 + 2&times;location</code> happens to be exactly where a big-endian low byte belongs &mdash; so the value that matters lands correctly. The stray high byte goes one register further on. That would corrupt the neighbour, except that <code>hardwareAbstraction.py</code> clamps <code>gst</code> and <code>hpt</code> to 255 before publishing them and every other register in the block is a flag, so each high byte is already <code>00</code>. Driving the proxy's own functions with the eleven live values captured off the stack returns precisely the intended forgery; set register 1127 to 4097 first and it comes back as 1.</figcaption>
</figure>

There is a third latent fault in the same place. The queue is pushed on a request with function code `0x03` and popped on a response with function code `0x03`; a Modbus exception reply carries `0x83`, so it is never popped, and the queue keeps one stale entry from then on. Here that costs nothing, because every FUXA poll requests the same eleven registers and every note is therefore identical. The proxy works &mdash; three times over, for reasons its author did not write down.

## Two ways in, and they win different things

The module gives two ways to reach the middle. It presents the second as a prerequisite, but it is a complete alternative, and the two are not equivalent.

**ARP poisoning.** `arpspoof` or `ettercap` tells FUXA that the PLC's address belongs to the attacker's MAC, and tells the PLC the same about FUXA. Nothing in ARP asks for proof, so both caches simply believe the last thing they heard. Traffic now crosses the attacker's machine &mdash; but with forwarding enabled and no redirection rule it is routed straight on to OpenPLC. `mitm.py` listens on port 5020, and there is no `iptables ... REDIRECT --to-port 5020` anywhere in the repository. On this route the proxy is a bystander: the poisoning is real, the interception is not.

**Repointing FUXA.** Log in as an administrator and edit the device: point its PLC connection at the proxy's address and port. No ARP is touched; the traffic arrives at the attacker because the operator's own configuration sends it there. This is the route that actually feeds the proxy.

<figure>
<style>
.article figure svg.mm-a {min-width: 488px;}
.mm-a {--d: 11s; --on:#ff6b00;}
html.light-mode .mm-a {--on:#b34700;}
/* The resting state is the detected one, because that is what the caption
   under the figure describes. The keyframes replay the "before" at the start
   of each cycle rather than the other way round. */
.mm-a .old,.mm-a .m1 {opacity:0; animation: a-old var(--d) steps(1,end) infinite;}
.mm-a .new,.mm-a .m2 {animation: a-new var(--d) steps(1,end) infinite;}
.mm-a .fire{animation: a-fire var(--d) steps(1,end) infinite;}
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
  <text x="166" y="56" font-size="13" opacity="0.72">last heard</text>

  <text x="276" y="28" font-size="13" opacity="0.8">the IDS remembers</text>
  <rect x="276" y="36" width="170" height="30" rx="4" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.6"/>
  <text class="m1" x="288" y="56" font-size="13" font-family="monospace">1 MAC</text>
  <text class="m2" x="288" y="56" font-size="13" font-family="monospace" fill="var(--on)" font-weight="bold">2 MACs</text>

  <text class="fire" x="14" y="92" font-size="14" fill="var(--on)" font-weight="bold">arp_spoof &mdash; one address, two MACs</text>
  <text x="14" y="116" font-size="13" opacity="0.8">Nothing in the cache is verified; nothing in the set is ever removed.</text>
</svg>
<figcaption>Rule 8 does not detect interception &mdash; it detects an address that has been seen with more than one MAC. That is why the configuration route is invisible to it, nobody having lied about a MAC, and why a plain container restart raises the same alert: Docker hands out a fresh random MAC each time, and <code>cleanup()</code> empties only <code>recent_alerts</code> and <code>port_scan_tracker</code>, so the alert outlives both the attack and the container.</figcaption>
</figure>

That split matters for the challenge, because `check_mitm_attack.py` asks the IDS one question: did `arp_spoof` fire? Its docstring claims either route leaves a trace. The proxy route leaves none it looks for &mdash; and in fact none at all, because the proxy's upstream is `172.17.0.1`, the docker0 gateway, while the IDS captures the `172.18.0.0/24` bridge. So the ARP route wins the flag without deceiving anyone, and the configuration route deceives the operator without winning the flag. Joining them takes the redirection rule the module never gives you.

Why ARP accepts anyone's word for it is worth a sentence of its own: the protocol dates from 1982, when the machines that could answer were the ones you had cabled up yourself. There was no threat model in which a reply might be a lie, so no field was reserved for proving it was not &mdash; and by the time that mattered, every stack on earth had shipped.

## The skill

Poison the two ARP tables and the IDS will see it; that is what the flag is scored on. To see the deception itself you need the traffic to actually enter the proxy, which means either repointing FUXA or adding the redirection rule yourself. The flag and the lesson are not in the same place here, which is worth knowing before you spend an hour wondering why nothing on the screen changed.

> **MITRE ATT&CK for ICS:** T0830 Adversary-in-the-Middle, and for the forged readings **T1692.002 Reporting Message** (Evasion / Impair Process Control). The module still cites T0856 Spoof Reporting Message, which the catalogue has since superseded &mdash; that page now serves only a redirect. Defence: static ARP entries, segmentation so the attacker is never on the same broadcast domain, and protocols that authenticate the endpoint rather than trusting the address.
