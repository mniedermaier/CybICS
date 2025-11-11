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

Use the s7-info NSE script to identify the S7 PLC and discover the CTF flag:
```bash
nmap -p 102 --script s7-info $DEVICE_IP
```
This will show PLC details including module type, version, serial number, and system name. **The CTF flag is embedded in one of these fields!**

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>

  ### S7-Info Scan Results
  Execute the nmap command with the s7-info script:
  ```bash
  nmap -p 102 --script s7-info $DEVICE_IP
  ```

  The output shows PLC identification details:
  ```
  Starting Nmap 7.94SVN ( https://nmap.org ) at 2025-11-11 09:26 CET
  Nmap scan report for localhost (127.0.0.1)
  Host is up (0.00012s latency).

  PORT    STATE SERVICE
  102/tcp open  iso-tsap
  | s7-info:
  |   Module: 6ES7 315-2AG10-0AB0
  |   Basic Hardware: SIMATIC 300
  |   Version: 2.6.9
  |   System Name: SIMATIC 300(1)
  |   Module Type: CybICS(s7comm_analysis_complete)
  |_  Plant Identification:
  Service Info: Device: specialized

  Nmap done: 1 IP address (1 host up) scanned in 0.04 seconds
  ```

  ### 🔎 Key Discovery
  Notice the **Module Type** field shows: `CybICS(s7comm_analysis_complete)` - **This is the flag!**

  The s7-info NSE script queries the S7 PLC using the **SZL (System Status List)** protocol to retrieve module identification information. The custom S7 server has been configured to embed the CTF flag in the Module Type field.

  ### 📊 Output Analysis
  - **Module**: Hardware module identifier (6ES7 315-2AG10-0AB0)
  - **Basic Hardware**: Basic hardware type (SIMATIC 300)
  - **Version**: Firmware version (2.6.9)
  - **System Name**: System identifier (SIMATIC 300(1))
  - **Module Type**: Extended module type - **Contains the CTF flag!** 🚩

  ### ✅ Conclusion
  Using Nmap's s7-info script, you can:
  - Identify Siemens S7 PLCs on the network  - Retrieve detailed system information including module type, version, and serial number
  - Discover sensitive information embedded in PLC identification fields

  This demonstrates how industrial protocols expose system information that can be valuable for reconnaissance. In real-world scenarios, attackers use this information to:
  - Identify specific PLC models and firmware versions
  - Search for known vulnerabilities affecting those versions
  - Plan targeted attacks against industrial control systems

  **Security Best Practice**: Always restrict access to port 102 and monitor S7 communication for unauthorized scanning attempts.

  Submit the flag found in the Module Type field:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(s7comm_analysis_complete)
  </div>
</details>
