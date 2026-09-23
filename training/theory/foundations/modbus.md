# Modbus TCP

**Modbus** is the lingua franca of industrial automation. It was designed in 1979 for
serial links and later wrapped in TCP/IP as **Modbus TCP** on port **502**. It is simple,
open, and everywhere &mdash; and it has no authentication, no encryption, and no
*cryptographic* integrity. (There is error detection: a CRC on serial lines, the TCP
checksum here. It catches a corrupted frame, not a forged one.) Whoever can reach port 502
can read and write the controller.

That is not an oversight. In 1979 the "network" was a shielded cable running a few metres
inside a locked cabinet. Physical access *was* the authentication. When that cable became
Ethernet, and Ethernet reached the office LAN, the protocol did not notice. A secure
variant does exist &mdash; Modbus/TCP Security, TLS on port 802, published in 2018 &mdash;
and almost nobody deploys it, because the installed base is measured in decades and a
controller from 2004 will not learn TLS.

## The data model

Modbus exposes four tables of values. Two are bits, two are 16-bit words:

| Table | Access | Typical use |
|---|---|---|
| Coils | read/write | digital outputs (a valve, a motor) |
| Discrete inputs | read only | digital inputs (a limit switch) |
| Holding registers | read/write | analogue setpoints, counters |
| Input registers | read only | sensor readings |

In CybICS the plant's variables live in holding registers: gas storage tank at 1124, high
pressure tank at 1126, and so on.

## Request and response

A client (the "master") sends a request naming a **function code** and an address; the
server (the PLC) answers. There is no session and no login. Watch what that means: the
register changes on the *first Modbus request* the PLC ever sees from this client. A
TCP handshake did precede it &mdash; what never happens is an authentication handshake.

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
                    5%{opacity:1} 19%{transform:translateX(232px);opacity:1}
                    21%,100%{transform:translateX(232px);opacity:0}}
@keyframes mb-back {0%,26%{transform:translateX(0);opacity:0}
                    28%{opacity:1} 41%{transform:translateX(-232px);opacity:1}
                    43%,100%{transform:translateX(-232px);opacity:0}}
@keyframes mb-fade {0%,20%{opacity:1} 22%,92%{opacity:0} 94%,100%{opacity:1}}
@keyframes mb-show {0%,20%{opacity:0} 22%,92%{opacity:1} 94%,100%{opacity:0}}
@keyframes mb-blink{0%,45%{opacity:0} 48%,90%{opacity:1} 92%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .mb-x .pkt,.mb-x .ack,.mb-x .old,.mb-x .new,.mb-x .hs {animation: none;}
  .mb-x .pkt,.mb-x .ack {opacity:1;}
  .mb-x .old {opacity:0;} .mb-x .new {opacity:1;} .mb-x .hs {opacity:1;}
}
</style>
<svg class="mb-x" viewBox="0 0 520 136" role="img"
     aria-label="A Modbus write travels from client to PLC; the register changes on arrival and the PLC echoes it back. A TCP handshake preceded it, but no authentication did.">
  <rect x="20" y="30" width="120" height="56" rx="6" fill="#ff6b00" opacity="0.85"/>
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
    <rect x="278" y="64" width="96" height="20" rx="3" fill="currentColor" opacity="0.45"/>
    <text x="326" y="78" text-anchor="middle" font-size="11">echo · 1126 · 90</text>
  </g>

  <g class="hs">
    <text x="260" y="118" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">
      no authentication happened here
    </text>
  </g>
</svg>
<figcaption>A Modbus write. Function code 6 writes one register; the PLC applies it and echoes
it back. TCP got the bytes there; nothing in Modbus asked who sent them. The gap where an
authentication step would be is the whole attack surface.</figcaption>
</figure>

The value changed before anything asked who was writing. There is no session to hijack and no
login to brute-force, because there is neither. This single fact underlies the flood,
overwrite and MITM attacks.

## The frame

