# Detection and monitoring

Because ICS protocols do not authenticate, a defender cannot ask "is this client allowed?". The question has to become "does this traffic look like the plant running normally?", which is a question about behaviour rather than identity. An **Intrusion Detection System (IDS)** watches the traffic passively and raises alerts when the answer is no. CybICS ships a small rule-based one, and it is worth reading rather than taking on trust.

## Where it actually sits, and what it actually gets

The textbook picture is a switch mirror port feeding a sensor. This deployment is simpler and the difference matters. The IDS container runs with `network_mode: host`, finds the Docker bridge by scanning `ip -o addr show` for the `172.18.0.` subnet, and runs `tcpdump` on it. Its capture path never transmits &mdash; nothing in `detector.py` or `rules.py` puts a packet on the wire, and the only socket the service opens is the dashboard it serves on 8443 &mdash; which is the property that makes passive monitoring safe in OT, where an IDS that could interfere with the process would be a liability rather than a control.

What it gets is a copy, and the copy is cut short.

<figure>
<style>
.article figure svg.dm-s {min-width: 428px;}
.dm-s {--s: 11s;}
/* The frame stays put; what moves is the capture, taking its fixed-length
   bite and stopping. Sliding the frame in from off-canvas would have put half
   of it outside the viewBox for a quarter of every loop, which is a different
   figure from the one this is about. */
.dm-s .grab {transform-box: fill-box; transform-origin: left;
             animation: ds-grab var(--s) cubic-bezier(.4,0,.2,1) infinite;}
.dm-s .cut  {opacity:1; animation: ds-cut var(--s) steps(1,end) infinite;}
.dm-s .lost {opacity:1; animation: ds-cut var(--s) steps(1,end) infinite;}
.dm-s .grab {transform: scaleX(1);}
@keyframes ds-grab {0%{transform:scaleX(0)} 28%,100%{transform:scaleX(1)}}
@keyframes ds-cut  {0%,29.9%{opacity:0} 30%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dm-s * {animation:none !important;} }
</style>
<svg class="dm-s" viewBox="0 0 400 190" role="img"
     aria-label="One frame on the wire, drawn to scale by byte count. Fourteen bytes of Ethernet header, twenty of IP, twenty of TCP, then the payload. The capture runs with a snap length of one hundred and twenty-eight bytes, so the copy the rules see stops after sixty-two bytes of payload, because the sixty-six bytes of Ethernet, IP and TCP headers come first. A Modbus write request is twelve bytes and fits easily. An HTTP request line fits too; what does not fit is anything in the body of the request.">
  <text x="8" y="18" font-size="12" font-weight="bold">one frame, drawn by byte count</text>
  <g>
    <rect x="8"  y="34" width="28"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="38" y="34" width="40"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="80" y="34" width="64"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="146" y="34" width="124" height="34" rx="3" fill="#ff6b00"/>
    <rect class="lost" x="270" y="34" width="122" height="34" rx="3" fill="#ff6b00" fill-opacity="0.12" stroke="#ff6b00" stroke-dasharray="4 3"/>
    <rect class="grab" x="8" y="28" width="262" height="46" rx="3" fill="none" stroke="#ff6b00" stroke-width="3"/>
    <g font-size="11" text-anchor="middle">
      <text x="22" y="55">Eth</text><text x="22" y="66" font-size="11" opacity="0.8">14</text>
      <text x="58" y="55">IP</text><text x="58" y="66" font-size="11" opacity="0.8">20</text>
      <text x="112" y="55">TCP</text><text x="112" y="66" font-size="11" opacity="0.8">32</text>
      <text x="208" y="55" style="fill:#1a1a1a" font-weight="bold">payload the rules see</text>
      <text x="208" y="66" style="fill:#1a1a1a">62 bytes</text>
      <text x="331" y="55" fill="#ff6b00" font-weight="bold">never captured</text>
    </g>
  </g>
  <g class="cut">
    <line x1="270" y1="26" x2="270" y2="80" stroke="#ff6b00" stroke-width="3"/>
    <text x="264" y="94" text-anchor="end" font-size="12" font-weight="bold" fill="#ff6b00">tcpdump -s 128 cuts here</text>
  </g>
  <text x="8" y="130" font-size="12" opacity="0.9">A Modbus write request is 12 bytes. It fits easily.</text>
  <text x="8" y="150" font-size="12" opacity="0.9">An HTTP request line fits. A request body does not.</text>
  <text x="8" y="176" font-size="11" opacity="0.85">A marker past byte 62 is invisible to every rule.</text>
