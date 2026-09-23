# Modbus TCP

**Modbus** is the lingua franca of industrial automation. It was designed in 1979 for
serial links and later wrapped in TCP/IP as **Modbus TCP** on port **502**. It is simple,
open, and everywhere &mdash; and it has no authentication, no encryption, and no integrity
checking. Whoever can reach port 502 can read and write the controller.

That is not an oversight. In 1979 the "network" was a shielded cable running a few metres
inside a locked cabinet. Physical access *was* the authentication. When that cable became
Ethernet, and Ethernet reached the office LAN, nothing in the protocol changed to notice.

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
register changes on the *first* packet the PLC ever sees from this client.

<figure>
<style>
.mb-x {--mb-dur: 5s;}
.mb-x .pkt {animation: mb-fly var(--mb-dur) linear infinite;}
.mb-x .ack {animation: mb-back var(--mb-dur) linear infinite;}
.mb-x .old {animation: mb-fade var(--mb-dur) linear infinite;}
.mb-x .new {animation: mb-show var(--mb-dur) linear infinite;}
.mb-x .hs  {animation: mb-blink var(--mb-dur) linear infinite;}
@keyframes mb-fly  {0%,4%{transform:translateX(0);opacity:0}
                    8%{opacity:1} 34%{transform:translateX(232px);opacity:1}
                    38%,100%{transform:translateX(232px);opacity:0}}
@keyframes mb-back {0%,46%{transform:translateX(0);opacity:0}
                    50%{opacity:1} 74%{transform:translateX(-232px);opacity:1}
                    78%,100%{transform:translateX(-232px);opacity:0}}
@keyframes mb-fade {0%,36%{opacity:1} 40%,100%{opacity:0}}
@keyframes mb-show {0%,36%{opacity:0} 40%,100%{opacity:1}}
@keyframes mb-blink{0%,82%{opacity:0} 86%,96%{opacity:1} 100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .mb-x .pkt,.mb-x .ack,.mb-x .old,.mb-x .new,.mb-x .hs {animation: none;}
  .mb-x .pkt,.mb-x .ack {opacity:1;}
  .mb-x .old {opacity:0;} .mb-x .new {opacity:1;} .mb-x .hs {opacity:1;}
}
</style>
<svg class="mb-x" viewBox="0 0 520 200" role="img"
     aria-label="A Modbus write travels from client to PLC; the register changes on arrival and the PLC echoes it back. No handshake precedes it.">
  <rect x="20" y="30" width="120" height="56" rx="6" fill="#ff6b00" opacity="0.85"/>
  <text x="80" y="52" text-anchor="middle" font-size="12" fill="#1a1a1a" font-weight="bold">Client</text>
  <text x="80" y="68" text-anchor="middle" font-size="10" fill="#1a1a1a">HMI / attacker</text>
  <text x="80" y="80" text-anchor="middle" font-size="9" fill="#1a1a1a">first packet ever</text>

  <rect x="380" y="30" width="120" height="56" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="440" y="50" text-anchor="middle" font-size="12" font-weight="bold">PLC : 502</text>
  <text x="440" y="66" text-anchor="middle" font-size="10">reg 1126 =</text>
  <text class="old" x="440" y="80" text-anchor="middle" font-size="13" font-weight="bold">45</text>
  <text class="new" x="440" y="80" text-anchor="middle" font-size="13" font-weight="bold" fill="#ff6b00">90</text>

  <line x1="144" y1="46" x2="376" y2="46" stroke="currentColor" stroke-width="1"
        stroke-dasharray="3 4" opacity="0.3"/>
  <line x1="144" y1="74" x2="376" y2="74" stroke="currentColor" stroke-width="1"
        stroke-dasharray="3 4" opacity="0.3"/>

  <g class="pkt">
    <rect x="146" y="36" width="96" height="20" rx="3" fill="#ff6b00"/>
    <text x="194" y="50" text-anchor="middle" font-size="10" fill="#1a1a1a">FC 06 · 1126 · 90</text>
  </g>
  <g class="ack">
    <rect x="278" y="64" width="96" height="20" rx="3" fill="currentColor" opacity="0.45"/>
    <text x="326" y="78" text-anchor="middle" font-size="10">echo · 1126 · 90</text>
  </g>

  <g class="hs">
    <text x="260" y="118" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">
      no handshake happened here
    </text>
  </g>
  <text x="20" y="150" font-size="11" opacity="0.8">The value changed before anything asked who was writing. There is no</text>
  <text x="20" y="166" font-size="11" opacity="0.8">session to hijack and no login to brute-force, because there is neither.</text>
  <text x="20" y="182" font-size="11" opacity="0.8">This single fact underlies the flood, overwrite and MITM attacks.</text>
