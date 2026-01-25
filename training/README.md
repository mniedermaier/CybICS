# 🎓 CybICS Training Modules

## 📋 Overview
This section provides an overview of the training modules available for the CybICS testbed.
These modules are designed to offer a foundational understanding and practical experience with the testbed's capabilities.
While they serve as an excellent starting point for your training journey, it is important to note that they are not exhaustive and may not cover every aspect of the system in detail.

## 🎯 Learning Path
You have the flexibility to complete the training modules in any sequence that best suits your needs and interests.
However, to maximize your learning and ensure a structured approach, we recommend following the suggested order.
This recommended sequence is designed to build your knowledge progressively, laying a solid groundwork before advancing to more complex topics.

## 🛡️ Security Framework Alignment

All training modules are mapped to industry-standard security frameworks to help you understand the real-world relevance of each exercise:

- **[MITRE ATT&CK for ICS](https://attack.mitre.org/matrices/ics/)** - Adversary tactics and techniques for Industrial Control Systems
- **[MITRE D3FEND](https://d3fend.mitre.org/)** - Defensive countermeasures (for detection modules)
- **[NIST SP 800-82r3](https://csrc.nist.gov/pubs/sp/800/82/r3/final)** - Guide to Operational Technology (OT) Security

### 📊 MITRE ATT&CK for ICS Coverage Matrix

| Module | Tactic | Techniques | IDs |
|--------|--------|------------|-----|
| [Physical Process](physical_process/README.md) | Impair Process Control | Manipulation of Control | T0831 |
| [PLC Programming](plc_programming/README.md) | Execution, Persistence | Modify Program, Program Download | T0889, T0843 |
| [Service Scanning](scanning/README.md) | Discovery | Remote System Discovery, Network Connection Enumeration | T0846, T0840 |
| [S7comm Scanning](scanning2/README.md) | Discovery | Remote System Discovery, Point & Tag Identification | T0846, T0861 |
| [Wireshark Capture](wireshark_capture/README.md) | Collection | Network Sniffing | T0842 |
| [Flood & Overwrite](flood_overwrite/README.md) | Impair Process Control | Modify Parameter, Unauthorized Command Message, Brute Force I/O | T0836, T0855, T0806 |
| [Password Attack](password_attack/README.md) | Initial Access, Persistence | Default Credentials, Valid Accounts | T0812, T0859 |
| [OPC-UA](opcua/README.md) | Initial Access, Lateral Movement | Valid Accounts, Exploitation of Remote Services | T0859, T0866 |
| [Fuzzing Modbus](fuzzingMB/README.md) | Impair Process Control, Impact | Unauthorized Command Message, Denial of Service | T0855, T0814 |
| [MitM Attack](mitm/README.md) | Collection, Evasion | Adversary-in-the-Middle, Spoof Reporting Message | T0830, T0856 |
| [UART Training](uart_basic/README.md) | Initial Access | Default Credentials, External Remote Services | T0812, T0822 |
| [Detect Basic](detect_basic/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Protocol Metadata Anomaly Detection | D3-NTA |
| [Detect Overwrite](detect_overwrite/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Operational Process Monitoring | D3-NTA, D3-OPM |

## 📚 Training Modules

### 🏭 Basic Understanding
1. [Understanding the physical process](physical_process/README.md) - Learn about industrial processes and control systems
2. [PLC programming](plc_programming/README.md) - Introduction to PLC programming and control logic

### 🔍 Network Analysis
3. [Service scanning](scanning/README.md) - Discover network services and open ports
4. [S7comm scanning](scanning2/README.md) - Analyze Siemens S7 communication
5. [Wireshark capture](wireshark_capture/README.md) - Learn network traffic analysis

### 🛡️ Security Testing
6. [Flood & overwrite](flood_overwrite/README.md) - Test system resilience against flooding attacks
7. [Password attack](password_attack/README.md) - Practice password security testing
8. [OPC-UA](opcua/README.md) - Explore OPC-UA protocol security
9. [Fuzzing Modbus](fuzzingMB/README.md) - Test Modbus protocol robustness

### 🔐 Advanced Security
10. [Man-in-the-Middle (MitM)](mitm/README.md) - Learn about network interception
11. [UART Training Guide (Hardware Required)](uart_basic/README.md) - Hardware-level communication
12. [Detect Basic](detect_basic/README.md) - Basic intrusion detection
13. [Detect Overwrite](detect_overwrite/README.md) - Advanced detection techniques

---

## 📖 Further Reading

### Security Frameworks
- [MITRE ATT&CK for ICS Matrix](https://attack.mitre.org/matrices/ics/) - Complete ICS attack techniques reference
- [MITRE ATT&CK for ICS Techniques](https://attack.mitre.org/techniques/ics/) - Detailed technique descriptions
- [MITRE D3FEND](https://d3fend.mitre.org/) - Defensive countermeasures framework
- [NIST SP 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) - Guide to OT Security (PDF)