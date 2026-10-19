# S7comm

Siemens is one of the biggest PLC makers in the world, and its S7 controllers run factories, water works and power plants. They talk **S7comm**, a protocol Siemens designed for its own devices. Like [Modbus](/theory/modbus), classic S7comm will tell anyone who asks what device it is, and that is where an attacker starts.

## Where S7comm comes from

S7comm is **proprietary**: Siemens wrote it and never published a full specification. Everything public about it was worked out by people reading network captures. Wireshark and the scanner nmap both understand it today.

That is a lesson in itself. Keeping a protocol secret is not a security measure: it slows down curious people for a while, and once the format is known, nothing else stands in the way. Security has to come from the protocol checking who is talking, and classic S7comm does not.

It grew up on Siemens' own industrial networks (MPI and Profibus), not on the internet. To carry it over TCP/IP, Siemens uses a standard called **ISO-on-TCP** (RFC 1006), which listens on TCP port **102**. That bridge adds two small headers in front of every S7comm message:

- **TPKT** (4 bytes) says how long the whole message is. TCP delivers a continuous stream of bytes, so the receiver needs this to know where one message ends.
- **COTP** (Connection-Oriented Transport Protocol, 3 bytes in a data message) is a transport layer from the older OSI network model. S7comm already used it before TCP, so it came along.

<div class="callout analogy" markdown="1">
**Analogy:** a Modbus request is a postcard: the message is written right on it. An S7comm request is a letter inside two envelopes. The outer envelope (TPKT) says how thick the letter is, the inner one (COTP) carries the old OSI addressing, and only inside is the actual request.
</div>

## The handshake

A Modbus client can send a write as its very first packet. S7comm expects three steps first: open a COTP connection, agree on settings with an S7 "Setup Communication" request, and only then ask real questions.

<figure class="wide">
<style>
.s7h {--d: 9s;}
.s7h .st {opacity:0; animation-duration:var(--d); animation-timing-function:steps(1,end); animation-iteration-count:3; animation-fill-mode:forwards;}
.s7h .e1{animation-name:s7h-e1}
.s7h .e2{animation-name:s7h-e2}
.s7h .e3{animation-name:s7h-e3}
.s7h .e4{animation-name:s7h-e4}
.s7h .e5{animation-name:s7h-e5}
.s7h .e6{animation-name:s7h-e6}
@keyframes s7h-e1{0%{opacity:0} 0.01%,100%{opacity:1}}
@keyframes s7h-e2{0%,9%{opacity:0} 9.01%,100%{opacity:1}}
@keyframes s7h-e3{0%,18%{opacity:0} 18.01%,100%{opacity:1}}
@keyframes s7h-e4{0%,27%{opacity:0} 27.01%,100%{opacity:1}}
@keyframes s7h-e5{0%,36%{opacity:0} 36.01%,100%{opacity:1}}
@keyframes s7h-e6{0%,45%{opacity:0} 45.01%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .s7h .st{animation:none; opacity:1}
}
</style>
<svg class="s7h" viewBox="0 0 420 268" role="img"
     aria-label="A sequence diagram of an S7comm session on real hardware. The client sends a COTP connection request and receives a confirm, then sends an S7 setup communication request and receives the agreed PDU size, and only then may it send a userdata request to read a system status list and receive the device identity.">
  <rect x="14" y="16" width="100" height="38" rx="5" fill="#ff6b00"/>
  <text x="64" y="40" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">client</text>
  <rect x="306" y="16" width="100" height="38" rx="5" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="356" y="40" text-anchor="middle" font-size="12" font-weight="bold">a real S7-300</text>
  <line x1="64" y1="58" x2="64" y2="256" stroke="currentColor" stroke-opacity="0.3" stroke-dasharray="4 4"/>
  <line x1="356" y1="58" x2="356" y2="256" stroke="currentColor" stroke-opacity="0.3" stroke-dasharray="4 4"/>
  <rect class="gate" x="14" y="64" width="392" height="130" rx="5" fill="none"
        stroke="currentColor" stroke-opacity="0.25" stroke-dasharray="5 4"/>
  <text class="gate" x="400" y="190" text-anchor="end" font-size="11" opacity="0.7">overhead</text>
  <g font-size="11" text-anchor="middle">
    <g class="st e1">
      <text x="210" y="82">COTP connection request</text>
      <path d="M 67 92 L 351 92" stroke="#ff6b00" stroke-width="2"/>
      <path d="M 343 87 L 353 92 L 343 97" fill="none" stroke="#ff6b00" stroke-width="2"/>
    </g>
    <g class="st e2">
      <text x="210" y="112">COTP connection confirm</text>
      <path d="M 353 122 L 66 122" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
      <path d="M 74 117 L 64 122 L 74 127" fill="none" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
    </g>
    <g class="st e3">
      <text x="210" y="142">S7 setup communication</text>
      <path d="M 67 152 L 351 152" stroke="#ff6b00" stroke-width="2"/>
      <path d="M 343 147 L 353 152 L 343 157" fill="none" stroke="#ff6b00" stroke-width="2"/>
    </g>
    <g class="st e4">
      <text x="210" y="172">setup response, PDU size agreed</text>
      <path d="M 353 182 L 66 182" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
      <path d="M 74 177 L 64 182 L 74 187" fill="none" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
    </g>
    <g class="st e5">
      <text x="210" y="208">userdata: read SZL 0x001c</text>
      <path d="M 67 218 L 351 218" stroke="#ff6b00" stroke-width="2"/>
      <path d="M 343 213 L 353 218 L 343 223" fill="none" stroke="#ff6b00" stroke-width="2"/>
    </g>
    <g class="st e6">
      <text x="210" y="238">system name, module type name</text>
      <path d="M 353 248 L 66 248" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
      <path d="M 74 243 L 64 248 L 74 253" fill="none" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
    </g>
  </g>
