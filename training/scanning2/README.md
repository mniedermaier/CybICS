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

### Step 1: Identify the S7 PLC
First, use the s7-info NSE script to identify the S7 PLC:
```bash
nmap -p 102 --script s7-info $DEVICE_IP
```
This will show PLC details like module type, version, and serial number.

### Step 2: Read the Flag from Data Block
The CTF flag is stored in **Data Block 1 (DB1)** on the S7 PLC. To read it, you need to use an S7 client tool.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>

  ### Step 1: S7-Info Scan Results
  Running `nmap -p 102 --script s7-info` shows:
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
  - **System Name**: System identifier (shows SNAP7-SERVER)
  - **Copyright**: Manufacturer details (Siemens AG)

  ### Step 2: Read Data Block to Get Flag
  The flag is stored in **DB1** (Data Block 1). You can read it using a Python script with the snap7 library:

  ```python
  #!/usr/bin/env python3
  import snap7

  # Connect to S7 PLC
  client = snap7.client.Client()
  client.connect('$DEVICE_IP', 0, 1)

  # Read 33 bytes from DB1, starting at offset 0
  data = client.db_read(1, 0, 33)

  # Convert bytes to string
  flag = data.decode('ascii').rstrip('\x00')
  print(f"Flag: {flag}")

  client.disconnect()
  ```

  **Alternative using command line:**
  ```bash
  python3 -c "import snap7; c = snap7.client.Client(); c.connect('$DEVICE_IP', 0, 1); print(c.db_read(1, 0, 33).decode('ascii').rstrip('\x00')); c.disconnect()"
  ```

  ### 📊 Expected Output
  ```
  Flag: CybICS(s7comm_analysis_complete)
  ```

  ### ✅ Conclusion
  By combining Nmap's s7-info script with S7 protocol client tools, you can:
  - Identify Siemens S7 PLCs on the network
  - Read data blocks to discover sensitive information (including CTF flags!)

  This demonstrates how attackers can gather intelligence from industrial control systems and emphasizes the importance of securing S7 communication protocols.

  Happy Scanning! 🔍🚀

  After reading DB1 and discovering the flag, submit it:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(s7comm_analysis_complete)
  </div>
</details>
