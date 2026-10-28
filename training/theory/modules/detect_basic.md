# Detecting a scan

In this challenge you switch sides. You run a port scan like the one from the reconnaissance modules, then go to the CybICS intrusion detection system (IDS) and find the alert your scan caused. You will see the whole detection chain once from end to end: an action, the packets it creates, the rule that matches them and the alert a defender reads.

## The idea

Before attackers can attack a device, they have to find out what it offers. A **port scan** knocks on many network ports of a host, one after another, to see which ones answer. It is the network version of walking down a hotel corridor and trying every door handle.

That is noisy. Normal clients connect to one or two ports they already know: the HMI talks to Modbus port 502, a browser to a web port. A single source touching many different ports in a few seconds almost never happens by accident.

An **intrusion detection system** watches traffic and compares it with **rules**. A simple and effective rule for scans is: *count how many different ports one source has tried on one target within a short time window, and raise an alert when the count passes a threshold.*

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Eight connection attempts from one source to different ports inside a sliding time window. Once the number of distinct ports reaches the threshold, a port_scan alert is raised.">
  <text x="20" y="24" font-size="11">one source, unique ports in a sliding window</text>
  <rect x="20" y="40" width="360" height="30" rx="4" fill="currentColor" opacity="0.12" stroke="currentColor"/>
  <g fill="#ff6b00">
    <rect x="30" y="46" width="10" height="18"/><rect x="55" y="46" width="10" height="18"/>
    <rect x="80" y="46" width="10" height="18"/><rect x="110" y="46" width="10" height="18"/>
    <rect x="140" y="46" width="10" height="18"/><rect x="175" y="46" width="10" height="18"/>
    <rect x="210" y="46" width="10" height="18"/><rect x="250" y="46" width="10" height="18"/>
  </g>
  <text x="400" y="60" font-size="11">&ge; threshold &rarr;</text>
  <rect x="400" y="70" width="110" height="28" rx="4" fill="#ff6b00" opacity="0.6"/>
  <text x="455" y="89" text-anchor="middle" font-size="11" fill="#1a1a1a">port_scan alert</text>
  <text x="20" y="112" font-size="11" opacity="0.7">Counting unique destination ports per source over a time window.</text>
</svg>
<figcaption>The port-scan rule counts how many distinct ports a single source probes on one target within a window. Past the threshold, it alerts.</figcaption>
</figure>

## How it looks on CybICS

The CybICS IDS runs on the host and listens to all traffic on the plant network `172.18.0.0/24`. It has ten rules; the one for this challenge is called `port_scan`.

| Part of the rule | Value on CybICS |
|---|---|
| What it counts | TCP packets with only the SYN flag set, the first step of a connection |
| Grouped by | source address and target address |
| Threshold | 5 or more different destination ports |
| Window | 10 seconds |
| Repeat alerts | at most one per source every 30 seconds |

You can see the result in two places. The IDS dashboard on port **8443** shows the alerts as they arrive. Behind it is a small web API: `/api/alerts` lists the alerts, and `/api/rules/stats` counts how often each rule has fired. The challenge asks you to look there once your scan has been detected.

<div class="callout cybics" markdown="1">
**On CybICS:** your scan of the OpenPLC container at `172.18.0.3` appears with your attack machine's address as the source. The alert also lists the ports it saw, so you can compare them with your scanner's output.
</div>

<div data-widget="checkpoint" data-id="threshold"></div>

## How to approach it

1. **Open the IDS dashboard** first, so you can watch the alert appear live.
2. **Scan a target.** Use `nmap` against the PLC, or the `recon.py` script from the challenge folder, which checks six common industrial ports. Note which ports are open and which closed.
3. **Find the alert** on the dashboard. Check its source, target, severity and the list of ports.
4. **Query the API.** Use `curl` or a browser to read `/api/rules/stats` and look at the `port_scan` entry.
5. **Think like a defender.** Compare the number of ports you scanned with the threshold. What would have happened with four?

<details class="deep-dive" markdown="1">
<summary>Deep dive: scans that slip under this rule</summary>

Every threshold rule has an edge, and attackers look for it. Against this rule:

- **Slow scans** probe one port every few seconds, so fewer than five fall into any 10-second window.
- **Wide scans** check one port on many hosts. The rule counts ports per source-and-target pair, so each pair stays at one.
- **Scans without SYN packets**, for example nmap's ACK or UDP scans, are not counted, because the rule only looks at TCP SYN packets.

Defenders answer with longer windows, counting per source across all targets, or flagging *any* connection to a port that is never used in this plant. Each change catches more but also risks more false alarms. The [IDS evasion](/theory/ids_evasion) module explores this trade-off from the attacker's side.

</details>

With the threshold, the window and the deep dive in mind, sort these observations the way a defender would.

<div data-widget="sequence" data-id="triage"></div>

## Detect and defend

This whole module *is* the detection side, but a few lessons carry over to any real plant:

- **Industrial networks are predictable.** The same hosts talk to the same ports all day, so anything new stands out. That makes scan detection far more reliable than on an office network.
- **Detection needs someone to look.** An alert that nobody reads stops nothing. Send alerts somewhere they are seen and acted on.
- **Detection is not prevention.** A firewall that only allows the ports each host needs makes the scan return almost nothing in the first place.

The attacker's technique is MITRE ATT&CK for ICS **T0846.001 Remote System Discovery: Port Scan**. The defence is MITRE D3FEND **Network Traffic Analysis** and **Connection Attempt Analysis**.

## Before you start

- [Detection and monitoring](/theory/detection-monitoring): how an IDS and its rules work.
- [Network scanning](/theory/scanning): running the scan you are about to detect.
- [The ICS attack lifecycle](/theory/attack-lifecycle): why discovery comes first.
