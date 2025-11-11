# 🔍 S7 Communication Scanning Guide

## 📋 Introduction
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

The S7 service runs on port 1102 (not the standard port 102, which is used by OpenPLC). Due to nmap's s7-info script being hardcoded for port 102, you'll need to use an alternative approach to query the S7 service and discover the CTF flag.

### Method 1: Manual S7 Client (Recommended)
Use a Python script to connect to the S7 server and query system information:

```python
#!/usr/bin/env python3
import socket
import struct

def query_s7_info(host, port=1102):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    # COTP Connection Request
    cotp_req = bytes.fromhex('0300001611e00000001400c1020100c2020102c0010a')
    sock.send(cotp_req)
    sock.recv(1024)

    # S7 Communication Setup
    s7_setup = bytes.fromhex('0300001902f08032010000000000080000f0000001000101e0')
    sock.send(s7_setup)
    sock.recv(1024)

    # SZL Read Request (0x001c - Extended identification)
    szl_req = bytes.fromhex('0300002102f080320700000000000800080001120411440100ff090004001c0001')
    sock.send(szl_req)
    response = sock.recv(1024)

    # Parse Module Type field (position 78+ with offset 4)
    if len(response) > 78:
        # Extract null-terminated string
        module_type = response[78:].split(b'\x00')[0].decode('ascii')
        print(f"Module Type: {module_type}")

    sock.close()

query_s7_info('$DEVICE_IP')
```

### Method 2: Port Scanning Discovery
First, discover which ports are running S7 services:
```bash
nmap -p 102,1102 $DEVICE_IP
```
Then investigate port 1102 using the manual client method above.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>

  ### Step 1: Port Discovery
  First, scan for S7 services:
  ```bash
  nmap -p 102,1102 $DEVICE_IP
  ```

  Output:
  ```
  PORT     STATE SERVICE
  102/tcp  open  iso-tsap
  1102/tcp open  adobeserver-1
  ```

  Port 102 is the standard S7 port (OpenPLC), but port 1102 is also open - this is our target!

  ### Step 2: Query S7 System Information
  Create a Python script to query the S7 server on port 1102:

  ```python
  #!/usr/bin/env python3
  import socket

  def query_s7_info(host, port=1102):
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.connect((host, port))

      # COTP Connection Request
      cotp_req = bytes.fromhex('0300001611e00000001400c1020100c2020102c0010a')
      sock.send(cotp_req)
      sock.recv(1024)

      # S7 Communication Setup
      s7_setup = bytes.fromhex('0300001902f08032010000000000080000f0000001000101e0')
      sock.send(s7_setup)
      sock.recv(1024)

      # SZL Read Request (0x001c - Extended identification)
      szl_req = bytes.fromhex('0300002102f080320700000000000800080001120411440100ff090004001c0001')
      sock.send(szl_req)
      response = sock.recv(1024)

      # Parse Module Type field (position 78+ with offset 4)
      if len(response) > 78:
          module_type = response[78:].split(b'\x00')[0].decode('ascii')
          print(f"Module Type: {module_type}")

      sock.close()

  query_s7_info('$DEVICE_IP')
  ```

  ### Step 3: Execute and Discover Flag
  Run the script:
  ```bash
  python3 s7_query.py
  ```

  Output:
  ```
  Module Type: CybICS(s7comm_analysis_complete)
  ```

  ### 🔎 Key Discovery
  The **Module Type** field contains: `CybICS(s7comm_analysis_complete)` - **This is the flag!**

  The script uses the **SZL (System Status List)** protocol to query system identification information from the S7 PLC. The custom S7 server has been configured to embed the CTF flag in the Module Type field of the SZL 0x001c (Extended Identification) response.

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

  **Security Best Practice**: Always restrict access to S7 communication ports (102, 1102, or custom ports) and monitor S7 communication for unauthorized scanning attempts.

  Submit the flag found in the Module Type field:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(s7comm_analysis_complete)
  </div>
</details>
