# 🔍 Detection Training - Basic

> **MITRE D3FEND:** `Detect` | [D3-NTA - Network Traffic Analysis](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | [D3-PMAD - Protocol Metadata Anomaly Detection](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/)

## 📋 Overview
In this training, we focus on how to detect network scanning activities using PCAP (Packet Capture) data.
PCAP files capture the raw network traffic data and are valuable for the security operation center (SOC) or forensic analysis of network communications.

## 🎯 Network Scanning Techniques
Attackers use different types of network scanning techniques to map out the network and gather intelligence.
Common techniques include:

### 1. 🎯 Ping Sweep
- Attackers send ICMP Echo Requests to multiple IP addresses
- Used to determine which hosts are online

### 2. 🔍 Port Scanning
Tools like Nmap are used to scan for open ports on target systems. Common scan types include:
- **SYN scan (Half-Open Scan)**: Sends SYN packets to check if a port is open
- **TCP Connect Scan**: Establishes a full TCP connection with the target port
- **UDP Scan**: Tests for open UDP ports, commonly used on industrial protocols like Modbus (port 502)
- **Service Detection**: Queries services running on open ports to determine their versions (e.g., OPC UA on port 4840)

### 3. 🛠️ Application Layer Scanning
- Attackers scan for specific application protocols
- Targets industrial control protocols like Modbus, DNP3, or OPC UA
- Helps identify system roles and functions

## ⚠️ Importance of Detection
Detecting and mitigating network scanning on industrial systems is a critical first step in preventing cyberattacks.
By capturing and analyzing network traffic through PCAP files, security teams can:
- Identify early signs of an attack
- Take appropriate action before an adversary gains deeper access
- Protect critical infrastructure

## 🎯 Training Questions
1. Which ports do the attacker scan?
2. Which ports are open, and which are closed?

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Detected Techniques

This training focuses on **detecting** the following adversary techniques:

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | Scanning to identify ICS devices |
| Discovery | Network Connection Enumeration | [T0840](https://attack.mitre.org/techniques/T0840/) | Enumerating network connections and topology |

**Why this matters:** Detection is the first step in incident response. Network scanning is typically the earliest indicator of an attack—adversaries must discover targets before they can exploit them. By learning to identify scanning patterns in PCAP data, you develop the foundational skills for security monitoring in ICS environments.

### MITRE D3FEND - Defensive Techniques (Primary Focus)

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Analyzing network traffic to detect malicious patterns |
| Protocol Metadata Anomaly Detection | [D3-PMAD](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | Detecting anomalies in protocol behavior |
| Connection Attempt Analysis | [D3-CAA](https://d3fend.mitre.org/technique/d3f:ConnectionAttemptAnalysis/) | Identifying scanning through connection patterns |
| Packet Analysis | [D3-PA](https://d3fend.mitre.org/technique/d3f:PacketAnalysis/) | Deep inspection of packets for malicious indicators |

**Detection indicators to look for:**
- High volume of SYN packets from single source
- Sequential port scanning patterns
- Connection attempts to multiple ICS ports (102, 502, 4840, 20000, 44818)
- Unusual source IPs contacting control system networks

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-4 | System monitoring—the core control for detection capabilities |
| **Audit and Accountability (AU)** | AU-3, AU-6, AU-12 | Audit record content, review, and generation |
| **Incident Response (IR)** | IR-4, IR-5, IR-6 | Incident handling, monitoring, and reporting |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.7 emphasizes the importance of continuous monitoring (SI-4) in OT environments. Unlike IT systems where signature-based detection dominates, OT environments benefit from anomaly detection because "normal" traffic patterns are more predictable. AU-6 (Audit Review, Analysis, and Reporting) recommends regular review of captured traffic—this training teaches you what to look for during that review. IR-4 (Incident Handling) capabilities depend on first having the detection skills practiced here.

</details>

## 🔍 Solution

<details>
  <summary><span style="color:orange;font-weight: 900">Click to expand</span></summary>

  After completion, use the following flag:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(basic_detection_complete)
  </div>

</details>
