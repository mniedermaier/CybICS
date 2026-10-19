# Modbus TCP

Modbus is the protocol the CybICS PLC speaks most, and the one you will meet most often in real plants. It is simple, open and trusts everyone: whoever reaches the PLC on port 502 can read and change its values.

## Why Modbus trusts everyone

Modbus was designed in 1979 for a serial cable. Its network version, **Modbus TCP**, listens on TCP port **502**. A port is like a door number: the address finds the machine, the port finds the program.

Modbus has no login, no encryption and no way to check who sent a message. In 1979 the cable sat in a locked cabinet, so touching it *was* the permission. The cable became Ethernet; the protocol stayed the same.

<div class="callout warning" markdown="1">
**No authentication:** Modbus notices a frame that was damaged in transit, but nothing notices a frame that someone *forged*.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: checksums and Modbus/TCP Security</summary>

Serial Modbus RTU carries its own checksum; Modbus TCP relies on the one in TCP. Either only catches accidental damage: a forger simply computes a valid checksum. A secure variant with TLS on port 802 exists since 2018, but almost no plant uses it.

</details>

## The data model

<div class="callout analogy" markdown="1">
**Analogy:** think of the PLC as a wall of numbered mailboxes. A Modbus client names a mailbox number and either looks inside or puts a new value in. Nobody at the wall checks ID.
</div>

Modbus has four tables of mailboxes. Two hold single bits (on or off), two hold 16-bit numbers (0 to 65535):

| Table | Holds | Access | Typical use |
|---|---|---|---|
| Coils | 1 bit | read and write | digital outputs: a valve, a motor |
| Discrete inputs | 1 bit | read only | digital inputs: a limit switch |
| Holding registers | 16 bits | read and write | setpoints, counters |
| Input registers | 16 bits | read only | sensor readings |

In CybICS the plant's values live in **holding registers** and **coils**:

| Address | Table | Meaning |
|---|---|---|
| 1124 | holding register | GST: pressure in the gas storage tank |
| 1126 | holding register | HPT: pressure in the high-pressure tank |
| 1132 | holding register | system sensor |
| 1134 | holding register | blow-out sensor |
| 0 to 3 | coils | heartbeat, compressor, system valve, GST signal |

<details class="deep-dive" markdown="1">
<summary>Deep dive: the two tank pressures, live</summary>

These are the values in registers 1124 and 1126 right now, read from the PLC:

<div data-widget="plant-live" data-fields="gst,hpt"></div>

</details>

The HPT pressure at 1126 is a sensor reading, yet it sits in a writable *holding* register. Anyone may write it, and the *Flood &amp; Overwrite* challenge uses exactly that.

<div data-widget="checkpoint" data-id="holding"></div>

## Request and response

The **client** (older texts say "master") sends a request; the **server** (the PLC, or "slave") answers. The request names a **function code** (what to do) and an address (where). There is no login, so the very first request can already be a write.

<figure class="wide">
<style>
/* A long cycle with most of it at rest: the motion makes its point and then
   leaves the reader alone with the paragraph, instead of looping tightly. */
.mb-x {--mb-dur: 9s;}
.mb-x .rm {opacity:0;}
.mb-x .pkt {animation: mb-fly var(--mb-dur) linear infinite;}
.mb-x .ack {animation: mb-back var(--mb-dur) linear infinite;}
.mb-x .old {opacity:0; animation: mb-fade var(--mb-dur) steps(1,end) infinite;}
.mb-x .new {animation: mb-show var(--mb-dur) steps(1,end) infinite;}
.mb-x .hs  {animation: mb-blink var(--mb-dur) linear infinite;}
@keyframes mb-fly  {0%,2%{transform:translateX(0);opacity:0}
                    5%{opacity:1} 19%{transform:translateX(134px);opacity:1}
                    21%,100%{transform:translateX(134px);opacity:0}}
@keyframes mb-back {0%,26%{transform:translateX(0);opacity:0}
                    28%{opacity:1} 41%{transform:translateX(-134px);opacity:1}
                    43%,100%{transform:translateX(-134px);opacity:0}}
