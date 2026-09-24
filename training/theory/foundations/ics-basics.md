# What is an Industrial Control System?

An **Industrial Control System (ICS)** is the combination of hardware and software that monitors and controls a physical process: a gas plant, a water works, a power grid, a production line. Unlike ordinary IT, an ICS acts on the real world. A wrong value does not corrupt a spreadsheet, it opens a valve.

This is why the priorities are inverted compared to IT. A control system runs for twenty or thirty years, there is rarely a window in which it can be stopped to patch, and a process that halts can be more dangerous than one running badly. In IT the order is usually **confidentiality, integrity, availability**. In operational technology (OT) it is the reverse: keeping the process running safely comes first.

<figure>
<style>
/* The inversion is a reordering, so the figure reorders: the two outer goals
   trade places and the reader sees which one moved. Orange marks rank 1 and
   nothing else, in both the animated and the static version -- when it marked
   a goal instead, the two versions disagreed about what the colour meant. */
.pri {--p: 12s;}
.pri .swap-c {animation: p-right var(--p) ease-in-out infinite;}
.pri .swap-a {animation: p-left  var(--p) ease-in-out infinite;}
.pri .lab-it {animation: p-it    var(--p) steps(1,end) infinite;}
.pri .lab-ot {opacity:0; animation: p-ot var(--p) steps(1,end) infinite;}
/* Inverted: the static two-row version is the default, so a browser that
   simply drops animations gets both orderings rather than the IT row alone
   with no hint that anything was meant to move. */
.pri {display:none;}
.pri-static {display:block;}
@media (prefers-reduced-motion: no-preference) {
  .pri {display:block;}
  .pri-static {display:none;}
}
@keyframes p-right {0%,25%{transform:translate(0,0)} 27%{transform:translate(16px,38px)}
                    36%{transform:translate(324px,38px)} 38%,88%{transform:translate(340px,0)}
                    90%{transform:translate(324px,38px)} 98%{transform:translate(16px,38px)}
                    100%{transform:translate(0,0)}}
@keyframes p-left  {0%,25%{transform:translate(0,0)} 27%{transform:translate(-16px,76px)}
                    36%{transform:translate(-324px,76px)} 38%,88%{transform:translate(-340px,0)}
                    90%{transform:translate(-324px,76px)} 98%{transform:translate(-16px,76px)}
                    100%{transform:translate(0,0)}}
@keyframes p-it {0%,31%{opacity:1} 31.01%,94%{opacity:0} 94.01%,100%{opacity:1}}
@keyframes p-ot {0%,31%{opacity:0} 31.01%,94%{opacity:1} 94.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .pri {display:none;}
  .pri-static {display:block;}
  /* kept explicit: the no-preference block above must not win here */
}
</style>
<svg class="pri" viewBox="0 0 520 166" role="img"
     aria-label="The same three security goals in one row, ordered most important on the left. IT ranks them confidentiality, integrity, availability; OT swaps the outer two, so availability leads and confidentiality comes last.">
  <text class="lab-it" x="10" y="20" font-size="13" font-weight="bold">IT priorities</text>
  <text class="lab-ot" x="10" y="20" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>

  <text x="20" y="60" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
  <text x="190" y="60" font-size="12" font-weight="bold" opacity="0.78">2.</text>
  <text x="360" y="60" font-size="12" font-weight="bold" opacity="0.78">3.</text>

  <g class="swap-c">
    <rect x="34" y="38" width="136" height="30" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="102" y="58" font-size="12" text-anchor="middle">Confidentiality</text>
  </g>
  <g class="swap-a">
    <rect x="374" y="38" width="136" height="30" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="442" y="58" font-size="12" text-anchor="middle">Availability</text>
  </g>
  <g>
    <rect x="204" y="38" width="136" height="30" rx="4" fill="currentColor" fill-opacity="0.28" stroke="currentColor"/>
    <text x="272" y="58" font-size="12" text-anchor="middle">Integrity</text>
  </g>
  <text x="102" y="160" font-size="13" opacity="0.7" text-anchor="middle">most important</text>
  <text x="442" y="160" font-size="13" opacity="0.7" text-anchor="middle">least important</text>
