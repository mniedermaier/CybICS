# 🎓 CybICS Training Modules

## 📋 Overview
This section provides an overview of the training modules available for the CybICS testbed.
These modules are designed to offer a foundational understanding and practical experience with the testbed's capabilities.
While they serve as an excellent starting point for your training journey, it is important to note that they are not exhaustive and may not cover every aspect of the system in detail.

## 🎯 Learning Path
You have the flexibility to complete the training modules in any sequence that best suits your needs and interests.
However, to maximize your learning and ensure a structured approach, we recommend following the suggested order.
This recommended sequence is designed to build your knowledge progressively, laying a solid groundwork before advancing to more complex topics.
The modules below and the CTF page in the landing page (`/ctf`) follow the same seven stages: plant basics, reconnaissance, access attacks, process attacks, detection, forensics and defense.
Inside a stage the challenges go from easy to hard; easy ones are worth 100 points, medium ones 200 and hard ones 300.
On the CTF page every attack names the defense challenge that stops it, and every challenge links to its Theory Path briefing.

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
| [Physical Process](physical_process/README.md) | Impact | Manipulation of Control | T0831 |
| [PLC Programming](plc_programming/README.md) | Persistence, Lateral Movement | Modify Program, Program Download | T0889, T0843 |
| [Plant Physics Sandbox](plant_physics_sandbox/README.md) | Evasion, Impair Process Control, Impact | Unauthorized Message: Reporting Message, Manipulation of Control, Loss of Safety | T1692.002, T0831, T0880 |
| [Service Scanning](scanning/README.md) | Discovery | Remote System Discovery, Network Connection Enumeration | T0846, T0840 |
| [S7comm Scanning](scanning2/README.md) | Discovery | Remote System Discovery, Remote System Information Discovery | T0846, T0888 |
| [HMI Project Recon](hmi_project_recon/README.md) | Collection | Data from Information Repositories, Point & Tag Identification, Monitor Process State | T0811, T0861, T0801 |
| [Wireshark Capture](wireshark_capture/README.md) | Discovery | Network Sniffing | T0842 |
| [Packet Anatomy](packet_anatomy/README.md) | Collection, Evasion, Impair Process Control | Monitor Process State, Unauthorized Message: Command Message | T0801, T1692.001 |
| [Register Map Recon](register_map_recon/README.md) | Collection | Point & Tag Identification, Monitor Process State, Automated Collection | T0861, T0801, T0802 |
| [Password Attack](password_attack/README.md) | Persistence, Lateral Movement | Insecure Credentials: Default Credentials, Valid Accounts | T1694.001, T0859 |
| [OPC-UA](opcua/README.md) | Persistence, Lateral Movement | Valid Accounts | T0859 |
| [Forged HMI Token](fuxa_jwt/README.md) | Persistence, Lateral Movement, Collection | Insecure Credentials: Default Credentials, Data from Information Repositories | T1694.001, T0811 |
| [The Forgotten API](openplc_restapi/README.md) | Discovery, Initial Access, Persistence, Lateral Movement | Remote System Discovery: Port Scan, Exploitation of Remote Services, Valid Accounts, Remote System Information Discovery | T0846.001, T0866, T0859, T0888 |
| [UART Training](uart_basic/README.md) | Persistence, Lateral Movement | Insecure Credentials: Hardcoded Credentials | T1694.002 |
| [Flood & Overwrite](flood_overwrite/README.md) | Evasion, Impair Process Control, Impact | Brute Force I/O, Unauthorized Message: Command Message, Manipulation of View | T0806, T1692.001, T0832 |
| [S7 Side Door](s7_sidedoor/README.md) | Evasion, Impair Process Control, Impact | Unauthorized Message: Command Message, Manipulation of Control, Loss of Availability | T1692.001, T0831, T0826 |
| [Stop Means Stop?](s7_cpu_stop/README.md) | Execution, Evasion, Impair Process Control, Collection | Change Operating Mode, Unauthorized Message: Command Message, Detect Operating Mode | T0858, T1692.001, T0868 |
| [Fuzzing Modbus](fuzzingMB/README.md) | Evasion, Impair Process Control, Inhibit Response Function | Unauthorized Message: Command Message, Denial of Service | T1692.001, T0814 |
| [MitM Attack](mitm/README.md) | Collection, Evasion | Adversary-in-the-Middle, Unauthorized Message: Reporting Message | T0830, T1692.002 |
| [DNP3 Side Door](dnp3_sidedoor/README.md) | Discovery, Evasion, Impair Process Control, Impact | Remote System Discovery, Unauthorized Message: Command Message, Manipulation of Control, Loss of Availability | T0846, T1692.001, T0831, T0826 |
| [Detect Basic](detect_basic/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Protocol Metadata Anomaly Detection | D3-NTA |
| [IDS Challenge](ids_challenge/README.md) | Discovery, Evasion, Impair Process Control, Inhibit Response Function | Remote System Discovery, Denial of Service, Unauthorized Message: Command Message | T0846, T0814, T1692.001 |
| [Detect Overwrite](detect_overwrite/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Operational Process Monitoring | D3-NTA, D3-OPM |
| [IDS Evasion](ids_evasion/README.md) | Evasion, Impair Process Control, Impact | Unauthorized Message: Command Message, Manipulation of Control | T1692.001, T0831 |
| [Trusted Writer](fuxa_trusted_writer/README.md) | Execution, Evasion, Impair Process Control, Impact | Execution through API, Unauthorized Message: Command Message, Manipulation of Control, Loss of Availability | T0871, T1692.001, T0831, T0826 |
| [IDS Forensics](ids_forensics/README.md) | *Defensive* | D3FEND: Network Traffic Analysis | D3-NTA |
| [Incident PCAP](incident_pcap/README.md) | *Defensive* (reconstructs Discovery, Collection, Evasion, Impair Process Control, Impact) | D3FEND: Network Traffic Analysis, Protocol Metadata Anomaly Detection, Application Protocol Command Analysis; ATT&CK for ICS: Remote System Discovery, Port Scan, Adversary-in-the-Middle, Unauthorized Message: Command Message, Manipulation of Control, Loss of Availability | D3-NTA, D3-PMAD, D3-APCA; T0846, T0846.001, T0830, T1692.001, T0831, T0826 |
| [Physics Never Lies](physics_forensics/README.md) | *Defensive* (reconstructs Collection, Evasion, Impair Process Control, Impact) | D3FEND: Operational Process Monitoring, Domain Logic Validation, Operational Logic Validation; ATT&CK for ICS: Adversary-in-the-Middle, Unauthorized Message: Reporting Message, Manipulation of View, Manipulation of Control | D3-OPM, D3-DLV, D3-OLV; T0830, T1692.002, T0832, T0831 |
| [Whispering PLC](modbus_covert_c2/README.md) | *Defensive* (reconstructs Command and Control) | D3FEND: Network Traffic Analysis, Protocol Metadata Anomaly Detection, Application Protocol Command Analysis; ATT&CK for ICS: Standard Application Layer Protocol, Commonly Used Port | D3-NTA, D3-PMAD, D3-APCA; T0869, T0885 |
| [Credential Hardening](defense_password/README.md) | *Defensive* | D3FEND: Strong Password Policy, Credential Rotation | D3-SPP |
| [Rotate the FUXA Token Key](defense_fuxa_jwt/README.md) | *Defensive* | D3FEND: Credential Rotation, Application Configuration Hardening | D3-CRO, D3-ACH |
| [Modbus Firewall](defense_firewall/README.md) | *Defensive* | D3FEND: Inbound Traffic Filtering, Network Traffic Filtering | D3-ITF, D3-NTF |
| [IDS Monitoring](defense_ids/README.md) | *Defensive* | D3FEND: Network Traffic Analysis, Protocol Metadata Anomaly Detection | D3-NTA, D3-PMAD |
| [Close the Side Doors](defense_unused_protocols/README.md) | *Defensive* | D3FEND: Application Configuration Hardening, Inbound Traffic Filtering | D3-ACH, D3-ITF |
| [Network Segmentation](defense_network/README.md) | *Defensive* | D3FEND: Network Isolation | D3-NI |

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

### Plant Basics
Start here: what the plant does, how the PLC controls it and what the physics does when control goes wrong.

1. [Understanding the physical process](physical_process/README.md) - Learn about industrial processes and control systems
2. [PLC programming](plc_programming/README.md) - Introduction to PLC programming and control logic
3. [Plant physics sandbox](plant_physics_sandbox/README.md) - Predict what the plant does with frozen outputs and one forged reading, before you touch it

### Reconnaissance & Traffic
Find out what is on the network, look inside its packets and map the plant's registers before you change anything.

4. [Service scanning](scanning/README.md) - Discover network services and open ports
5. [S7comm scanning](scanning2/README.md) - Analyze Siemens S7 communication
6. [HMI project recon](hmi_project_recon/README.md) - Download the HMI's project without a login and map every register and button of the plant
7. [Wireshark capture](wireshark_capture/README.md) - Learn network traffic analysis
8. [Packet anatomy](packet_anatomy/README.md) - Build Modbus/TCP frames byte by byte and take the PLC's answers and errors apart
9. [Register map recon](register_map_recon/README.md) - Rebuild the PLC's memory map from reads alone and find the latches no screen shows

### Access Attacks
Get in where you should not: default passwords, a forged session, a forgotten interface and a debug port.

10. [Password attack](password_attack/README.md) - Practice password security testing
11. [OPC-UA](opcua/README.md) - Explore OPC-UA protocol security
12. [Forged HMI token](fuxa_jwt/README.md) - Sign your own FUXA administrator session with the HMI's default key
13. [The forgotten API](openplc_restapi/README.md) - Claim OpenPLC's unused REST API on port 8443 before its owner does
14. [UART Training Guide (Hardware Required)](uart_basic/README.md) - Hardware-level communication

### Process Attacks
Change what the plant does: overwrite values, stop the PLC through its side doors and sit between the HMI and the PLC.

15. [Flood & overwrite](flood_overwrite/README.md) - Test system resilience against flooding attacks
16. [S7 side door](s7_sidedoor/README.md) - Stop the plant through the PLC's S7comm server when Modbus is closed
17. [Stop means stop?](s7_cpu_stop/README.md) - Send the PLC an S7comm CPU STOP and prove from the plant what it really did
18. [Fuzzing Modbus](fuzzingMB/README.md) - Test Modbus protocol robustness
19. [Man-in-the-Middle (MitM)](mitm/README.md) - Learn about network interception
20. [DNP3 side door](dnp3_sidedoor/README.md) - Find OpenPLC's forgotten DNP3 outstation and stop the plant with a frame you build by hand

### Detection & Evasion
Watch your own attacks show up in the IDS, then find out what it cannot see.

21. [Detect Basic](detect_basic/README.md) - Basic intrusion detection
22. [IDS Challenge](ids_challenge/README.md) - Trigger IDS detection rules and retrieve the flag
23. [Detect Overwrite](detect_overwrite/README.md) - Advanced detection techniques
24. [IDS Evasion](ids_evasion/README.md) - Perform stealth Modbus writes without triggering alerts
25. [Trusted writer](fuxa_trusted_writer/README.md) - Make the HMI stop the plant for you, from the one address the IDS never counts

### Forensics
After the fact: rebuild what happened from IDS alerts, a packet capture and the plant's own history.

26. [IDS Forensics](ids_forensics/README.md) - Analyze IDS alert data for incident investigation
27. [Incident PCAP](incident_pcap/README.md) - Rebuild a night of plant stops from a capture and unmask the device behind the borrowed addresses
28. [Physics Never Lies](physics_forensics/README.md) - Catch a forged pressure reading in a historian export with nothing but the plant's physics
29. [Whispering PLC](modbus_covert_c2/README.md) - Find the implant that hides a message in harmless Modbus reads and design the allowlist that catches it

### Defense & Hardening
Close the doors the attacks used: change passwords, rotate a key, filter traffic and segment the network.

30. [Credential Hardening](defense_password/README.md) - Change default passwords on OpenPLC and FUXA
31. [Rotate the FUXA token key](defense_fuxa_jwt/README.md) - Give the HMI a signing key of its own so forged sessions are refused
32. [Modbus Firewall Rules](defense_firewall/README.md) - Restrict Modbus access with iptables
33. [IDS Monitoring & Tuning](defense_ids/README.md) - Ensure IDS is running and detecting threats
34. [Close the Side Doors](defense_unused_protocols/README.md) - Switch off the PLC protocols the plant does not use and firewall the one without a switch
35. [Network Segmentation](defense_network/README.md) - Block attack machine from critical services

---

## 📖 Further Reading

### Security Frameworks
- [MITRE ATT&CK for ICS Matrix](https://attack.mitre.org/matrices/ics/) - Complete ICS attack techniques reference
- [MITRE ATT&CK for ICS Techniques](https://attack.mitre.org/techniques/ics/) - Detailed technique descriptions
- [MITRE D3FEND](https://d3fend.mitre.org/) - Defensive countermeasures framework
- [NIST SP 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) - Guide to OT Security (PDF)