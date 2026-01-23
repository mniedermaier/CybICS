# 🕵️‍♂️ Man-in-the-Middle (MitM) Attack Guide

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

## 🎯 Find the Flag
The flag has the format `CybICS(flag)`.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>
  
  After completion, use the following flag:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(mitm_attack_successful)
  </div>

</details>
