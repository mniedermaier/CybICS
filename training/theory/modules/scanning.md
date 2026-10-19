# Network scanning

In this challenge you map the CybICS network with `nmap`: which hosts answer, which ports are open and which services run behind them. Reconnaissance is the first step of almost every attack, and in an industrial plant it also tells a defender what is really connected.

## The idea

Imagine walking down a corridor of an office building and knocking on every door. Some doors stay shut, some open, and behind some of them someone answers and says who they are. A port scanner does the same with a computer: it "knocks" on numbered doors, called **ports**, and notes which ones answer.

A port is just a number from 0 to 65535 that tells the computer which program a message is for. Well-known services have fixed numbers: web servers usually listen on 80, Modbus TCP on 502, S7comm on 102 and OPC-UA on 4840. Finding port 502 open is a strong hint that the host is a PLC or talks to one.

Going one step further, **service detection** (`nmap -sV`) does not just knock, it starts a short conversation. Many services greet a visitor with a **banner**: a line of text naming the software and its version. That banner is often the most revealing thing a scan returns. MITRE ATT&CK for ICS calls this step *Remote System Discovery* (T0846).

<div class="callout warning" markdown="1">
**Warning:** Scan only systems you are allowed to scan. In real plants, aggressive scans have crashed fragile controllers, so OT teams scan slowly, at agreed times, or prefer passive methods.
</div>

## How it looks on CybICS

The Docker stack runs its containers in the network 172.18.0.0/24. The attack machine is 172.18.0.100, and the services you will meet include:

| Host | Ports you will find |
|---|---|
| openplc, 172.18.0.3 | 502 Modbus, 102 S7comm, 8080 web interface, 20000 DNP3, 44818 EtherNet/IP |
| fuxa, 172.18.0.4 | 1881 HMI web interface |
| opcua, 172.18.0.5 | 4840 OPC-UA |
| s7com, 172.18.0.6 | 1102 S7comm on a non-standard port |
| the host itself | 80 landing page, plus every port Docker publishes |

Click a host below to see what runs on it:

<div data-widget="purdue-explorer"></div>

What `nmap` prints is partly observation and partly guesswork. The service name in its output is often looked up from a table of port numbers, not read from the answer. The same reply can therefore get two different labels depending on the port it came from.