</svg>
<figcaption>A Modbus write. Function code 6 writes one register; the PLC applies it and echoes
it back. Nothing before that moment proves the client is allowed to write &mdash; the gap where a
handshake would be is the whole attack surface.</figcaption>
</figure>

## The frame

A Modbus TCP message is a 7-byte **MBAP header** followed by the function code and its data.
Only two of those bytes carry anything an attacker must get right.

<figure>
<style>
.mb-f {--f-dur: 9s;}
.mb-f .sweep {animation: f-sweep var(--f-dur) steps(1,end) infinite;}
.mb-f .cap   {opacity:0; animation: f-cap var(--f-dur) steps(1,end) infinite;}
.mb-f .c1{animation-delay:0s}   .mb-f .c2{animation-delay:1.5s}
.mb-f .c3{animation-delay:3s}   .mb-f .c4{animation-delay:4.5s}
.mb-f .c5{animation-delay:6s}   .mb-f .c6{animation-delay:7.5s}
@keyframes f-sweep{
  0%,16%   {transform:translateX(0px);   width:70px}
  16.01%,33%{transform:translateX(70px); width:70px}
  33.01%,50%{transform:translateX(140px);width:70px}
  50.01%,66%{transform:translateX(210px);width:50px}
  66.01%,83%{transform:translateX(260px);width:60px}
  83.01%,100%{transform:translateX(320px);width:180px}}
@keyframes f-cap{0%,16%{opacity:1} 16.01%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .mb-f .sweep{animation:none;opacity:0}
  .mb-f .cap{animation:none;opacity:0}
  .mb-f .c6{opacity:1}
}
</style>
<svg class="mb-f" viewBox="0 0 520 132" role="img"
     aria-label="The Modbus TCP frame: a highlight steps through transaction id, protocol id, length, unit id, function code and data, naming each field.">
  <g font-size="10" text-anchor="middle">
    <rect x="10" y="30" width="70" height="40" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="45" y="20">2 B</text><text x="45" y="54">Transaction</text>
    <rect x="80" y="30" width="70" height="40" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="115" y="20">2 B</text><text x="115" y="54">Protocol</text>
    <rect x="150" y="30" width="70" height="40" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="185" y="20">2 B</text><text x="185" y="54">Length</text>
    <rect x="220" y="30" width="50" height="40" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="245" y="20">1 B</text><text x="245" y="54">Unit</text>
    <rect x="270" y="30" width="60" height="40" fill="#ff6b00" opacity="0.7"/>
    <text x="300" y="20">1 B</text><text x="300" y="54" fill="#1a1a1a">Func</text>
    <rect x="330" y="30" width="180" height="40" fill="#ff6b00" opacity="0.35"/>
    <text x="420" y="20">n B</text><text x="420" y="54">Data (address, values)</text>
  </g>
  <rect class="sweep" x="10" y="26" width="70" height="48" fill="none"
        stroke="#ff6b00" stroke-width="3" rx="2"/>
  <g font-size="11" text-anchor="middle">
    <text class="cap c1" x="260" y="96">Transaction id &mdash; echoed back, so a client can match replies. Anything fits.</text>
    <text class="cap c2" x="260" y="96">Protocol id &mdash; always 0. Never checked for anything useful.</text>
    <text class="cap c3" x="260" y="96">Length &mdash; bytes that follow. Get this wrong and the parse desynchronises.</text>
    <text class="cap c4" x="260" y="96">Unit id &mdash; addresses a device behind a serial gateway. Usually 1.</text>
    <text class="cap c5" x="260" y="96">Function code &mdash; read or write, bit or word. This the PLC acts on.</text>
    <text class="cap c6" x="260" y="96">Data &mdash; the register address and the value. This is what changes the plant.</text>
  </g>
  <text x="10" y="120" font-size="10" opacity="0.7">MBAP header (7 bytes)</text>
  <text x="420" y="120" font-size="10" opacity="0.7" text-anchor="middle">PDU</text>
</svg>
<figcaption>Six fields, and only the last two decide what happens to the plant. In the Wireshark
challenge you read a flag that was written byte-by-byte into holding registers &mdash; you are
reading the Data field of one frame after another.</figcaption>
</figure>

