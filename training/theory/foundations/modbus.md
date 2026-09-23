# Modbus TCP

**Modbus** is the lingua franca of industrial automation. It was designed in 1979 for serial links and later wrapped in TCP/IP as **Modbus TCP** on port **502**. It is simple, open, and everywhere &mdash; and it has no authentication, no encryption, and no *cryptographic* integrity. (There is error detection: a CRC on serial lines, the TCP checksum here. It catches a corrupted frame, not a forged one.) Whoever can reach port 502 can read and write the controller.

That is not an oversight. In 1979 the "network" was a shielded cable running a few metres inside a locked cabinet. Physical access *was* the authentication. When that cable became Ethernet, and Ethernet reached the office LAN, the protocol did not notice. A secure variant does exist &mdash; Modbus/TCP Security, TLS on port 802, published in 2018 &mdash; and almost nobody deploys it, because the installed base is measured in decades and a controller from 2004 will not learn TLS.

## The data model

Modbus exposes four tables of values. Two are bits, two are 16-bit words:

| Table | Access | Typical use |
|---|---|---|
| Coils | read/write | digital outputs (a valve, a motor) |
| Discrete inputs | read only | digital inputs (a limit switch) |
| Holding registers | read/write | analogue setpoints, counters |
| Input registers | read only | sensor readings |

In CybICS the plant's variables live in holding registers: gas storage tank at 1124, high pressure tank at 1126, and so on.

## Request and response

A client (the "master") sends a request naming a **function code** and an address; the server (the PLC) answers. There is no session and no login. Watch what that means: the register changes on the *first Modbus request* the PLC ever sees from this client. A TCP handshake did precede it &mdash; what never happens is an authentication handshake.

<figure>
<style>
/* A long cycle with most of it at rest: the motion makes its point and then
   leaves the reader alone with the paragraph, instead of looping tightly. */
.mb-x {--mb-dur: 9s;}
.mb-x .pkt {animation: mb-fly var(--mb-dur) linear infinite;}
.mb-x .ack {animation: mb-back var(--mb-dur) linear infinite;}
.mb-x .old {animation: mb-fade var(--mb-dur) linear infinite;}
.mb-x .new {animation: mb-show var(--mb-dur) linear infinite;}
.mb-x .hs  {animation: mb-blink var(--mb-dur) linear infinite;}
@keyframes mb-fly  {0%,2%{transform:translateX(0);opacity:0}
                    5%{opacity:1} 19%{transform:translateX(134px);opacity:1}
                    21%,100%{transform:translateX(134px);opacity:0}}
@keyframes mb-back {0%,26%{transform:translateX(0);opacity:0}
                    28%{opacity:1} 41%{transform:translateX(-134px);opacity:1}
                    43%,100%{transform:translateX(-134px);opacity:0}}
@keyframes mb-fade {0%,20%{opacity:1} 22%,92%{opacity:0} 94%,100%{opacity:1}}
@keyframes mb-show {0%,20%{opacity:0} 22%,92%{opacity:1} 94%,100%{opacity:0}}
/* Appears the instant the register flips, i.e. in the gap where a check
   would have been, and stays for the long rest phase. */