@keyframes mb-fade {0%,20%{opacity:1} 22%,92%{opacity:0} 94%,100%{opacity:1}}
@keyframes mb-show {0%,20%{opacity:0} 22%,92%{opacity:1} 94%,100%{opacity:0}}
@keyframes mb-blink{0%,21%{opacity:0} 23%,92%{opacity:1} 94%,100%{opacity:0}}
@media (prefers-reduced-motion: reduce) {
  .mb-x .pkt,.mb-x .ack,.mb-x .old,.mb-x .new,.mb-x .hs {animation: none;}
  .mb-x .pkt,.mb-x .ack {opacity:1;}
  /* .old and .new occupy the same spot, so the still shows "45 -> 90". */
  .mb-x .old {opacity:0;} .mb-x .new {opacity:0;} .mb-x .hs {opacity:1;}
  .mb-x .rm {opacity:1;}
}
</style>
<svg class="mb-x" viewBox="0 0 520 136" role="img"
     aria-label="A Modbus write travels from client to PLC: function code 06 carrying register 1126 and the value 90. The register changes from 45 to 90 on arrival and the PLC echoes the write back. A TCP handshake preceded it, but no authentication did.">
  <rect x="20" y="30" width="120" height="56" rx="6" fill="#ff6b00"/>
  <text x="80" y="52" text-anchor="middle" font-size="12" fill="#1a1a1a" font-weight="bold">Client</text>
  <text x="80" y="68" text-anchor="middle" font-size="11" fill="#1a1a1a">hwio or attacker</text>
  <text x="80" y="80" text-anchor="middle" font-size="11" fill="#1a1a1a">first request ever</text>

  <rect x="380" y="30" width="120" height="56" rx="6" fill="currentColor" fill-opacity="0.2" stroke="currentColor" stroke-opacity="0.55"/>
  <text x="440" y="50" text-anchor="middle" font-size="12" font-weight="bold">PLC : 502</text>
  <text x="440" y="66" text-anchor="middle" font-size="11">reg 1126 =</text>
  <text class="old" x="440" y="80" text-anchor="middle" font-size="13" font-weight="bold">45</text>
  <g class="new"><rect x="420" y="70" width="40" height="18" rx="3" fill="#ff6b00"/><text x="440" y="84" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">90</text></g>
  <g class="rm"><rect x="406" y="70" width="68" height="18" rx="3" fill="#ff6b00"/><text x="440" y="84" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">45 &rarr; 90</text></g>

  <line x1="144" y1="46" x2="376" y2="46" stroke="currentColor" stroke-width="1"
        stroke-dasharray="3 4" opacity="0.55"/>
  <line x1="144" y1="74" x2="376" y2="74" stroke="currentColor" stroke-width="1"
        stroke-dasharray="3 4" opacity="0.55"/>

  <g class="pkt">
    <rect x="146" y="36" width="96" height="20" rx="3" fill="#ff6b00"/>
    <text x="194" y="50" text-anchor="middle" font-size="11" fill="#1a1a1a">FC 06 · 1126 · 90</text>
  </g>
  <g class="ack">
    <rect x="278" y="64" width="96" height="20" rx="3" fill="currentColor" fill-opacity="0.28"/>
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
<figcaption>A Modbus write. Function code 6 writes one register; the PLC applies it and echoes it back. Nothing asked who sent it.</figcaption>
</figure>

The forged value does not last, though. The `hwio` container, which simulates the plant, writes the real HPT pressure back into 1126 about fifty times a second. So the *Flood &amp; Overwrite* attack is a loop, not a single packet.

## The frame

Every Modbus TCP message starts with a 7-byte **MBAP header** (Modbus Application Protocol header), followed by the **PDU** (Protocol Data Unit): the function code and its data.

<div class="callout tip" markdown="1">
**New to hex?** A **byte** is 8 bits and holds a number from 0 to 255. Network tools write bytes in **hexadecimal** (base 16): the digits 0 to 9, then A to F for 10 to 15. Every byte is two hex digits: `0a` is 10, `5a` is 5 &times; 16 + 10 = 90, `ff` is 255. A 16-bit register takes two bytes, high byte first: 1126 is `04 66`.
</div>

Only three fields have to be right: the **length** (how many bytes follow), the **function code** and the **data** (address and value). The transaction, protocol and unit fields can hold almost anything.

<details class="deep-dive" markdown="1">
<summary>Deep dive: every field of the frame</summary>

