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
To scan for Siemens S7 PLCs, use the following Nmap command:
```bash
nmap -p 102 --script s7-info $DEVICE_IP
```

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>

  ### 📊 Sample Output
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

  ### ✅ Conclusion
  Using Nmap's s7-info script, you can gather valuable details about Siemens PLCs on a network. This helps security analysts, pentesters, and industrial engineers identify and secure S7 devices.

  Happy Scanning! 🔍🚀
</details>
