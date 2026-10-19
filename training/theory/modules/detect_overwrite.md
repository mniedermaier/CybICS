# Detecting a flood

In this challenge you launch a Modbus write flood against the PLC, watch its effect on the plant, and then find it again from the defender's side: in the IDS alerts and in a packet capture. You learn how a rate-based rule tells an attack apart from the plant's own busy traffic, and how to connect evidence from different sources into one story.

## The idea

Modbus has no login. Anyone who can reach port 502 can tell the PLC "write this value into that register", and the PLC obeys. A **write flood** sends that command again and again, hundreds of times a second, so the attacker's value wins over whatever the real process writes.

Detection starts from a simple observation: how *often* something happens is itself a signal. Think of a doorbell. One ring is a visitor. Fifty rings in five seconds is not a visitor.

A **rate rule** counts events from one source in a sliding time window and alerts when the count crosses a threshold. The hard part is choosing the numbers. Set the threshold too low and normal traffic causes **false alarms**; set it too high and a careful attacker slips underneath.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="A line chart of writes per second from one host over time. The rate is low at first, then jumps above a dashed threshold line, and a modbus_flood alert is raised.">
  <polyline points="20,90 60,88 100,85 140,84 180,50 220,30 260,25 300,24" fill="none" stroke="#ff6b00" stroke-width="2"/>
  <line x1="20" y1="45" x2="320" y2="45" stroke="currentColor" stroke-dasharray="5 4" opacity="0.5"/>
  <text x="324" y="48" font-size="11">threshold</text>
  <text x="20" y="110" font-size="11" opacity="0.7">writes per second from one host over time</text>
  <rect x="360" y="30" width="150" height="30" rx="4" fill="#ff6b00" opacity="0.6"/>
  <text x="435" y="49" text-anchor="middle" font-size="11" fill="#1a1a1a">modbus_flood alert</text>
</svg>
<figcaption>When the write rate from a single host jumps past the threshold, the flood rule fires.</figcaption>
</figure>

## How it looks on CybICS

The attack script `override.py` in the challenge folder connects to OpenPLC at `172.18.0.3:502` and writes the gas storage tank (GST) register, holding register 1124, in a tight loop. On the FUXA HMI the GST value stops behaving like a real tank.

The plant itself writes to the PLC all the time: the hardware simulation (`hwio`) writes the sensor values many times a second, and FUXA writes when the operator presses a button. So the IDS rules must not simply count writes. They count writes **per source** and ignore the hosts that are expected to write.

| Rule | Counts | Threshold | Ignores |
|---|---|---|---|
| `modbus_flood` | write function codes 5, 6, 15 and 16 | 50 in 5 seconds | hwio, FUXA, OpenPLC |
| `modbus_unauth_write` | the same write codes | 10 in 30 seconds | hwio, FUXA |

Both rules only look at **writes**. A flood of read requests raises neither of them; reads are normal polling traffic in this plant.

<div data-widget="ids-threshold"></div>

Try the simulator above. Lower the threshold until the attacker is caught quickly, and watch when the legitimate HMI starts to cause false alarms.

<div data-widget="checkpoint" data-id="reads"></div>

## How to approach it

1. **Watch the plant.** Open the FUXA HMI so you can see the effect of the attack.
2. **Start a capture.** Record traffic to port 502 with `tcpdump` or Wireshark before you attack, so you have evidence to analyse afterwards.
3. **Run the flood** from the attack machine against the PLC for about half a minute, then stop it and the capture.
4. **Read the IDS.** On the dashboard (port 8443) and in `/api/alerts`, find the Modbus alerts. Note source, target and severity. Then check `/api/rules/stats` as the challenge asks.
5. **Analyse the capture.** In Wireshark, filter for write requests, for example `modbus.func_code == 6`. Which register is written, with which value, how fast? **Statistics > I/O Graphs** shows the rate as a spike.
6. **Correlate.** Do the attacker address, target and rate in the capture match what the IDS reported? Matching evidence from two independent sources is much stronger than either alone.

## Detect and defend

- **Count per source, allow-list known writers.** The CybICS rules show the pattern: high-rate writes are only suspicious from hosts that have no reason to write.
- **Watch the process, not only the network.** A tank value that jumps or stays frozen while the compressor runs is a process-level warning that works even if the network rule is evaded. D3FEND calls this **Operational Process Monitoring**.
- **Block unauthorised writers.** A firewall or a protocol-aware gateway that only lets FUXA and hwio send write function codes to the PLC stops the attack instead of just reporting it.
- **Know your thresholds' limits.** An attacker who sends nine writes every 30 seconds stays under both rules. The [IDS evasion](/theory/ids_evasion) module is built on exactly that gap.

The attack maps to MITRE ATT&CK for ICS **T0806 Brute Force I/O** (repeatedly forcing a value) and **T1692.001 Unauthorized Message: Command Message**.

<details class="deep-dive" markdown="1">
<summary>Deep dive: why there are two rules</summary>

`modbus_flood` answers "is someone writing far too fast?" It has a short window and a high threshold, so even a legitimate but buggy client would be caught.

`modbus_unauth_write` answers "is someone writing who should not write at all?" It has a long window and a low threshold, and it does not exempt OpenPLC, because the PLC is a Modbus server and should not send write requests to anyone.

Together they cover a loud attacker (both fire) and a slower one from an unknown host (only the second fires). Each alert carries a severity, critical for the flood and high for the unauthorised write, which helps an analyst decide what to look at first.

</details>

## Before you start

- [Flood and overwrite](/theory/flood_overwrite): the attack this module detects.
- [Detecting a scan](/theory/detect_basic): the IDS dashboard and the threshold idea.
- [Wireshark capture](/theory/wireshark_capture): filtering and reading Modbus packets.
- [Modbus TCP](/theory/modbus): the write function codes.