## Why the IDS cannot ask "who is this?"

Here is the same write, sent twice: once by the HMI that is supposed to send it, once by the
attack machine. On the wire they are the same bytes. The PLC applies both.

<figure>
<style>
.mb-t {--t-dur: 6s;}
.mb-t .p1{animation: t-a var(--t-dur) linear infinite;}
.mb-t .p2{animation: t-b var(--t-dur) linear infinite;}
.mb-t .verdict{opacity:0; animation: t-v var(--t-dur) linear infinite;}
@keyframes t-a{0%{transform:translateX(0);opacity:0} 4%{opacity:1}
               30%{transform:translateX(196px);opacity:1} 34%,100%{opacity:0}}
@keyframes t-b{0%,36%{transform:translateX(0);opacity:0} 40%{opacity:1}
               66%{transform:translateX(196px);opacity:1} 70%,100%{opacity:0}}
@keyframes t-v{0%,70%{opacity:0} 76%,96%{opacity:1} 100%{opacity:0}}
@media (prefers-reduced-motion: reduce){
  .mb-t .p1,.mb-t .p2{animation:none;opacity:1;transform:translateX(98px)}
  .mb-t .verdict{animation:none;opacity:1}
}
</style>
<svg class="mb-t" viewBox="0 0 520 190" role="img"
     aria-label="The same Modbus write sent by the HMI and by the attack machine. The frames are byte-identical, so the PLC accepts both; only the source address differs.">
  <rect x="10" y="24" width="112" height="38" rx="5" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="66" y="40" text-anchor="middle" font-size="11" font-weight="bold">HMI</text>
  <text x="66" y="54" text-anchor="middle" font-size="9">172.18.0.4</text>

  <rect x="10" y="96" width="112" height="38" rx="5" fill="#ff6b00" opacity="0.85"/>
  <text x="66" y="112" text-anchor="middle" font-size="11" fill="#1a1a1a" font-weight="bold">Attack machine</text>
  <text x="66" y="126" text-anchor="middle" font-size="9" fill="#1a1a1a">172.18.0.100</text>

  <rect x="398" y="60" width="112" height="38" rx="5" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="454" y="76" text-anchor="middle" font-size="11" font-weight="bold">PLC</text>
  <text x="454" y="90" text-anchor="middle" font-size="9">applies both</text>

  <g class="p1">
    <rect x="130" y="32" width="176" height="20" rx="3" fill="currentColor" opacity="0.4"/>
    <text x="218" y="46" text-anchor="middle" font-size="9">00 01 00 00 00 06 01 06 04 66 00 5a</text>
  </g>
  <g class="p2">
    <rect x="130" y="104" width="176" height="20" rx="3" fill="#ff6b00"/>
    <text x="218" y="118" text-anchor="middle" font-size="9" fill="#1a1a1a">00 01 00 00 00 06 01 06 04 66 00 5a</text>
  </g>

  <g class="verdict">
    <text x="260" y="160" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">
      identical frames &mdash; the protocol carries no identity to check
    </text>
    <text x="260" y="176" text-anchor="middle" font-size="10" opacity="0.85">
      so the IDS watches behaviour instead: who, how often, and what
    </text>
  </g>
</svg>
<figcaption>Both frames write 0x5a (90) to register 0x0466 (1126). Byte for byte they are the
same request. Only the IP header outside the Modbus frame differs, which is why every
Modbus detection in CybICS is a statement about behaviour rather than about identity.</figcaption>
</figure>

## Common function codes

- **1/2** read coils / discrete inputs
- **3/4** read holding / input registers
- **5/6** write single coil / register
- **15/16** write multiple coils / registers
- **8** diagnostics (used by the fuzzing challenge)

## Security relevance

Because Modbus authenticates nothing, the CybICS IDS cannot rely on identity. Instead it
watches **behaviour**: a burst of writes (flood), writes from an unexpected host
(unauthorised write), or odd function codes (diagnostics/fuzzing). That is the seam every
Modbus attack &mdash; and every Modbus detection &mdash; runs through.

Note what that costs. A behavioural rule has no ground truth to appeal to, so it is a
judgement about what is normal here, tuned against this plant's traffic. Change the polling
rate and the flood threshold is wrong. That trade-off is the subject of the *Tuning the IDS*
challenge.
