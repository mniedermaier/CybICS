# 🌊 Flood & Overwrite Attack Guide

> **MITRE ATT&CK for ICS:** `Impair Process Control` | [T0836 - Modify Parameter](https://attack.mitre.org/techniques/T0836/) | [T0855 - Unauthorized Command Message](https://attack.mitre.org/techniques/T0855/) | [T0806 - Brute Force I/O](https://attack.mitre.org/techniques/T0806/)

## 📋 Overview
A flooding attack in an industrial security context can have devastating consequences, disrupting critical operations and compromising safety.
By overwhelming industrial control systems (ICS) or Supervisory Control and Data Acquisition (SCADA) networks with excessive traffic, attackers can cause delays or complete halts in manufacturing processes, energy distribution, or other essential industrial functions.
These disruptions can lead to significant financial losses, damage to equipment, and potential safety hazards for workers and the surrounding community.

In this scenario, an attacker is continuously flooding the Modbus server (e.g., a PLC) with malicious commands to override a specific register value.

## 🔄 Attack Flow
```
Client       Attacker           PLC (Server)
   |            |                      |
   |            |  Floods              |
   |            |  Write Command       |
   |            |  (Register X = 0)    |
   |            |  --------------------> 
   |            |                      |
   |            |  Floods              |
   |            |  Write Command       |
   |            |  (Register X = 0)    |
   |            |  -------------------->
   |            |                      |
   |            |   Override           |
   |            |   Register X         |
   |            |  (Continuously)      |
   |            |  -------------------->
```

### 🎯 How It Works
- The Attacker floods the PLC (Modbus server) with write commands targeting a specific Modbus register (e.g., Register X)
- The attacker's command overrides the correct value of Register X, continuously forcing it to a specific value (e.g., 0)
- This continuous flood makes it impossible for the legitimate Client to write or control the register normally

The attacker's goal is to override the register and control the behavior of the device by continuously sending malicious write commands to the PLC.

## 🎭 Spoofing
Spoofing a Modbus register involves an attacker sending fraudulent data to a Modbus device, tricking it into believing the data is legitimate.
This type of attack can severely disrupt industrial processes by manipulating the readings or settings of critical devices such as sensors, actuators, or controllers.
For instance, an attacker could alter temperature or pressure readings, causing a system to operate outside safe parameters, potentially leading to equipment damage or safety hazards.

## 🚀 Example Implementation

### 📝 Script Overview
The provided script `flooding_hpt.py` floods via modbus the high pressure tank (HPT) values to 10.
With this flooding, the OpenPLC does not get the correct values and enables the compressor (C) all the time.
This is leading to a critical pressure value in the HPT.

### ⚙️ Configuration
The script uses the `.dev.env` file in the root folder of the git.
Check if these settings are correct, before executing the flooding script.

### 📚 Prerequisites
A basic understanding of Modbus/TCP is required for this example.

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Impair Process Control | Modify Parameter | [T0836](https://attack.mitre.org/techniques/T0836/) | Adversaries may modify parameters to disrupt normal process operation |
| Impair Process Control | Unauthorized Command Message | [T0855](https://attack.mitre.org/techniques/T0855/) | Adversaries may send unauthorized commands to ICS devices |
| Impair Process Control | Brute Force I/O | [T0806](https://attack.mitre.org/techniques/T0806/) | Adversaries may repeatedly write to I/O points to override legitimate control |

**Why this matters:** This attack demonstrates how an adversary can take control of a physical process by flooding Modbus registers faster than legitimate controllers can update them. The Ukrainian power grid attacks in 2015-2016 used similar techniques to manipulate breaker controls. This is a direct path from cyber access to physical impact—the core concern in ICS security.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Operational Process Monitoring | [D3-OPM](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/) | Monitoring process values for unexpected changes |
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Detecting abnormal Modbus write frequencies |
| Message Analysis | [D3-MA](https://d3fend.mitre.org/technique/d3f:MessageAnalysis/) | Analyzing message content to detect unauthorized commands |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Communications Protection (SC)** | SC-5, SC-7 | Denial of service protection and boundary protection |
| **System and Information Integrity (SI)** | SI-4, SI-10 | System monitoring and information input validation |
| **Access Control (AC)** | AC-3, AC-4 | Access enforcement and information flow enforcement |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.10 addresses the challenges of securing legacy protocols that lack authentication. SC-5 (Denial of Service Protection) and SI-10 (Information Input Validation) are particularly relevant—OT systems should validate command sources and rate-limit writes where possible. AC-4 (Information Flow Enforcement) recommends implementing application-layer firewalls that understand industrial protocols and can block unauthorized commands.

</details>

## 🔍 Solution

<details>
  <summary><span style="color:orange;font-weight: 900">Click to expand</span></summary>

  ### 🚀 Running the Attack
  Execute the provided script to flood the sensor values of the high pressure tank (HPT):
  ```sh
  python3 flooding_hpt.py
  ```

  ### 📊 Script Details
  This script is designed to:
  - Continuously send a specific value to a Modbus TCP device
  - Simulate flooding a high-pressure tank (HPT) in a system controlled by an OpenPLC
  - Flood a high-pressure tank's register by repeatedly writing a value (10) to register 1126
  - Connect to a Modbus TCP device using the IP address from the environment file
  - Perform flooding operations at a very high frequency

  ### 👀 Observations
  What can be observed on the FUXA HMI and what happens to the physical process?

  #### 📈 Historical Data and Trends
  - The interface provides access to historical data and trend analysis
  - Enables operators to review past performance
  - Helps analyze trends over time
  - Supports data-driven decisions to optimize process efficiency

  #### ⚠️ Response to Alerts
  - When an alert is triggered, it prompts immediate action
  - Example: Temperature sensor anomaly detection
  - Operator notifications for corrective measures
  - Potential actions: reducing heat or shutting down components

  After completion, use the following flag:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(flood_attack_successful)
  </div>
</details>