</svg>
<svg class="pri-static" viewBox="0 0 520 134" role="img"
     aria-label="IT ranks the three goals confidentiality, integrity, availability. OT reverses the outer two: availability first, integrity second, confidentiality last.">
  <g font-size="12">
    <text x="10" y="20" font-size="13" font-weight="bold">IT priorities</text>
    <text x="4" y="45" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
    <rect x="22" y="28" width="148" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="96" y="45" text-anchor="middle">Confidentiality</text>
    <rect x="180" y="28" width="160" height="26" rx="4" fill="currentColor" fill-opacity="0.28" stroke="currentColor"/>
    <text x="260" y="45" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="28" width="160" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="430" y="45" text-anchor="middle">3. Availability</text>

    <text x="10" y="86" font-size="13" font-weight="bold" fill="#ff6b00">OT priorities</text>
    <text x="4" y="111" font-size="12" font-weight="bold" fill="#ff6b00">1.</text>
    <rect x="22" y="94" width="148" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="96" y="111" text-anchor="middle">Availability</text>
    <rect x="180" y="94" width="160" height="26" rx="4" fill="currentColor" fill-opacity="0.28" stroke="currentColor"/>
    <text x="260" y="111" text-anchor="middle">2. Integrity</text>
    <rect x="350" y="94" width="160" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor"/>
    <text x="430" y="111" text-anchor="middle">3. Confidentiality</text>
  </g>
</svg>
<figcaption>Integrity does not move. What changes is which of the other two you give up first &mdash; and above both of them sits safety, because the process must not hurt anyone.</figcaption>
</figure>

## The Purdue model

ICS networks are traditionally described with the **Purdue Enterprise Reference Architecture**, a layered model that separates the office from the plant floor. Each level talks mostly to its neighbours, and the security boundary that matters most sits between Level 3 and the enterprise above it &mdash; usually as an OT DMZ, so that no host in the office ever speaks directly to a controller.

<figure>
<style>
.pur {--u: 10s;}
/* The intruder walks down the levels. The boundary it crosses is the one the
   DMZ is supposed to occupy, so the crossing is the moment worth watching. */
.pur .walk {animation: u-walk var(--u) ease-in-out infinite;}
/* theory_article.html retints text[fill], path[fill] and [stroke] for the
   light theme but cannot reach a circle, so the intruder marker stayed at
   #ff6b00 on white: 2.86:1. */
