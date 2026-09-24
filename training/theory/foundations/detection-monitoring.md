# Detection and monitoring

Because ICS protocols do not authenticate, a defender cannot ask "is this client allowed?". The question has to become "does this traffic look like the plant running normally?", which is a question about behaviour rather than identity. An **Intrusion Detection System (IDS)** watches the traffic passively and raises alerts when the answer is no. CybICS ships a small rule-based one, and it is worth reading rather than taking on trust.

## Where it actually sits, and what it actually gets

The textbook picture is a switch mirror port feeding a sensor. This deployment is simpler and the difference matters. The IDS container runs with `network_mode: host`, finds the Docker bridge by scanning `ip -o addr show` for the `172.18.0.` subnet, and runs `tcpdump` on it. It never transmits &mdash; there is no send path anywhere in `software/ids/` &mdash; which is the property that makes passive monitoring safe in OT, where an IDS that could interfere with the process would be a liability rather than a control.

What it gets is a copy, and the copy is cut short.

<figure>
<style>
.article figure svg.dm-s {min-width: 400px;}
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
     aria-label="One frame on the wire, drawn to scale by byte count. Fourteen bytes of Ethernet header, twenty of IP, twenty of TCP, then the payload. The capture runs with a snap length of one hundred and twenty-eight bytes, so the copy the rules see ends fifty-four bytes into the payload region: about seventy-four bytes of payload survive and everything past that is gone. A Modbus write request is twelve bytes and fits easily. An HTTP request line and its headers do not.">
  <text x="8" y="18" font-size="12" font-weight="bold">one frame, drawn by byte count</text>
  <g>
    <rect x="8"  y="34" width="28"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="38" y="34" width="40"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="80" y="34" width="40"  height="34" rx="3" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="122" y="34" width="148" height="34" rx="3" fill="#ff6b00"/>
    <rect class="lost" x="270" y="34" width="122" height="34" rx="3" fill="#ff6b00" fill-opacity="0.22" stroke="#ff6b00" stroke-dasharray="4 3"/>
    <rect class="grab" x="8" y="28" width="262" height="46" rx="3" fill="none" stroke="#ff6b00" stroke-width="3"/>
    <g font-size="11" text-anchor="middle">
      <text x="22" y="55">Eth</text><text x="22" y="66" font-size="11" opacity="0.8">14</text>
      <text x="58" y="55">IP</text><text x="58" y="66" font-size="11" opacity="0.8">20</text>
      <text x="100" y="55">TCP</text><text x="100" y="66" font-size="11" opacity="0.8">20</text>
      <text x="196" y="55" style="fill:#1a1a1a" font-weight="bold">payload the rules see</text>
      <text x="196" y="66" style="fill:#1a1a1a">~74 bytes</text>
      <text x="331" y="55" fill="#ff6b00" font-weight="bold">never captured</text>
    </g>
  </g>
  <g class="cut">
    <line x1="270" y1="26" x2="270" y2="80" stroke="#ff6b00" stroke-width="3"/>
    <text x="264" y="94" text-anchor="end" font-size="12" font-weight="bold" fill="#ff6b00">tcpdump -s 128 cuts here</text>
  </g>
  <text x="8" y="130" font-size="12" opacity="0.9">A Modbus write request is 12 bytes. It fits easily.</text>
  <text x="8" y="150" font-size="12" opacity="0.9">An HTTP request line and its headers do not.</text>
  <text x="8" y="176" font-size="11" opacity="0.85">The limit is in the capture, not in the rule.</text>
</svg>
<figcaption>Drawn to scale: fifty-four bytes of headers before the payload even starts, and a 128-byte snap length. The comment in <code>detector.py</code> says the snap length is "enough for headers + Modbus payload", which is exactly true and exactly the limit &mdash; the engine was sized for the protocol it was written for, and the HTTP rule inherited a window it cannot fill. It asks for the first 200 bytes of a POST and is handed about 74. No rule can match what was never copied, and nothing in the rule says so.</figcaption>
</figure>

## One packet is tested by at most one rule

The dispatch is an `if`/`elif` chain on the destination port, which has a consequence worth seeing before reading any individual rule.

<figure>
<style>
.article figure svg.dm-d {min-width: 400px;}
.dm-d {--d: 16s;}
/* Four packets take the same chain in turn and stop at different rungs. The
   last one has a port nothing matches and falls off the end -- which is the
   frame the still version rests on. */