@keyframes mb-blink{0%,18%{opacity:0} 21%,92%{opacity:1} 94%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .mb-x .pkt,.mb-x .ack,.mb-x .old,.mb-x .new,.mb-x .hs {animation: none;}
  .mb-x .pkt,.mb-x .ack {opacity:1;}
  .mb-x .old {opacity:0;} .mb-x .new {opacity:1;} .mb-x .hs {opacity:1;}
}
</style>
<svg class="mb-x" viewBox="0 0 520 136" role="img"
     aria-label="A Modbus write travels from client to PLC; the register changes on arrival and the PLC echoes it back. A TCP handshake preceded it, but no authentication did.">
  <rect x="20" y="30" width="120" height="56" rx="6" fill="#ff6b00"/>
  <text x="80" y="52" text-anchor="middle" font-size="12" fill="#1a1a1a" font-weight="bold">Client</text>
  <text x="80" y="68" text-anchor="middle" font-size="11" fill="#1a1a1a">hwio or attacker</text>
  <text x="80" y="80" text-anchor="middle" font-size="11" fill="#1a1a1a">first request ever</text>

  <rect x="380" y="30" width="120" height="56" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="440" y="50" text-anchor="middle" font-size="12" font-weight="bold">PLC : 502</text>
  <text x="440" y="66" text-anchor="middle" font-size="11">reg 1126 =</text>
  <text class="old" x="440" y="80" text-anchor="middle" font-size="13" font-weight="bold">45</text>
  <text class="new" x="440" y="80" text-anchor="middle" font-size="13" font-weight="bold" fill="#ff6b00">90</text>

  <line x1="144" y1="46" x2="376" y2="46" stroke="currentColor" stroke-width="1"
        stroke-dasharray="3 4" opacity="0.3"/>
  <line x1="144" y1="74" x2="376" y2="74" stroke="currentColor" stroke-width="1"
        stroke-dasharray="3 4" opacity="0.3"/>

  <g class="pkt">
    <rect x="146" y="36" width="96" height="20" rx="3" fill="#ff6b00"/>
    <text x="194" y="50" text-anchor="middle" font-size="11" fill="#1a1a1a">FC 06 · 1126 · 90</text>
  </g>
  <g class="ack">
    <rect x="278" y="64" width="96" height="20" rx="3" fill="currentColor" opacity="0.2"/>
    <text x="326" y="78" text-anchor="middle" font-size="11">echo · 1126 · 90</text>
  </g>

  <g class="hs">
    <rect x="150" y="96" width="228" height="24" rx="4" fill="none"
          stroke="#ff6b00" stroke-width="1.5" stroke-dasharray="5 4"/>
    <text x="264" y="112" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">
      nothing asked who was writing
    </text>
    <path d="M 378 108 L 404 108 L 404 84" fill="none"
          stroke="#ff6b00" stroke-width="1.5" stroke-dasharray="4 3"/>
  </g>
</svg>
<figcaption>A Modbus write. Function code 6 writes one register; the PLC applies it and echoes
it back. TCP got the bytes there; nothing in Modbus asked who sent them. The gap where an
authentication step would be is the whole attack surface.</figcaption>
</figure>

The value changed before anything asked who was writing. There is no session to hijack and no login to brute-force, because there is neither. This single fact underlies the flood, overwrite and MITM attacks.

It also does not last. Register 1126 is the HPT pressure reading, and `hwio` writes the true value back into it every 20 milliseconds &mdash; so the forged 90 survives ten milliseconds on average and is gone. Nothing defended the register; something simply overwrote it, the way it overwrites it fifty times a second regardless. That is the whole reason the *Flood &amp; Overwrite* challenge is a loop rather than a single packet: the attacker is not defeating a check, they are winning a race against a process that never stops writing.

## The frame

A Modbus TCP message is a 7-byte **MBAP header** followed by the function code and its data. Three of the six fields are free for the taking; three decide what happens.

<figure>
<svg viewBox="0 0 520 108" role="img"
     aria-label="The Modbus TCP frame: a seven-byte MBAP header holding transaction id, protocol id, length and unit id, followed by the PDU holding the function code and its data. The table below the figure says what each field does.">
  <g font-size="11" text-anchor="middle">
    <rect x="10" y="30" width="80" height="42" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="50" y="22">2 B</text><text x="50" y="56">Transaction</text>
    <rect x="90" y="30" width="80" height="42" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="130" y="22">2 B</text><text x="130" y="56">Protocol</text>
    <rect x="170" y="30" width="80" height="42" fill="#ff6b00" opacity="0.4" stroke="#ff6b00"/>
    <text x="210" y="22">2 B</text><text x="210" y="56">Length</text>
    <rect x="250" y="30" width="40" height="42" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="270" y="22">1 B</text><text x="270" y="56">Unit</text>
    <rect x="290" y="30" width="40" height="42" fill="#ff6b00" stroke="#ff6b00"/>
    <text x="310" y="22">1 B</text><text x="310" y="56" style="fill:#1a1a1a">Func</text>
    <rect x="330" y="30" width="180" height="42" fill="#ff6b00" opacity="0.4" stroke="#ff6b00"/>
    <text x="420" y="22">n B</text><text x="420" y="56">Data (address, values)</text>
  </g>

  <!-- The header ends and the PDU begins at byte 7, between Unit and Func. -->
  <line x1="290" y1="24" x2="290" y2="96" stroke="currentColor" stroke-width="2"/>
  <path d="M 10 80 L 10 88 L 290 88 L 290 80" fill="none" stroke="currentColor"
        stroke-opacity="0.55"/>
  <path d="M 290 80 L 290 88 L 510 88 L 510 80" fill="none" stroke="currentColor"
        stroke-opacity="0.55"/>
  <text x="150" y="102" text-anchor="middle" font-size="11" opacity="0.8">MBAP header, 7 bytes</text>
  <text x="400" y="102" text-anchor="middle" font-size="11" opacity="0.8">PDU &mdash; what the PLC acts on</text>
