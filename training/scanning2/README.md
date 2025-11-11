# 🔍 S7 Communication Scanning Guide

## 📋 Introduction
Siemens **S7 Communication (S7comm)** operates on **port 102** and is used for **communication between Siemens PLCs and industrial automation systems**. Nmap provides an **NSE script (`s7-info`)** to scan for and retrieve information from **S7 PLCs**.

## ⚙️ Prerequisites
Before scanning, ensure you have:

### 🛠️ Required Tools
1. **Nmap Installation**
   - On Debian-based systems (Ubuntu, Kali, etc.):
     ```bash
     sudo apt update && sudo apt install nmap -y
     ```
   - On RedHat-based systems (CentOS, Fedora, etc.):
     ```bash
     sudo yum install nmap -y
     ```
   - On Windows, download it from [Nmap's official site](https://nmap.org/download.html)

2. **Target Requirements**
   - Siemens PLC or S7-compatible device running on port 102
   - Ensure the target device has port 102 open

3. **Access Requirements**
   - Root or administrator access may be required

## ⚠️ Security Considerations
- 🔒 Only scan authorized devices! Unauthorized scanning may violate network security policies
- ⏰ Avoid scanning production systems during working hours to prevent disruptions
- 🔐 Use a VPN or secure network when scanning remote devices

## 🚀 Running the Scan
There are multiple ways to discover information about the S7 communication service. You can scan port 102 for S7 protocol information, or perform service version detection to find the flag.

### Method 1: S7-Info Script
To scan for Siemens S7 PLCs using the s7-info script:
```bash
nmap -p 102 --script s7-info $DEVICE_IP
```

### Method 2: Service Version Detection
To discover the CTF flag, scan with service version detection:
```bash
nmap -sV -p 1102 $DEVICE_IP
```

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>

  ### 📊 S7-Info Script Output (Port 102)
  ```
  Starting Nmap 7.94SVN ( https://nmap.org ) at 2025-02-07 22:25 CET
  Nmap scan report for localhost (127.0.0.1)
  Host is up (0.00011s latency).

  PORT    STATE SERVICE
  102/tcp open  iso-tsap
  | s7-info: 
  |   Module: 6ES7 315-2EH14-0AB0 
  |   Basic Hardware: 6ES7 315-2EH14-0AB0 
  |   Version: 3.2.6
  |   System Name: SNAP7-SERVER
  |   Module Type: CPU 315-2 PN/DP
  |   Serial Number: S C-C2UR28922012
  |_  Copyright: Original Siemens Equipment
  Service Info: Device: specialized

  Nmap done: 1 IP address (1 host up) scanned in 0.05 seconds
  ```

  ### 🔎 Output Analysis
  - **Module**: The type of Siemens PLC (e.g., CPU 315-2 PN/DP)
  - **Version**: Firmware version installed on the PLC
  - **Serial**: Unique hardware identifier
  - **Plant Identification**: Custom plant or site name configured in the PLC
  - **Copyright**: Manufacturer details (Siemens AG)

  ### 📊 Service Version Detection Output (Port 1102)
  When you run service version detection on port 1102, you'll discover the CTF flag:
  ```
  Starting Nmap 7.95 ( https://nmap.org ) at 2025-11-11 08:00 UTC
  Nmap scan report for localhost (127.0.0.1)
  Host is up (0.00010s latency).

  PORT     STATE SERVICE    VERSION
  1102/tcp open  http       CybICS(s7comm_analysis_complete)

  Nmap done: 1 IP address (1 host up) scanned in 0.15 seconds
  ```

  ### 🔎 Flag Discovery
  Notice that **port 1102** shows an unusual service version string: `CybICS(s7comm_analysis_complete)`

  This is the CTF flag! The S7comm service runs an additional HTTP server on port 1102 that includes the flag in its Server header. When nmap performs service version detection with the `-sV` flag, it reads this banner and displays the flag.

  ### ✅ Conclusion
  Using Nmap's s7-info script and service version detection, you can:
  - Gather technical details about Siemens S7 PLCs (port 102)
  - Discover hidden flags in service banners (port 1102)

  This helps security analysts, pentesters, and industrial engineers identify and secure S7 devices while also testing for security weaknesses in service configurations.

  Happy Scanning! 🔍🚀

  After completing the scan, submit the following flag:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(s7comm_analysis_complete)
  </div>
</details>
