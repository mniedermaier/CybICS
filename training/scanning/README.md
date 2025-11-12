# 🔍 Service Scanning Guide

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
To identify open ports and services within the CybICS testbed you can use nmap. Your goal is to perform service version detection to discover the flag hidden in a service banner.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>

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
  - **80/tcp**: HTTP service - Landing page with flag in Server header 🚩
  - **102/tcp**: S7 Communication (S7comm) - Siemens PLC communication protocol
  - **502/tcp**: Modbus TCP - Industrial device communication
  - **1881/tcp**: HTTP (Node.js Express) - Web application interface
  - **4840/tcp**: OPC UA TCP - Industrial automation protocol
  - **8080/tcp**: HTTP Proxy (Werkzeug/Python) - OpenPLC web interface
  - **20000/tcp**: DNP3 - Industrial control protocol
  - **44818/tcp**: EtherNet/IP - Industrial networking protocol


  Submit the flag found in the service banner:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(scanning_d0ne)
  </div>
</details>