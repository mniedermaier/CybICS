# The ICS attack lifecycle

Real intrusions are not single tricks. They are campaigns with stages, and the **MITRE ATT&CK for ICS** knowledge base names the tactics an adversary moves through. The CybICS challenges are arranged along the same arc, so the CTF is a guided walk through one.

The usual moral is that the stages get louder as they go, so a defender who watches the network turns a silent campaign into a series of alerts. That is the argument for monitoring, and it is mostly right. It is also worth checking against a real detector rather than assuming, because this platform has one and it does not behave that way.

## Walking the arc, and what the IDS hears

<figure>
<style>
.article figure svg.al-w {min-width: 400px;}
.al-w {--w: 20s;}
/* One marker, five stages, and the alert each stage actually produces. The
   stage highlight and the alert row share the clock, because the point is
   which of them arrive together and which stage arrives alone. */
.al-w .mk {animation: aw-mk var(--w) steps(1,end) infinite;}
.al-w .s1 {animation: aw-s1 var(--w) steps(1,end) infinite;}
.al-w .s2 {animation: aw-s2 var(--w) steps(1,end) infinite;}
.al-w .s3 {animation: aw-s3 var(--w) steps(1,end) infinite;}
.al-w .s4 {animation: aw-s4 var(--w) steps(1,end) infinite;}
.al-w .s5 {animation: aw-s5 var(--w) steps(1,end) infinite;}
.al-w .a1 {opacity:0; animation: aw-o1 var(--w) steps(1,end) infinite;}
.al-w .a2 {opacity:0; animation: aw-o2 var(--w) steps(1,end) infinite;}
.al-w .a3 {opacity:0; animation: aw-o3 var(--w) steps(1,end) infinite;}
.al-w .a4 {opacity:0; animation: aw-o4 var(--w) steps(1,end) infinite;}
.al-w .a5 {opacity:0; animation: aw-o5 var(--w) steps(1,end) infinite;}
/* Base state is stage 3, the one that produces nothing -- the frame worth
   landing on when the animation is switched off. */
.al-w .s3 {stroke-width:3;}
.al-w .s1,.al-w .s2,.al-w .s4,.al-w .s5 {stroke-width:0;}
.al-w .a3 {opacity:1;}
.al-w .mk {transform: translateX(152px);}
@keyframes aw-mk {0%,19.9%{transform:translateX(0)}    20%,39.9%{transform:translateX(76px)}
                  40%,59.9%{transform:translateX(152px)} 60%,79.9%{transform:translateX(228px)}
                  80%,100%{transform:translateX(304px)}}
/* The panels animate stroke-width only. They used to animate `opacity` too,
   which faded the orange rect out from under its own dark labels and left
   them at 1.06:1 on the figure ground -- four of the five stage captions were
   ghosts while the animation ran, and legible only when it stopped. The alert
   rows below carry the opacity on their own keyframes. */
