# HMI and SCADA

The **Human-Machine Interface (HMI)** is the screen an operator watches: tank levels, pressures, pumps, alarms, and the buttons to start and stop the process. **SCADA** (Supervisory Control and Data Acquisition) is the wider system that gathers that data from many controllers and presents it. In CybICS the HMI is **FUXA**, a web-based SCADA/HMI on port 1881.

## The operator sees nothing directly

The HMI is not wired to a sensor. It is a Modbus client. Every number on the screen is a register it polled from OpenPLC, and every button is a register it writes back. The operator's picture of the plant is an inference, three hops from the gas.

<figure>
<style>
.article figure svg.hm-c {min-width: 388px;}
.hm-c {--p: 6s; --k: 18s;}
/* theory_article.html retints text, path and stroke for the light theme but
   never a circle, so this marker stayed #ff6b00 on white: 2.86:1. */
html.light-mode .hm-c .cmd {fill:#b34700;}
/* and it cannot reach a rect: the FUXA and OpenPLC panels and the wire panel
   in figure 3 were all #ff6b00 on white, 2.86:1. Retinting a panel means
   retinting the ink on it as well -- #1a1a1a is 6.10:1 on #ff6b00 but only
   3.14:1 on #b34700, which is why the template deliberately leaves filled
   panels alone. White is 5.48:1 there. */
html.light-mode .hm-c rect[fill="#ff6b00"],
html.light-mode .hm-a rect[fill="#ff6b00"] {fill:#b34700;}
html.light-mode .hm-c text[style*="#1a1a1a"],
html.light-mode .hm-a text[style*="#1a1a1a"] {fill:#ffffff !important;}
/* Two clocks in phase: the command-and-value round trip replays every 6 s,
   and which link is under attack changes every 6 s, cycling through three
   over 18. The base state is the middle one, the man in the middle, because
   it is the link a reader is least likely to think of unprompted. */
.hm-c .cmd {animation: hc-cmd var(--p) ease-in-out infinite;}
.hm-c .val {animation: hc-val var(--p) ease-in-out infinite;}
.hm-c .k1,.hm-c .k3 {opacity:0;}
.hm-c .k2 {opacity:1;}
.hm-c .k1 {animation: hc-k1 var(--k) steps(1,end) infinite;}
.hm-c .k2 {animation: hc-k2 var(--k) steps(1,end) infinite;}
.hm-c .k3 {animation: hc-k3 var(--k) steps(1,end) infinite;}
@keyframes hc-cmd {0%{transform:translateX(0);   opacity:0}
                   4%{transform:translateX(0);   opacity:1}
                   40%{transform:translateX(172px); opacity:1}
                   46%,100%{transform:translateX(172px); opacity:0}}
@keyframes hc-val {0%,50%{transform:translateX(0); opacity:0}
                   54%{transform:translateX(0); opacity:1}
                   90%{transform:translateX(-172px); opacity:1}
                   96%,100%{transform:translateX(-172px); opacity:0}}
@keyframes hc-k1 {0%,33.32%{opacity:1} 33.33%,100%{opacity:0}}
@keyframes hc-k2 {0%,33.32%{opacity:0} 33.33%,66.65%{opacity:1} 66.66%,100%{opacity:0}}
@keyframes hc-k3 {0%,66.65%{opacity:0} 66.66%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .hm-c * {animation:none !important;} }
</style>
<svg class="hm-c" viewBox="0 0 360 204" role="img"
     aria-label="Four boxes in a row: operator, HMI FUXA on port 1881, PLC OpenPLC on Modbus port 502, and the plant. A command travels left to right from the operator to the plant; a measured value travels right to left back to the operator's screen. Three attacks cut the chain at three different links: a dictionary attack on the FUXA login, a man in the middle on the Modbus connection between HMI and PLC, and a register flood at the PLC end. Each breaks a different link of the same chain of trust.">
  <g font-size="12" text-anchor="middle">
    <rect x="8" y="30" width="76" height="40" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="46" y="48" font-weight="bold">Operator</text><text x="46" y="62" font-size="11" opacity="0.85">eyes &amp; hands</text>
    <rect x="94" y="30" width="76" height="40" rx="5" fill="#ff6b00"/>
    <text x="132" y="48" font-weight="bold" style="fill:#1a1a1a">FUXA</text><text x="132" y="62" font-size="11" style="fill:#1a1a1a">:1881</text>
    <rect x="180" y="30" width="76" height="40" rx="5" fill="#ff6b00"/>
    <text x="218" y="48" font-weight="bold" style="fill:#1a1a1a">OpenPLC</text><text x="218" y="62" font-size="11" style="fill:#1a1a1a">:502</text>
    <rect x="266" y="30" width="86" height="40" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="309" y="48" font-weight="bold">the plant</text><text x="309" y="62" font-size="11" opacity="0.85">tanks, valves</text>
  </g>
  <g stroke="currentColor" stroke-opacity="0.65" stroke-width="2">
    <line x1="84" y1="50" x2="92" y2="50"/><line x1="170" y1="50" x2="178" y2="50"/><line x1="256" y1="50" x2="264" y2="50"/>
  </g>
  <text x="176" y="22" text-anchor="middle" font-size="11" opacity="0.85">Modbus TCP &mdash; the same writes anyone else can send</text>

  <circle class="cmd" cx="88" cy="86" r="6" fill="#ff6b00"/>
  <text x="88" y="104" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">command</text>
  <circle class="val" cx="260" cy="86" r="6" fill="currentColor" fill-opacity="0.85"/>
  <text x="260" y="104" text-anchor="middle" font-size="11" opacity="0.85">measured value</text>

  <g font-size="12" font-weight="bold">
    <g class="k1">
      <path d="M 132 122 L 132 78" stroke="#ff6b00" stroke-width="3"/>
      <path d="M 124 88 L 140 104 M 124 104 L 140 88" stroke="#ff6b00" stroke-width="3"/>
      <text x="8" y="146" fill="#ff6b00">Password Attack &mdash; guess the login</text>
      <text x="8" y="164" font-size="11" opacity="0.85">credentials and a path, in one step</text>
    </g>
    <g class="k2">
      <path d="M 176 122 L 176 60" stroke="#ff6b00" stroke-width="3"/>
      <path d="M 168 76 L 184 92 M 168 92 L 184 76" stroke="#ff6b00" stroke-width="3"/>
      <text x="8" y="146" fill="#ff6b00">Man in the Middle &mdash; sit on the wire</text>
      <text x="8" y="164" font-size="11" opacity="0.85">neither end can tell</text>
    </g>
    <g class="k3">
      <path d="M 218 122 L 218 78" stroke="#ff6b00" stroke-width="3"/>
      <path d="M 210 88 L 226 104 M 210 104 L 226 88" stroke="#ff6b00" stroke-width="3"/>
      <text x="8" y="146" fill="#ff6b00">Flood &amp; Overwrite &mdash; pin the register</text>
      <text x="8" y="164" font-size="11" opacity="0.85">no login, no wire access</text>
    </g>
  </g>
  <text x="8" y="194" font-size="11" opacity="0.85">Three challenges, three depths, one chain.</text>
</svg>
<figcaption>Watch the round trip first: a command goes right and becomes a coil write, a measured value comes back left and becomes a number on a screen. Then watch where each of the three challenges cuts in. They are usually taught as separate exercises; they are the same chain attacked at three depths. Depth is not the same as stealth, though, and the ranking here is not the obvious one. The flood raises <code>modbus_flood</code> at critical severity &mdash; but so does the man in the middle: <code>arp_spoof</code> is critical too, and it fires on the first ARP reply carrying a second MAC rather than after fifty writes. The MitM challenge will not award its flag unless that rule has fired. The quietest of the three is the login attempt, which raises <code>http_brute_force</code> at high severity, and against FUXA's own sign-in route raises nothing at all. Guess the login and you inherit the HMI&rsquo;s credentials and its network path in one step. Sit on the wire and neither end can tell, because Modbus has no field in which to disagree. Pin the register and you need neither: just write the word more often than the sensor does.</figcaption>
</figure>

FUXA's device entry says `openplc:502`, plain Modbus TCP, and its tag table is a list of register addresses: `GST`, `HPT`, `systemSen`, `boSen`, `stop`, `manual` as holding registers, and `heartbeat`, `compressor`, `systemValve`, `gstSig` as coils. Nothing in that list is authenticated. FUXA ships an `operator` account with `operator` as its password and a `viewer` beside it, though the *Password Attack* challenge goes after `admin`, on both FUXA and OpenPLC. Either way the login protects the *screen*, not the plant. Anyone who can reach port 502 skips the screen.

## The screen can contradict itself, and does

The most useful thing about an HMI for a defender is that it shows several values from several sources. The most dangerous is that the operator reads them as one picture.

<figure>
<style>
.article figure svg.hm-t {min-width: 388px;}
.hm-t {--t: 18s;}
/* Each trace draws on its own dash length rather than a shared normalised
   sweep. They used to share one, and because the HPT trace spends arc length
   climbing its spikes, its pen ran up to 31 s of plant time behind the other
   on a figure whose whole point is "same moment, two registers". */
.hm-t .head {animation: ht-head var(--t) linear infinite;}
.hm-t .hpt  {stroke-dasharray:1400; animation: ht-hpt var(--t) linear infinite;}
.hm-t .bo   {stroke-dasharray:1000; animation: ht-bo  var(--t) linear infinite;}
.hm-t .alm  {opacity:1; animation: ht-alm var(--t) steps(1,end) infinite;}
@keyframes ht-head {0%{transform:translateX(0)} 92%,100%{transform:translateX(292px)}}
@keyframes ht-hpt  {0%{stroke-dashoffset:1400} 92%,100%{stroke-dashoffset:0}}
@keyframes ht-bo   {0%{stroke-dashoffset:1000} 92%,100%{stroke-dashoffset:0}}
@keyframes ht-alm  {0%,43.4%{opacity:0} 43.5%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .hm-t * {animation:none !important;} }
</style>
<svg class="hm-t" viewBox="0 0 360 240" role="img"
     aria-label="Two FUXA trends over one run of three hundred and thirty seconds, flooding register 1126 from the plant's normal resting band. The HPT trend sits at ten almost throughout, with six single-sample spikes where a poll landed in the fraction of a millisecond before the next forged write. The spikes rise as the run goes on, from 131 at sixty-one seconds to 254 at two hundred and ninety-eight, because what escapes is the real pressure and the real pressure is climbing. The blow-out flag, read from register 1134 and written by hwio from that same real pressure, steps from zero to one at a hundred and fifty-six seconds.">
  <text x="8" y="18" font-size="12" font-weight="bold">FUXA, &ldquo;System values&rdquo;, one flood, 330 s</text>

  <text x="52" y="38" font-size="11" opacity="0.85">HPT &mdash; register 1126 &mdash; what the trend shows</text>
  <polyline class="hpt" pathLength="1400" points="52,136 104,136 106,93 108,136 108,136 110,93 112,136 164,136 166,71 168,136 200,136 202,60 204,136 220,136 222,57 224,136 314,136 316,50 318,136 344,136" fill="none" stroke="#ff6b00" stroke-width="2.5" stroke-linejoin="round"/>
  <text x="114" y="88" font-size="11" fill="#ff6b00" font-weight="bold">131</text>
  <text x="172" y="66" font-size="11" fill="#ff6b00" font-weight="bold">195</text>
  <text x="228" y="52" font-size="11" fill="#ff6b00" font-weight="bold">234</text>
  <text x="322" y="46" font-size="11" fill="#ff6b00" font-weight="bold">254</text>
  <text x="348" y="140" text-anchor="end" font-size="11" opacity="0.85">10</text>

  <text x="52" y="158" font-size="11" opacity="0.85">boSen &mdash; register 1134 &mdash; the blow-out flag</text>
  <polyline class="bo" pathLength="1000" points="52,190 190,190 190,166 344,166" fill="none" stroke="currentColor" stroke-width="2.5" stroke-opacity="0.85"/>
  <text class="alm" x="344" y="162" text-anchor="end" font-size="11" font-weight="bold" fill="#ff6b00">alarm at 156 s</text>

  <line x1="52" y1="198" x2="344" y2="198" stroke="currentColor" stroke-opacity="0.6"/>
  <g class="head"><line x1="52" y1="198" x2="52" y2="208" stroke="currentColor" stroke-width="2"/></g>
  <g font-size="11" opacity="0.8">
    <text x="52" y="220" text-anchor="middle">0 s</text>
    <text x="185" y="220" text-anchor="middle">150</text>
    <text x="318" y="220" text-anchor="middle">300</text>
  </g>
  <text x="8" y="236" font-size="11" opacity="0.85">The spikes climb. That is the tank, seen through the gaps.</text>
</svg>
<figcaption>One run, every number from it. Flooding register 1126 at about 830 writes a second from the plant&rsquo;s own resting band: <code>boSen</code> went high at 156 s, and six of 330 polls at FUXA&rsquo;s one-per-second rate came back with the real pressure instead of 10 &mdash; 131 and 133 within the first minute, then 195, 226, 234 and 254. <code>hwio</code> puts the true value back every 20.7 ms and the next forged write buries it about a millisecond later, so a poll occasionally lands in the gap; how often is a race, and six events is too few to quote a rate from. What matters is the shape: the spikes rise, because what escapes is the real pressure and the real pressure is climbing. A single sample out of line reads as noise. On this trend it is the only measurement on the screen.</figcaption>
</figure>

Why does the flag survive when the pressure does not? Because `hwio` never reads the pressure back. Its loop reads the four coils and nothing else, and then writes five register blocks; the true pressure lives as a local variable inside the plant model and reaches Modbus only on the way out. Flooding 1126 cannot *write* the model's variable &mdash; but it drives it. The PLC reads the forged 10, latches the compressor on and shuts the system valve; `hwio` reads those four coils back, and the tank climbs for real. So the attacker owns what everyone reads and controls what actually happens, and the one thing out of reach is the model's own arithmetic. `boSen` is computed from that arithmetic, which is why the flag stays honest while the trend does not.

That is the general defensive shape: **a value and its corroboration should not come down the same path.** Here they very nearly do &mdash; `HPT` and `boSen` are both holding registers from the same PLC, and FUXA fetches them in a single eleven-register response, so they arrive in the same frame. What separates them is only that one of them is a copy of something the attacker cannot reach. Real corroboration means a different sensor, a different protocol, or a different network. The *Detect Modbus Flooding* module takes the other route again: it does not compare values at all, it watches the wire for the flood itself.

## The address on the screen is not the address on the wire

One practical trap, and it is the reason a learner's first Modbus client usually reads the wrong word.

<figure>
<style>
.article figure svg.hm-a {min-width: 388px;}
.hm-a {--a: 9s;}
/* The base state is the settled one: the tag number has arrived and become
   the register number. Without it both texts sat at x=304 with opacity 1 and
   printed over each other -- "register 112" with a 6 and a 7 in the same
   place -- in the reduced-motion frame and with animations simply off. */
.hm-a .slide {opacity:0; transform: translateX(-86px);
              animation: ha-slide var(--a) cubic-bezier(.4,0,.2,1) infinite;}
.hm-a .off   {opacity:1; animation: ha-off var(--a) steps(1,end) infinite;}
@keyframes ha-slide {0%,22%{opacity:1; transform:translateX(0)}
                     43.9%{opacity:1; transform:translateX(-86px)}
                     44%,100%{opacity:0; transform:translateX(-86px)}}
@keyframes ha-off   {0%,43.9%{opacity:0} 44%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .hm-a * {animation:none !important;} }
</style>
<svg class="hm-a" viewBox="0 0 360 176" role="img"
     aria-label="FUXA lists the HPT tag at address 1127 and the GST tag at 1125. Those are one-based Modbus addresses. On the wire the same words are holding registers 1126 and 1124, which is what the PLC program declares as percent MW 102 and percent MW 100. The tag address slides down by one to become the register address. Every coil is offset the same way: FUXA's compressor at 2 is coil 1.">
  <text x="8" y="18" font-size="12" font-weight="bold">The same word, counted twice</text>
  <rect x="8" y="34" width="158" height="44" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="87" y="52" text-anchor="middle" font-size="11" opacity="0.85">FUXA tag table</text>
  <text x="87" y="70" text-anchor="middle" font-size="13" font-weight="bold">HPT &rarr; address 1127</text>

  <rect x="194" y="34" width="158" height="44" rx="5" fill="#ff6b00"/>
  <text x="273" y="52" text-anchor="middle" font-size="11" style="fill:#1a1a1a">on the wire</text>
  <text class="slide" x="273" y="70" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">register 1127</text>
  <text class="off" x="273" y="70" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">register 1126</text>

  <text class="off" x="180" y="100" text-anchor="middle" font-size="12" fill="#ff6b00" font-weight="bold">&minus;1</text>
  <text x="8" y="128" font-size="12" opacity="0.9">FUXA counts from one. The protocol counts from zero.</text>
  <text x="8" y="146" font-size="12" opacity="0.9">&#37;MW102 &rarr; 1024 + 102 = 1126, listed as 1127.</text>
  <text x="8" y="168" font-size="11" opacity="0.85">Coils too: compressor at 2 is coil 1.</text>
</svg>
<figcaption>FUXA shows one-based addresses, the wire carries zero-based ones, and the two tables sit in different files. Coils are offset the same way, so FUXA&rsquo;s compressor at address 2 is coil 1 &mdash; read coil 2 and you get the system valve, which will also look like a plausible answer. Copy a number out of the HMI into a Modbus client and you read the neighbouring word &mdash; which usually holds something plausible, so nothing announces the mistake. This platform contains a live example. <code>software/opcua/opcua.py</code> mirrors six PLC values and gets four addresses wrong, in two different ways: <code>stop</code> and <code>manual</code> read 1129 and 1131, the HMI&rsquo;s numbers, one above the 1128 and 1130 the program declares. <code>systemSen</code> and <code>boSen</code> are not off by one at all &mdash; they read holding registers 2 and 3, which the program declares nowhere, so those two nodes are permanently zero.</figcaption>
</figure>

## Why the HMI is a high-value target

- It holds **valid credentials** and a working network path to the controllers. Compromising it skips the hard part.
- It can **command** the process, and its commands look exactly like an engineer's, because they are the same writes.
- The operator **trusts what it shows**. Stuxnet replayed recorded normal readings while the centrifuges tore themselves apart underneath, and it is the cover rather than the sabotage that bought the time. Worth being precise about where that cover lived: in the controller itself and in a shim DLL on the engineering workstation, *below* the HMI. The screen was honest about what it was given. Everything it was given had been prepared.

In CybICS the FUXA login is the *Password Attack* target, the *Man in the Middle* challenge sits on the HMI-to-PLC link, and *Flood &amp; Overwrite* pins the register the HMI reads. Three different depths, one screen.

## Security relevance

Protecting the supervisory layer means strong authentication on the HMI, restricting who can reach it *and who can reach past it*, and giving the operator at least one value whose path is independent of the others. The last one is the hardest and the most valuable: when every number on the screen came down the same wire, an attacker who owns that wire owns the operator's reality, and the screen will look completely normal while it happens.