A Modbus TCP message is a 7-byte **MBAP header** followed by the function code and its data.
Three of the six fields are free for the taking; three decide what happens.

<figure>
<svg viewBox="0 0 520 250" role="img"
     aria-label="The Modbus TCP frame: transaction id, protocol id, length, unit id, function code and data, each labelled with what it does and whether an attacker must get it right.">
  <g font-size="11" text-anchor="middle">
    <rect x="10" y="26" width="70" height="42" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="45" y="18">2 B</text><text x="45" y="52">Transaction</text>
    <rect x="80" y="26" width="70" height="42" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="115" y="18">2 B</text><text x="115" y="52">Protocol</text>
    <rect x="150" y="26" width="70" height="42" fill="#ff6b00" opacity="0.4" stroke="#ff6b00"/>
    <text x="185" y="18">2 B</text><text x="185" y="52">Length</text>
    <rect x="220" y="26" width="50" height="42" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="245" y="18">1 B</text><text x="245" y="52">Unit</text>
    <rect x="270" y="26" width="60" height="42" fill="#ff6b00" opacity="0.75" stroke="#ff6b00"/>
    <text x="300" y="18">1 B</text><text x="300" y="52" style="fill:#1a1a1a">Func</text>
    <rect x="330" y="26" width="180" height="42" fill="#ff6b00" opacity="0.4" stroke="#ff6b00"/>
    <text x="420" y="18">n B</text><text x="420" y="52">Data (address, values)</text>
  </g>

  <g stroke="currentColor" stroke-opacity="0.35" stroke-width="1">
    <line x1="45" y1="68" x2="45" y2="96"/>   <line x1="45" y1="96" x2="26" y2="96"/>
    <line x1="115" y1="68" x2="115" y2="116"/><line x1="115" y1="116" x2="26" y2="116"/>
    <line x1="185" y1="68" x2="185" y2="136"/><line x1="185" y1="136" x2="26" y2="136"/>
    <line x1="245" y1="68" x2="245" y2="156"/><line x1="245" y1="156" x2="26" y2="156"/>
    <line x1="300" y1="68" x2="300" y2="176"/><line x1="300" y1="176" x2="26" y2="176"/>
    <line x1="420" y1="68" x2="420" y2="196"/><line x1="420" y1="196" x2="26" y2="196"/>
  </g>

  <g font-size="11">
    <text x="32" y="100"><tspan opacity="0.65">Transaction</tspan>  echoed back so a client can match replies. Any value works.</text>
    <text x="32" y="120"><tspan opacity="0.65">Protocol</tspan>  always 0. Nothing ever checks it for anything useful.</text>
    <text x="32" y="140"><tspan fill="#ff6b00">Length</tspan>  bytes that follow. Wrong here and the parse desynchronises.</text>
    <text x="32" y="160"><tspan opacity="0.65">Unit</tspan>  addresses a device behind a serial gateway. Usually 1.</text>
    <text x="32" y="180"><tspan fill="#ff6b00">Function</tspan>  read or write, bit or word. This the PLC acts on.</text>
    <text x="32" y="200"><tspan fill="#ff6b00">Data</tspan>  the register address and the value. This changes the plant.</text>
  </g>
  <text x="10" y="228" font-size="11" opacity="0.7">MBAP header (7 bytes)</text>
  <text x="420" y="228" font-size="11" opacity="0.7" text-anchor="middle">PDU</text>
  <text x="10" y="244" font-size="11" opacity="0.85">Orange: the three fields a forged frame has to get right.</text>
</svg>
<figcaption>Six fields, three of which an attacker can fill with anything. This figure is
deliberately still: the fields are a layout, not a sequence, so there is nothing for motion to
show and six captions at once are read faster than six shown in turn.</figcaption>
</figure>

## Reading a flag out of the registers

