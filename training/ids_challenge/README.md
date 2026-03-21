# 🔍 Intrusion Detection System Challenge

> **MITRE ATT&CK for ICS:** `Discovery` | [T0846 - Remote System Discovery](https://attack.mitre.org/techniques/T0846/) | [T0855 - Unauthorized Command Message](https://attack.mitre.org/techniques/T0855/)

## 📋 Overview

Industrial Control Systems (ICS) are often deployed without proper network monitoring. An IDS watches network traffic for signs of reconnaissance, unauthorized access, and attacks against industrial protocols like Modbus TCP, S7comm, and OPC-UA.

The CybICS IDS is a lightweight, purpose-built IDS designed for ICS environments. It monitors the CybICS network (172.18.0.0/24) and applies detection rules based on MITRE ATT&CK for ICS.

## 🎯 Task

Learn how intrusion detection systems work in ICS environments by interacting with the CybICS IDS and triggering real detection rules.

1. **Access the IDS Dashboard** at [http://localhost:8443](http://localhost:8443)
2. Ensure the IDS is running (it auto-starts by default)
3. **Trigger at least 3 different detection rules** using the attack machine or webshell
4. **Observe the alerts** on the IDS dashboard
5. Once you have triggered at least 3 alerts, retrieve the flag:
   ```bash
   curl http://localhost:8443/api/flag
   ```

### 📝 Suggested Attacks to Trigger

From the attack machine (http://localhost:6081/vnc.html) or webshell:

#### Port Scan (Rule: port_scan)
```bash
nmap -sS 172.18.0.3
```

#### Modbus Write Flood (Rule: modbus_flood)
```bash
# Use the flooding script from the training materials
python3 /usr/local/bin/flooding_hpt.py
```

#### S7comm Enumeration (Rule: s7_enumeration)
```bash
nmap --script s7-info -p 102 172.18.0.3
```

#### Modbus Unauthorized Write (Rule: modbus_unauth_write)
```python
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('172.18.0.3', port=502)
client.connect()
for i in range(15):
    client.write_register(1124, 999)
client.close()
```

## 📖 Detection Rules

The CybICS IDS implements 9 detection rules:

1. **Port Scan** — Detects SYN packets to multiple ports on a single target
2. **SYN Flood** — Detects excessive SYN packets from a single source
3. **Modbus Write Flood** — Detects high-rate Modbus write operations
4. **Modbus Unauthorized Write** — Detects Modbus writes from non-service hosts
5. **Modbus Diagnostic** — Detects use of diagnostic function codes
6. **S7comm Enumeration** — Detects S7 protocol access attempts
7. **HTTP Brute Force** — Detects repeated login attempts on OpenPLC/FUXA
8. **ARP Spoofing** — Detects multiple MAC addresses for a single IP
9. **OPC-UA Unauthorized Access** — Detects OPC-UA connections from unknown hosts

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS — Techniques Detected

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | Port scan, S7 enumeration, OPC-UA access |
| Impact | Denial of Service | [T0836](https://attack.mitre.org/techniques/T0836/) | SYN flood, Modbus write flood |
| Impair Process Control | Unauthorized Command Message | [T0855](https://attack.mitre.org/techniques/T0855/) | Modbus writes from unexpected sources |
| Collection | Spoof Reporting Message | [T0856](https://attack.mitre.org/techniques/T0856/) | ARP spoofing |
| Initial Access | Default Credentials | [T0812](https://attack.mitre.org/techniques/T0812/) | HTTP brute force against OpenPLC/FUXA |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-4 | Information system monitoring — detecting attacks in real time |
| **Incident Response (IR)** | IR-4, IR-5 | Incident handling and monitoring |
| **Audit and Accountability (AU)** | AU-6 | Audit review, analysis, and reporting |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.7 emphasizes continuous monitoring (SI-4) as essential for OT security. An IDS that is not actively monitoring traffic cannot detect attacks. Understanding which attacks are detectable — and which are not — is a fundamental skill for both attackers and defenders in ICS environments.

</details>

## 🔍 Defensive Thinking

After completing the offensive tasks, consider:
- Which attacks were detected? Which were missed?
- How could you modify your attacks to evade detection?
- What additional rules would you add to improve detection?
- How would you implement alerting (email, SMS, SIEM integration)?
- What is the trade-off between detection sensitivity and false positives?