@keyframes aw-s1 {0%,19.9%{stroke-width:3} 20%,100%{stroke-width:0}}
@keyframes aw-s2 {0%,19.9%{stroke-width:0} 20%,39.9%{stroke-width:3} 40%,100%{stroke-width:0}}
@keyframes aw-s3 {0%,39.9%{stroke-width:0} 40%,59.9%{stroke-width:3} 60%,100%{stroke-width:0}}
@keyframes aw-s4 {0%,59.9%{stroke-width:0} 60%,79.9%{stroke-width:3} 80%,100%{stroke-width:0}}
@keyframes aw-s5 {0%,79.9%{stroke-width:0} 80%,100%{stroke-width:3}}
@keyframes aw-o1 {0%,19.9%{opacity:1} 20%,100%{opacity:0}}
@keyframes aw-o2 {0%,19.9%{opacity:0} 20%,39.9%{opacity:1} 40%,100%{opacity:0}}
@keyframes aw-o3 {0%,39.9%{opacity:0} 40%,59.9%{opacity:1} 60%,100%{opacity:0}}
@keyframes aw-o4 {0%,59.9%{opacity:0} 60%,79.9%{opacity:1} 80%,100%{opacity:0}}
@keyframes aw-o5 {0%,79.9%{opacity:0} 80%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .al-w * {animation:none !important;} }
</style>
<svg class="al-w" viewBox="0 0 400 214" role="img"
     aria-label="Five stages of a campaign against this plant, walked in order. Scanning raises a port scan alert at medium severity and an S7 enumeration alert. Man in the middle raises an ARP spoofing alert at critical severity. Guessing the HMI password raises nothing at all, because the rule matches the word login or auth in the request and the HMI's endpoint is called api slash signin. Downloading a modified program raises nothing. Flooding a register raises a Modbus flood alert at critical severity. The quiet stage is in the middle, not at the start.">
  <text x="8" y="18" font-size="12" font-weight="bold">one campaign, five stages</text>
  <g font-size="11" text-anchor="middle">
    <rect class="s1" x="8"   y="30" width="68" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="42" y="48" style="fill:#1a1a1a" font-weight="bold">scan</text><text x="42" y="62" style="fill:#1a1a1a">find the ports</text>
    <rect class="s2" x="84"  y="30" width="68" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="118" y="48" style="fill:#1a1a1a" font-weight="bold">MitM</text><text x="118" y="62" style="fill:#1a1a1a">sit on the wire</text>
    <rect class="s3" x="160" y="30" width="68" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="194" y="48" style="fill:#1a1a1a" font-weight="bold">creds</text><text x="194" y="62" style="fill:#1a1a1a">guess the HMI</text>
    <rect class="s4" x="236" y="30" width="68" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="270" y="48" style="fill:#1a1a1a" font-weight="bold">program</text><text x="270" y="62" style="fill:#1a1a1a">change the logic</text>
    <rect class="s5" x="312" y="30" width="80" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="352" y="48" style="fill:#1a1a1a" font-weight="bold">flood</text><text x="352" y="62" style="fill:#1a1a1a">pin the register</text>
  </g>
  <g class="mk"><path d="M 34 82 L 50 82 L 42 92 Z" fill="#ff6b00"/></g>

  <text x="8" y="116" font-size="12" font-weight="bold" opacity="0.85">what the IDS hears:</text>
  <g font-size="12" font-weight="bold">
    <text class="a1" x="8" y="140" fill="#ff6b00">port_scan &mdash; medium &nbsp;&middot;&nbsp; s7_enumeration &mdash; medium</text>
    <text class="a2" x="8" y="140" fill="#ff6b00">arp_spoof &mdash; critical</text>
    <text class="a3" x="8" y="140">&mdash; silence &mdash;</text>
    <text class="a4" x="8" y="140">&mdash; silence &mdash;</text>
    <text class="a5" x="8" y="140" fill="#ff6b00">modbus_flood &mdash; critical</text>
  </g>
  <g font-size="11" opacity="0.85">
    <text class="a1" x="8" y="160">Five ports in ten seconds, and any payload to 102.</text>
    <text class="a2" x="8" y="160">One IP claiming two MAC addresses.</text>
    <text class="a3" x="8" y="160">The rule looks for &ldquo;login&rdquo; or &ldquo;auth&rdquo;. FUXA&rsquo;s endpoint is /api/signin.</text>
    <text class="a4" x="8" y="160">No rule watches a program upload at all.</text>
    <text class="a5" x="8" y="160">Fifty writes in five seconds, from a host outside the exempt three.</text>
  </g>
  <text x="8" y="190" font-size="11" opacity="0.85">Both ends raise something. The two silent stages are in the middle,</text>
  <text x="8" y="206" font-size="11" opacity="0.85">which is where an attacker takes control.</text>
</svg>
<figcaption>Measured against the running IDS, not read off a diagram. Eight failed logins against OpenPLC&rsquo;s <code>/login</code> produced a HIGH <code>http_brute_force</code> alert on the fifth; eight against FUXA&rsquo;s <code>/api/signin</code> produced nothing, because <code>_check_http_brute</code> only proceeds when the first 200 bytes of the POST contain <code>login</code> or <code>auth</code>. The received wisdom is that a campaign gets louder as it advances. On this plant it is loud at both ends and quiet in the middle, which is exactly the wrong shape.</figcaption>
</figure>

## A signature sees the string, not the meaning

That gap is worth more than the embarrassment. It is the clearest example on the platform of how a detection rule actually fails.

