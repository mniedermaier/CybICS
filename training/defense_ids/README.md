# 🔍 IDS Monitoring & Tuning

> **MITRE D3FEND:** `Detect` | [D3-NTA - Network Traffic Analysis](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | [D3-PMAD - Protocol Metadata Anomaly Detection](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/)

## 📋 Overview
An Intrusion Detection System (IDS) is only effective when it is properly configured, actively monitoring, and tuned to detect relevant threats. A misconfigured or disabled IDS provides a false sense of security.

This challenge requires you to ensure the CybICS IDS is fully operational and capable of detecting multiple types of attacks against the industrial network.

## 🎯 Task

Ensure the IDS meets all three criteria:
1. **Running** — The IDS service is operational
2. **Capturing** — The IDS is actively monitoring network traffic
3. **Detecting** — At least 3 different detection rules have been triggered

### 📝 Steps

#### Step 1: Access the IDS Dashboard
Open a web browser and navigate to `http://<DEVICE_IP>:8443`

#### Step 2: Start the IDS
If the IDS is not running, start it from the dashboard or via the API:
```bash
curl -X POST http://localhost:8443/api/start
```

#### Step 3: Trigger Detection Rules
The IDS has 9 detection rules. You need to trigger at least 3 different ones. Some examples:

**Port Scan** (Rule: `port_scan`):
```bash
nmap -sS 172.18.0.3
```

**S7comm Enumeration** (Rule: `s7_enumeration`):
```bash
nmap --script s7-info -p 102 172.18.0.3
```

**Modbus Unauthorized Write** (Rule: `modbus_unauth_write`):
```python
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('172.18.0.3', port=502)
client.connect()
for i in range(15):
    client.write_register(1124, 999)
client.close()
```

#### Step 4: Verify Detection
Check the IDS dashboard to confirm alerts have been generated from at least 3 different rules. Then click **Verify Defense** on this challenge page.

<details>
<summary>💡 Hint</summary>

Start the IDS capture via `curl -X POST http://localhost:8443/api/start`, then trigger attacks from the webshell or attack machine. A quick port scan (`nmap -sS 172.18.0.3`), some Modbus writes, and an S7 access attempt will each trigger a different rule. Check the IDS dashboard to confirm 3+ rules have fired.

</details>

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques Detected

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | Port scanning and service enumeration |
| Impair Process Control | Unauthorized Command Message | [T0855](https://attack.mitre.org/techniques/T0855/) | Unauthorized Modbus write commands |
| Impact | Denial of Service | [T0814](https://attack.mitre.org/techniques/T0814/) | Flooding attacks against ICS protocols |

### MITRE D3FEND - Defensive Techniques Applied

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Analyzing network traffic for attack patterns |
| Protocol Metadata Anomaly Detection | [D3-PMAD](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | Detecting anomalies in industrial protocol traffic |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-4 | System monitoring — continuous IDS operation |
| **Incident Response (IR)** | IR-4, IR-5 | Incident handling and monitoring |
| **Audit and Accountability (AU)** | AU-6 | Audit review and analysis |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.7 emphasizes continuous monitoring (SI-4) as essential for OT security. An IDS that is not actively monitoring traffic cannot detect attacks. Furthermore, AU-6 (Audit Review) requires that security alerts are reviewed and analyzed — simply having an IDS is not enough if no one monitors its output.

</details>

## 🔍 Defensive Thinking

After completing this challenge, consider:
- What is the difference between signature-based and anomaly-based detection in ICS?
- How do you balance detection sensitivity with false positive rates?
- What additional detection rules would you add for this environment?
- How would you integrate IDS alerts with a SIEM for centralized monitoring?
