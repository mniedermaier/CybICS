# 🔥 Detect Modbus Flooding

> **MITRE D3FEND:** `Detect` | [D3-NTA - Network Traffic Analysis](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | [D3-OPM - Operational Process Monitoring](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/)

## 📋 Overview

Modbus TCP has **no authentication** — any device on the network can write to PLC registers. A flooding attack sends hundreds or thousands of write commands per second to overwrite process values, disrupting the physical process.

In this challenge you will launch a Modbus flooding attack, observe its impact on the physical process, verify the IDS detected it, analyze the attack in a packet capture, and retrieve the flag from the IDS.

### Detection Rules

The IDS has two rules that detect Modbus write attacks:

| Rule | Threshold | What It Detects |
|------|-----------|-----------------|
| `modbus_flood` | **50 writes in 5 seconds** | High-rate Modbus writes (flooding) |
| `modbus_unauth_write` | **10 writes in 30 seconds** | Modbus writes from unauthorized sources |

The flooding script sends ~1000 writes/second — far above both thresholds.

## 🎯 Task

Launch the attack, observe the IDS detection, capture and analyze the traffic, and find the flag.

The flag has the format `CybICS(flag)`.

---

### Phase 1: Launch the Attack

> **Important:** Run the script first **without looking at its source code** — observe the effects before understanding the cause.

1. Open the FUXA HMI at [http://localhost:1881](http://localhost:1881) in one browser tab to watch the physical process.

2. In a terminal, start a packet capture (stop it later with Ctrl+C):
   ```bash
   tcpdump -i any -w modbus_attack.pcap 'tcp port 502' &
   ```

3. Run the attack script:
   ```bash
   python3 override.py 172.18.0.3
   ```

4. Watch the FUXA HMI — what happens to the process values? The Gas Storage Tank (GST) register is being overwritten with a fixed value.

5. After ~30 seconds, stop the attack (Ctrl+C) and stop tcpdump (`kill %1`).

### Phase 2: IDS Analysis

Your attack triggered IDS alerts. Verify this:

1. Open the IDS dashboard at [http://localhost:8443](http://localhost:8443) and check the **Alerts** tab.

2. Query the rule statistics:
   ```bash
   curl -s http://localhost:8443/api/rules/stats | python3 -m json.tool
   ```

3. Look at the `modbus_flood` entry — when `count > 0`, the **flag is revealed** in the response:
   ```bash
   curl -s http://localhost:8443/api/rules/stats | python3 -c "
   import sys, json
   data = json.load(sys.stdin)
   for rule in ['modbus_flood', 'modbus_unauth_write']:
       r = data.get(rule, {})
       print(f'{rule}: count={r.get(\"count\", 0)}, flag={r.get(\"flag\", \"-\")}')
   "
   ```

4. Check the alert details — what source IP was detected? What severity?
   ```bash
   curl -s http://localhost:8443/api/alerts | python3 -c "
   import sys, json
   for a in json.load(sys.stdin).get('alerts', []):
       if 'modbus' in a['rule']:
           print(f\"{a['rule']:25s} | {a['src']:15s} -> {a['dst']:15s} | {a['severity']}\")
   "
   ```

### Phase 3: PCAP Forensics

Analyze the captured traffic to understand the attack pattern:

1. Open the packet capture in Wireshark (or use tshark):
   ```bash
   wireshark modbus_attack.pcap
   ```

2. Apply this filter to see only Modbus write commands:
   ```
   modbus.func_code == 6 || modbus.func_code == 16
   ```

3. Answer these analysis questions:

   | Question | How to Find It |
   |----------|---------------|
   | How many total Modbus write packets? | Wireshark status bar after applying filter |
   | What is the write rate (writes/second)? | Total writes / capture duration |
   | Which register is being overwritten? | Check Modbus payload: register address 1124 |
   | What value is being written? | Check Modbus payload: value = 1 |
   | What is the attacker's source IP? | Source column in Wireshark |

4. Use Wireshark's **IO Graph** (Statistics -> IO Graphs) to visualize the write rate spike:
   - Display filter: `modbus.func_code == 16`
   - This shows the dramatic spike during the flooding attack

### Phase 4: Correlation

Connect your findings across all three data sources:

| Data Point | PCAP (Wireshark) | IDS Alert | Match? |
|------------|-------------------|-----------|--------|
| Attacker IP | ___________ | ___________ | Yes / No |
| Target IP | ___________ | ___________ | Yes / No |
| Write rate | ___/sec | Threshold: 50/5s | Exceeded? |
| Rule triggered | N/A | `modbus_flood` | |

**Why did `modbus_flood` fire?**
- Threshold: 50 writes in 5 seconds
- Your attack: ~1000 writes/second = ~5000 writes in 5 seconds
- 5000 >> 50 = rule triggered

**Why did `modbus_unauth_write` fire?**
- Threshold: 10 writes in 30 seconds from a non-service IP
- Your attack machine is not in the authorized Modbus writers list (hwio, fuxa)
- Any write from your IP triggers this rule after 10 writes

## 🛡️ Security Framework References

<details>
<summary>Click to expand</summary>

### MITRE ATT&CK for ICS — Detected Techniques

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Impair Process Control | Modify Parameter | [T0836](https://attack.mitre.org/techniques/T0836/) | Modifying process parameters to affect operation |
| Impair Process Control | Unauthorized Command Message | [T0855](https://attack.mitre.org/techniques/T0855/) | Sending unauthorized commands to ICS devices |
| Impair Process Control | Brute Force I/O | [T0806](https://attack.mitre.org/techniques/T0806/) | Repeatedly overwriting I/O values |

### MITRE D3FEND — Defensive Techniques

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Analyzing Modbus traffic for flooding patterns |
| Operational Process Monitoring | [D3-OPM](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/) | Monitoring process values for unexpected changes |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-4, SI-7 | System monitoring and integrity verification |
| **Audit and Accountability (AU)** | AU-3, AU-6 | Audit record content and automated review |
| **Incident Response (IR)** | IR-4, IR-5 | Incident handling and monitoring |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.7 emphasizes that OT monitoring (SI-4) must include both network-level detection (IDS alerts) and process-level monitoring (register values). The combination of PCAP forensics and IDS analysis practiced here mirrors real SOC workflows where analysts correlate multiple data sources during incident response.

</details>

## 🔍 Defensive Thinking

After completing this challenge, consider:
- The attack sends ~1000 writes/second but the threshold is only 50/5s. How would you lower the threshold without causing false positives from legitimate FUXA polling?
- What if the attacker sent only 9 writes per 30 seconds (below `modbus_unauth_write` threshold)? The **IDS Evasion** challenge explores exactly this.
- How would you implement **allowlisting** so only FUXA and hwio can write to Modbus?
- What process-level indicators (register values, control loop behavior) could supplement network detection?


## 💡 Hints

Run `override.py` against the PLC, then query `http://localhost:8443/api/rules/stats`. Look at the `modbus_flood` entry — when `count > 0`, a `flag` field appears in the JSON response. For the PCAP analysis, use Wireshark filter `modbus.func_code == 16` to isolate the write commands.

## 🔍 Solution

Run the Modbus flooding attack, then query the IDS rule statistics API:

```bash
curl -s http://localhost:8443/api/rules/stats
```

Look for the `flag` field in the `modbus_flood` entry when `count > 0`.

**Flag:** `CybICS(m0dbus_fl00d_d3tect3d)`