<figure class="wide">
<style>
.sc-r {--r: 14s;}
.sc-r .v1 {opacity:1; animation: sr-v1 var(--r) steps(1,end) infinite;}
.sc-r .v2 {opacity:1; animation: sr-v2 var(--r) steps(1,end) infinite;}
.sc-r .fp {opacity:1; animation: sr-fp var(--r) steps(1,end) infinite;}
@keyframes sr-v1 {0%,21.9%{opacity:0} 22%,100%{opacity:1}}
@keyframes sr-v2 {0%,49.9%{opacity:0} 50%,100%{opacity:1}}
@keyframes sr-fp {0%,67.9%{opacity:0} 68%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .sc-r * {animation:none !important;} }
</style>
<svg class="sc-r" viewBox="0 0 340 250" role="img"
     aria-label="The landing page answers on port 80 and on port 8082 with identical responses, including the same Server header with a custom banner. Scanned on port 80, nmap reports the service as http and prints the banner in the VERSION column. Scanned on port 8082, the same bytes are reported as blackice-alerts with a question mark and no version, and the banner appears only inside the unmatched-service fingerprint nmap prints underneath. The only difference is the port number.">
  <text x="8" y="18" font-size="12" font-weight="bold">one response, two ports</text>
  <rect x="8" y="28" width="324" height="40" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <g font-family="monospace" font-size="11">
    <text x="16" y="44">HTTP/1.1 200 OK</text>
    <text x="16" y="60">Server: &lt;custom banner&gt;</text>
  </g>
  <text x="8" y="84" font-size="11" opacity="0.85">identical on both &mdash; 8082 is a raw TCP passthrough</text>

  <g class="v1" font-family="monospace" font-size="11">
    <text x="8" y="112" opacity="0.7">PORT   STATE SERVICE VERSION</text>
    <text x="8" y="128">80/tcp open  http    &lt;custom banner&gt;</text>
  </g>
  <text class="v1" x="8" y="146" font-size="11" fill="#ff6b00" font-weight="bold">matched &rarr; the banner is the VERSION column</text>

  <g class="v2" font-family="monospace" font-size="11">
    <text x="8" y="176">8082/tcp open  blackice-alerts?</text>
  </g>
  <text class="v2" x="8" y="194" font-size="11" opacity="0.85">unmatched &rarr; the port-table name, and no version</text>
  <g class="fp" font-family="monospace" font-size="11">
    <text x="8" y="216" opacity="0.85">SF:(GetRequest,...,"HTTP/1\.1\x20200\x20OK</text>
    <text x="8" y="230">SF:\r\nServer:\x20&lt;custom banner&gt;</text>
  </g>
  <text class="fp" x="8" y="246" font-size="11" opacity="0.85">&mdash; still there, in the dump nmap could not match.</text>
</svg>
<figcaption>The landing page answers on port 80 and, through a proxy, on 8082 with the same bytes. On 80, nmap recognises HTTP and prints the banner as the version. On 8082, a port registered long ago for an unrelated product, the reply goes unmatched: the service name falls back to the port table, and the banner appears only in the raw fingerprint below the table. Same evidence, two verdicts.</figcaption>
</figure>

## How to approach it

1. Open a terminal on the attack machine and find your own address and network with `ip addr`.
2. Find out which hosts are alive. A host discovery scan (`nmap -sn`) only checks who answers, without probing ports.
3. Scan the interesting hosts for open ports. A plain `nmap <target>` checks the 1000 most common ports; `-p` lets you choose your own list.
4. Add service detection with `-sV` and read every line of the result, not only the service names. Unusual version strings and banners are where hosts give themselves away.
5. If a port shows a question mark or an unknown service, look at the fingerprint nmap prints underneath. It contains the raw reply.

<div data-widget="checkpoint" data-id="banner"></div>

## Detect and defend

Scans are noisy. The CybICS IDS has a port-scan rule: it fires when one source sends connection attempts (TCP SYN packets) to five or more different ports of the same target within ten seconds. The [Detecting a scan](/theory/detect_basic) challenge asks you to find your own scan in its alerts. Rules like this have blind spots, though.

<figure class="wide">
<style>
.sc-d {--d: 14s;}
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
     aria-label="Two scans of the same size. Probing five ports on one host fills a single counter to five within the ten second window and raises a port scan alert. Probing one port on each of five hosts creates five separate counters, each holding one, because the rule counts per source and destination pair. The second scan sends as many packets from the same attacker and never reaches the threshold.">
  <text x="8" y="18" font-size="12" font-weight="bold">five ports on one host</text>
  <text x="8" y="36" font-size="11" opacity="0.85">172.18.0.3 &rarr; 102, 502, 8080, 20000, 44818</text>
  <rect x="8" y="46" width="230" height="20" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <rect class="barA" x="8" y="46" width="230" height="20" rx="4" fill="#ff6b00" stroke="currentColor" stroke-width="1"/>
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

  <text x="8" y="178" font-size="11" opacity="0.85">The counter is kept per source-and-destination pair, so five</text>
  <text x="8" y="194" font-size="11" opacity="0.85">counters each hold one and none of them reaches five.</text>
  <text x="8" y="216" font-size="11" opacity="0.85">Same packets. Same attacker. Same window. No alert.</text>
</svg>
<figcaption>The threshold of five ports counts per target. Sweeping one port across many hosts, which is how you find every Modbus device on a network, never reaches it. The rule also does not care whether a port is open: it counts knocks, not discoveries.</figcaption>
</figure>

<details class="deep-dive" markdown="1">
<summary>Deep dive: what else slips past the port-scan rule</summary>

The rule in `software/ids/rules.py` only looks at TCP packets with the SYN flag set and the ACK flag clear. FIN, NULL and Xmas scans, and any UDP scan, never reach it. It is also a rate rule: five ports spread over more than ten seconds never sit in the window together. The [IDS evasion](/theory/ids_evasion) challenge plays with exactly this kind of gap on a different rule.

</details>

Defences that make scanning less useful:

- **Segmentation.** If the office network cannot reach the control network, a scan from there finds nothing. See [Network segmentation](/theory/defense_network).
- **Minimal services.** Every open port is a door. Close what the plant does not need.
- **Quiet banners.** Services do not have to announce their exact software and version.
- **Asset inventory.** If you know what should be on the network, a scan of your own quickly shows what should not.

## Before you start

- [The ICS attack lifecycle](/theory/attack-lifecycle) for where reconnaissance fits.
- [Modbus TCP](/theory/modbus) and [DNP3, EtherNet/IP and friends](/theory/other-protocols) for the services you will find.