</svg>
<figcaption>Two round trips inside the dashed box only set up the conversation; the third carries device data. None of them checks who the client is: COTP agrees on addressing and the S7 setup agrees on a maximum message size.</figcaption>
</figure>

The important word is *negotiation*. The handshake agrees on technical details, such as the largest message both sides accept (the **PDU size**). It is not a login. Anybody who completes it may continue.

## One request, layer by layer

Put together, a request to read a device's identity is 33 bytes long. The two transport headers take 7 of them, the S7 part the remaining 26.

<figure class="wide">
<style>
.s7w {--d: 10s;}
.s7w .st {opacity:0; animation-duration:var(--d); animation-timing-function:steps(1,end); animation-iteration-count:3; animation-fill-mode:forwards;}
.s7w .w1{animation-name:s7w-w1}
.s7w .w2{animation-name:s7w-w2}
.s7w .w3{animation-name:s7w-w3}
.s7w .w4{animation-name:s7w-w4}
@keyframes s7w-w1{0%{opacity:0} 0.01%,100%{opacity:1}}
@keyframes s7w-w2{0%,16%{opacity:0} 16.01%,100%{opacity:1}}
@keyframes s7w-w3{0%,32%{opacity:0} 32.01%,100%{opacity:1}}
@keyframes s7w-w4{0%,48%{opacity:0} 48.01%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .s7w .st{animation:none; opacity:1}
}
</style>
<svg class="s7w" viewBox="0 0 520 160" role="img"
     aria-label="The 33-byte SZL request drawn to scale at 14 units per byte: a 4-byte TPKT header, a 3-byte COTP header, and a 26-byte S7 protocol data unit, all carried in one TCP stream.">
  <g font-size="13" text-anchor="middle">
    <g class="st w1">
      <rect x="114" y="52" width="364" height="40" rx="4" fill="#ff6b00"/>
      <text x="296" y="42">26 bytes</text>
      <text x="296" y="77" style="fill:#1a1a1a" font-weight="bold">S7 PDU &mdash; function and data</text>
    </g>
    <g class="st w2">
      <rect x="72" y="52" width="42" height="40" rx="4" fill="currentColor" opacity="0.28" stroke="currentColor"/>
      <text x="93" y="42">3 B</text><text x="93" y="77">COTP</text>
    </g>
    <g class="st w3">
      <rect x="16" y="52" width="56" height="40" rx="4" fill="currentColor" opacity="0.2" stroke="currentColor"/>
      <text x="44" y="42">4 B</text><text x="44" y="77">TPKT</text>
    </g>
    <g class="st w4">
      <rect x="16" y="104" width="462" height="26" rx="4" fill="currentColor" opacity="0.12" stroke="currentColor" stroke-opacity="0.5"/>
      <text x="247" y="122">one TCP stream, to port 102 or 1102</text>
    </g>
  </g>
  <text x="16" y="150" font-size="13" opacity="0.75">14 units per byte &mdash; 33 bytes in all</text>