The *Wireshark Capture* challenge hides a flag in Modbus traffic. It is worth seeing exactly
how, because the mechanism &mdash; two ASCII characters packed into each 16-bit register
&mdash; is how text crosses a protocol that only knows numbers.

<figure>
<style>
.mb-d {--d: 11s;}
.mb-d .reg  {opacity:0.35; animation: d-reg var(--d) steps(1,end) infinite;}
.mb-d .chr  {opacity:0;    animation: d-chr var(--d) steps(1,end) infinite;}
.mb-d .r1,.mb-d .k1{animation-delay:0s}    .mb-d .r2,.mb-d .k2{animation-delay:0.9s}
.mb-d .r3,.mb-d .k3{animation-delay:1.8s}  .mb-d .r4,.mb-d .k4{animation-delay:2.7s}
.mb-d .r5,.mb-d .k5{animation-delay:3.6s}  .mb-d .r6,.mb-d .k6{animation-delay:4.5s}
.mb-d .r7,.mb-d .k7{animation-delay:5.4s}
.mb-d .flag {opacity:0; animation: d-flag var(--d) steps(1,end) infinite;}
@keyframes d-reg {0%,8%{opacity:1} 8.01%,100%{opacity:0.35}}
@keyframes d-chr {0%{opacity:0} 0.01%,92%{opacity:1} 92.01%,100%{opacity:0}}
@keyframes d-flag{0%,58%{opacity:0} 62%,94%{opacity:1} 94.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .mb-d .reg,.mb-d .chr,.mb-d .flag{animation:none;opacity:1}
}
</style>
<svg class="mb-d" viewBox="0 0 520 210" role="img"
     aria-label="One Write Multiple Registers frame carries seven registers from address 1200. Each register splits into two ASCII characters, spelling the flag CybICS(m0dbu$).">
  <rect x="10" y="14" width="500" height="30" rx="4" fill="#ff6b00" opacity="0.75"/>
  <text x="260" y="34" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">
    one frame &mdash; FC 16 Write Multiple Registers, address 1200, 7 registers
  </text>

  <g font-size="11" text-anchor="middle">
    <g class="reg r1"><rect x="14" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="47" y="82">0x4379</text></g>
    <g class="reg r2"><rect x="86" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="119" y="82">0x6249</text></g>
    <g class="reg r3"><rect x="158" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="191" y="82">0x4353</text></g>
    <g class="reg r4"><rect x="230" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="263" y="82">0x286D</text></g>
    <g class="reg r5"><rect x="302" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="335" y="82">0x3064</text></g>
    <g class="reg r6"><rect x="374" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="407" y="82">0x6275</text></g>
    <g class="reg r7"><rect x="446" y="62" width="66" height="30" rx="3" fill="currentColor" opacity="0.18" stroke="currentColor"/><text x="479" y="82">0x2429</text></g>
  </g>

  <g font-size="13" text-anchor="middle" font-weight="bold" fill="#ff6b00">
    <text class="chr k1" x="47"  y="118">C y</text>
    <text class="chr k2" x="119" y="118">b I</text>
    <text class="chr k3" x="191" y="118">C S</text>
    <text class="chr k4" x="263" y="118">( m</text>
    <text class="chr k5" x="335" y="118">0 d</text>
    <text class="chr k6" x="407" y="118">b u</text>
    <text class="chr k7" x="479" y="118">$ )</text>
  </g>

  <text x="260" y="142" text-anchor="middle" font-size="11" opacity="0.8">
    high byte first, then low byte &mdash; 0x43 = 'C', 0x79 = 'y'
  </text>
  <g class="flag">
    <rect x="150" y="156" width="220" height="30" rx="4" fill="#ff6b00"/>
    <text x="260" y="176" text-anchor="middle" font-size="14" style="fill:#1a1a1a" font-weight="bold">CybICS(m0dbu$)</text>
  </g>
  <text x="260" y="202" text-anchor="middle" font-size="11" opacity="0.75">
    all of it in a single packet &mdash; find the FC 16 write to 1200, not a stream of small writes
  </text>