html.light-mode .pur .intr {fill:#b34700;}
/* and the glyph on it: #1a1a1a was 6.10:1 on #ff6b00 but only 3.16:1 once the
   circle became #b34700. White is 5.50:1 there. */
html.light-mode .pur .intr-t {fill:#ffffff !important;}
.pur .dmz  {animation: u-dmz  var(--u) linear infinite;}
@keyframes u-walk {0%,6%{transform:translateY(0)}      14%,22%{transform:translateY(0)}
                   30%,38%{transform:translateY(50px)}  46%,54%{transform:translateY(100px)}
                   62%,70%{transform:translateY(150px)} 78%,94%{transform:translateY(200px)}
                   100%{transform:translateY(0)}}
/* The resting state was 0.5 opacity, which blends to 2.47:1 on the dark
   ground and 2.21:1 on the light one -- under the 3:1 a meaningful graphic
   needs, for 92 per cent of the loop, on the one line the caption calls the
   point of the figure. The pulse still reads as a pulse at 0.75. */
@keyframes u-dmz  {0%,24%{stroke-opacity:0.75; stroke-width:2}
                   26%,34%{stroke-opacity:1; stroke-width:3}
                   36%,100%{stroke-opacity:0.75; stroke-width:2}}
@media (prefers-reduced-motion: reduce) {
  .pur .walk {animation:none; transform:translateY(200px);}
  .pur .dmz  {animation:none;}
}
</style>
<svg class="pur" viewBox="0 0 520 266" role="img"
     aria-label="The five Purdue levels from enterprise IT down to the physical process. An intruder starting at the enterprise level descends one level at a time to the process. The DMZ boundary it crosses sits between Level 3 and the enterprise; CybICS has no such boundary: the plant components share one flat network, and the IDS watches from the host.">
  <g font-size="14">
    <rect x="70" y="10" width="440" height="40" rx="5" fill="currentColor" opacity="0.10" stroke="currentColor"/>
    <text x="82" y="35">Level 4/5 &mdash; Enterprise IT</text>
    <rect x="70" y="60" width="440" height="40" rx="5" fill="currentColor" opacity="0.14" stroke="currentColor"/>
    <text x="82" y="85">Level 3 &mdash; Operations</text>
    <rect x="70" y="110" width="440" height="40" rx="5" fill="#ff6b00" opacity="0.30" stroke="#ff6b00"/>
    <text x="82" y="135">Level 2 &mdash; Supervisory (SCADA, HMI)</text>
    <rect x="70" y="160" width="440" height="40" rx="5" fill="#ff6b00" opacity="0.45" stroke="#ff6b00"/>
    <text x="82" y="185">Level 1 &mdash; Control (PLCs)</text>
    <rect x="70" y="210" width="440" height="40" rx="5" fill="#ff6b00" stroke="#ff6b00"/>
    <text x="82" y="235" style="fill:#1a1a1a">Level 0 &mdash; Process (sensors, valves)</text>
  </g>

  <line class="dmz" x1="70" y1="55" x2="510" y2="55" stroke="#ff6b00" stroke-dasharray="6 4"/>

  <g class="walk">
    <circle class="intr" cx="40" cy="30" r="10" fill="#ff6b00"/>
    <text class="intr-t" x="40" y="34" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">!</text>
  </g>

</svg>
<figcaption>The dashed line is where the IT/OT boundary belongs: between the enterprise and everything that can reach a controller, usually built as an OT DMZ. An intruder that starts at the top reaches the process by descending all five levels. The descent is the point: each step meets a different service and a different topic in this path, and the only thing that would have stopped it is a boundary CybICS deliberately does not have.</figcaption>
</figure>

## Where CybICS fits

CybICS is a small but complete ICS, and every simulated plant component sits on the same bridge network, `172.18.0.0/24`, with nothing between them. That is not an oversight &mdash; it is what makes the attacks in the later modules reachable from a single machine. Two services are deliberately outside it: the landing page and the IDS run on the *host* network, which is how the IDS gets to see traffic between containers it is not a party to.

| Purdue level | CybICS component | Address |
|---|---|---|
| Level 4/5 (Enterprise) | Attack machine, standing in for any compromised office host | 172.18.0.100 |
| Level 3 (Operations) | Engineering workstation | 172.18.0.10 |
| Level 2 (Supervisory) | FUXA HMI; OPC-UA and S7comm servers alongside it | 172.18.0.4, .5, .6 |
| Level 1 (Control) | OpenPLC runtime executing the plant program | 172.18.0.3 |
| Level 0 (Process) | `hwio`, which runs the gas pressure simulation and writes its readings into the PLC | 172.18.0.2 |

On real hardware, Level 0 is not a container at all: the STM32 on the CybICS board runs the process, and `hwio` becomes a genuine bridge, talking to it over I&sup2;C at address 0x20.

## The process you are actually protecting

Everything above exists to run one small plant. A compressor pumps gas from a storage tank (**GST**) into a high pressure tank (**HPT**), and the downstream process draws from the HPT while the system valve is open &mdash; but only while the compressor is off, because the simulation puts the draw in the `else` of `if compressor > 0` and so gives the plant one job per tick. Both readings are a single byte, 0 to 255, and OpenPLC is the thing that decides: it reads the HPT pressure out of register 1126 and drives the compressor on coil 1. That loop &mdash; sensor, controller, actuator, process, sensor again &mdash; is what makes this a *control* system rather than a machine.

Left alone, the loop is dull on purpose. OpenPLC starts the compressor when the HPT falls below 60 and stops it at 90, so the pressure saws gently between the two, comfortably inside the 50-to-100 band in which the plant reports itself healthy. Nothing ever goes near the relief valve.

<figure>
<style>
/* `.article figure svg` is capped at max-width:100%, so on a 390 px screen a
   520-unit viewBox rendered its 13-unit labels at 7.9 CSS px. min-width beats
   max-width, so each figure keeps one viewBox unit per pixel and scrolls
   inside its own figure instead of shrinking below readability. The selector
   has to be at least as specific as the template's `.article figure svg`: a
   bare `svg.plt` is one step weaker and loses, silently. */
.article figure svg.pri, .article figure svg.pri-static,
.article figure svg.pur {min-width: 520px;}
.article figure svg.plt {min-width: 400px;}
.plt {--t: 20s; --on:#ff6b00; --on-ink:#1a1a1a;}
html.light-mode .plt {--on:#b34700; --on-ink:#ffffff;}
html.light-mode .plt .hpt {fill:#b34700;}
html.light-mode .plt .gst {opacity:0.55;}
/* transform-box defaults to view-box for SVG, so `center bottom` would anchor
   at the bottom of the *viewBox*, not of the rect -- which put the fills
   outside their tanks entirely. fill-box anchors on the element's own box. */
.plt .lvl {transform-box: fill-box; transform-origin: bottom;}
.plt .gst {transform: scaleY(0.941);}
.plt .hpt {transform: scaleY(0.235);}
/* The template sets `.article figure svg text:not([fill])` at (0,2,3); a bare
   `.plt .compt` is (0,2,0) and loses to it, so with animations switched off
   this label rendered light grey on orange at 2.34:1. Only the running
   keyframes were holding it dark. */
.article figure svg text.compt {fill:var(--on-ink);}
.plt .gst {animation: t-gst var(--t) linear infinite;}
.plt .hpt {animation: t-hpt var(--t) linear infinite;}
.plt .comp{fill:var(--on); animation: t-comp var(--t) steps(1,end) infinite;}
.plt .compt{animation: t-compt var(--t) steps(1,end) infinite;}
.plt .vent{opacity:0; animation: t-vent var(--t) steps(1,end) infinite;}
.plt .man {opacity:0; animation: t-hold var(--t) steps(1,end) infinite;}
.plt .sup {opacity:0; animation: t-man  var(--t) steps(1,end) infinite;}
.plt .ph-n{animation: t-phn var(--t) steps(1,end) infinite;}
.plt .ph-a{opacity:0; animation: t-man var(--t) steps(1,end) infinite;}
.plt .stuck{opacity:0; animation: t-stuck var(--t) steps(1,end) infinite;}
.plt .rst  {opacity:0; animation: t-rst   var(--t) steps(1,end) infinite;}
.plt .sv-open{animation: t-phn var(--t) steps(1,end) infinite;}
.plt .sv-shut{opacity:0; animation: t-man var(--t) steps(1,end) infinite;}
/* One clock for every segment, from a single chained run of
   physical_process_thread over 3000 seeds -- one scenario start to finish, not
   eight independent segments, so the state each segment hands to the next is
   the state the model actually produces:
     A  30  auto, compressor on,  60 -> 90     E   93  venting, 221 -> 255
     B  30  auto, compressor off, 90 -> 60     F   10  pinned at the 255 cap
     C  15  auto, compressor on,  60 -> 75     G  109  vent only, 255 -> 200
     D 147  manual, valve shut,   75 -> 221    H   20  supply fills GST to 251
     + 55 ticks of dwell = 509 ticks over 20 s = 25.4 ticks per second.
   The vent segment used to be drawn at 124 ticks, a third too long, which made
   the climb above 220 look 3.6x slower than the fill below it where the model
   gives 2.7x. The extra slowdown is not the spring: by then the compressor is
   duty-cycling on the `gst >= 50` guard about nine ticks in ten. The dwell is
   real -- with the compressor off, the valve shut and the vent latch released
   at 200 nothing moves the pressure, and once GST reaches the 251 supply cap
   nothing moves that either. It is a genuine fixed point, which is the whole
   point of the figure, so it now gets 2.9 s instead of 0.6 s. */
@keyframes t-hpt {0%{transform:scaleY(0.235)}     5.90%{transform:scaleY(0.353)}
                  11.84%{transform:scaleY(0.235)} 14.85%{transform:scaleY(0.294)}
                  43.78%{transform:scaleY(0.867)} 61.98%,63.94%{transform:scaleY(1)}
                  85.31%,100%{transform:scaleY(0.784)}}
@keyframes t-gst {0%{transform:scaleY(0.941)}     5.90%,11.84%{transform:scaleY(0.706)}
                  14.85%{transform:scaleY(0.588)} 43.78%{transform:scaleY(0.298)}
                  61.98%{transform:scaleY(0.212)} 63.94%{transform:scaleY(0.236)}
                  85.31%{transform:scaleY(0.871)} 89.19%,100%{transform:scaleY(0.984)}}
@keyframes t-comp {0%,5.90%{fill:var(--on); fill-opacity:1}
                   5.91%,11.84%{fill:currentColor; fill-opacity:0.18}
                   11.85%,63.94%{fill:var(--on); fill-opacity:1}
                   63.95%,100%{fill:currentColor; fill-opacity:0.18}}
@keyframes t-compt{0%,5.90%{fill:var(--on-ink)} 5.91%,11.84%{fill:currentColor}
                   11.85%,63.94%{fill:var(--on-ink)} 63.95%,100%{fill:currentColor}}
@keyframes t-vent {0%,43.77%{opacity:0} 43.78%,85.31%{opacity:1} 85.32%,100%{opacity:0}}
@keyframes t-man  {0%,14.84%{opacity:0} 14.85%,100%{opacity:1}}
@keyframes t-hold {0%,14.84%{opacity:0} 14.85%,63.94%{opacity:1} 63.95%,100%{opacity:0}}
@keyframes t-phn  {0%,14.84%{opacity:1} 14.85%,100%{opacity:0}}
@keyframes t-stuck{0%,85.30%{opacity:0} 85.31%,100%{opacity:1}}
/* The loop restart snaps the pressure from 200 back to 60, which silently
   undoes the damage three paragraphs say cannot be undone. Naming it stops the
   restart from reading as recovery. */
@keyframes t-rst  {0%,97.49%{opacity:0} 97.50%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) {
  /* The frozen frame is the end state: compressor stopped, valve shut, the
     pressure resting at 200 -- and the storage tank at 251, where the supply
     valve's own `gst < 251` guard stops it. */
  .plt .gst {animation:none; transform:scaleY(0.984);}
  .plt .hpt {animation:none; transform:scaleY(0.784);}
  .plt .comp {animation:none; fill:currentColor; fill-opacity:0.18;}
  .plt .compt{animation:none; fill:currentColor;}
  .plt .sup,.plt .ph-a,.plt .stuck,.plt .sv-shut {animation:none; opacity:1;}
  .plt .rst {animation:none; opacity:0;}
  .plt .sv-open{animation:none; opacity:0;}
  .plt .man {animation:none; opacity:0;}
  .plt .vent{animation:none; opacity:0;}
  .plt .ph-n{animation:none; opacity:0;}
}
</style>
<svg class="plt" viewBox="0 0 460 320" role="img"
     aria-label="The CybICS control loop. OpenPLC reads the high pressure tank from register 1126 and drives the compressor on coil 1, holding the pressure between 60 and 90 while the system valve lets the downstream process draw from it. An operator then switches to manual mode, shuts the system valve and runs the compressor; the pressure climbs past 220, the relief valve opens but only halves the rate of rise, and when the compressor finally stops the pressure settles at 200 and stays there, because the shut valve leaves no consumer.">
  <!-- storage tank; the fill is 126 units tall with its base at y=198, so a
       value v sits at y = 198 - 126*v/255 -->
  <rect x="24" y="70" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl gst" x="26" y="72" width="52" height="126" fill="currentColor" opacity="0.6"/>
  <text x="52" y="216" text-anchor="middle" font-size="13" font-weight="bold">GST</text>
  <g class="sup">
    <path d="M 52 36 L 52 62" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 46 54 L 52 64 L 58 54" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="52" y="28" text-anchor="middle" font-size="13" fill="#ff6b00">supply</text>
  </g>

  <rect class="comp" x="134" y="115" width="90" height="40" rx="5" stroke="currentColor" stroke-opacity="0.5"/>
  <text class="compt" x="179" y="140" text-anchor="middle" font-size="13" font-weight="bold">compressor</text>
  <path d="M 84 135 L 130 135" stroke="currentColor" stroke-width="2"/>
  <path d="M 228 135 L 286 135" stroke="currentColor" stroke-width="2"/>
  <text x="179" y="176" text-anchor="middle" font-size="13" opacity="0.85">&minus;2 GST &rarr; +1 HPT</text>
  <g class="man">
    <rect x="132" y="90" width="94" height="20" rx="3" fill="var(--on)"/>
    <text x="179" y="105" text-anchor="middle" font-size="13" style="fill:var(--on-ink)" font-weight="bold">held on by hand</text>
  </g>

  <rect x="290" y="70" width="56" height="130" rx="4" fill="none" stroke="currentColor"/>
  <rect class="lvl hpt" x="292" y="72" width="52" height="126" fill="#ff6b00"/>
  <text x="318" y="216" text-anchor="middle" font-size="13" font-weight="bold">HPT</text>
  <g font-size="11">
    <line x1="288" y1="89" x2="348" y2="89" stroke="currentColor" stroke-width="2" stroke-dasharray="5 5"/>
    <line x1="288" y1="89" x2="348" y2="89" stroke="var(--on-ink)" stroke-width="2" stroke-dasharray="5 5" stroke-dashoffset="5"/>
    <text x="284" text-anchor="end" y="85" fill="#ff6b00" font-weight="bold">220</text>
    <line x1="288" y1="99" x2="348" y2="99" stroke="currentColor" stroke-dasharray="5 5" stroke-opacity="0.8"/>
    <line x1="288" y1="99" x2="348" y2="99" stroke="var(--on-ink)" stroke-dasharray="5 5" stroke-dashoffset="5" stroke-opacity="0.8"/>
    <text x="284" text-anchor="end" y="111" opacity="0.75">200</text>
    <line x1="288" y1="149" x2="348" y2="149" stroke="currentColor" stroke-dasharray="5 5" stroke-opacity="0.8"/>
    <line x1="288" y1="149" x2="348" y2="149" stroke="var(--on-ink)" stroke-dasharray="5 5" stroke-dashoffset="5" stroke-opacity="0.8"/>
    <text x="284" text-anchor="end" y="153" opacity="0.75">100</text>
    <line x1="288" y1="168" x2="348" y2="168" stroke="currentColor" stroke-dasharray="5 5" stroke-opacity="0.8"/>
    <line x1="288" y1="168" x2="348" y2="168" stroke="var(--on-ink)" stroke-dasharray="5 5" stroke-dashoffset="5" stroke-opacity="0.8"/>
    <text x="284" text-anchor="end" y="172" opacity="0.75">60</text>
  </g>
  <g class="vent">
    <path d="M 318 62 L 318 36" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 312 44 L 318 34 L 324 44" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="318" y="26" text-anchor="middle" font-size="13" fill="#ff6b00" font-weight="bold">venting</text>
  </g>

  <!-- the system valve: the one thing the challenge asks you to close -->
  <text x="372" y="210" text-anchor="middle" font-size="13" font-weight="bold">SV</text>
  <path d="M 346 186 L 398 186" stroke="currentColor" stroke-width="2"/>
  <g class="sv-open">
    <path d="M 364 178 L 364 194 L 380 186 Z" fill="none" stroke="currentColor" stroke-width="2"/>
    <path d="M 380 178 L 380 194 L 364 186 Z" fill="none" stroke="currentColor" stroke-width="2"/>
    <text x="372" y="226" text-anchor="middle" font-size="13" opacity="0.8">open</text>
  </g>
  <g class="sv-shut">
    <path d="M 364 178 L 364 194 L 380 186 Z" fill="#ff6b00"/>
    <path d="M 380 178 L 380 194 L 364 186 Z" fill="#ff6b00"/>
    <text x="372" y="226" text-anchor="middle" font-size="13" fill="#ff6b00" font-weight="bold">shut</text>
  </g>

  <rect x="160" y="242" width="180" height="44" rx="5" fill="currentColor" opacity="0.15" stroke="currentColor"/>
  <text x="250" y="262" text-anchor="middle" font-size="13" font-weight="bold">OpenPLC</text>
  <text x="250" y="278" text-anchor="middle" font-size="13" opacity="0.8">on below 60, off at 90</text>
  <path d="M 346 198 L 428 198 L 428 264 L 346 264" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 354 258 L 344 264 L 354 270" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="336" y="236" font-size="14" opacity="0.8" text-anchor="end">reads 1126</text>
  <path d="M 160 264 L 96 264 L 96 135 L 128 135" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <path d="M 120 129 L 130 135 L 120 141" fill="none" stroke="currentColor" stroke-width="1.5"/>
  <text x="102" y="210" font-size="12" opacity="0.8">drives coil 1</text>

  <text class="stuck" x="284" y="112" text-anchor="end" font-size="13" fill="#ff6b00" font-weight="bold">stuck here</text>
  <text class="ph-n" x="10" y="308" font-size="13" opacity="0.85">automatic: the loop holds 60 to 90</text>
  <text class="ph-a" x="10" y="308" font-size="13" fill="#ff6b00" font-weight="bold">manual: the operator has the controls</text>
  <text class="rst" x="450" y="308" font-size="13" text-anchor="end" font-weight="bold" fill="#ff6b00">loop restarts &mdash; the plant does not</text>
</svg>
<figcaption>The same plant twice: first with OpenPLC holding it between 60 and 90 with the system valve open, then with an operator in manual mode who has shut that valve. When the compressor finally stops, the pressure falls to 200 and no further. With reduced motion the figure holds that end state instead of animating: valve shut, compressor stopped, the tank resting at 200 with the storage tank filled to its supply cap. One tick is one pass of the simulation's `delay > 50` gate over a 20 ms sleep, so it is about a second of plant time: the twenty seconds here are roughly eight and a half minutes on the plant.</figcaption>
</figure>

The attack is the second half of that loop, and it is not a network attack at all. The *Physical Process* challenge has you log in to the FUXA HMI as `operator:operator`, press **Manual / Automatic**, close the system valve and run the compressor. Every step is a legitimate operator action; the damage comes from the combination &mdash; a shut valve with a running compressor.

Three details make it work, and each of them is a design decision rather than a bug.

**Manual mode does not fail safe, it freezes.** The whole automatic block is wrapped in `IF manual < 1`, and the inner block has no `ELSE`. In manual mode OpenPLC stops assigning the compressor, the system valve and the supply valve entirely &mdash; they keep whatever value they had at the instant the operator switched over, and the panel hands all three to the operator. The `Comp.`, `SV` and `GST` buttons in FUXA write those same three coils, and each is gated on manual mode being on. The operator opens the supply deliberately &mdash; unless manual mode was entered during the tank's own refill window, in which case `gstSig` freezes on and the supply is already feeding. Either way it matters, because of the budget at the end of this section.

All of this is in two files that must agree: `physical_process_thread` in `software/hwio-virtual/hardwareAbstraction.py` is what runs in Docker, and `thread_physical` in `software/stm32/src/main.c` is the reference it mirrors. The control logic is `software/OpenPLC/cybICS.st`.

**The relief valve does not hold the tank, it only slows it.** Above 220 the blow-out valve opens and stays open until the pressure has fallen back to 200, but it vents a random 0 or 1 unit per tick &mdash; half a unit on average &mdash; against the compressor's steady +1. The net is still positive. The valve halves the rate of rise and the tank goes to 255 anyway. The last line of defence here is a spring, and the spring loses.

The figure draws that stretch slower still, and the spring is only half the reason. By the time the pressure passes 220 the compressor has been pulling two units of storage for every one and a half the supply valve puts back, and the tank is down to about 76 &mdash; still clear of the `gst >= 50` floor, but losing half a unit a tick. It reaches the floor about two fifths of the way up the vent, and from there the compressor stalls whenever the tank is momentarily empty, waiting on the supply. Averaged over the whole climb that is roughly one tick in ten. So the stretch above 220 runs at about two fifths of the rate below it, and the two causes are not equal partners. Simulated over 4000 seeds: one unit a tick below the valve, 0.51 with the valve open and storage unlimited, 0.41 with the real `gst >= 50` floor as well. The valve does 84 per cent of the slowing and the empty tank the remaining 16 &mdash; which is what a stall rate of one tick in ten ought to cost, and a useful check on the arithmetic. Neither of them stops it.

**And the damage does not undo itself.** Once the compressor stops, the only thing removing gas is the blow-out valve, which latches shut again at 200. The downstream consumer cannot help either. The valve is shut because the operator shut it, and handing the plant back to OpenPLC does not reopen it: the automatic rule only opens the valve between 50 and 100, and the tank is sitting at 200. The tank settles at 200 and sits there. Recovering it takes something from outside the loop &mdash; which is the part of an ICS incident that does not appear in the network capture.

For scale: draining two units of storage per unit of pressure, a completely full storage tank buys 103 units of pressure before the compressor stalls at the `gst >= 50` guard. That is not enough to reach 220 from the normal band on its own, which is exactly why the supply valve matters.

## Why it matters for security

Most ICS protocols have **no authentication and no encryption**, and the reason is concrete rather than philosophical: they were designed for a serial cable running inside a locked cabinet, where the cabinet was the access control. Nothing about the protocol changed when that cable became a network. OPC-UA, the newest thing on this plant, is the exception that shows the rule: it has sessions, certificates and users, and it is the only one of them that does. Having them is not the same as using them, though &mdash; the CybICS server offers `Anonymous` and `NoSecurity` alongside its signed-and-encrypted policy, which is precisely why the OPC-UA challenge on this platform is solvable at all. Any host that can reach a PLC can usually read and write its values. The rest of the Theory Path shows exactly how each protocol works, how that trust is abused, and how to detect and contain it.

> **Key idea:** in ICS security you are protecting a physical process. Every attack in the later modules ends in a real-world effect &mdash; a frozen reading, a forced valve, a tank driven past the pressure its relief valve can bleed off.
