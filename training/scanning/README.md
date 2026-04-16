# 🔍 Service Scanning Guide

> **MITRE ATT&CK for ICS:** `Discovery` | [T0846 - Remote System Discovery](https://attack.mitre.org/techniques/T0846/) | [T0840 - Network Connection Enumeration](https://attack.mitre.org/techniques/T0840/)

## 📋 Overview
Network scanning in industrial environments involves systematically probing the network to identify connected devices, open ports, and potential vulnerabilities.
This process is crucial for maintaining the security and integrity of industrial control systems (ICS) and Supervisory Control and Data Acquisition (SCADA) networks.
By performing regular network scans, organizations can detect unauthorized devices, assess the security posture of their systems, and identify weak points that could be exploited by attackers.

Effective network scanning helps ensure that only approved devices are connected and that all systems are up-to-date with the latest security patches.
It also aids in discovering misconfigurations and vulnerabilities that could be exploited in a cyber attack.
To maximize security, network scans should be conducted periodically and after any significant changes to the network infrastructure, and results should be analyzed to inform ongoing security measures and improvements.

## ⚠️ Security Considerations
- 🔒 Only scan authorized devices! Unauthorized scanning may violate network security policies
- ⏰ Avoid scanning production systems during working hours to prevent disruptions
- 🔐 Use a VPN or secure network when scanning remote devices

## 🛠️ Using Nmap
To identify open ports and services within the CybICS testbed you can use nmap. Nmap (Network Mapper) is an open-source tool for network discovery and security auditing.

### Service Version Detection with `-sV`
One of nmap's most powerful features is **service version detection**, enabled with the `-sV` flag. When you run `nmap -sV <target>`, nmap doesn't just check which ports are open — it actively probes each open port and analyzes the responses to determine:
- What **service** is running (HTTP, Modbus, SSH, etc.)
- The **version** of that service
- The **service banner** — a text string the service returns to identify itself

The basic syntax is:
```bash
nmap -sV $DEVICE_IP
```

### Flags Hidden in Service Banners
In ICS environments, services expose identification information through **banners** and **headers**. For example, an HTTP server includes a `Server` header in its responses that identifies the web server software. These banners can reveal detailed system information — and in a CTF context, flags can be embedded in these service banners and HTTP headers.

When performing service version detection, pay close attention to any unusual or non-standard version strings in the scan results, as these may contain valuable information.

## 🎯 Task
Your goal is to perform service version detection against the CybICS testbed using nmap's `-sV` flag and discover the flag hidden in a service banner.

### Steps
1. Run nmap with the `-sV` flag against the target device to perform service version detection:
   ```bash
   nmap -sV $DEVICE_IP
   ```
2. Examine the scan output and look at the service banners and version strings reported for each open port.
3. Look for the flag embedded in an HTTP service banner or header. Pay close attention to any unusual or non-standard version strings.

The flag has the format `CybICS(flag)`.

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | Adversaries may attempt to get a listing of other systems by IP address, hostname, or other logical identifier |
| Discovery | Network Connection Enumeration | [T0840](https://attack.mitre.org/techniques/T0840/) | Adversaries may enumerate connections to identify targets and understand network topology |

**Why this matters:** Network scanning is typically the first step in any attack chain. Adversaries use tools like Nmap to identify ICS devices, determine running services, and find potential vulnerabilities. Understanding how attackers perform reconnaissance helps you implement effective detection mechanisms and network segmentation strategies.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Analyzing network traffic to detect scanning and enumeration activities |
| Protocol Metadata Anomaly Detection | [D3-PMAD](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | Detecting anomalies in protocol metadata that indicate reconnaissance |
| Connection Attempt Analysis | [D3-CAA](https://d3fend.mitre.org/technique/d3f:ConnectionAttemptAnalysis/) | Analyzing connection attempts to identify scanning behavior |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Communications Protection (SC)** | SC-7 | Boundary protection and network segmentation to limit scan effectiveness |
| **System and Information Integrity (SI)** | SI-4 | System monitoring to detect unauthorized scanning activities |
| **Risk Assessment (RA)** | RA-5 | Vulnerability scanning (authorized) to identify exposures before attackers |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 5.1.2 emphasizes defense-in-depth through network segmentation and monitoring. By understanding how scanning works, you can better implement SC-7 (Boundary Protection) controls like firewalls and intrusion detection systems. The information revealed by service banners (as seen in this exercise) demonstrates why SI-4 (System Monitoring) is critical for detecting early-stage attacks.

</details>


## 💡 Hints

Pay attention to the HTTP server banner on port 80.

## 🔍 Solution

Execute the following nmap command to perform service version detection:
  ```sh
  nmap -sV $DEVICE_IP
  ```

  ### 📝 Command Breakdown
  The `nmap -sV` command is used with Nmap to perform service version detection on common ports:

  - `nmap`: The command-line tool for network discovery and security auditing
  - `-sV`: Performs service version detection, probing open ports to determine service and version information

  This scan probes open ports and attempts to determine what service is running and its version by analyzing service banners and responses.

  ### 📊 Scan Results
  When you scan the system, you'll see something like:
  ```sh
  PORT      STATE SERVICE       VERSION
  80/tcp    open  http          CybICS(scanning_d0ne)
  102/tcp   open  iso-tsap
  502/tcp   open  modbus        Modbus TCP
  1881/tcp  open  http          Node.js Express framework
  4840/tcp  open  opcua-tcp?
  8080/tcp  open  http-proxy    Werkzeug/2.3.7 Python/3.11.2
  20000/tcp open  dnp?
  44818/tcp open  EtherNetIP-2?
  ```

  ### 🔎 Key Discovery
  Notice **80/tcp** shows an unusual service version string: `CybICS(scanning_d0ne)`

  This is the flag! The `-sV` flag triggers nmap to perform service version detection by connecting to the HTTP service and reading the Server header, which has been configured to contain the CTF flag.

  ### 🔎 Port Analysis
  - **80/tcp**: HTTP service - Landing page with flag in Server header
  - **102/tcp**: S7 Communication (S7comm) - Siemens PLC communication protocol
  - **502/tcp**: Modbus TCP - Industrial device communication
  - **1881/tcp**: HTTP (Node.js Express) - Web application interface
  - **4840/tcp**: OPC UA TCP - Industrial automation protocol
  - **8080/tcp**: HTTP Proxy (Werkzeug/Python) - OpenPLC web interface
  - **20000/tcp**: DNP3 - Industrial control protocol
  - **44818/tcp**: EtherNet/IP - Industrial networking protocol


  Submit the flag found in the service banner:

**Flag:** `CybICS(scanning_d0ne)`