</svg>
<figcaption>An SZL read request drawn to scale. TPKT only states the total length, the same job the length field does in Modbus. COTP marks the message as data. Everything that matters to the PLC sits in the S7 part.</figcaption>
</figure>

The bytes are written in hexadecimal, two digits per byte. If that is new to you, read the short hex callout in the [Modbus article](/theory/modbus) first. Then step through a real **Setup Communication** request below and see which bytes belong to which layer:

<div data-widget="s7-layers" data-sample="setup"></div>

## Reading device identity

S7 PLCs keep a **System Status List**, or **SZL** after its German name *Systemzustandsliste*. It is a set of numbered records that describe the device: its order number, its hardware, its firmware, the name the engineer gave it. A client asks for one record by its **SZL ID**:

| SZL ID | Name | What it returns |
|---|---|---|
| 0x0011 | module identification | order number and hardware, for example `6ES7 315-2AG10-0AB0` |
| 0x001c | component identification | system name, module type name, serial number and more |

On classic S7-300 and S7-400 controllers, reading the SZL needs no password. That is useful for an engineer and just as useful for an attacker, who learns exactly which model and firmware to look up in a list of known vulnerabilities. Here is a real SZL 0x0011 request, taken apart:

<div data-widget="s7-layers" data-sample="szl"></div>

In MITRE ATT&amp;CK for ICS, a catalogue of attacker techniques, finding the PLC on the network is **T0846 Remote System Discovery**, and reading its model and firmware is **T0888 Remote System Information Discovery**.

## In CybICS: two S7 servers

CybICS runs two services that both look like a Siemens S7-300 from the outside:

| Host | Port | Software | Introduces itself as |
|---|---|---|---|
| `openplc`, 172.18.0.3 | 102 | OpenPLC's built-in S7 server (the snap7 library) | `CPU 315-2 PN/DP` |
| `s7com`, 172.18.0.6 | 1102 | a small Python server written for CybICS | `SIMATIC 300(1)` |

<figure class="wide">
<style>
.s7z {--d: 13s;}
.s7z .st {opacity:0; animation-duration:var(--d); animation-timing-function:steps(1,end); animation-iteration-count:3; animation-fill-mode:forwards;}
.s7z .q1{animation-name:s7z-q1}
.s7z .a1{animation-name:s7z-a1}
.s7z .q2{animation-name:s7z-q2}
.s7z .a2{animation-name:s7z-a2}
.s7z .fl{animation-name:s7z-fl}
@keyframes s7z-q1{0%,2%{opacity:0} 2.01%,100%{opacity:1}}
@keyframes s7z-a1{0%,14%{opacity:0} 14.01%,100%{opacity:1}}
@keyframes s7z-q2{0%,40%{opacity:0} 40.01%,100%{opacity:1}}
@keyframes s7z-a2{0%,52%{opacity:0} 52.01%,100%{opacity:1}}
@keyframes s7z-fl{0%,64%{opacity:0} 64.01%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .s7z .st{animation:none; opacity:1}
}
</style>
<svg class="s7z" viewBox="0 0 520 244" role="img"
     aria-label="The same SZL query sent to both S7 endpoints. Port 102 answers with system name SNAP7-SERVER and module type CPU 315-2 PN/DP. Port 1102 answers with system name SIMATIC 300(1), and its module type name field is hidden behind a question mark: that is the field the challenge asks you to read.">
  <rect x="14" y="14" width="96" height="34" rx="5" fill="#ff6b00"/>
  <text x="62" y="36" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">nmap</text>
  <g class="st q1">
    <path d="M 114 31 L 392 31" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 384 26 L 394 31 L 384 36" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="253" y="25" text-anchor="middle" font-size="13">SZL 0x001c</text>
    <rect x="398" y="14" width="108" height="34" rx="5" fill="currentColor" opacity="0.2" stroke="currentColor"/>
    <text x="452" y="36" text-anchor="middle" font-size="12" font-weight="bold">openplc :102</text>
  </g>
  <g class="st a1" font-size="13">
    <rect x="14" y="58" width="492" height="58" rx="4" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.4"/>
    <text x="26" y="78" opacity="0.75">System name</text>
    <text x="180" y="78" font-family="monospace">SNAP7-SERVER</text>
    <text x="26" y="102" opacity="0.75">Module type name</text>
    <text x="180" y="102" font-family="monospace">CPU 315-2 PN/DP</text>
  </g>
  <line x1="62" y1="48" x2="62" y2="156" stroke="currentColor" stroke-opacity="0.3" stroke-dasharray="4 4"/>
  <g class="st q2">
    <path d="M 114 148 L 392 148" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 384 143 L 394 148 L 384 153" fill="none" stroke="#ff6b00" stroke-width="2"/>
    <text x="253" y="142" text-anchor="middle" font-size="13">the same SZL 0x001c</text>
    <rect x="398" y="131" width="108" height="34" rx="5" fill="currentColor" opacity="0.2" stroke="currentColor"/>
    <text x="452" y="153" text-anchor="middle" font-size="12" font-weight="bold">s7com :1102</text>
  </g>
  <g class="st a2" font-size="13">
    <rect x="14" y="175" width="492" height="58" rx="4" fill="currentColor" opacity="0.1" stroke="currentColor" stroke-opacity="0.4"/>
    <text x="26" y="195" opacity="0.75">System name</text>
    <text x="180" y="195" font-family="monospace">SIMATIC 300(1)</text>
    <text x="26" y="219" opacity="0.75">Module type name</text>
  </g>
  <g class="st fl">
    <rect x="168" y="204" width="250" height="22" rx="3" fill="#ff6b00"/>
    <text x="293" y="220" text-anchor="middle" font-size="12" font-family="monospace" style="fill:#1a1a1a" font-weight="bold">? &mdash; read it yourself</text>
  </g>