<figure class="wide">
<svg viewBox="0 0 520 108" role="img"
     aria-label="The Modbus TCP frame: a seven-byte MBAP header holding transaction id, protocol id, length and unit id, followed by the PDU holding the function code and its data. The table below the figure says what each field does.">
  <g font-size="11" text-anchor="middle">
    <rect x="10" y="30" width="80" height="42" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.55"/>
    <text x="50" y="22">2 B</text><text x="50" y="56">Transaction</text>
    <rect x="90" y="30" width="80" height="42" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.55"/>
    <text x="130" y="22">2 B</text><text x="130" y="56">Protocol</text>
    <rect x="170" y="30" width="80" height="42" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="210" y="22">2 B</text><text x="210" y="56" style="fill:#1a1a1a">Length</text>
    <rect x="250" y="30" width="40" height="42" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.55"/>
    <text x="270" y="22">1 B</text><text x="270" y="56">Unit</text>
    <rect x="290" y="30" width="40" height="42" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="310" y="22">1 B</text><text x="310" y="56" style="fill:#1a1a1a">Func</text>
    <rect x="330" y="30" width="180" height="42" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="420" y="22">n B</text><text x="420" y="56" style="fill:#1a1a1a">Data (address, values)</text>
  </g>
  <line x1="290" y1="24" x2="290" y2="96" stroke="currentColor" stroke-width="2"/>
  <path d="M 10 80 L 10 88 L 290 88 L 290 80" fill="none" stroke="currentColor"
        stroke-opacity="0.55"/>
  <path d="M 290 80 L 290 88 L 510 88 L 510 80" fill="none" stroke="currentColor"
        stroke-opacity="0.55"/>
  <text x="150" y="102" text-anchor="middle" font-size="11" opacity="0.8">MBAP header, 7 bytes</text>
  <text x="400" y="102" text-anchor="middle" font-size="11" opacity="0.8">PDU &mdash; what the PLC acts on</text>
</svg>
<figcaption>The six fields of a Modbus TCP request. Orange marks the three a forged frame has to get right; the other three can hold almost anything.</figcaption>
</figure>

| Field | Size | What it does | Must it be right? |
|---|---|---|---|
| Transaction | 2 B | Copied into the reply so the client can match answer to question. | No, any value works. |
| Protocol | 2 B | Always 0 for Modbus. | No. |
| Length | 2 B | How many bytes follow, counted from the unit field on. | **Yes**, or the PLC misreads the frame. |
| Unit | 1 B | Picks a device behind a serial gateway. Usually 1. | Only if a gateway is in the path. |
| Function | 1 B | What to do: read or write, bits or registers. | **Yes.** |
| Data | n B | The address and the value. This is what changes the plant. | **Yes.** |

</details>

Try it. The builder starts with the write from the figure. Change a field and watch the bytes, or paste bytes to decode them.

<div data-widget="modbus-frame" data-fc="6" data-address="1126" data-value="90"></div>

<div data-widget="checkpoint" data-id="frame"></div>

## Function codes

The function code picks the table and the direction. These are the everyday ones:

| Code | Meaning |
|---|---|
| 1 / 2 | read coils / read discrete inputs |
| 3 / 4 | read holding registers / read input registers |
| 5 / 6 | write one coil / write one register |
| 15 / 16 | write several coils / write several registers |

<details class="deep-dive" markdown="1">
<summary>Deep dive: diagnostic codes and OpenPLC's own function codes</summary>

Two more standard codes matter for security: 8 (diagnostics, meant for serial lines) and 43 (0x2B, device identification). The OpenPLC in CybICS refuses both with exception 1, "illegal function". The refused request is still on the wire, where the IDS sees it: that is how the *Fuzzing Modbus* challenge is detected.

OpenPLC adds five function codes that are not in the Modbus specification: 0x41 to 0x45, used by its web editor for debugging. They return the number of debug variables (0x41), force a program variable (0x42), read variables (0x43 and 0x44) and return the MD5 hash of the running program (0x45). They are answered on the same unauthenticated port 502.

The CybICS IDS only watches the standard diagnostic codes 0x08 and 0x2B. A rule catches what somebody thought to write it for, and this one was written for the specification, not for this implementation.

</details>

<details class="deep-dive" markdown="1">
<summary>Deep dive: text hidden in numbers</summary>

Modbus only knows numbers, but a 16-bit register can carry two text characters: one in the high byte, one in the low byte. Each byte is looked up in the ASCII table, where for example `48` is `H` and `65` is `e`. The *Wireshark Capture* challenge hides its secret this way. The decoder shows the method on a harmless example:

