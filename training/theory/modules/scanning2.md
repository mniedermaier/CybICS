# S7comm enumeration

Beyond open ports, an attacker wants identity: make, model, firmware. S7comm hands that over through its System Status List with no authentication at all, so a scanner can fingerprint a controller before touching the process.

On this plant that produces two answers, from two different servers, and neither of them is true.

## Two S7 endpoints, two fabricated identities

<figure>
<style>
.article figure svg.s7-t {min-width: 360px;}
.s7-t {--t: 16s;}
/* The probe visits each endpoint in turn and its answer stays on screen, so
   the figure ends holding both identities side by side -- which is the
   comparison, and which a single-state crossfade would have withheld. */
.s7-t .prb {animation: st-prb var(--t) cubic-bezier(.4,0,.2,1) infinite;}
.s7-t .a1  {opacity:1; animation: st-a1 var(--t) steps(1,end) infinite;}
.s7-t .a2  {opacity:1; animation: st-a2 var(--t) steps(1,end) infinite;}
.s7-t .prb {transform: translateY(96px);}
@keyframes st-prb {0%,42%{transform:translateY(0)} 50%,100%{transform:translateY(96px)}}
@keyframes st-a1  {0%,17.9%{opacity:0} 18%,100%{opacity:1}}
@keyframes st-a2  {0%,67.9%{opacity:0} 68%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .s7-t * {animation:none !important;} }
</style>
<svg class="s7-t" viewBox="0 0 360 246" role="img"
     aria-label="The plant answers S7comm on two ports. Port 102 on the OpenPLC container is snap7's own server, and it reports the snap7 library defaults: a CPU 315-2 PN slash DP, serial SNAP7-SERVER, Original Siemens Equipment. There is no flag there. Port 1102 on the s7com container is a hand-written server, and it reports a fabricated Siemens 300 identity whose module type field carries the challenge flag. Neither endpoint is a Siemens PLC and both claim to be one.">
  <text x="8" y="18" font-size="12" font-weight="bold">the same question, asked twice</text>
  <g class="prb"><rect x="8" y="28" width="64" height="24" rx="4" fill="#ff6b00"/>
    <text x="40" y="44" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">SZL read</text></g>

  <text x="86" y="44" font-size="12" font-weight="bold">172.18.0.3 : 102</text>
  <text x="86" y="60" font-size="11" opacity="0.85">OpenPLC&rsquo;s own snap7 server</text>
  <g class="a1" font-family="monospace" font-size="11">
    <text x="86" y="80">CPU 315-2 PN/DP</text>
    <text x="86" y="94">SNAP7-SERVER</text>
    <text x="86" y="108">Original Siemens Equipment</text>
  </g>
  <text class="a1" x="86" y="126" font-size="11" opacity="0.85">&mdash; snap7&rsquo;s defaults. No flag here.</text>

  <text x="86" y="160" font-size="12" font-weight="bold">172.18.0.6 : 1102</text>
  <text x="86" y="176" font-size="11" opacity="0.85">s7com, a hand-written server</text>
  <g class="a2" font-family="monospace" font-size="11">
    <text x="86" y="196">6ES7 315-2AG10-0AB0</text>
    <text x="86" y="210">SIMATIC 300, v2.6.9</text>
    <text x="86" y="224" fill="#ff6b00" font-weight="bold">CybICS(s7comm_&hellip;)</text>
  </g>
  <text class="a2" x="86" y="242" font-size="11" opacity="0.85">&mdash; the flag, in the Module Type field.</text>
</svg>
<figcaption>Read from the running stack. Port 102 belongs to OpenPLC, whose snap7 server answers with the library&rsquo;s built-in strings &mdash; <code>CPU 315-2 PN/DP</code>, <code>SNAP7-SERVER</code>, <code>Original Siemens Equipment</code> &mdash; and carries no flag. The challenge&rsquo;s flag is on <strong>1102</strong>, on the separate <code>s7com</code> container, in the <code>Module Type</code> field of a fabricated SIMATIC 300 record. Both endpoints claim to be Siemens hardware. One is a C++ library&rsquo;s placeholder and the other is a Python socket server; the actual controller is OpenPLC, which is neither.</figcaption>
</figure>

That is the first lesson of fingerprinting, and it is not a CybICS quirk. An identity record is a string the device chooses to send. It is evidence about what the device *says*, and it is only evidence about what the device *is* when nobody has a reason to lie.

## The fingerprint answers before it listens

The second lesson is sharper, and you can reach it with three requests.