</svg>
<figcaption>Orange marks the three fields a forged frame has to get right. The fields are a
layout, not a sequence, so this figure stays still: six labels read at a glance beat six shown
in turn.</figcaption>
</figure>

<table>
<thead><tr><th>Field</th><th>Size</th><th>What it does</th><th>Has to be right?</th></tr></thead>
<tbody>
<tr><td>Transaction</td><td>2 B</td><td>Echoed back so a client can match a reply to its request.</td><td>No &mdash; any value works.</td></tr>
<tr><td>Protocol</td><td>2 B</td><td>Always 0 for Modbus TCP. Nothing useful is ever checked here.</td><td>No.</td></tr>
<tr><td>Length</td><td>2 B</td><td>Number of bytes that follow, from the unit id onwards.</td><td><strong>Yes</strong> &mdash; wrong and the parse desynchronises.</td></tr>
<tr><td>Unit</td><td>1 B</td><td>Addresses a device behind a serial gateway. Usually 1.</td><td>No &mdash; unless a gateway is in the path.</td></tr>
<tr><td>Function</td><td>1 B</td><td>Read or write, bit or word. This is what the PLC acts on.</td><td><strong>Yes.</strong></td></tr>
<tr><td>Data</td><td>n B</td><td>The register address and the value. This is what changes the plant.</td><td><strong>Yes.</strong></td></tr>
</tbody>
</table>

## Reading a flag out of the registers

The *Wireshark Capture* challenge hides a flag in Modbus traffic. It is worth seeing exactly how, because the mechanism &mdash; two ASCII characters packed into each 16-bit register &mdash; is how text crosses a protocol that only knows numbers.

<figure>
<style>
.mb-d {--d: 11s;}
/* Each register is taken apart in three beats: the box is picked out, it
   splits into its two bytes, and the bytes become their characters. That
   sequence is the thing being taught, so the motion carries it rather than
   merely revealing a finished picture.
   The stagger lives in the keyframe percentages, not in animation-delay: a
   delay shifts an element's whole cycle permanently, so the figure would
   never reset together and would be correct only on its first loop. */
