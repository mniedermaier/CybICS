# 🕵️‍♂️ Man-in-the-Middle (MitM) Attack Guide

> **MITRE ATT&CK for ICS:** `Collection` `Evasion` | [T0830 - Adversary-in-the-Middle](https://attack.mitre.org/techniques/T0830/) | [T0856 - Spoof Reporting Message](https://attack.mitre.org/techniques/T0856/)

## 📋 Overview
This guide explains how to create a Modbus TCP proxy in Python that listens on all network interfaces (`0.0.0.0`).
The proxy intercepts Modbus traffic between a Modbus client and a Modbus server, allowing you to manipulate the traffic (requests and responses) like a "man-in-the-middle" attack.

## 🧑‍💻 What is a Man-in-the-Middle Attack?
A Man-in-the-Middle (MITM) attack is a type of cyberattack where a malicious actor secretly intercepts and possibly alters the communication between two parties, without either party realizing it. In the context of Modbus TCP, a widely used protocol in industrial control systems (ICS) for communication between controllers (like PLCs) and devices (like sensors or actuators), a MITM attack can be particularly dangerous.

### 🔄 Modbus TCP MITM Flow
Modbus TCP works over a TCP/IP network and follows a client-server model, where:
- **Client** (usually the Human-Machine Interface (HMI) or SCADA system) sends Modbus requests (like read/write commands) to control devices.
- **Server** (typically a Programmable Logic Controller (PLC) or other field devices) responds to these commands.

In a MITM attack on Modbus TCP, an attacker positions themselves between the client and the server to intercept and manipulate Modbus requests and responses.

```
Client     🕵️‍♂️ Attacker (Proxy)  Server
   |            |              |
   |----->      |              |
   |            |----->        |
   |            |<-----        |
   |<-----      |              |
```

This shows the basic flow:
- Client sends a request (----->) to the Attacker (posing as the server).
- Attacker forwards the request to the Server.
- Server responds (<-----) to the Attacker.
- Attacker potentially modifies and sends the response back to the Client.

## 🔧 ARP Spoofing: Becoming the Man-in-the-Middle

To position yourself between the client (FUXA HMI) and server (OpenPLC), you need to redirect their network traffic through your machine. This is accomplished using **ARP spoofing** (also called ARP cache poisoning).

### What is ARP Spoofing?

The Address Resolution Protocol (ARP) maps IP addresses to MAC addresses on a local network. Each device maintains an ARP cache — a table of IP-to-MAC mappings. ARP spoofing exploits the fact that ARP has **no authentication**: any device can send ARP replies claiming to be any other device.

By sending forged ARP replies, you trick both the client and server into sending their traffic to your machine instead of directly to each other:

1. **Tell the client (FUXA):** "I am the server (OpenPLC)" — send a spoofed ARP reply to FUXA with OpenPLC's IP but your MAC address
2. **Tell the server (OpenPLC):** "I am the client (FUXA)" — send a spoofed ARP reply to OpenPLC with FUXA's IP but your MAC address

Once both devices update their ARP caches, all traffic between them flows through your machine.

### Tools for ARP Spoofing

Common tools include:
- **arpspoof** (part of the `dsniff` package) — simple command-line ARP spoofing
- **ettercap** — full-featured MITM framework
- **scapy** — Python-based packet crafting (for custom scripts)

You will need to run ARP spoofing in **both directions** (one for each target) so that traffic flows through your machine bidirectionally. You also need IP forwarding enabled on your machine so that intercepted packets are forwarded rather than dropped.

## 🛠️ Two-Step Attack Process

The full MITM attack requires two steps running simultaneously:

### Step 1: ARP Spoof to Redirect Traffic

Use ARP spoofing to redirect traffic between FUXA and OpenPLC through your machine. This must remain running for the duration of the attack.

### Step 2: Run the Modbus Proxy

Once traffic is flowing through your machine, run the Modbus TCP proxy to intercept and optionally manipulate the traffic.

## 🛠️ Prerequisite: Admin Access on FUXA HMI
Before setting up the Python proxy for intercepting Modbus traffic, you need administrator access on the FUXA HMI. This is necessary to modify the IP settings of the connected PLC, directing its communication through the Python proxy.

With admin access, you'll be able to change the PLC's configuration to use the proxy's IP address and port, ensuring all traffic is routed through the proxy for monitoring and manipulation.

![FUXA IP Configuration](doc/fuxa_ip.png)

## 🚀 Example: Running the Proxy
An example of this proxy can be found in the `mitm.py` file.
By default, it does not modify or manipulate any values, allowing the proxy to only focus on significant traffic changes. You can easily extend it to customize the manipulations as needed for your specific use case.
For this, a good understanding of Modbus/TCP is required.

```sh
python3 mitm.py
```

## 🎯 Task
Perform a Man-in-the-Middle attack using ARP spoofing and the provided Modbus proxy to intercept and analyze PLC communication.

The flag has the format `CybICS(flag)`.

### Steps
1. Ensure you have access to the attack machine and identify the target IPs (PLC and HMI)
2. Enable IP forwarding on the attack machine
3. Run ARP spoofing to poison the ARP caches of both the PLC and HMI
4. Start the provided mitm.py Modbus proxy script
5. Observe the intercepted Modbus traffic and find the flag

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Collection | Adversary-in-the-Middle | [T0830](https://attack.mitre.org/techniques/T0830/) | Adversaries may position themselves between endpoints to intercept and manipulate communications |
| Evasion | Spoof Reporting Message | [T0856](https://attack.mitre.org/techniques/T0856/) | Adversaries may spoof messages to hide malicious activity from operators |

**Why this matters:** Man-in-the-Middle attacks allow adversaries to intercept, monitor, and modify communications between HMI/SCADA systems and PLCs. Since Modbus lacks authentication, an attacker can inject commands, modify responses, or hide attacks from operators. This was demonstrated in the Industroyer/CrashOverride malware, which used similar techniques to control power grid equipment while hiding its actions from operators.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Encrypted Tunnels | [D3-ET](https://d3fend.mitre.org/technique/d3f:EncryptedTunnels/) | Encrypting communications to prevent interception |
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Detecting anomalous traffic patterns indicating MitM |
| Message Authentication | [D3-MAN](https://d3fend.mitre.org/technique/d3f:MessageAuthentication/) | Authenticating messages to detect tampering |
| Network Segmentation | [D3-NI](https://d3fend.mitre.org/technique/d3f:NetworkIsolation/) | Limiting attacker positioning opportunities |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Communications Protection (SC)** | SC-7, SC-8, SC-23 | Boundary protection, transmission confidentiality, and session authenticity |
| **System and Information Integrity (SI)** | SI-4, SI-7 | System monitoring and data integrity verification |
| **Access Control (AC)** | AC-4 | Information flow enforcement |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.10 identifies the lack of authentication in legacy protocols as a critical vulnerability. SC-8 (Transmission Confidentiality) and SC-23 (Session Authenticity) recommend cryptographic protections where feasible. When protocol encryption isn't possible, SC-7 (Boundary Protection) and AC-4 (Information Flow Enforcement) become critical—limiting which systems can communicate with which devices reduces MitM opportunities. SI-4 (System Monitoring) helps detect the traffic anomalies that MitM attacks create.

</details>


## 💡 Hints

Use `arpspoof -i eth0 -t <FUXA_IP> <OpenPLC_IP>` in one terminal and `arpspoof -i eth0 -t <OpenPLC_IP> <FUXA_IP>` in another. Enable IP forwarding with `echo 1 > /proc/sys/net/ipv4/ip_forward`. Then run `python3 mitm.py` in a third terminal.

## 🔍 Solution

After completion, use the following flag:

**Flag:** `CybICS(mitm_attack_successful)`