</svg>
<figcaption>The same question asked of both servers. Both answers look like a Siemens S7-300, because both were written to look like one. The difference is in a single field, and finding it is the <em>S7comm Scanning</em> challenge.</figcaption>
</figure>

<div class="callout tip" markdown="1">
**Tip:** nmap's `s7-info` script reads the SZL for you, but every nmap script decides for itself which ports it runs on. Look at how `s7-info` makes that decision before you wonder why it stays silent on a non-standard port.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: neither server insists on the handshake</summary>

On a real S7-300, a client must finish the COTP connection and the setup step before the PLC answers an SZL read. Both CybICS servers are more relaxed: an SZL request sent as the very first packet on a new connection gets a full answer from each. The CybICS server in `software/s7com/s7_server_custom.py` looks only at two bytes of each message, the COTP message type and the S7 message type, and keeps no memory of earlier steps.

Protocol emulators often work this way. It is worth knowing before you spend time debugging a handshake that nothing checks.

</details>

## Detect and defend

Classic S7comm has no authentication on the identity functions. An optional "protection level" password guards some other functions, but it is off by default and weak. Siemens' newer S7-1200 and S7-1500 controllers speak **S7comm-Plus**, which adds protection against replayed and modified messages, but many plants still run the older controllers.

The CybICS IDS handles S7comm with one blunt rule. **Rule 6** raises an alert for any TCP message of four bytes or more sent to port 102 or 1102, from any source. It does not read the content. To avoid a thousand alerts for one scan, it reports each source address at most once every 30 seconds:

<figure class="wide">
<style>
.s7c {--d: 12s;}
/* The cooldown is a timing relationship, so the figure is a clock: the scan
   never stops, and the alert row stays empty for thirty seconds anyway. */
.s7c .head {animation: c-head var(--d) linear 3 forwards;}
.s7c .pk   {opacity:0; animation-duration:var(--d); animation-timing-function:steps(1,end);
            animation-iteration-count:3; animation-fill-mode:forwards;}
