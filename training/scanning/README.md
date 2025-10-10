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
To identify open ports and services within the CybICS testbed you can use nmap.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>
  
  Execute the following nmap command:
  ```sh
  nmap -sV -p- $DEVICE_IP
  ```

  ### 📝 Command Breakdown
  The `nmap -sV -p-` command is used with Nmap, a popular network scanning tool, to perform a comprehensive service version detection scan on all ports of a target system:
  
  - `nmap`: The command-line tool for network discovery and security auditing
  - `-sV`: Performs service version detection, probing open ports to determine service and version
  - `-p-`: Scans all 65,535 TCP ports (1-65535)
  
  The scan will take several minutes.

  ### 📊 Scan Results
  ```sh
  PORT      STATE SERVICE       VERSION
  22/tcp    open  ssh           OpenSSH 9.2p1 Debian 2+deb12u1 (protocol 2.0)
  102/tcp   open  iso-tsap
  502/tcp   open  modbus        Modbus TCP
  1881/tcp  open  http          Node.js Express framework
  4840/tcp  open  opcua-tcp?
  8080/tcp  open  http-proxy    Werkzeug/2.3.7 Python/3.11.2
  20000/tcp open  dnp?
  44818/tcp open  EtherNetIP-2?
  ```

  ### 🔎 Port Analysis
  - **22/tcp**: SSH service (OpenSSH 9.2p1) - Secure remote access
  - **102/tcp**: S7 Communication (S7comm) - Siemens PLC communication
  - **502/tcp**: Modbus TCP - Industrial device communication
  - **1881/tcp**: HTTP (Node.js Express) - Web application interface
  - **4840/tcp**: OPC UA TCP - Industrial automation protocol
  - **8080/tcp**: HTTP Proxy (Werkzeug/Python) - Web server
  - **20000/tcp**: DNP3 - Industrial control protocol
  - **44818/tcp**: EtherNet/IP - Industrial networking protocol

  
  After completion, use the following flag:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(scanning_d0ne)
  </div>
</details>