</svg>
<figcaption>The plant writes this once per cycle from <code>hwio</code>. In Wireshark you are
looking for one <em>Write Multiple Registers</em> frame at address 1200, and the work is decoding
it: each register is two characters, high byte first. Filtering for <code>modbus</code> and reading
the Data field of that one frame is the whole challenge.</figcaption>
</figure>

## What the IDS has to work with instead

Here is the same write, sent twice: once by `hwio`, the bridge that is supposed to write the
plant's registers, and once by the attack machine. Stacked and aligned, the Modbus frames are
the same bytes. Only the IP header outside them differs.

<figure>
<svg viewBox="0 0 520 180" role="img"
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
    <rect x="10" y="74" width="176" height="34" rx="4" fill="#ff6b00" opacity="0.8"/>
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

  <text x="10" y="166" font-size="12" fill="#ff6b00">A source address is identity you can forge. That is the honest limit here.</text>
</svg>
<figcaption>Both frames write 0x5a (90) to register 0x0466 (1126). This one is still on purpose:
comparing two things is what eyes do well when both are visible at once, and sliding them past
each other in turn would make it harder, not clearer. Only <code>hwio</code> writes 1126 in this
plant.</figcaption>
</figure>

So the IDS cannot ask Modbus who is writing. It asks the IP header, and then asks how often
and what:

- **Rule 3, flood** &mdash; 50 writes in 5 seconds from one source. Exempts `hwio`, `fuxa`
  *and* `openplc`, which all write at rate legitimately.
- **Rule 4, unauthorised write** &mdash; 10 writes in 30 seconds from a source that is not
  `hwio` or `fuxa`. A narrower list than rule 3's, and note the threshold: a *single* write
  from the attack machine raises nothing at all.
- **Rule 5, diagnostic** &mdash; function code 0x08 or 0x2B from anywhere.

That rule 4 threshold is not a detail. Three writes five seconds apart stay under it
indefinitely, which is exactly what the *IDS Evasion* challenge does &mdash; its solver says
so in as many words. A detector tuned to catch a flood is, by construction, blind to
patience.

## Common function codes

- **1/2** read coils / discrete inputs
- **3/4** read holding / input registers
- **5/6** write single coil / register
- **15/16** write multiple coils / registers
- **8** diagnostics &mdash; specified for serial lines. OpenPLC does *not* implement it:
  `processModbusMessage()` falls through to `ERR_ILLEGAL_FUNCTION` and answers with
  exception 0x01
- **43 (0x2B)** encapsulated transport / device identification &mdash; likewise refused

Those last two are worth dwelling on. The PLC rejecting a function code does not make the
attempt harmless or invisible: the *Fuzzing Modbus* challenge passes when the IDS's
`modbus_diagnostic` rule fires, which happens because the **request crossed the wire**, not
because anything replied. `check_fuzzing_attack.py` asks the IDS, not the PLC. Detection has
to sit on the network precisely because a refusal at the endpoint leaves no trace the
endpoint will tell you about.

## Security relevance

Because Modbus carries no identity of its own, the CybICS IDS borrows one from the layer
below and mixes it with behaviour: a burst of writes (flood, rule 3), a write from a source
address that is not `hwio` or `fuxa` (unauthorised write, rule 4), or a diagnostic function
code (rule 5). Two of those three are behavioural; the middle one is an allowlist of IP
addresses, which is identity of a sort &mdash; just the weakest sort, since the attack
machine sits on the same bridge and can claim any address it likes.

Note what that costs. A behavioural rule has no ground truth to appeal to, so it is a
judgement about what is normal *here*, tuned against this plant's traffic. Change the polling
rate and the flood threshold is wrong. An address allowlist is worse: it is exactly as strong
as the assumption that nobody spoofs. Both trade-offs are the subject of the *IDS Monitoring
& Tuning* challenge.
