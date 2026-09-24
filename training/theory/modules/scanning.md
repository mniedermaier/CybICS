# Network scanning

Reconnaissance comes first. A scan maps which hosts answer and which industrial services they run, so an attacker knows where the PLC, the HMI and the protocols live. In OT this needs care &mdash; aggressive scans have knocked over fragile devices &mdash; but the more interesting problem on this platform is not the scanning. It is reading the result.

## What a scanner says, and what it saw

`nmap -sV` prints a service name for every open port. That name is usually a lookup, not an observation.

<figure>
<style>
.article figure svg.sc-r {min-width: 340px;}
.sc-r {--r: 14s;}
/* One response, two ports, two verdicts. Both verdicts stay once reached, so
   the figure ends holding the comparison rather than alternating between its
   halves -- the comparison is the whole content. */
.sc-r .v1 {opacity:1; animation: sr-v1 var(--r) steps(1,end) infinite;}
.sc-r .v2 {opacity:1; animation: sr-v2 var(--r) steps(1,end) infinite;}
.sc-r .fp {opacity:1; animation: sr-fp var(--r) steps(1,end) infinite;}
@keyframes sr-v1 {0%,21.9%{opacity:0} 22%,100%{opacity:1}}
@keyframes sr-v2 {0%,49.9%{opacity:0} 50%,100%{opacity:1}}
@keyframes sr-fp {0%,67.9%{opacity:0} 68%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .sc-r * {animation:none !important;} }
</style>
<svg class="sc-r" viewBox="0 0 340 250" role="img"
     aria-label="The landing page answers on port 80 and on port 8082 with byte-identical responses, including the same Server header carrying the flag. Scanned on port 80, nmap reports the service as http and prints the flag in the VERSION column. Scanned on port 8082, the same bytes are reported as blackice-alerts with a question mark and no version, and the flag appears only inside the unmatched-service fingerprint nmap dumps underneath. The difference is the port number.">
  <text x="8" y="18" font-size="12" font-weight="bold">one response, two ports</text>
  <rect x="8" y="28" width="324" height="40" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <g font-family="monospace" font-size="11">
    <text x="16" y="44">HTTP/1.1 200 OK</text>
    <text x="16" y="60">Server: CybICS(scanning_d0ne)</text>
  </g>
  <text x="8" y="84" font-size="11" opacity="0.85">byte-identical on both &mdash; 8082 is a raw TCP passthrough</text>

  <g class="v1" font-family="monospace" font-size="11">
    <text x="8" y="112" opacity="0.7">PORT   STATE SERVICE VERSION</text>
    <text x="8" y="128">80/tcp open  http    CybICS(scanning_d0ne)</text>
  </g>
  <text class="v1" x="8" y="146" font-size="11" fill="#ff6b00" font-weight="bold">matched &rarr; the banner is the VERSION column</text>

  <g class="v2" font-family="monospace" font-size="11">
    <text x="8" y="176">8082/tcp open  blackice-alerts?</text>
  </g>
  <text class="v2" x="8" y="194" font-size="11" opacity="0.85">unmatched &rarr; the port-table name, and no version</text>
  <g class="fp" font-family="monospace" font-size="11">
    <text x="8" y="216" opacity="0.85">SF:(GetRequest,26F65,"HTTP/1\.1\x20200\x20OK</text>
    <text x="8" y="230">SF:\r\nServer:\x20CybICS\(scanning_d0ne\)</text>
  </g>
  <text class="fp" x="8" y="246" font-size="11" opacity="0.85">&mdash; still there, in the dump nmap could not match.</text>
</svg>
<figcaption>Measured on this stack. The landing page binds <code>0.0.0.0:80</code> and is also reachable on 8082 through a raw TCP passthrough; both return the same bytes, the same <code>Server</code> header, the same <code>Content-Length</code>. Scanned on 80, nmap matches HTTP and puts the banner in VERSION, where you cannot miss it. Scanned on 8082 &mdash; registered as <code>blackice-alerts</code> since long before CybICS existed &mdash; the same bytes go unmatched, the SERVICE column falls back to the port-number lookup, and the banner survives only in the fingerprint nmap dumps because it failed. Identical evidence, two verdicts, and nmap is equally confident about both.</figcaption>
</figure>

A scanner's idea of what a port is comes from a table of port numbers, and its willingness to look harder depends on that same table. The *S7comm Scanning* module meets the identical problem: 1102 is registered as `adobeserver-1`, and the script that would fingerprint it runs only because 1102 happens to be in its own hard-coded port list.

## The scan detector counts pairs, not probes

The other half of this module is that the scan is meant to be caught. Rule 1 in `software/ids/rules.py` fires on five distinct destination ports within ten seconds &mdash; but of what?

<figure>
<style>
.article figure svg.sc-d {min-width: 340px;}
.sc-d {--d: 14s;}
/* The template retints text, strokes and path fills but not a rect, and these
   bars are the data rather than a backdrop: #ff6b00 on white is 2.86:1, and
   2.00:1 against its own track. Nothing is written on them, so unlike a
   labelled panel they can simply be retinted. */
html.light-mode .sc-d rect[fill="#ff6b00"] {fill:#b34700;}
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
@keyframes sd-calm {0%,61.9%{opacity:0} 62%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .sc-d * {animation:none !important;} }
</style>
<svg class="sc-d" viewBox="0 0 340 232" role="img"
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
  <text class="calm" x="252" y="143" font-size="12" font-weight="bold">1 each</text>

  <text x="8" y="178" font-size="11" opacity="0.85">The tracker key is the source-and-destination pair, so five</text>
  <text x="8" y="194" font-size="11" opacity="0.85">counters each hold one and none of them reaches five.</text>
  <text x="8" y="216" font-size="11" opacity="0.85">Same packets. Same attacker. Same window. No alert.</text>
</svg>
<figcaption><code>_check_syn</code> keys its tracker on <code>(src_ip, dst_ip)</code>, so the threshold of five distinct ports is five <em>per target</em>. Sweeping one port across many hosts &mdash; which is how you find every Modbus endpoint on a subnet &mdash; never reaches it. Two things the rule does not care about: whether the port is open, and what runs on it. A default <code>nmap</code> of OpenPLC fired on <code>[22, 25, 80, 143, 8888]</code> &mdash; five ports that host has closed &mdash; long before it reached any of its five real services. The detector counts destinations, not discoveries.</figcaption>
</figure>

Two more things worth knowing before you rely on the rule. The tracker is per pair, but the *alert* is not: `_should_alert` is keyed on the source alone with a thirty-second cooldown, so an attacker who crosses the threshold on ten hosts in a row still produces one alert. And `check_packet` only reaches this rule for TCP packets with the SYN flag set, so a FIN, ACK or NULL scan &mdash; or any UDP scan &mdash; is invisible to it without any timing trick at all.

The timing trick works too, of course: five ports on one host is only a scan if they arrive inside ten seconds, and one probe every three seconds never puts five in the window. That is what the *IDS Evasion* module does to a different rule. A rate rule is a statement about rate, and an attacker who does not care how long it takes is not constrained by it.

## Doing it

Run `nmap -sV` across the lab subnet from the attack machine. The flag is `CybICS(scanning_d0ne)` &mdash; note the zero &mdash; and it arrives as an HTTP `Server` header on the landing page, on **port 80**, where nmap prints it in the VERSION column. You will not have to work for it. The figure above is what happens to the same banner one port number away, and it is the case worth carrying to a plant that does not lay its services out so conveniently.

> **MITRE ATT&CK for ICS:** T0846 Remote System Discovery. The scan is loud on purpose, because *Detect a Scan* asks you to go and find it in the alert stream afterwards &mdash; and a scan you tuned to stay quiet is one you will not find there either.
