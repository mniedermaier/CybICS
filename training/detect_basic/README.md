# 🔍 Detect Port Scan

> **MITRE D3FEND:** `Detect` | [D3-NTA - Network Traffic Analysis](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | [D3-CAA - Connection Attempt Analysis](https://d3fend.mitre.org/technique/d3f:ConnectionAttemptAnalysis/)

## 📋 Overview

Network scanning is typically the **earliest indicator** of an attack — adversaries must discover targets before they can exploit them. In this challenge you will perform a port scan against the ICS network, then verify that the CybICS IDS detected your scan and find the flag hidden in the IDS rule statistics.

This teaches the full detection loop: **attacker action → network packets → IDS rule → observable alert → flag**.

### Detection Rule: `port_scan`

The IDS triggers the `port_scan` rule when it observes **5 or more unique destination ports** probed by a single source IP within a **10-second sliding window**.

## 🎯 Task

Perform a port scan, observe the IDS detection, and retrieve the flag from the IDS API.

---

### Phase 1: Launch the Scan

Run the provided reconnaissance script against the OpenPLC target:

```bash
python3 recon.py 172.18.0.3
```

This scans 6 industrial ports: **80** (HTTP), **102** (S7comm), **502** (Modbus), **4840** (OPC UA), **20000** (DNP3), **44818** (EtherNet/IP).

Alternatively, use nmap directly:

```bash
nmap -sV 172.18.0.3
```

Note the output — which ports are **open** and which are **closed**?

### Phase 2: Verify IDS Detection

Your scan triggered the IDS. Open the IDS dashboard at [http://localhost:8443](http://localhost:8443) and check the **Alerts** tab. You should see a `port_scan` alert with your source IP.

Query the IDS API to confirm:

```bash
curl -s http://localhost:8443/api/rules/stats | python3 -m json.tool
```

Look for the `port_scan` entry — if `count` is greater than 0, the rule has fired and the **flag is revealed** in the response.

You can also query just the port_scan rule:

```bash
curl -s http://localhost:8443/api/rules/stats | python3 -c "
import sys, json
data = json.load(sys.stdin)
ps = data.get('port_scan', {})
print(f'Count: {ps.get(\"count\", 0)}')
print(f'Flag:  {ps.get(\"flag\", \"Not yet — trigger the rule first\")}')
"
```

### Phase 3: Understand the Detection

Answer these questions to solidify your understanding:

1. **How many ports did you scan?** (Check the recon.py output)
2. **What is the IDS threshold for port_scan?** (5 ports in 10 seconds)
3. **Did your scan exceed the threshold?** (6 ports > 5 threshold → YES)
4. **What source IP appears in the alert?** (Your machine's IP on the 172.18.0.0/24 network)

This demonstrates the detection pipeline:
```
Your scan (6 ports) → IDS sees SYN packets → 6 > 5 threshold → port_scan rule fires → Alert + Flag
```

## 🛡️ Security Framework References

<details>
<summary>Click to expand</summary>

### MITRE ATT&CK for ICS — Detected Techniques

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | Scanning to identify ICS devices |
| Discovery | Network Connection Enumeration | [T0840](https://attack.mitre.org/techniques/T0840/) | Enumerating network connections and topology |

### MITRE D3FEND — Defensive Techniques

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Analyzing network traffic to detect malicious patterns |
| Connection Attempt Analysis | [D3-CAA](https://d3fend.mitre.org/technique/d3f:ConnectionAttemptAnalysis/) | Identifying scanning through connection patterns |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-4 | System monitoring — the core control for detection |
| **Audit and Accountability (AU)** | AU-3, AU-6 | Audit record content and review |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.7 emphasizes continuous monitoring (SI-4) in OT environments. Unlike IT systems where signature-based detection dominates, OT environments benefit from anomaly detection because "normal" traffic patterns are more predictable — a port scan stands out clearly.

</details>

<details>
<summary>💡 Hint</summary>

Run the scan, then query `http://localhost:8443/api/rules/stats`. Look at the `port_scan` entry — when `count > 0`, a `flag` field appears in the JSON response with the CTF flag.

</details>

## 🔍 Defensive Thinking

After completing this challenge, consider:
- What if the attacker scanned only 4 ports (below the threshold)? Would the IDS detect it?
- How would you detect slow scans (1 port every 30 seconds)?
- What other protocols besides TCP could be used for reconnaissance?
- How does the IDS distinguish a legitimate service check from a malicious scan?