</svg>
<figcaption>Drawn to scale, with the real header sizes on this bridge: fourteen bytes of Ethernet, twenty of IP, and thirty-two of TCP because Linux puts timestamp options on every data packet. That leaves sixty-two. The comment in <code>detector.py</code> says the snap length is "enough for headers + Modbus payload", which is exactly true and exactly the limit. The brute-force rule asks for the first 200 bytes of a POST and is handed sixty-two &mdash; which is enough, because <code>POST /login HTTP/1.1</code> is twenty bytes and the rule only looks for a word in the request line. The truncation is a limit waiting to matter: a rule whose marker lives in the request <em>body</em> would never see it, and nothing in the rule would say why.</figcaption>
</figure>

## One packet takes at most one branch of the chain

The dispatch is an `if`/`elif` chain on the destination port. That is not the same as one rule per packet &mdash; `_check_syn` runs before the chain and can raise two, and the Modbus branch runs three rules in one call, so a single write stream raises both `modbus_unauth_write` and `modbus_flood`. What the chain decides is which *branch* a packet takes, and that has a consequence worth seeing before reading any individual rule.

<figure>
<style>
.article figure svg.dm-d {min-width: 428px;}
.dm-d {--d: 16s;}
/* Five beats: four ports that each take a branch, and then one that matches
   nothing and drops out of the bottom. The fifth is the frame the still
   version rests on, and it needs its own position -- parking the packet on the
   last rung while calling it a fall-through said the opposite of the truth. */
.dm-d .pk {animation: dd-pk var(--d) cubic-bezier(.4,0,.2,1) infinite;}
.dm-d .l1 {animation: dd-l1 var(--d) steps(1,end) infinite;}
.dm-d .l2 {animation: dd-l2 var(--d) steps(1,end) infinite;}
.dm-d .l3 {animation: dd-l3 var(--d) steps(1,end) infinite;}
.dm-d .l4 {animation: dd-l4 var(--d) steps(1,end) infinite;}
.dm-d .p5 {animation: dd-p5 var(--d) steps(1,end) infinite;}
.dm-d .p1,.dm-d .p2,.dm-d .p3,.dm-d .p4 {opacity:0;}
.dm-d .p5 {opacity:1;}
.dm-d .p1 {animation: dd-p1 var(--d) steps(1,end) infinite;}
.dm-d .p2 {animation: dd-p2 var(--d) steps(1,end) infinite;}
.dm-d .p3 {animation: dd-p3 var(--d) steps(1,end) infinite;}
.dm-d .p4 {animation: dd-p4 var(--d) steps(1,end) infinite;}
.dm-d .pk {transform: translateY(168px);}
.dm-d .l1,.dm-d .l2,.dm-d .l3,.dm-d .l4 {stroke-width:0;}
@keyframes dd-pk {0%,18%{transform:translateY(0)}      20%,38%{transform:translateY(42px)}
                  40%,58%{transform:translateY(84px)}  60%,78%{transform:translateY(126px)}
                  80%,100%{transform:translateY(168px)}}
