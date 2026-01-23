# 🔍 S7 Communication Scanning Guide

## 📋 Overview
Siemens **S7 Communication (S7comm)** typically operates on **port 102**, but can also run on custom ports. In this environment, the S7 service runs on **port 1102**. Nmap provides an **NSE script (`s7-info`)** to scan for and retrieve information from **S7 PLCs**.

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
   - Siemens PLC or S7-compatible device running on port 1102
   - Ensure the target device has port 1102 open

3. **Access Requirements**
   - Root or administrator access may be required

## ⚠️ Security Considerations
- 🔒 Only scan authorized devices! Unauthorized scanning may violate network security policies
- ⏰ Avoid scanning production systems during working hours to prevent disruptions
- 🔐 Use a VPN or secure network when scanning remote devices

## 🚀 Running the Scan

There are two S7 services running on port 102 and 1102 (the standard port 102 is used by OpenPLC). Due to nmap's s7-info script being hardcoded for port 102, you'll need to do changes to the s7-info script or use an alternative approach to query the S7 service and discover the CTF flag.

```bash
locate s7-info.nse
```
Usually at: /usr/share/nmap/scripts/s7-info.nse

Edit the script (you'll need sudo):

```bash
sudo nano /usr/share/nmap/scripts/s7-info.nse
```

Find the portrule section (near the top) and modify it:
```bash
portrule = shortport.port_or_service({102, 1102}, "iso-tsap", "tcp")
```

### 📊 Output Analysis
  - **Module**: Hardware module identifier (6ES7 315-2AG10-0AB0)
  - **Basic Hardware**: Basic hardware type (SIMATIC 300)
  - **Version**: Firmware version (2.6.9)
  - **System Name**: System identifier (SIMATIC 300(1))
  - **Module Type**: Extended module type - **Contains the CTF flag!** 🚩

### ✅ Conclusion
Using Nmap's s7-info script, you can:
  - Identify Siemens S7 PLCs on the network
  - Retrieve detailed system information including module type, version, and serial number
  - Discover sensitive information embedded in PLC identification fields

  This demonstrates how industrial protocols expose system information that can be valuable for reconnaissance. In real-world scenarios, attackers use this information to:
  - Identify specific PLC models and firmware versions
  - Search for known vulnerabilities affecting those versions
  - Plan targeted attacks against industrial control systems

  **Security Best Practice**: Always restrict access to S7 communication ports (102, 1102, or custom ports) and monitor S7 communication for unauthorized scanning attempts.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>
  Submit the flag found in the Module Type field:

  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(s7comm_analysis_complete)
  </div>
</details>