<figure>
<style>
.article figure svg.al-f {min-width: 400px;}
.al-f {--f: 10s; --pkt-ink:#141414;}
/* The grey packet is filled with currentColor, so its fill flips with the
   theme while a fixed ink on it would not: #141414 on the light-mode fill
   measures about 1.6:1. The ink has to flip with it. */
html.light-mode .al-f {--pkt-ink:#ffffff;}
/* Two identical attacks, one filter, two outcomes. The packets travel on the
   same clock so the divergence happens at the same x for both rows -- the
   filter is the only thing that differs. */
/* Base state is both packets at their endpoints, matching the two outcome
   labels below -- otherwise switching animations off showed the verdicts with
   both packets still sitting at the start line. */
.al-f .p1 {transform: translateX(164px); animation: af-p1 var(--f) linear infinite;}
.al-f .p2 {transform: translateX(292px); animation: af-p2 var(--f) linear infinite;}
.al-f .hit  {opacity:1; animation: af-hit var(--f) steps(1,end) infinite;}
.al-f .miss {opacity:1; animation: af-miss var(--f) steps(1,end) infinite;}
@keyframes af-p1 {0%{transform:translateX(0); opacity:0} 4%{transform:translateX(0); opacity:1}
                  52%,100%{transform:translateX(164px); opacity:1}}
@keyframes af-p2 {0%{transform:translateX(0); opacity:0} 4%{transform:translateX(0); opacity:1}
                  52%{transform:translateX(164px); opacity:1}
                  76%,100%{transform:translateX(292px); opacity:1}}
@keyframes af-hit  {0%,51.9%{opacity:0} 52%,100%{opacity:1}}
@keyframes af-miss {0%,75.9%{opacity:0} 76%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .al-f * {animation:none !important;} }
</style>
<svg class="al-f" viewBox="0 0 400 200" role="img"
     aria-label="Two identical brute-force attempts arrive at the same rule. The rule tests whether the first two hundred bytes of the POST contain the string login or auth. The request to OpenPLC's slash login endpoint matches and is counted, and the fifth one in thirty seconds raises an alert. The request to FUXA's slash api slash signin endpoint does not match, is never counted, and passes straight through the detector untouched.">
  <text x="8" y="18" font-size="12" font-weight="bold">the same attack, one rule, two outcomes</text>
  <rect x="150" y="34" width="100" height="112" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="200" y="46" text-anchor="middle" font-size="11" opacity="0.9">the rule&rsquo;s filter:</text>
  <text x="200" y="94" text-anchor="middle" font-size="11" opacity="0.9">first 200 bytes</text>
  <text x="200" y="108" text-anchor="middle" font-size="11" opacity="0.9">contain</text>
  <text x="200" y="124" text-anchor="middle" font-size="12" font-weight="bold" fill="#ff6b00">login or auth?</text>

  <text x="8" y="52" font-size="11" opacity="0.85">POST /login</text>
  <g class="p1"><rect x="8" y="58" width="56" height="18" rx="3" fill="#ff6b00"/>
    <text x="36" y="71" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">OpenPLC</text></g>
  <text class="hit" x="260" y="71" font-size="12" font-weight="bold" fill="#ff6b00">counted &rarr; alert</text>

  <text x="8" y="112" font-size="11" opacity="0.85">POST /api/signin</text>
  <g class="p2"><rect x="8" y="118" width="56" height="18" rx="3" fill="currentColor" fill-opacity="0.85"/>
    <text x="36" y="131" text-anchor="middle" font-size="11" style="fill:var(--pkt-ink)" font-weight="bold">FUXA</text></g>
  <text class="miss" x="392" y="112" text-anchor="end" font-size="12" font-weight="bold">never counted</text>

  <text x="8" y="170" font-size="11" opacity="0.85">Eight failed logins each, same host, under thirty seconds.</text>
  <text x="8" y="186" font-size="11" opacity="0.85">The rule is not wrong about rate. It is wrong about where to look.</text>
</svg>
<figcaption>The rule in <code>software/ids/rules.py</code> is a rate rule wearing a string match: it counts POSTs per source and port, but only ones whose first 200 bytes contain <code>login</code> or <code>auth</code>. FUXA&rsquo;s sign-in route contains neither, so its attempts are never counted and the rate it is counting never rises. The <em>Password Attack</em> module&rsquo;s own instructions point the learner at that route.</figcaption>
</figure>

There is a second reason a signature can be blind here, and it is in the same file: the capture runs with `tcpdump -s 128`, so only the first 128 bytes of each frame reach the rules. About sixty of those are payload. A rule that needs to see something further into a request cannot, whatever it matches on.

## The stages, with CybICS challenges

| Stage | ATT&CK for ICS | CybICS challenge | Detected here? |
|---|---|---|---|
| Discovery | T0846 Remote System Discovery | Service scanning, S7comm scanning | yes &mdash; `port_scan`, `s7_enumeration` |
| Collection | T0842 Network Sniffing | Wireshark capture | no &mdash; passive |
| Adversary-in-the-Middle | T0830 Adversary-in-the-Middle | MitM | yes &mdash; `arp_spoof` |
| Initial access | T0859 Valid Accounts | Password attack | OpenPLC yes, FUXA no |
| Execution, persistence | T0843 Program Download, T0889 Modify Program | PLC programming | no |
| Impair process control | T0836 Modify Parameter | Flood &amp; overwrite | yes &mdash; `modbus_flood` |
| Manipulation of control | T0831 Manipulation of Control | IDS evasion | by design, no |
| Impact | T0828 Loss of Productivity and Revenue | the blow-out | not a network event |

Two notes on that table. The identifiers are checked against the current ATT&CK for ICS catalogue &mdash; three that this repository still uses elsewhere (`T0812`, `T0855`, `T0856`) are no longer in it, including in the `mitre` field the IDS puts on its own alerts. And *Collection* is undetectable on principle, not by oversight: a host that only listens sends nothing to notice.

## Why the order matters for defenders

Reconnaissance is quiet, impact is obvious, and the further left you detect the more options you have and the less damage is done. That argument survives, but this plant sharpens it into something more useful than "monitor the network".

The coverage here is not a gradient, it is a set of holes. Two stages are watched by rate rules, one by a protocol rule, one by an ARP rule, and the two stages where an attacker actually takes control &mdash; getting credentials and changing the program &mdash; are watched by a rule with the wrong string in it and by nothing at all. **Shifting detection left is not the same as adding a rule per stage.** A defender who read only the stage names would conclude the middle was covered. Sending eight requests and reading the log is what tells you otherwise, and it takes a minute.

That is the habit worth taking from this page: a detection you have not fired is a detection you do not have.