.s7c .al1  {opacity:0; animation: c-a1 var(--d) steps(1,end) 3 forwards;}
.s7c .al2  {opacity:0; animation: c-a2 var(--d) steps(1,end) 3 forwards;}
.s7c .band {opacity:0; animation: c-a1 var(--d) steps(1,end) 3 forwards;}
.s7c .p0{animation-name:c-p0}
.s7c .p1{animation-name:c-p1}
.s7c .p2{animation-name:c-p2}
.s7c .p3{animation-name:c-p3}
.s7c .p4{animation-name:c-p4}
.s7c .p5{animation-name:c-p5}
.s7c .p6{animation-name:c-p6}
.s7c .p7{animation-name:c-p7}
.s7c .p8{animation-name:c-p8}
.s7c .p9{animation-name:c-p9}
.s7c .p10{animation-name:c-p10}
.s7c .p11{animation-name:c-p11}
.s7c .p12{animation-name:c-p12}
.s7c .p13{animation-name:c-p13}
.s7c .p14{animation-name:c-p14}
.s7c .p15{animation-name:c-p15}
.s7c .p16{animation-name:c-p16}
.s7c .p17{animation-name:c-p17}
.s7c .p18{animation-name:c-p18}
.s7c .p19{animation-name:c-p19}
.s7c .p20{animation-name:c-p20}
.s7c .p21{animation-name:c-p21}
.s7c .p22{animation-name:c-p22}
.s7c .p23{animation-name:c-p23}
.s7c .p24{animation-name:c-p24}
.s7c .p25{animation-name:c-p25}
.s7c .p26{animation-name:c-p26}
.s7c .p27{animation-name:c-p27}
.s7c .p28{animation-name:c-p28}
.s7c .p29{animation-name:c-p29}
.s7c .p30{animation-name:c-p30}
.s7c .p31{animation-name:c-p31}
.s7c .p32{animation-name:c-p32}
.s7c .p33{animation-name:c-p33}
.s7c .p34{animation-name:c-p34}
.s7c .p35{animation-name:c-p35}
.s7c .p36{animation-name:c-p36}
.s7c .p37{animation-name:c-p37}
.s7c .p38{animation-name:c-p38}
.s7c .p39{animation-name:c-p39}
.s7c .p40{animation-name:c-p40}
.s7c .p41{animation-name:c-p41}
.s7c .p42{animation-name:c-p42}
.s7c .p43{animation-name:c-p43}
.s7c .p44{animation-name:c-p44}
.s7c .p45{animation-name:c-p45}
.s7c .p46{animation-name:c-p46}
.s7c .p47{animation-name:c-p47}
.s7c .p48{animation-name:c-p48}
.s7c .p49{animation-name:c-p49}
.s7c .p50{animation-name:c-p50}
.s7c .p51{animation-name:c-p51}
.s7c .p52{animation-name:c-p52}
.s7c .p53{animation-name:c-p53}
.s7c .p54{animation-name:c-p54}
.s7c .p55{animation-name:c-p55}
.s7c .p56{animation-name:c-p56}
.s7c .p57{animation-name:c-p57}
.s7c .p58{animation-name:c-p58}
.s7c .p59{animation-name:c-p59}
@keyframes c-p0{0%{opacity:0} 0.01%,100%{opacity:1}}
@keyframes c-p1{0%,1.53%{opacity:0} 1.54%,100%{opacity:1}}
@keyframes c-p2{0%,3.07%{opacity:0} 3.08%,100%{opacity:1}}
@keyframes c-p3{0%,4.6%{opacity:0} 4.61%,100%{opacity:1}}
@keyframes c-p4{0%,6.13%{opacity:0} 6.14%,100%{opacity:1}}
@keyframes c-p5{0%,7.67%{opacity:0} 7.68%,100%{opacity:1}}
@keyframes c-p6{0%,9.2%{opacity:0} 9.21%,100%{opacity:1}}
@keyframes c-p7{0%,10.7%{opacity:0} 10.7%,100%{opacity:1}}
@keyframes c-p8{0%,12.3%{opacity:0} 12.3%,100%{opacity:1}}
@keyframes c-p9{0%,13.8%{opacity:0} 13.8%,100%{opacity:1}}
@keyframes c-p10{0%,15.3%{opacity:0} 15.3%,100%{opacity:1}}
@keyframes c-p11{0%,16.9%{opacity:0} 16.9%,100%{opacity:1}}
@keyframes c-p12{0%,18.4%{opacity:0} 18.4%,100%{opacity:1}}
@keyframes c-p13{0%,19.9%{opacity:0} 19.9%,100%{opacity:1}}
@keyframes c-p14{0%,21.5%{opacity:0} 21.5%,100%{opacity:1}}
@keyframes c-p15{0%,23%{opacity:0} 23%,100%{opacity:1}}
@keyframes c-p16{0%,24.5%{opacity:0} 24.5%,100%{opacity:1}}
@keyframes c-p17{0%,26.1%{opacity:0} 26.1%,100%{opacity:1}}
@keyframes c-p18{0%,27.6%{opacity:0} 27.6%,100%{opacity:1}}
@keyframes c-p19{0%,29.1%{opacity:0} 29.1%,100%{opacity:1}}
@keyframes c-p20{0%,30.7%{opacity:0} 30.7%,100%{opacity:1}}
@keyframes c-p21{0%,32.2%{opacity:0} 32.2%,100%{opacity:1}}
@keyframes c-p22{0%,33.7%{opacity:0} 33.7%,100%{opacity:1}}
@keyframes c-p23{0%,35.3%{opacity:0} 35.3%,100%{opacity:1}}
@keyframes c-p24{0%,36.8%{opacity:0} 36.8%,100%{opacity:1}}
@keyframes c-p25{0%,38.3%{opacity:0} 38.3%,100%{opacity:1}}
@keyframes c-p26{0%,39.9%{opacity:0} 39.9%,100%{opacity:1}}
@keyframes c-p27{0%,41.4%{opacity:0} 41.4%,100%{opacity:1}}
@keyframes c-p28{0%,42.9%{opacity:0} 42.9%,100%{opacity:1}}
@keyframes c-p29{0%,44.5%{opacity:0} 44.5%,100%{opacity:1}}
@keyframes c-p30{0%,46%{opacity:0} 46%,100%{opacity:1}}
@keyframes c-p31{0%,47.5%{opacity:0} 47.5%,100%{opacity:1}}
@keyframes c-p32{0%,49.1%{opacity:0} 49.1%,100%{opacity:1}}
@keyframes c-p33{0%,50.6%{opacity:0} 50.6%,100%{opacity:1}}
@keyframes c-p34{0%,52.1%{opacity:0} 52.1%,100%{opacity:1}}
@keyframes c-p35{0%,53.7%{opacity:0} 53.7%,100%{opacity:1}}
@keyframes c-p36{0%,55.2%{opacity:0} 55.2%,100%{opacity:1}}
@keyframes c-p37{0%,56.7%{opacity:0} 56.7%,100%{opacity:1}}
@keyframes c-p38{0%,58.3%{opacity:0} 58.3%,100%{opacity:1}}
@keyframes c-p39{0%,59.8%{opacity:0} 59.8%,100%{opacity:1}}
@keyframes c-p40{0%,61.3%{opacity:0} 61.3%,100%{opacity:1}}
@keyframes c-p41{0%,62.9%{opacity:0} 62.9%,100%{opacity:1}}
@keyframes c-p42{0%,64.4%{opacity:0} 64.4%,100%{opacity:1}}
@keyframes c-p43{0%,65.9%{opacity:0} 65.9%,100%{opacity:1}}
@keyframes c-p44{0%,67.5%{opacity:0} 67.5%,100%{opacity:1}}
@keyframes c-p45{0%,69%{opacity:0} 69%,100%{opacity:1}}
@keyframes c-p46{0%,70.5%{opacity:0} 70.5%,100%{opacity:1}}
@keyframes c-p47{0%,72.1%{opacity:0} 72.1%,100%{opacity:1}}
@keyframes c-p48{0%,73.6%{opacity:0} 73.6%,100%{opacity:1}}
@keyframes c-p49{0%,75.1%{opacity:0} 75.1%,100%{opacity:1}}
@keyframes c-p50{0%,76.7%{opacity:0} 76.7%,100%{opacity:1}}
@keyframes c-p51{0%,78.2%{opacity:0} 78.2%,100%{opacity:1}}
@keyframes c-p52{0%,79.7%{opacity:0} 79.7%,100%{opacity:1}}
@keyframes c-p53{0%,81.3%{opacity:0} 81.3%,100%{opacity:1}}
@keyframes c-p54{0%,82.8%{opacity:0} 82.8%,100%{opacity:1}}
@keyframes c-p55{0%,84.3%{opacity:0} 84.3%,100%{opacity:1}}
@keyframes c-p56{0%,85.9%{opacity:0} 85.9%,100%{opacity:1}}
@keyframes c-p57{0%,87.4%{opacity:0} 87.4%,100%{opacity:1}}
@keyframes c-p58{0%,88.9%{opacity:0} 88.9%,100%{opacity:1}}
@keyframes c-p59{0%,90.5%{opacity:0} 90.5%,100%{opacity:1}}
@keyframes c-head{0%{transform:translateX(0)} 92%,100%{transform:translateX(330px)}}
@keyframes c-a1{0%{opacity:0} 0.5%,100%{opacity:1}}
@keyframes c-a2{0%,46%{opacity:0} 46.1%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce){
  .s7c .head{animation:none; transform:translateX(330px)}
  .s7c .pk,.s7c .al1,.s7c .al2,.s7c .band{animation:none; opacity:1}
}
</style>
<svg class="s7c" viewBox="0 0 420 134" role="img"
     aria-label="A sixty-second timeline. An attacker scans continuously, one packet per second. The IDS raises an alert on the first packet and then nothing at all for thirty seconds, because rule 6 has a thirty-second cooldown per source address. The second alert fires at thirty seconds, while the scan has never paused.">
  <text x="6" y="30" font-size="13" opacity="0.8">scan</text>
  <line x1="70" y1="40" x2="400" y2="40" stroke="currentColor" stroke-opacity="0.3"/>
  <rect class="pk p0" x="70.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p1" x="75.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p2" x="81.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p3" x="86.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p4" x="92.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p5" x="97.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p6" x="103.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p7" x="108.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p8" x="114.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p9" x="119.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p10" x="125.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p11" x="130.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p12" x="136.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p13" x="141.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p14" x="147.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p15" x="152.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p16" x="158.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p17" x="163.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p18" x="169.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p19" x="174.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p20" x="180.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p21" x="185.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p22" x="191.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p23" x="196.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p24" x="202.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p25" x="207.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p26" x="213.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p27" x="218.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p28" x="224.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p29" x="229.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p30" x="235.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p31" x="240.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p32" x="246.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p33" x="251.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p34" x="257.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p35" x="262.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p36" x="268.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p37" x="273.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p38" x="279.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p39" x="284.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p40" x="290.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p41" x="295.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p42" x="301.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p43" x="306.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p44" x="312.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p45" x="317.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p46" x="323.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p47" x="328.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p48" x="334.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p49" x="339.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p50" x="345.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p51" x="350.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p52" x="356.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p53" x="361.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p54" x="367.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p55" x="372.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p56" x="378.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p57" x="383.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p58" x="389.0" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="pk p59" x="394.5" y="26" width="3" height="14" rx="1" fill="#ff6b00"/>
  <rect class="band" x="70" y="72" width="165" height="30" rx="3" fill="currentColor" opacity="0.12"/>
  <text x="6" y="92" font-size="13" opacity="0.8">alerts</text>
  <line x1="70" y1="102" x2="400" y2="102" stroke="currentColor" stroke-opacity="0.3"/>
  <g class="al1"><rect x="67" y="76" width="6" height="26" rx="2" fill="#ff6b00"/></g>
  <g class="al2"><rect x="232" y="76" width="6" height="26" rx="2" fill="#ff6b00"/></g>
  <text class="band" x="152" y="92" text-anchor="middle" font-size="13" opacity="0.85">nothing, for 30 s</text>

  <line class="head" x1="70" y1="20" x2="70" y2="110" stroke="currentColor" stroke-width="2"/>
  <g font-size="13" opacity="0.7">
    <text x="70" y="126" text-anchor="middle">0 s</text>
    <text x="235" y="126" text-anchor="middle">30</text>
    <text x="400" y="126" text-anchor="middle">60</text>
  </g>
</svg>
<figcaption>Sixty seconds of non-stop scanning produce just two alerts: one at the first packet and one when the 30-second cooldown ends. The alerts tell you a host is talking S7comm, not how much it sent.</figcaption>
</figure>

Because it has no allowlist, the rule would also fire on a legitimate engineering workstation. A real plant would at least exempt known engineering hosts and, better, block port 102 from everywhere else with a firewall. The [Detection and monitoring](/theory/detection-monitoring) article explains this trade-off between catching everything and drowning in false alarms.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

- Rule 6 has a 30-second cooldown per source and does not count suppressed packets, so two alerts cannot be told apart from a single probe or a full sweep. A good class discussion: how would you narrow this rule without missing an attacker?
- `training/README.md` maps the S7comm Scanning challenge to T0846 and T0861 (Point &amp; Tag Identification). Reading the SZL is closer to T0888 Remote System Information Discovery, which this article uses.

</details>
