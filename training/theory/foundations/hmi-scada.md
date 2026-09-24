# HMI and SCADA

The **Human-Machine Interface (HMI)** is the screen an operator watches: tank levels, pressures, pumps, alarms, and the buttons to start and stop the process. **SCADA** (Supervisory Control and Data Acquisition) is the wider system that gathers that data from many controllers and presents it. In CybICS the HMI is **FUXA**, a web-based SCADA/HMI on port 1881.

## The operator sees nothing directly

The HMI is not wired to a sensor. It is a Modbus client. Every number on the screen is a register it polled from OpenPLC, and every button is a register it writes back. The operator's picture of the plant is an inference, three hops from the gas.

<figure>
<style>
.article figure svg.hm-c {min-width: 360px;}
.hm-c {--p: 6s; --k: 18s;}
/* theory_article.html retints text, path and stroke for the light theme but
   never a circle, so this marker stayed #ff6b00 on white: 2.86:1. */
html.light-mode .hm-c .cmd {fill:#b34700;}
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
  <text x="8" y="194" font-size="11" opacity="0.85">Three challenges, three links, one chain.</text>
</svg>
<figcaption>Watch the round trip first: a command goes right and becomes a coil write, a measured value comes back left and becomes a number on a screen. Then watch where each of the three challenges cuts in. They are usually taught as separate exercises; they are the same chain attacked at three depths. Depth is not the same as stealth, though &mdash; the rightmost of the three is the loudest, because flooding a register is exactly what the IDS watches for. The quiet one is the middle. Guess the login and you inherit the HMI&rsquo;s credentials and its network path in one step. Sit on the wire and neither end can tell, because Modbus has no field in which to disagree. Pin the register and you need neither: just write the word more often than the sensor does.</figcaption>
</figure>

FUXA's device entry says `openplc:502`, plain Modbus TCP, and its tag table is a list of register addresses: `GST`, `HPT`, `systemSen`, `boSen`, `stop`, `manual` as holding registers, and `heartbeat`, `compressor`, `systemValve`, `gstSig` as coils. Nothing in that list is authenticated. FUXA's own login &mdash; `operator` with an `operator` password, and a `viewer` account beside it &mdash; protects the *screen*, not the plant. Anyone who can reach port 502 skips the screen.

## The screen can contradict itself, and does

The most useful thing about an HMI for a defender is that it shows several values from several sources. The most dangerous is that the operator reads them as one picture.

<figure>
<style>
.article figure svg.hm-t {min-width: 360px;}
.hm-t {--t: 18s;}
/* One 18 s loop over 210 s of plant time, so 1 s here is 11.7 s there. The
   playhead runs below the axis rather than across the plot: at full height it
   swept through both trace labels for half of every loop. */
.hm-t .head {animation: ht-head var(--t) linear infinite;}
.hm-t .hpt  {stroke-dasharray:1000; animation: ht-draw var(--t) linear infinite;}
.hm-t .bo   {stroke-dasharray:1000; animation: ht-draw var(--t) linear infinite;}
.hm-t .alm  {opacity:1; animation: ht-alm var(--t) steps(1,end) infinite;}
@keyframes ht-head {0%{transform:translateX(0)} 92%,100%{transform:translateX(292px)}}
@keyframes ht-draw {0%{stroke-dashoffset:1000} 92%,100%{stroke-dashoffset:0}}
@keyframes ht-alm  {0%,78.9%{opacity:0} 79%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .hm-t * {animation:none !important;} }
</style>
<svg class="hm-t" viewBox="0 0 360 232" role="img"
     aria-label="Two FUXA trends over two hundred and ten seconds of a register flood, measured on this stack from the plant's normal resting band. The HPT trend, which reads holding register 1126, sits at ten almost the whole time, with two single-sample spikes to the real pressure where a poll happened to land in the fraction of a millisecond before the next forged write. The blow-out flag, which reads holding register 1134 and is written by hwio from the true pressure, steps from zero to one at a hundred and eighty-one seconds. The operator's screen therefore shows a near-flat tank and a blow-out alarm at the same time, and the alarm is the honest one.">
  <text x="8" y="18" font-size="12" font-weight="bold">FUXA, &ldquo;System values&rdquo;, during a flood</text>

  <text x="52" y="40" font-size="11" opacity="0.85">HPT &mdash; register 1126 &mdash; what the trend shows</text>
  <polyline class="hpt" pathLength="1000" points="52,136 113,136 115,50 117,136 259,136 261,50 263,136 344,136" fill="none" stroke="#ff6b00" stroke-width="2.5" stroke-linejoin="round"/>
  <text x="122" y="62" font-size="11" fill="#ff6b00" font-weight="bold">one poll in 75</text>
  <text x="122" y="75" font-size="11" fill="#ff6b00">catches the truth</text>
  <text x="348" y="140" text-anchor="end" font-size="11" opacity="0.85">10</text>

  <text x="52" y="156" font-size="11" opacity="0.85">boSen &mdash; register 1134 &mdash; the blow-out flag</text>
  <polyline class="bo" pathLength="1000" points="52,188 304,188 304,164 344,164" fill="none" stroke="currentColor" stroke-width="2.5" stroke-opacity="0.85"/>
  <text class="alm" x="344" y="160" text-anchor="end" font-size="11" font-weight="bold" fill="#ff6b00">alarm at 181 s</text>

  <line x1="52" y1="196" x2="344" y2="196" stroke="currentColor" stroke-opacity="0.6"/>
  <g class="head"><line x1="52" y1="196" x2="52" y2="206" stroke="currentColor" stroke-width="2"/></g>
  <g font-size="11" opacity="0.8">
    <text x="52" y="218" text-anchor="middle">0 s</text>
    <text x="191" y="218" text-anchor="middle">100</text>
    <text x="330" y="218" text-anchor="middle">200</text>
  </g>
  <text x="8" y="232" font-size="11" opacity="0.85">Same chart. Different registers. Only one is lying.</text>
</svg>
<figcaption>Measured on this stack, starting from the plant&rsquo;s own resting band rather than a pre-charged tank: it takes about three minutes of flooding for the pressure to climb from the 60-to-90 band to the relief valve, and <code>boSen</code> went high at 181 s. Until then the operator sees nothing wrong at all. And the HPT trend is not quite the flat line it looks like &mdash; <code>hwio</code> puts the true pressure back every 20.7 ms and the next forged write buries it within about a millisecond, so a poll occasionally lands in that gap. Two of 150 polls at FUXA&rsquo;s one-per-second rate came back with the real value, 236 and 242. A single-sample spike on a trend reads as noise, which is exactly what it is not.</figcaption>
</figure>

Why does the flag survive when the pressure does not? Because `hwio` never reads the pressure back. Its loop reads the four coils and nothing else, and then writes five register blocks; the true pressure lives as a local variable inside the plant model and reaches Modbus only on the way out. Flooding 1126 corrupts what the PLC and the HMI *see*; it cannot reach the number the model is computing from, and `boSen` is written from that number. The attacker owns the copy, not the original.

That is the general defensive shape: **a value and its corroboration should not come down the same path.** Here they very nearly do &mdash; `HPT` and `boSen` are both holding registers from the same PLC, and FUXA fetches them in a single eleven-register response, so they arrive in the same frame. What separates them is only that one of them is a copy of something the attacker cannot reach. Real corroboration means a different sensor, a different protocol, or a different network. The *Detect Modbus Flooding* module takes the other route again: it does not compare values at all, it watches the wire for the flood itself.

## The address on the screen is not the address on the wire

One practical trap, and it is the reason a learner's first Modbus client usually reads the wrong word.

<figure>
<style>
.article figure svg.hm-a {min-width: 400px;}
.hm-a {--a: 9s;}
/* The base state is the settled one: the tag number has arrived and become
   the register number. Without it both texts sat at x=304 with opacity 1 and
   printed over each other -- "register 112" with a 6 and a 7 in the same
   place -- in the reduced-motion frame and with animations simply off. */
.hm-a .slide {opacity:0; transform: translateX(-96px);
              animation: ha-slide var(--a) cubic-bezier(.4,0,.2,1) infinite;}
.hm-a .off   {opacity:1; animation: ha-off var(--a) steps(1,end) infinite;}
@keyframes ha-slide {0%,22%{opacity:1; transform:translateX(0)}
                     43.9%{opacity:1; transform:translateX(-96px)}
                     44%,100%{opacity:0; transform:translateX(-96px)}}
@keyframes ha-off   {0%,43.9%{opacity:0} 44%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .hm-a * {animation:none !important;} }
</style>
<svg class="hm-a" viewBox="0 0 400 176" role="img"
     aria-label="FUXA lists the HPT tag at address 1127 and the GST tag at 1125. Those are one-based Modbus addresses. On the wire the same words are holding registers 1126 and 1124, which is what the PLC program declares as percent MW 102 and percent MW 100. The tag address slides down by one to become the register address. Every coil is offset the same way: FUXA's compressor at 2 is coil 1.">
  <text x="8" y="18" font-size="12" font-weight="bold">The same word, counted twice</text>
  <rect x="8" y="34" width="176" height="44" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="96" y="52" text-anchor="middle" font-size="11" opacity="0.85">FUXA tag table</text>
  <text x="96" y="70" text-anchor="middle" font-size="13" font-weight="bold">HPT &rarr; address 1127</text>

  <rect x="216" y="34" width="176" height="44" rx="5" fill="#ff6b00"/>
  <text x="304" y="52" text-anchor="middle" font-size="11" style="fill:#1a1a1a">on the wire</text>
  <text class="slide" x="304" y="70" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">register 1127</text>
  <text class="off" x="304" y="70" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">register 1126</text>

  <text class="off" x="200" y="100" text-anchor="middle" font-size="12" fill="#ff6b00" font-weight="bold">&minus;1</text>
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
