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
     aria-label="The plant answers S7comm on two ports. Port 102 on the OpenPLC container is snap7's own server, and it reports the snap7 library defaults: a CPU 315-2 PN slash DP, system name SNAP7-SERVER, Original Siemens Equipment. There is no flag there. Port 1102 on the s7com container is a hand-written server, and it reports a fabricated Siemens 300 identity whose module type field carries the challenge flag. Neither endpoint is a Siemens PLC and both claim to be one.">
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

## One `if`, and a list that does not exist

The second lesson takes three requests, and it is not the one you might expect.

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
@keyframes ss-rp {0%,39.9%{opacity:0} 40%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .s7-s * {animation:none !important;} }
</style>
<svg class="s7-s" viewBox="0 0 360 208" role="img"
     aria-label="Three System Status List requests sent to the s7com server: list 0x0011 which is the module identification, list 0x001c which is the component identification, and list 0xBEEF which does not exist. The first gets a one hundred and thirty-five byte module record with no flag. The other two get the same one hundred and eighty-five byte extended record carrying the flag, because the server tests only whether the requested list is 0x0011 and treats everything else alike.">
  <text x="8" y="18" font-size="12" font-weight="bold">three questions, two answers</text>
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
  <g stroke="#ff6b00" stroke-width="2" fill="none">
    <path class="q1" d="M 214 42 L 246 42"/>
    <path class="q2" d="M 214 74 L 240 74 L 240 96 L 246 96"/>
    <path class="q3" d="M 214 106 L 240 106 L 240 96 L 246 96"/>
  </g>
  <g class="q1">
    <rect x="252" y="28" width="100" height="32" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="302" y="42" text-anchor="middle" font-size="11" font-weight="bold">135 bytes</text>
    <text x="302" y="55" text-anchor="middle" font-size="11">no flag</text>
  </g>
  <g class="rp">
    <rect x="252" y="80" width="100" height="32" rx="4" fill="#ff6b00"/>
    <text x="302" y="94" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">185 bytes</text>
    <text x="302" y="107" text-anchor="middle" font-size="11" style="fill:#1a1a1a" font-weight="bold">the flag</text>
  </g>
  <text x="8" y="146" font-size="11" opacity="0.85">The whole dispatch is one comparison: is the list 0x0011?</text>
  <text x="8" y="162" font-size="11" opacity="0.85">If so, the module record. If not, the extended one, flag and all.</text>
  <text x="8" y="184" font-size="11" opacity="0.85">A list that does not exist is not an error here. It is simply</text>
  <text x="8" y="200" font-size="11" opacity="0.85">not 0x0011, which is all the server checks.</text>
</svg>
<figcaption>Measured: three complete handshakes to 172.18.0.6:1102, differing only in the SZL identifier at byte 29. <code>0x0011</code> returns 135 bytes with the module record and no flag; <code>0x001c</code> and <code>0xBEEF</code> both return the same 185 bytes with the flag. <code>s7_server_custom.py</code> reads the identifier and tests it against exactly one value, so everything that is not <code>0x0011</code> takes the same branch &mdash; including an identifier that names no list at all. A real controller answers an unknown SZL with an error. This one answers it with its most interesting record, which is why the flag is easier to reach by asking for something that does not exist than by asking correctly.</figcaption>
</figure>

## Doing it

There is a catch, and it is the challenge. Stock nmap's rule for the script is

```
portrule = shortport.version_port_or_service(102, "iso-tsap", "tcp")
```

&mdash; port **102 only**. The flag is on 1102. So `nmap --script s7-info 172.18.0.6` finds the port open, reports it as `adobeserver-1`, and never speaks S7 at all: the script does not consider itself applicable. `training/scanning2/README.md` tells you to add 1102 to that port list, and that edit *is* the exercise. Afterwards the flag arrives as `Module Type`.

The service half of the rule is worth understanding too, because it is easy to get backwards. `port.service` comes from **`nmap-services`**, the port-number table, where 102 is named `iso-tsap` and 1102 is named `adobeserver-1`. So the service half does fire &mdash; on 102, which is already in the port list, so it changes nothing. What it cannot do is rescue 1102, because nothing will ever name that port `iso-tsap`. (`nmap-service-probes`, the file that drives `-sV`, contains no `iso-tsap` entry at all, so version detection does not help either.)

A warning from doing this badly. I first read that rule on a machine where someone had already completed the challenge &mdash; `dpkg -V nmap-common` flags `s7-info.nse` as modified, its timestamp is a year and a half newer than every other nmap data file, and it said `{102, 1102}`. Measure nmap's behaviour inside the attack machine container, which is pristine, or you will measure your own past homework.

## It is not quiet

The IDS has a rule for exactly this. `s7_enumeration` fires on any TCP payload of four bytes or more to 102 or 1102, from any source, with no service exemption at all &mdash; so a successful fingerprint raises a medium-severity alert, and so does an unsuccessful one. The only version of this that stays silent is the one that never speaks S7, which is precisely what the unpatched script does.

> **MITRE ATT&CK for ICS:** T0846 Remote System Discovery for finding the device, and T0888 Remote System Information Discovery for what this module actually does &mdash; reading make, model and firmware off it. The protocol background is in the *S7comm* foundation topic; this module is about what the answer is worth.