.dm-d .pk {animation: dd-pk var(--d) cubic-bezier(.4,0,.2,1) infinite;}
.dm-d .l1 {animation: dd-l1 var(--d) steps(1,end) infinite;}
.dm-d .l2 {animation: dd-l2 var(--d) steps(1,end) infinite;}
.dm-d .l3 {animation: dd-l3 var(--d) steps(1,end) infinite;}
.dm-d .l4 {animation: dd-l4 var(--d) steps(1,end) infinite;}
.dm-d .p1,.dm-d .p2,.dm-d .p3 {opacity:0;}
.dm-d .p4 {opacity:1;}
.dm-d .p1 {animation: dd-p1 var(--d) steps(1,end) infinite;}
.dm-d .p2 {animation: dd-p2 var(--d) steps(1,end) infinite;}
.dm-d .p3 {animation: dd-p3 var(--d) steps(1,end) infinite;}
.dm-d .p4 {animation: dd-p4 var(--d) steps(1,end) infinite;}
.dm-d .pk {transform: translateY(126px);}
.dm-d .l1,.dm-d .l2,.dm-d .l3 {stroke-width:0;}
.dm-d .l4 {stroke-width:0;}
@keyframes dd-pk {0%{transform:translateY(0)}      20%,24.9%{transform:translateY(0)}
                  25%{transform:translateY(42px)}  45%,49.9%{transform:translateY(42px)}
                  50%{transform:translateY(84px)}  70%,74.9%{transform:translateY(84px)}
                  75%,100%{transform:translateY(126px)}}
@keyframes dd-l1 {0%,24.9%{stroke-width:3} 25%,100%{stroke-width:0}}
@keyframes dd-l2 {0%,24.9%{stroke-width:0} 25%,49.9%{stroke-width:3} 50%,100%{stroke-width:0}}
@keyframes dd-l3 {0%,49.9%{stroke-width:0} 50%,74.9%{stroke-width:3} 75%,100%{stroke-width:0}}
@keyframes dd-l4 {0%,74.9%{stroke-width:0} 75%,100%{stroke-width:3}}
@keyframes dd-p1 {0%,24.9%{opacity:1} 25%,100%{opacity:0}}
@keyframes dd-p2 {0%,24.9%{opacity:0} 25%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes dd-p3 {0%,49.9%{opacity:0} 50%,74.9%{opacity:1} 75%,100%{opacity:0}}
@keyframes dd-p4 {0%,74.9%{opacity:0} 75%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .dm-d * {animation:none !important;} }
</style>
<svg class="dm-d" viewBox="0 0 400 226" role="img"
     aria-label="The detector's dispatch chain. A packet with destination port 502 is handed to the Modbus rules. Port 102 or 1102 goes to the S7 rule. Port 8080 or 1881 goes to the HTTP brute force rule. Port 4840 goes to the OPC-UA rule. The chain is an if-elif, so a packet reaches at most one of them, and a packet to any other port falls off the end and is tested by no rule at all. SYN packets are handled separately before the chain and always reach the port scan and SYN flood rules.">
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
    <text class="p4" x="278" y="173">falls through</text>
  </g>
  <text x="8" y="204" font-size="11" opacity="0.85">SYN packets are checked before the chain, always.</text>
  <text x="8" y="220" font-size="11" opacity="0.85">Everything else: one rule at most; any other port, none.</text>
</svg>
<figcaption>An <code>elif</code> chain, not a list of independent detectors. A Modbus packet is never shown to the HTTP rule and an HTTP packet is never shown to the Modbus rules, which is efficient and also means coverage is decided by the port list rather than by the rules. A non-SYN packet to any port outside 502, 102, 1102, 8080, 1881 and 4840 is examined by nothing.</figcaption>
</figure>

## Two clocks decide whether you hear about it

Every rate rule carries a sliding window &mdash; how many events in how long &mdash; and every alert then passes a second gate, a per-source, per-rule cooldown of thirty seconds. They are easy to confuse and they do different jobs.

<figure>
<style>
.article figure svg.dm-c {min-width: 400px;}
.dm-c {--c: 15s;}
/* Writes arrive at a steady rate; the window count climbs to ten and fires;
   the cooldown then swallows everything for thirty plant-seconds while the
   window stays full. The gap between "the window is satisfied" and "you are
   told" is the whole figure. */
.dm-c .bar  {transform-box: fill-box; transform-origin: left; animation: dc-bar var(--c) linear infinite;}
.dm-c .fire {opacity:1; animation: dc-fire var(--c) steps(1,end) infinite;}
.dm-c .mute {opacity:1; animation: dc-mute var(--c) steps(1,end) infinite;}
.dm-c .cool {transform-box: fill-box; transform-origin: left; animation: dc-cool var(--c) linear infinite;}
.dm-c .bar {transform: scaleX(1);}
.dm-c .cool {transform: scaleX(0.55);}
@keyframes dc-bar  {0%{transform:scaleX(0)} 30%,100%{transform:scaleX(1)}}
@keyframes dc-fire {0%,29.9%{opacity:0} 30%,36%{opacity:1} 36.01%,100%{opacity:0}}
@keyframes dc-mute {0%,36%{opacity:0} 36.01%,100%{opacity:1}}
@keyframes dc-cool {0%,29.9%{transform:scaleX(0)} 30%{transform:scaleX(0)} 100%{transform:scaleX(1)}}
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
| `port_scan` | 5 distinct ports from one host in 10 s | medium | T0846 Remote System Discovery |
| `syn_flood` | 100 SYN packets in 10 s | high | T0836 Modify Parameter |
| `modbus_flood` | 50 writes in 5 s, from a host that is not `hwio`, `fuxa` or `openplc` | critical | T0836 Modify Parameter |
| `modbus_unauth_write` | 10 writes in 30 s, same exemptions | high | T0855 &mdash; no longer in the catalogue |
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
