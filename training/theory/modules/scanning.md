# Network scanning

Reconnaissance comes first. A scan maps which hosts answer and which industrial services they run, so an attacker knows where the PLC, the HMI and the protocols live. In OT this needs care &mdash; aggressive scans have knocked over fragile devices &mdash; but the more interesting problem on this platform is not the scanning. It is reading the result.

## What a scanner says, and what it saw

`nmap -sV` prints a service name for every open port. That name is usually a lookup, not an observation.

<figure>
<style>
.article figure svg.sc-r {min-width: 360px;}
.sc-r {--r: 12s;}
/* The result line appears first and the fingerprint block after it, because
   that is the order a reader meets them and the order in which the useful
   half arrives second. The block is the payload; the line above it is a
   guess from a registry file. */
.sc-r .ln  {opacity:1; animation: sr-ln var(--r) steps(1,end) infinite;}
.sc-r .fp  {opacity:1; animation: sr-fp var(--r) steps(1,end) infinite;}
.sc-r .hit {opacity:1; animation: sr-hit var(--r) steps(1,end) infinite;}
@keyframes sr-ln  {0%,14.9%{opacity:0} 15%,100%{opacity:1}}
@keyframes sr-fp  {0%,39.9%{opacity:0} 40%,100%{opacity:1}}
@keyframes sr-hit {0%,64.9%{opacity:0} 65%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .sc-r * {animation:none !important;} }
</style>
<svg class="sc-r" viewBox="0 0 360 214" role="img"
     aria-label="The output of nmap dash s V against port 8082. The result line reports the port as open and names the service blackice-alerts with a question mark, which is the name registered for that port number rather than anything nmap observed. Below it nmap prints the fingerprint it could not match, and inside that fingerprint is the HTTP Server header, which reads CybICS open bracket scanning underscore d zero n e close bracket. The name is a guess; the flag is in the evidence underneath it.">
  <text x="8" y="18" font-size="12" font-weight="bold">nmap -sV -p 8082</text>
  <g font-family="monospace" font-size="11">
    <text x="8" y="40" opacity="0.7">PORT     STATE SERVICE</text>
    <text class="ln" x="8" y="56">8082/tcp open  blackice-alerts?</text>
  </g>
  <text x="8" y="78" font-size="11" opacity="0.85">&mdash; the name registered for port 8082, not what answered</text>

  <rect class="fp" x="8" y="92" width="344" height="70" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <g class="fp" font-family="monospace" font-size="11">
    <text x="16" y="108" opacity="0.85">1 service unrecognized despite returning</text>
    <text x="16" y="122" opacity="0.85">data. &hellip; fingerprint:</text>
    <text x="16" y="140">SF:(GetRequest,26F65,"HTTP/1\.1\x20200\x20OK</text>
    <text x="16" y="154">SF:\r\nServer:\x20CybICS\(scanning_d0ne\)</text>
  </g>
  <rect class="hit" x="86" y="144" width="184" height="14" rx="3" fill="none" stroke="#ff6b00" stroke-width="2"/>

  <text x="8" y="184" font-size="11" opacity="0.85">The service column is a lookup in nmap-services. The evidence</text>
  <text x="8" y="200" font-size="11" opacity="0.85">is in the block nmap prints because it could not match it.</text>
</svg>
<figcaption>Run against this stack, at nmap&rsquo;s default version intensity, the landing page on 8082 comes back as <code>blackice-alerts?</code> &mdash; the name <code>nmap-services</code> has registered for that port number since long before CybICS existed. nmap did read the answer; it just could not classify it, so it dumped the raw fingerprint instead, and the flag is sitting in it as the HTTP <code>Server</code> header. A learner who reads only the SERVICE column has scanned the port, received the flag, and missed it. The header comes from <code>software/landing/app.py</code>, which monkey-patches Werkzeug&rsquo;s <code>version_string</code>.</figcaption>
</figure>

This is the same trap the *S7comm Scanning* module meets from the other side: a scanner's idea of what a port is comes from a table of port numbers, and a plant that runs a service on an unregistered port will be described wrongly with complete confidence.

## The scan detector counts pairs, not probes

The other half of this module is that the scan is meant to be caught. Rule 1 in `software/ids/rules.py` fires on five distinct destination ports within ten seconds &mdash; but of what?

<figure>
<style>
.article figure svg.sc-d {min-width: 360px;}
.sc-d {--d: 14s;}
/* Two scans of the same size at the same rate, one of which fires and one of
   which never can. The difference is only in how the probes are distributed,
   so the figure has to show them arriving -- a still could show the end state
   but not why the two ended differently. */
.sc-d .barA {transform-box: fill-box; transform-origin: left; animation: sd-a var(--d) steps(5,end) infinite;}
.sc-d .barB {transform-box: fill-box; transform-origin: left; animation: sd-b var(--d) steps(1,end) infinite;}
.sc-d .alrt {opacity:1; animation: sd-alrt var(--d) steps(1,end) infinite;}
.sc-d .calm {opacity:1; animation: sd-calm var(--d) steps(1,end) infinite;}
.sc-d .barA {transform: scaleX(1);}
.sc-d .barB {transform: scaleX(1);}
@keyframes sd-a    {0%{transform:scaleX(0)} 44%,100%{transform:scaleX(1)}}
@keyframes sd-b    {0%,49%{transform:scaleX(0)} 50%,100%{transform:scaleX(1)}}
@keyframes sd-alrt {0%,43.9%{opacity:0} 44%,100%{opacity:1}}
@keyframes sd-calm {0%,89.9%{opacity:0} 90%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .sc-d * {animation:none !important;} }
</style>
<svg class="sc-d" viewBox="0 0 360 232" role="img"
     aria-label="Two scans of the same size. Probing five ports on one host fills a single counter to five within the ten second window and raises a port scan alert. Probing one port on each of five hosts creates five separate counters, each holding one, because the rule keys its tracker on the source and destination pair. The second scan sends exactly as many packets from exactly the same attacker and never reaches the threshold.">
  <text x="8" y="18" font-size="12" font-weight="bold">five ports on one host</text>
  <text x="8" y="36" font-size="11" opacity="0.85">172.18.0.3 &rarr; 102, 502, 8080, 20000, 44818</text>
  <rect x="8" y="46" width="230" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="barA" x="8" y="46" width="230" height="20" rx="4" fill="#ff6b00"/>
  <text class="alrt" x="248" y="61" font-size="12" font-weight="bold" fill="#ff6b00">5 &rarr; ALERT</text>

  <text x="8" y="100" font-size="12" font-weight="bold">five hosts, one port each</text>
  <text x="8" y="118" font-size="11" opacity="0.85">.2 .3 .4 .5 .6 &mdash; same attacker, same ten seconds</text>
  <g>
    <rect x="8"   y="128" width="42" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="56"  y="128" width="42" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="104" y="128" width="42" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="152" y="128" width="42" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <rect x="200" y="128" width="42" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <g class="barB">
      <rect x="8"   y="128" width="9" height="20" rx="3" fill="#ff6b00"/>
      <rect x="56"  y="128" width="9" height="20" rx="3" fill="#ff6b00"/>
      <rect x="104" y="128" width="9" height="20" rx="3" fill="#ff6b00"/>
      <rect x="152" y="128" width="9" height="20" rx="3" fill="#ff6b00"/>
      <rect x="200" y="128" width="9" height="20" rx="3" fill="#ff6b00"/>
    </g>
  </g>
  <text class="calm" x="252" y="143" font-size="12" font-weight="bold">1 each, silence</text>

  <text x="8" y="178" font-size="11" opacity="0.85">The tracker key is the source-and-destination pair, so five</text>
  <text x="8" y="194" font-size="11" opacity="0.85">counters each hold one and none of them reaches five.</text>
  <text x="8" y="216" font-size="11" opacity="0.85">Same packets. Same attacker. Same window. No alert.</text>
</svg>
<figcaption><code>_check_syn</code> keys its tracker on <code>(src_ip, dst_ip)</code>, so the threshold of five distinct ports is five <em>per target</em>. Sweeping one port across many hosts &mdash; which is how you find every Modbus endpoint on a subnet &mdash; never reaches it. Note also that OpenPLC alone listens on exactly five service ports: 102, 502, 8080, 20000 and 44818. A full scan of that one host hits the threshold precisely, which is tidy for the exercise and worth not mistaking for a general rule.</figcaption>
</figure>

The same arithmetic gives the other evasion: five ports on one host is only a scan if they arrive inside ten seconds. One probe every three seconds never puts five in the window. That is what the *IDS Evasion* module does to a different rule, and the shape of the answer is the same both times &mdash; a rate rule is a statement about rate, and an attacker who does not care how long it takes is not constrained by it.

## Doing it

Run `nmap -sV` across the lab subnet from the attack machine. The flag is `CybICS(scanning_d0ne)` &mdash; note the zero &mdash; and it arrives as an HTTP `Server` header on the landing page, which means reading the fingerprint block rather than the service column.

> **MITRE ATT&CK for ICS:** T0846 Remote System Discovery. The scan is loud on purpose, because *Detect a Scan* asks you to go and find it in the alert stream afterwards &mdash; and a scan you tuned to stay quiet is one you will not find there either.