@keyframes dd-l1 {0%,19.9%{stroke-width:3} 20%,100%{stroke-width:0}}
@keyframes dd-l2 {0%,19.9%{stroke-width:0} 20%,39.9%{stroke-width:3} 40%,100%{stroke-width:0}}
@keyframes dd-l3 {0%,39.9%{stroke-width:0} 40%,59.9%{stroke-width:3} 60%,100%{stroke-width:0}}
@keyframes dd-l4 {0%,59.9%{stroke-width:0} 60%,79.9%{stroke-width:3} 80%,100%{stroke-width:0}}
@keyframes dd-p1 {0%,19.9%{opacity:1} 20%,100%{opacity:0}}
@keyframes dd-p2 {0%,19.9%{opacity:0} 20%,39.9%{opacity:1} 40%,100%{opacity:0}}
@keyframes dd-p3 {0%,39.9%{opacity:0} 40%,59.9%{opacity:1} 60%,100%{opacity:0}}
@keyframes dd-p4 {0%,59.9%{opacity:0} 60%,79.9%{opacity:1} 80%,100%{opacity:0}}
@keyframes dd-p5 {0%,79.9%{opacity:0} 80%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dm-d * {animation:none !important;} }
</style>
<svg class="dm-d" viewBox="0 0 400 258" role="img"
     aria-label="The detector's dispatch chain. A packet with destination port 502 is handed to the Modbus rules. Port 102 or 1102 goes to the S7 rule. Port 8080 or 1881 goes to the HTTP brute force rule. Port 4840 goes to the OPC-UA rule. The chain is an if-elif, so a packet takes at most one branch, and a packet to any other port drops out of the bottom untested. Within a branch several rules can still run on the same packet. SYN packets are handled separately before the chain and always reach the port scan and SYN flood rules.">
  <text x="8" y="18" font-size="12" font-weight="bold">dispatch on destination port</text>
  <g class="pk"><rect x="8" y="30" width="56" height="26" rx="4" fill="#ff6b00"/>
    <text x="36" y="47" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">packet</text></g>
  <g font-size="12">
    <rect class="l1" x="86" y="30" width="180" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00"/>
    <text x="96" y="47">dport 502 &rarr; Modbus rules</text>
    <rect class="l2" x="86" y="72" width="180" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00"/>
    <text x="96" y="89">102 / 1102 &rarr; S7 rule</text>
    <rect class="l3" x="86" y="114" width="180" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00"/>
    <text x="96" y="131">8080 / 1881 &rarr; HTTP rule</text>
    <rect class="l4" x="86" y="156" width="180" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00"/>
    <text x="96" y="173">4840 &rarr; OPC-UA rule</text>
  </g>
  <g font-size="12" font-weight="bold">
    <text class="p1" x="278" y="47" fill="#ff6b00">tested, then done</text>
    <text class="p2" x="278" y="89" fill="#ff6b00">tested, then done</text>
    <text class="p3" x="278" y="131" fill="#ff6b00">tested, then done</text>
    <text class="p4" x="278" y="173" fill="#ff6b00">tested, then done</text>
    <text class="p5" x="78" y="216">no branch matches &mdash; no rule at all</text>
  </g>
  <text x="8" y="240" font-size="11" opacity="0.85">SYN packets are checked before the chain, always. Within</text>
  <text x="8" y="254" font-size="11" opacity="0.85">one branch, several rules can fire on the same packet.</text>
</svg>
<figcaption>An <code>elif</code> chain, not a list of independent detectors. A Modbus packet is never shown to the HTTP rule and an HTTP packet is never shown to the Modbus rules, which is efficient and also means coverage is decided by the port list rather than by the rules. A non-SYN packet to any port outside 502, 102, 1102, 8080, 1881 and 4840 is examined by nothing. Within a branch, though, several rules can fire: the Modbus branch checks the flood rule, the unauthorised-write rule and the diagnostic rule on the same packet.</figcaption>
</figure>

## Two clocks decide whether you hear about it

Every rate rule carries a sliding window &mdash; how many events in how long &mdash; and every alert then passes a second gate, a per-source, per-rule cooldown of thirty seconds. They are easy to confuse and they do different jobs.

<figure>
<style>
.article figure svg.dm-c {min-width: 428px;}
.dm-c {--c: 15s;}
/* Writes arrive at a steady rate; the window count climbs to ten and fires;
   the cooldown then swallows everything for thirty plant-seconds while the
   window stays full. The gap between "the window is satisfied" and "you are
   told" is the whole figure. */
.dm-c .bar  {transform-box: fill-box; transform-origin: left; animation: dc-bar var(--c) linear infinite;}
.dm-c .fire {opacity:0; animation: dc-fire var(--c) steps(1,end) infinite;}
.dm-c .mute {opacity:1; animation: dc-mute var(--c) steps(1,end) infinite;}
.dm-c .cool {transform-box: fill-box; transform-origin: left; animation: dc-cool var(--c) linear infinite;}
.dm-c .bar {transform: scaleX(1);}
.dm-c .cool {transform: scaleX(0.55);}
@keyframes dc-bar  {0%{transform:scaleX(0)} 30%,100%{transform:scaleX(1)}}
/* The alert used to hold for 0.9 s and never come back, so the figure showed
   "one alert, then silence for ever" under a caption promising one every
   thirty seconds. It fires at 30%, goes quiet while the cooldown runs, and
   fires again the moment the cooldown completes at 94%. */