<div data-widget="register-decoder" data-values="18533,27756,28416"></div>

</details>

## What the IDS can see

Modbus carries no identity, so a forged write and a real one are the same bytes. The IDS can only judge traffic to port 502 by the sender's IP address, by *how often* it writes and by *which* function code it uses.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the three Modbus rules</summary>

- **Rule 3, write flood:** 50 or more writes within 5 seconds from one source, unless it is `hwio`, `fuxa` or `openplc`.
- **Rule 4, unauthorised write:** 10 or more writes within 30 seconds from a source other than `hwio` or `fuxa`. A single write raises nothing.
- **Rule 5, diagnostics:** any request with function code 0x08 or 0x2B.

The details of every rule are in [Detection and monitoring](/theory/detection-monitoring).

</details>

<details class="deep-dive" markdown="1">
<summary>Deep dive: the same write from two senders</summary>

Compare the same write sent by `hwio` and by the attack machine:

<figure class="wide">
<svg viewBox="0 0 520 146" role="img"
     aria-label="Two Modbus frames stacked and aligned, one from hwio at 172.18.0.2 and one from the attack machine at 172.18.0.100. Ten of the twelve bytes match exactly. The first two, the transaction id, differ: hwio counts its up per request while the attacker chose one freely. Nothing in the protocol or the rule checks either, so the attacker could have copied hwio's.">
  <text x="10" y="18" font-size="11" opacity="0.75">outside the Modbus frame</text>
  <text x="200" y="18" font-size="11" opacity="0.75">the Modbus frame itself</text>
  <g font-size="11">
    <rect x="10" y="28" width="176" height="34" rx="4" fill="currentColor" fill-opacity="0.2" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="20" y="43">src 172.18.0.2</text>
    <text x="20" y="57" opacity="0.75">hwio &mdash; the plant bridge</text>
    <rect x="194" y="28" width="316" height="34" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="226" y="49" font-family="monospace" font-size="12" fill="#ff6b00" font-weight="bold">0a ed</text>
    <text x="269" y="49" font-family="monospace" font-size="12">00 00 00 06 01 06 04 66 00 5a</text>
  </g>
  <g font-size="11">
    <rect x="10" y="74" width="176" height="34" rx="4" fill="#ff6b00"/>
    <text x="20" y="89" style="fill:#1a1a1a">src 172.18.0.100</text>
    <text x="20" y="103" style="fill:#1a1a1a">attack machine</text>
    <rect x="194" y="74" width="316" height="34" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="226" y="95" font-family="monospace" font-size="12" fill="#ff6b00" font-weight="bold">00 01</text>
    <text x="269" y="95" font-family="monospace" font-size="12">00 00 00 06 01 06 04 66 00 5a</text>
  </g>
  <line x1="194" y1="116" x2="510" y2="116" stroke="#ff6b00" stroke-width="1" stroke-dasharray="4 4"/>
  <text x="352" y="132" text-anchor="middle" font-size="11" fill="#ff6b00" font-weight="bold">
    ten of twelve bytes identical &mdash; the rest need not be
  </text>
  <line x1="10" y1="116" x2="186" y2="116" stroke="currentColor" stroke-opacity="0.6" stroke-width="1" stroke-dasharray="4 4"/>
  <text x="98" y="132" text-anchor="middle" font-size="11" opacity="0.85">the only difference</text>
</svg>
<figcaption>Both frames write 0x5a (90) to register 0x0466 (1126), and the PLC applies both. Apart from the freely chosen transaction id, only the sender's IP address differs, and that lies outside Modbus.</figcaption>
</figure>

</details>

Writing slowly stays below the write rules (the *IDS Evasion* challenge), and an IP address is easy to fake. The real defence is to keep untrusted hosts away from port 502, as [Defence in depth](/theory/defense-hardening) shows. Next, compare [S7comm](/theory/s7comm), and [OPC-UA](/theory/opcua-protocol), which adds the login Modbus lacks.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

- Rule 3 exempts `openplc`, but OpenPLC is only the Modbus server here and never sends writes to port 502, so that entry has no effect. The IDS only inspects traffic towards port 502.
- The allowlists in rules 3 and 4 trust source IPs on a shared bridge, where the attack machine can spoof them. A good discussion: how would you tune the thresholds and allowlists in `rules.py` for this plant? The *IDS Monitoring &amp; Tuning* challenge only checks that three rules fire, not that any was tuned.

</details>
