# 🎓 CybICS Training Modules

## 📋 Overview
This section provides an overview of the training modules available for the CybICS testbed.
These modules are designed to offer a foundational understanding and practical experience with the testbed's capabilities.
While they serve as an excellent starting point for your training journey, it is important to note that they are not exhaustive and may not cover every aspect of the system in detail.

## 🎯 Learning Path
You have the flexibility to complete the training modules in any sequence that best suits your needs and interests.
However, to maximize your learning and ensure a structured approach, we recommend following the suggested order.
This recommended sequence is designed to build your knowledge progressively, laying a solid groundwork before advancing to more complex topics.

New to industrial control systems? Start with the **Theory Path** in the landing page (`/theory`, or the 📚 button in the dashboard).
It is a numbered course of short, illustrated lessons for students with little IT or OT background: what a PLC is, how Modbus, S7comm and OPC-UA work, how attacks unfold and how defenders respond, plus four real-world case studies.
Every lesson has interactive examples (some read the live plant) and a short quiz, and every challenge has a briefing there that explains the idea behind it without giving the solution away.
The lessons live in [`theory/`](theory/); [`theory/AUTHORING.md`](theory/AUTHORING.md) explains how to write one.

## 🛡️ Security Framework Alignment

All training modules are mapped to industry-standard security frameworks to help you understand the real-world relevance of each exercise:

- **[MITRE ATT&CK for ICS](https://attack.mitre.org/matrices/ics/)** - Adversary tactics and techniques for Industrial Control Systems
- **[MITRE D3FEND](https://d3fend.mitre.org/)** - Defensive countermeasures (for detection modules)
- **[NIST SP 800-82r3](https://csrc.nist.gov/pubs/sp/800/82/r3/final)** - Guide to Operational Technology (OT) Security

### 📊 MITRE ATT&CK for ICS Coverage Matrix

The technique IDs follow the current ATT&CK for ICS catalogue. Several older IDs have been folded into new techniques and now redirect: T0855 is T1692.001, T0856 is T1692.002 and T0812 is T1694.001.

| Module | Tactic | Techniques | IDs |
|--------|--------|------------|-----|
| [Physical Process](physical_process/README.md) | Impair Process Control | Manipulation of Control | T0831 |
| [PLC Programming](plc_programming/README.md) | Execution, Persistence | Modify Program, Program Download | T0889, T0843 |
| [Service Scanning](scanning/README.md) | Discovery | Remote System Discovery, Network Connection Enumeration | T0846, T0840 |
| [S7comm Scanning](scanning2/README.md) | Discovery | Remote System Discovery, Remote System Information Discovery | T0846, T0888 |
| [Wireshark Capture](wireshark_capture/README.md) | Collection | Network Sniffing | T0842 |
| [Flood & Overwrite](flood_overwrite/README.md) | Impair Process Control, Evasion | Brute Force I/O, Unauthorized Message: Command Message, Manipulation of View | T0806, T1692.001, T0832 |
| [Password Attack](password_attack/README.md) | Persistence, Lateral Movement | Insecure Credentials: Default Credentials, Valid Accounts | T1694.001, T0859 |
| [OPC-UA](opcua/README.md) | Initial Access, Lateral Movement | Valid Accounts | T0859 |
| [Fuzzing Modbus](fuzzingMB/README.md) | Impair Process Control, Impact | Unauthorized Message: Command Message, Denial of Service | T1692.001, T0814 |
| [S7 Side Door](s7_sidedoor/README.md) | Impair Process Control, Impact | Unauthorized Message: Command Message, Manipulation of Control, Loss of Availability | T1692.001, T0831, T0826 |
| [MitM Attack](mitm/README.md) | Collection, Evasion | Adversary-in-the-Middle, Unauthorized Message: Reporting Message | T0830, T1692.002 |
| [UART Training](uart_basic/README.md) | Initial Access | Insecure Credentials: Hardcoded Credentials | T1694.002 |
| [Detect Basic](detect_basic/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Protocol Metadata Anomaly Detection | D3-NTA |
| [Detect Overwrite](detect_overwrite/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Operational Process Monitoring | D3-NTA, D3-OPM |
| [Credential Hardening](defense_password/README.md) | *Defensive* | D3FEND: Strong Password Policy, Credential Rotation | D3-SPP |
| [Modbus Firewall](defense_firewall/README.md) | *Defensive* | D3FEND: Inbound Traffic Filtering, Network Traffic Filtering | D3-ITF, D3-NTF |
| [Network Segmentation](defense_network/README.md) | *Defensive* | D3FEND: Network Isolation | D3-NI |
| [IDS Monitoring](defense_ids/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Protocol Metadata Anomaly Detection | D3-NTA, D3-PMAD |
| [IDS Challenge](ids_challenge/README.md) | Discovery, Impair Process Control | Remote System Discovery, Denial of Service, Unauthorized Message: Command Message | T0846, T0814, T1692.001 |
| [IDS Evasion](ids_evasion/README.md) | Impair Process Control, Evasion | Unauthorized Message: Command Message, Exploitation of Remote Services, Manipulation of Control | T1692.001, T0866, T0831 |
| [IDS Forensics](ids_forensics/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Alert Triage | D3-NTA, D3-AT |

## 📦 Prerequisites

Install the Python dependencies for all training modules:

```bash
pip install -r training/requirements.txt
```

Alternatively, each training module has its own `requirements.txt` if you only want dependencies for a specific exercise.

### Where to work from

There are two places to run the attacks from. Both sit at **172.18.0.100**
inside the plant network, so the IDS and the defense challenges see the same
attacker either way.

- **The attack shell** (the **WebShell** view of the landing page): a terminal
  in a small container, on the virtual stack and on a Raspberry Pi board. It
  has nmap with the ICS scripts, ffuf, hydra, socat, tcpdump, picocom, git, and
  Python with pymodbus, asyncua, python-snap7 and scapy. The modules are in
  `/CybICS/training`, the dependencies are already installed, and
  `$DEVICE_IP` is preset to `172.18.0.1`, the host that publishes every
  service's port. There is no Metasploit, Wireshark or desktop, and no
  internet access on a board; the modules note where the attack shell takes a
  different route.
- **The Kali attack machine** (virtual stack, `--mode full`): a full desktop
  with Wireshark, Metasploit and a browser.

The defense challenges change the target containers with `docker exec`. That
needs the Docker host, so run those commands from the landing page's admin
shell (WebShell view, *Admin shell*), not from the attack shell.

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
10. [S7 side door](s7_sidedoor/README.md) - Stop the plant through the PLC's S7comm server when Modbus is closed

### 🔐 Advanced Security
11. [Man-in-the-Middle (MitM)](mitm/README.md) - Learn about network interception
12. [UART Training Guide (Hardware Required)](uart_basic/README.md) - Hardware-level communication
13. [Detect Basic](detect_basic/README.md) - Basic intrusion detection
14. [Detect Overwrite](detect_overwrite/README.md) - Advanced detection techniques

### 🔍 IDS Challenges
15. [IDS Challenge](ids_challenge/README.md) - Trigger IDS detection rules and retrieve the flag
16. [IDS Forensics](ids_forensics/README.md) - Analyze IDS alert data for incident investigation
17. [IDS Evasion](ids_evasion/README.md) - Perform stealth Modbus writes without triggering alerts

### 🛡️ Defense & Hardening
18. [Credential Hardening](defense_password/README.md) - Change default passwords on OpenPLC and FUXA
19. [Modbus Firewall Rules](defense_firewall/README.md) - Restrict Modbus access with iptables
20. [Network Segmentation](defense_network/README.md) - Block attack machine from critical services
21. [IDS Monitoring & Tuning](defense_ids/README.md) - Ensure IDS is running and detecting threats

---

## 📖 Further Reading

### Security Frameworks
- [MITRE ATT&CK for ICS Matrix](https://attack.mitre.org/matrices/ics/) - Complete ICS attack techniques reference
- [MITRE ATT&CK for ICS Techniques](https://attack.mitre.org/techniques/ics/) - Detailed technique descriptions
- [MITRE D3FEND](https://d3fend.mitre.org/) - Defensive countermeasures framework
- [NIST SP 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) - Guide to OT Security (PDF)