@keyframes dc-fire {0%,29.9%{opacity:0} 30%,42%{opacity:1} 42.01%,93.9%{opacity:0} 94%,100%{opacity:1}}
@keyframes dc-mute {0%,42%{opacity:0} 42.01%,93.9%{opacity:1} 94%,100%{opacity:0}}
@keyframes dc-cool {0%,29.9%{transform:scaleX(0)} 30%{transform:scaleX(0)} 94%,100%{transform:scaleX(1)}}
@media (prefers-reduced-motion: reduce) { .dm-c * {animation:none !important;} }
</style>
<svg class="dm-c" viewBox="0 0 400 190" role="img"
     aria-label="A rate rule with two timers. Unauthorised Modbus writes accumulate in a thirty-second sliding window; the tenth one satisfies the window and an alert fires. From then on the window stays full because writes keep arriving, but a thirty-second per-source cooldown swallows every further alert. A run of hundreds of writes therefore produces one alert every thirty seconds, not hundreds of alerts.">
  <text x="8" y="18" font-size="12" font-weight="bold">modbus_unauth_write: 10 writes in 30 s</text>
  <text x="8" y="44" font-size="11" opacity="0.85">sliding window</text>
  <rect x="8" y="52" width="280" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="bar" x="8" y="52" width="280" height="20" rx="4" fill="#ff6b00"/>
  <text x="298" y="67" font-size="12" font-weight="bold" fill="#ff6b00">full at 10</text>

  <text x="8" y="100" font-size="11" opacity="0.85">30 s cooldown, per source and rule</text>
  <rect x="8" y="108" width="280" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="cool" x="8" y="108" width="280" height="20" rx="4" fill="currentColor" fill-opacity="0.55"/>
  <text x="298" y="123" font-size="12" opacity="0.85">counting down</text>

  <text class="fire" x="8" y="156" font-size="13" font-weight="bold" fill="#ff6b00">ALERT &mdash; unauthorized Modbus writes</text>
  <text class="mute" x="8" y="156" font-size="13" font-weight="bold">window still full &mdash; and you hear nothing</text>
  <text x="8" y="180" font-size="11" opacity="0.85">Hundreds of writes, one alert every 30 s.</text>
</svg>
<figcaption>The window decides whether the behaviour counts as an attack; the cooldown decides how often you are told. The second one is the reason an alert stream stays readable during a flood, and the reason a count of alerts is not a count of events &mdash; measured on the OPC-UA rule, two probes thirty-one seconds apart produced exactly two alerts, and a third in between would have produced none.</figcaption>
</figure>

## The nine rules

| Rule | Fires on | Severity | ATT&amp;CK id it emits |
|---|---|---|---|
| `port_scan` | 5 distinct ports in 10 s, counted per source-and-destination pair | medium | T0846 Remote System Discovery |
| `syn_flood` | 100 SYN packets in 10 s | high | T0836 Modify Parameter |
| `modbus_flood` | 50 writes in 5 s, from a host that is not `hwio`, `fuxa` or `openplc` | critical | T0836 Modify Parameter |
| `modbus_unauth_write` | 10 writes in 30 s, exempting only `hwio` and `fuxa` &mdash; `openplc` is not exempt here | high | T0855 &mdash; no longer in the catalogue |
| `modbus_diagnostic` | function code 0x08 or 0x2B, no rate gate | medium | T0846 Remote System Discovery |
| `s7_enumeration` | any payload of 4 bytes or more to 102 or 1102 | medium | T0846 Remote System Discovery |
| `http_brute_force` | 5 POSTs containing `login` or `auth` in 30 s, to 8080 or 1881 | high | T0812 &mdash; no longer in the catalogue |
| `arp_spoof` | one IP seen with more than one MAC | critical | T0856 &mdash; no longer in the catalogue |
| `opcua_access` | any payload of 8 bytes or more to 4840, from a host that is not `hwio`, `fuxa`, `openplc` or `opcua` | low | T0846 Remote System Discovery |

Three of the nine carry identifiers that are no longer in ATT&CK for ICS, and two of the mappings are questionable even setting that aside: `syn_flood` is labelled *Modify Parameter*, which a SYN flood does not do, and `arp_spoof` would be *T0830 Adversary-in-the-Middle* under the current catalogue. An identifier on an alert is a promise to the analyst about what the alert means, so it is worth being right.

## Detection is not prevention

An alert is only useful if someone acts on it, and a rule is only useful if it fires. Both halves fail quietly. A rule with an identifier nobody can look up wastes the analyst's first minute; a rule watching the wrong port, or matching a string the traffic does not contain, wastes everything.

The two detection challenges are built on the honest version of this: cause an attack, then go and find it in the alert stream. If it is not there, that is the finding.

> **Rule of thumb:** a good ICS detection is specific enough to stay quiet on normal plant traffic, tied to a technique an analyst can look up, and &mdash; the part that gets skipped &mdash; demonstrated to fire at least once against the thing it claims to catch.