<figure>
<style>
.article figure svg.s7-s {min-width: 360px;}
.s7-s {--s: 15s;}
/* Three different questions and one identical answer, drawn as three arrivals
   at one reply. The point is that the reply never changes, so the figure has
   to let you watch all three land on it. */
.s7-s .q1 {opacity:1; animation: ss-q1 var(--s) steps(1,end) infinite;}
.s7-s .q2 {opacity:1; animation: ss-q2 var(--s) steps(1,end) infinite;}
.s7-s .q3 {opacity:1; animation: ss-q3 var(--s) steps(1,end) infinite;}
.s7-s .rp {opacity:1; animation: ss-rp var(--s) steps(1,end) infinite;}
@keyframes ss-q1 {0%,9.9%{opacity:0} 10%,100%{opacity:1}}
@keyframes ss-q2 {0%,34.9%{opacity:0} 35%,100%{opacity:1}}
@keyframes ss-q3 {0%,59.9%{opacity:0} 60%,100%{opacity:1}}
@keyframes ss-rp {0%,14.9%{opacity:0} 15%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .s7-s * {animation:none !important;} }
</style>
<svg class="s7-s" viewBox="0 0 360 208" role="img"
     aria-label="Three System Status List requests sent to the s7com server: list 0x0011 which is the module identification, list 0x001c which is the component identification, and list 0xBEEF which does not exist. All three receive the same one hundred and eighty-five byte response containing the same record and the same flag. The server dispatches on the S7 message type alone and never reads which list was asked for.">
  <text x="8" y="18" font-size="12" font-weight="bold">three questions, one answer</text>
  <g font-family="monospace" font-size="11">
    <text class="q1" x="8" y="46">SZL 0x0011</text>
    <text class="q2" x="8" y="78">SZL 0x001c</text>
    <text class="q3" x="8" y="110">SZL 0xBEEF</text>
  </g>
  <g font-size="11" opacity="0.85">
    <text class="q1" x="86" y="46">module identification</text>
    <text class="q2" x="86" y="78">component identification</text>
    <text class="q3" x="86" y="110">does not exist</text>
  </g>
  <g stroke="#ff6b00" stroke-width="2">
    <path class="q1" d="M 214 42 L 246 42 L 246 66"/>
    <path class="q2" d="M 214 74 L 246 74"/>
    <path class="q3" d="M 214 106 L 246 106 L 246 82"/>
  </g>
  <g class="rp">
    <rect x="252" y="58" width="100" height="32" rx="4" fill="#ff6b00"/>
    <text x="302" y="72" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">185 bytes</text>
    <text x="302" y="85" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">the flag</text>
  </g>
  <text x="8" y="146" font-size="11" opacity="0.85">The server branches on the S7 message type alone:</text>
  <text x="8" y="162" font-size="11" opacity="0.85">a job request gets a setup reply, a userdata message gets this.</text>
  <text x="8" y="184" font-size="11" opacity="0.85">It never reads which list you asked for, so asking for one that</text>
  <text x="8" y="200" font-size="11" opacity="0.85">does not exist works exactly as well.</text>
</svg>
<figcaption>Measured: three complete handshakes to 172.18.0.6:1102, differing only in the SZL identifier, each answered with the same 185 bytes and the same flag &mdash; including <code>0xBEEF</code>, which is not a list at all. <code>software/s7com/s7_server_custom.py</code> dispatches on the S7 message type: <code>0x01</code> gets a setup reply and <code>0x07</code> gets the canned SZL record, whatever was requested. As an exercise that is fine. As a model of a controller it is worth knowing, because it means this endpoint cannot teach you what a real SZL negotiation looks like &mdash; only what one looks like from the outside.</figcaption>
</figure>

## Doing it

`nmap --script s7-info -p 1102 172.18.0.6` is the short path, and 1102 is inside nmap's default top-1000 port set, so a plain scan of the host finds it. The flag arrives as `Module Type`.

One detail worth knowing for the next plant. The script's own rule is `version_port_or_service({102, 1102}, "iso-tsap", "tcp")`, and the service half can never match: `nmap-service-probes` contains no `iso-tsap` entry at all, so nmap has no probe that would ever name a service `iso-tsap`. The script runs when 102 or 1102 is in the port set, and not otherwise &mdash; a plant that puts S7comm on any other port will be scanned, will answer, and will not be fingerprinted.

> **MITRE ATT&CK for ICS:** T0846 Remote System Discovery. The protocol background is in the *S7comm* foundation topic; this module is about what the answer is worth.
