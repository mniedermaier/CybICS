# 🔍 Detection Training - Basic

## 📋 Overview
In this training, we focus on how to detect network scanning activities using PCAP (Packet Capture) data.
PCAP files capture the raw network traffic data and are valuable for the security operation center (SOC) or forensic analysis of network communications.

## 🎯 Network Scanning Techniques
Attackers use different types of network scanning techniques to map out the network and gather intelligence.
Common techniques include:

### 1. 🎯 Ping Sweep
- Attackers send ICMP Echo Requests to multiple IP addresses
- Used to determine which hosts are online

### 2. 🔍 Port Scanning
Tools like Nmap are used to scan for open ports on target systems. Common scan types include:
- **SYN scan (Half-Open Scan)**: Sends SYN packets to check if a port is open
- **TCP Connect Scan**: Establishes a full TCP connection with the target port
- **UDP Scan**: Tests for open UDP ports, commonly used on industrial protocols like Modbus (port 502)
- **Service Detection**: Queries services running on open ports to determine their versions (e.g., OPC UA on port 4840)

### 3. 🛠️ Application Layer Scanning
- Attackers scan for specific application protocols
- Targets industrial control protocols like Modbus, DNP3, or OPC UA
- Helps identify system roles and functions

## ⚠️ Importance of Detection
Detecting and mitigating network scanning on industrial systems is a critical first step in preventing cyberattacks.
By capturing and analyzing network traffic through PCAP files, security teams can:
- Identify early signs of an attack
- Take appropriate action before an adversary gains deeper access
- Protect critical infrastructure

## 🎯 Training Questions
1. Which ports do the attacker scan?
2. Which ports are open, and which are closed?

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>
  
  <!-- Add solution content here -->
</details>