.mb-d .byt, .mb-d .chr {opacity:0;}
.mb-d .r1{animation: d-reg1 var(--d) steps(1,end) infinite;}
.mb-d .b1{animation: d-byt1 var(--d) steps(1,end) infinite;}
.mb-d .k1{animation: d-chr1 var(--d) steps(1,end) infinite;}
.mb-d .r2{animation: d-reg2 var(--d) steps(1,end) infinite;}
.mb-d .b2{animation: d-byt2 var(--d) steps(1,end) infinite;}
.mb-d .k2{animation: d-chr2 var(--d) steps(1,end) infinite;}
.mb-d .r3{animation: d-reg3 var(--d) steps(1,end) infinite;}
.mb-d .b3{animation: d-byt3 var(--d) steps(1,end) infinite;}
.mb-d .k3{animation: d-chr3 var(--d) steps(1,end) infinite;}
.mb-d .r4{animation: d-reg4 var(--d) steps(1,end) infinite;}
.mb-d .b4{animation: d-byt4 var(--d) steps(1,end) infinite;}
.mb-d .k4{animation: d-chr4 var(--d) steps(1,end) infinite;}
.mb-d .r5{animation: d-reg5 var(--d) steps(1,end) infinite;}
.mb-d .b5{animation: d-byt5 var(--d) steps(1,end) infinite;}
.mb-d .k5{animation: d-chr5 var(--d) steps(1,end) infinite;}
.mb-d .r6{animation: d-reg6 var(--d) steps(1,end) infinite;}
.mb-d .b6{animation: d-byt6 var(--d) steps(1,end) infinite;}
.mb-d .k6{animation: d-chr6 var(--d) steps(1,end) infinite;}
.mb-d .r7{animation: d-reg7 var(--d) steps(1,end) infinite;}
.mb-d .b7{animation: d-byt7 var(--d) steps(1,end) infinite;}
.mb-d .k7{animation: d-chr7 var(--d) steps(1,end) infinite;}
.mb-d .flag {opacity:0; animation: d-flag var(--d) steps(1,end) infinite;}
@keyframes d-reg1{0.00%,6.36%{stroke:#ff6b00; stroke-width:2.5} 6.37%,100%{stroke:currentColor; stroke-width:1}}
@keyframes d-byt1{0%,2.73%{opacity:0} 2.74%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-chr1{0%,5.91%{opacity:0} 5.92%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-reg2{0%,8.18%{stroke:currentColor; stroke-width:1} 8.18%,14.55%{stroke:#ff6b00; stroke-width:2.5} 14.56%,100%{stroke:currentColor; stroke-width:1}}
@keyframes d-byt2{0%,10.91%{opacity:0} 10.92%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-chr2{0%,14.09%{opacity:0} 14.10%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-reg3{0%,16.36%{stroke:currentColor; stroke-width:1} 16.36%,22.73%{stroke:#ff6b00; stroke-width:2.5} 22.74%,100%{stroke:currentColor; stroke-width:1}}
@keyframes d-byt3{0%,19.09%{opacity:0} 19.10%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-chr3{0%,22.27%{opacity:0} 22.28%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-reg4{0%,24.55%{stroke:currentColor; stroke-width:1} 24.55%,30.91%{stroke:#ff6b00; stroke-width:2.5} 30.92%,100%{stroke:currentColor; stroke-width:1}}
@keyframes d-byt4{0%,27.27%{opacity:0} 27.28%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-chr4{0%,30.45%{opacity:0} 30.46%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-reg5{0%,32.73%{stroke:currentColor; stroke-width:1} 32.73%,39.09%{stroke:#ff6b00; stroke-width:2.5} 39.10%,100%{stroke:currentColor; stroke-width:1}}
@keyframes d-byt5{0%,35.45%{opacity:0} 35.46%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-chr5{0%,38.64%{opacity:0} 38.65%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-reg6{0%,40.91%{stroke:currentColor; stroke-width:1} 40.91%,47.27%{stroke:#ff6b00; stroke-width:2.5} 47.28%,100%{stroke:currentColor; stroke-width:1}}
@keyframes d-byt6{0%,43.64%{opacity:0} 43.65%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-chr6{0%,46.82%{opacity:0} 46.83%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-reg7{0%,49.09%{stroke:currentColor; stroke-width:1} 49.09%,55.45%{stroke:#ff6b00; stroke-width:2.5} 55.46%,100%{stroke:currentColor; stroke-width:1}}
@keyframes d-byt7{0%,51.82%{opacity:0} 51.83%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-chr7{0%,55.00%{opacity:0} 55.01%,96%{opacity:1} 96.01%,100%{opacity:0}}
@keyframes d-flag{0%,60%{opacity:0} 64%,96%{opacity:1} 96.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .mb-d .byt,.mb-d .chr,.mb-d .flag{animation:none;opacity:1}
  /* .reg is on the rects themselves, which carry opacity="0.18"; forcing
     opacity:1 here would paint over the hex the figure exists to show. */
  .mb-d .reg{animation:none;stroke:currentColor}
}
</style>
<svg class="mb-d" viewBox="0 0 520 218" role="img"
     aria-label="One Write Multiple Registers frame carries seven registers from address 1200. Each 16-bit register splits into a high and a low byte, and each byte is one ASCII character, together spelling the flag CybICS(m0dbu$).">
  <rect x="10" y="14" width="500" height="30" rx="4" fill="#ff6b00"/>
  <text x="260" y="34" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">
    one frame &mdash; FC 16 Write Multiple Registers, address 1200, 7 registers
  </text>

  <g font-size="13" text-anchor="middle">
    <g><rect class="reg r1" x="14" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="47" y="82" font-size="13">0x4379</text></g>
    <g><rect class="reg r2" x="86" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="119" y="82" font-size="13">0x6249</text></g>
    <g><rect class="reg r3" x="158" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="191" y="82" font-size="13">0x4353</text></g>
    <g><rect class="reg r4" x="230" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="263" y="82" font-size="13">0x286D</text></g>
    <g><rect class="reg r5" x="302" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="335" y="82" font-size="13">0x3064</text></g>
    <g><rect class="reg r6" x="374" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="407" y="82" font-size="13">0x6275</text></g>
    <g><rect class="reg r7" x="446" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="479" y="82" font-size="13">0x2429</text></g>
  </g>

  <g font-size="11" text-anchor="middle">
    <g class="byt b1">
      <path d="M 47 92 L 47 98 M 30 98 L 64 98 M 30 98 L 30 102 M 64 98 L 64 102"
            stroke="currentColor" stroke-opacity="0.5" fill="none"/>
      <rect x="14" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="30" y="117" font-family="monospace" font-size="12">43</text>
      <rect x="48" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="64" y="117" font-family="monospace" font-size="12">79</text>
    </g>
    <g class="byt b2">
      <path d="M 119 92 L 119 98 M 102 98 L 136 98 M 102 98 L 102 102 M 136 98 L 136 102"
            stroke="currentColor" stroke-opacity="0.5" fill="none"/>
      <rect x="86" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="102" y="117" font-family="monospace" font-size="12">62</text>
      <rect x="120" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="136" y="117" font-family="monospace" font-size="12">49</text>
    </g>
    <g class="byt b3">
      <path d="M 191 92 L 191 98 M 174 98 L 208 98 M 174 98 L 174 102 M 208 98 L 208 102"
            stroke="currentColor" stroke-opacity="0.5" fill="none"/>
      <rect x="158" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="174" y="117" font-family="monospace" font-size="12">43</text>
      <rect x="192" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="208" y="117" font-family="monospace" font-size="12">53</text>
    </g>
    <g class="byt b4">
      <path d="M 263 92 L 263 98 M 246 98 L 280 98 M 246 98 L 246 102 M 280 98 L 280 102"
            stroke="currentColor" stroke-opacity="0.5" fill="none"/>
      <rect x="230" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="246" y="117" font-family="monospace" font-size="12">28</text>
      <rect x="264" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="280" y="117" font-family="monospace" font-size="12">6D</text>
    </g>
    <g class="byt b5">
      <path d="M 335 92 L 335 98 M 318 98 L 352 98 M 318 98 L 318 102 M 352 98 L 352 102"
            stroke="currentColor" stroke-opacity="0.5" fill="none"/>
      <rect x="302" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="318" y="117" font-family="monospace" font-size="12">30</text>
      <rect x="336" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="352" y="117" font-family="monospace" font-size="12">64</text>
    </g>
    <g class="byt b6">
      <path d="M 407 92 L 407 98 M 390 98 L 424 98 M 390 98 L 390 102 M 424 98 L 424 102"
            stroke="currentColor" stroke-opacity="0.5" fill="none"/>
      <rect x="374" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="390" y="117" font-family="monospace" font-size="12">62</text>
      <rect x="408" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="424" y="117" font-family="monospace" font-size="12">75</text>
    </g>
    <g class="byt b7">
      <path d="M 479 92 L 479 98 M 462 98 L 496 98 M 462 98 L 462 102 M 496 98 L 496 102"
            stroke="currentColor" stroke-opacity="0.5" fill="none"/>
      <rect x="446" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="462" y="117" font-family="monospace" font-size="12">24</text>
      <rect x="480" y="102" width="32" height="22" rx="3" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="496" y="117" font-family="monospace" font-size="12">29</text>
    </g>
  </g>

  <g font-size="13" text-anchor="middle" font-weight="bold">
    <g class="chr k1"><text x="30" y="146" style="fill:#ff6b00">C</text><text x="64" y="146" style="fill:#ff6b00">y</text></g>
    <g class="chr k2"><text x="102" y="146" style="fill:#ff6b00">b</text><text x="136" y="146" style="fill:#ff6b00">I</text></g>
    <g class="chr k3"><text x="174" y="146" style="fill:#ff6b00">C</text><text x="208" y="146" style="fill:#ff6b00">S</text></g>
    <g class="chr k4"><text x="246" y="146" style="fill:#ff6b00">(</text><text x="280" y="146" style="fill:#ff6b00">m</text></g>
    <g class="chr k5"><text x="318" y="146" style="fill:#ff6b00">0</text><text x="352" y="146" style="fill:#ff6b00">d</text></g>
    <g class="chr k6"><text x="390" y="146" style="fill:#ff6b00">b</text><text x="424" y="146" style="fill:#ff6b00">u</text></g>
    <g class="chr k7"><text x="462" y="146" style="fill:#ff6b00">$</text><text x="496" y="146" style="fill:#ff6b00">)</text></g>
  </g>

  <g class="flag">
    <rect x="150" y="180" width="220" height="30" rx="4" fill="#ff6b00"/>
    <text x="260" y="200" text-anchor="middle" font-size="14" style="fill:#1a1a1a" font-weight="bold">CybICS(m0dbu$)</text>
  </g>
</svg>
<figcaption>The plant writes this once per cycle from <code>hwio</code>. In Wireshark you are
looking for one <em>Write Multiple Registers</em> frame at address 1200, and the work is decoding
it: each register is two characters, high byte first. Filtering for <code>modbus</code> and reading
the Data field of that one frame is the whole challenge.</figcaption>
</figure>

## What the IDS has to work with instead

Here is the same write, sent twice: once by `hwio`, the bridge that is supposed to write the plant's registers, and once by the attack machine. Stacked and aligned, the Modbus frames are the same bytes. Only the IP header outside them differs.

<figure>
<svg viewBox="0 0 520 146" role="img"
     aria-label="Two identical Modbus frames stacked and aligned, one from hwio at 172.18.0.2 and one from the attack machine at 172.18.0.100. Every Modbus byte matches; only the source address in the IP header differs.">
  <text x="10" y="18" font-size="11" opacity="0.75">outside the Modbus frame</text>
  <text x="200" y="18" font-size="11" opacity="0.75">the Modbus frame itself</text>

  <g font-size="11">
    <rect x="10" y="28" width="176" height="34" rx="4" fill="currentColor" opacity="0.2" stroke="currentColor"/>
    <text x="20" y="43">src 172.18.0.2</text>
    <text x="20" y="57" opacity="0.75">hwio &mdash; the plant bridge</text>
    <rect x="194" y="28" width="316" height="34" rx="4" fill="currentColor" opacity="0.12" stroke="currentColor" stroke-opacity="0.5"/>
    <text x="352" y="49" text-anchor="middle" font-family="monospace" font-size="12">00 01 00 00 00 06 01 06 04 66 00 5a</text>
  </g>

  <g font-size="11">
    <rect x="10" y="74" width="176" height="34" rx="4" fill="#ff6b00"/>
    <text x="20" y="89" style="fill:#1a1a1a">src 172.18.0.100</text>
    <text x="20" y="103" style="fill:#1a1a1a">attack machine</text>
    <rect x="194" y="74" width="316" height="34" rx="4" fill="currentColor" opacity="0.12" stroke="currentColor" stroke-opacity="0.5"/>
    <text x="352" y="95" text-anchor="middle" font-family="monospace" font-size="12">00 01 00 00 00 06 01 06 04 66 00 5a</text>
  </g>

  <line x1="194" y1="116" x2="510" y2="116" stroke="#ff6b00" stroke-width="1" stroke-dasharray="4 4"/>
  <text x="352" y="132" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">
    byte for byte the same request
  </text>
  <line x1="10" y1="116" x2="186" y2="116" stroke="currentColor" stroke-opacity="0.4" stroke-width="1" stroke-dasharray="4 4"/>
  <text x="98" y="132" text-anchor="middle" font-size="11" opacity="0.85">the only difference</text>

</svg>
<figcaption>A source address is identity you can forge, and that is the honest limit of this rule. Both frames write 0x5a (90) to register 0x0466 (1126). Even the transaction id is the attacker's to choose: <code>hwio</code> lets pymodbus count it up per request, and a forged frame simply picks one. This one is still on purpose:
comparing two things is what eyes do well when both are visible at once, and sliding them past
each other in turn would make it harder, not clearer. Nothing but <code>hwio</code> has any business writing 1126 &mdash; which is not the same as nothing else being able to.</figcaption>
</figure>

So the IDS cannot ask Modbus who is writing. It asks the IP header, and then asks how often and what:

- **Rule 3, flood** &mdash; 50 writes in 5 seconds from one source. Its exemption list is `hwio`, `fuxa` and `openplc`, and only the first of those earns its place: `hwio` writes the plant registers at 50 Hz, `fuxa` writes a coil or a mode register when an operator clicks something, and `openplc` writes nothing at all &mdash; it is the *server* on 172.18.0.3, its `Slave_dev` table is empty, so it has no slave to poll and never originates a write at all. The Modbus rules would not have looked anyway: `check_packet` only runs them on traffic *towards* port 502, never on the replies coming back from it. The port-scan and ARP rules are not gated that way, which is why they still catch the neighbouring attacks. That entry exempts a host that was never going to trigger the rule. Allowlists accumulate entries like this, and nobody re-derives them.
- **Rule 4, unauthorised write** &mdash; 10 writes in 30 seconds from a source that is not `hwio` or `fuxa`. A narrower list than rule 3's, and note the threshold: a *single* write from the attack machine raises nothing at all.
- **Rule 5, diagnostic** &mdash; function code 0x08 or 0x2B from anywhere.

That rule 4 threshold is not a detail. Three writes five seconds apart stay under it indefinitely, which is exactly what the *IDS Evasion* challenge does &mdash; its solver says so in as many words. A detector tuned to catch a flood is, by construction, blind to patience.

## Common function codes

- **1/2** read coils / discrete inputs
- **3/4** read holding / input registers
- **5/6** write single coil / register
- **15/16** write multiple coils / registers
- **8** diagnostics &mdash; specified for serial lines. OpenPLC does *not* implement it: `processModbusMessage()` falls through to `ERR_ILLEGAL_FUNCTION` and answers with exception 0x01
- **43 (0x2B)** encapsulated transport / device identification &mdash; likewise refused

Those last two are worth dwelling on. The PLC rejecting a function code does not make the attempt harmless or invisible: the *Fuzzing Modbus* challenge passes when the IDS's `modbus_diagnostic` rule fires, which happens because the **request crossed the wire**, not because anything replied. `check_fuzzing_attack.py` asks the IDS, not the PLC. Detection has to sit on the network precisely because a refusal at the endpoint leaves no trace the endpoint will tell you about.

## Security relevance

Because Modbus carries no identity of its own, the CybICS IDS borrows one from the layer below and mixes it with behaviour: a burst of 50 writes in 5 seconds (flood, rule 3), 10 writes in 30 seconds from a source that is not `hwio` or `fuxa` (unauthorised write, rule 4), or a single diagnostic function code (rule 5). Only rule 5 is a signature: one byte matched, alerting on the first packet that carries it. The other two are rate rules, and *both* carry an IP allowlist on top of their counter &mdash; which is identity of a sort &mdash; just the weakest sort, since the attack machine sits on the same bridge and can claim any address it likes.

Note what that costs. A behavioural rule has no ground truth to appeal to, so it is a judgement about what is normal *here*, tuned against this plant's traffic. Change the polling rate and the flood threshold is wrong. An address allowlist is worse: it is exactly as strong as the assumption that nobody spoofs. Both trade-offs are the subject of the *IDS Monitoring & Tuning* challenge.
