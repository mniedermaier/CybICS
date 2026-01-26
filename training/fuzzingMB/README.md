# 🧪 Network Fuzzing Guide

> **MITRE ATT&CK for ICS:** `Impair Process Control` `Impact` | [T0855 - Unauthorized Command Message](https://attack.mitre.org/techniques/T0855/) | [T0814 - Denial of Service](https://attack.mitre.org/techniques/T0814/)

## 📋 Introduction
Network fuzzing is a security testing technique used to identify vulnerabilities in network protocols, services, and applications by sending malformed or unexpected data. The goal is to discover security flaws such as buffer overflows, denial-of-service (DoS) vulnerabilities, and other unintended behaviors.

## 🔄 How It Works
Network fuzzing involves the following steps:

1. **🎯 Selecting a Target** – Identify the network service, protocol, or application to be tested
2. **🧩 Generating Test Cases** – Create malformed, randomized, or unexpected inputs
3. **📤 Sending Inputs** – Transmit the test cases to the target over the network
4. **👀 Monitoring Responses** – Observe how the target handles the malformed data
5. **📊 Analyzing Results** – Identify potential security vulnerabilities

## 📚 Types of Network Fuzzing
There are different approaches to network fuzzing:

- **🔄 Mutation-based Fuzzing** – Modifies existing valid inputs to generate test cases
- **🏗️ Generation-based Fuzzing** – Constructs test cases from scratch based on protocol specifications
- **🔗 Stateful vs. Stateless Fuzzing** – Maintains session states vs. individual test cases

## ⚠️ Challenges and Considerations
- **❌ False Positives** – Some anomalies may not indicate real vulnerabilities
- **💻 Target Stability** – Frequent crashes may disrupt testing
- **📖 Protocol Complexity** – Some protocols require deep understanding
- **⚖️ Legal and Ethical Considerations** – Unauthorized fuzzing can violate laws

## 🚀 Using the Modbus Fuzzer

### 🔧 Setup Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/s-e-knudsen/Modbus_network_fuzzer
   ```

2. Switch to the folder:
   ```sh
   cd Modbus_network_fuzzer 
   ```

3. Install dependencies:
   ```sh
   python3 -m pip install -r requirements.txt
   ```

### 🎮 Running the Fuzzer
Select the proper fuzzing method (e.g., 1 for all):
```sh
        --------------------------------------
        Created by Soren Egede Knudsen @Egede
        --------------------------------------
        What do you want to fuzz?
        1.  Fuzz all function codes and base
        2.  Fuzz Read Device Identification
        3.  Fuzz Read Discrete Inputs
        4.  Fuzz Read Input Registers
        5.  Fuzz Read Multiple Holding Registers
        6.  Fuzz Write Single Holding Register
        7.  Fuzz Write Single Coil
        8.  Fuzz Write Multiple Coils
        9.  Fuzz Write Multiple Holding Registers
        10. Fuzz Read/Write Multiple Registers
        11. Fuzz Mask Write Register
        12. Fuzz Read File Record
        13. Fuzz Write File Record
        14. Fuzz Read Exception Status
        15. Fuzz Report Slave ID
        16. Fuzz Read Coil Memory
        20. Fuzz ModbusTCP - Base protocol
        - - - - - - - - - - - - - - - - - - - 
        90. Fuzz ModbusTCP - FC67 - non standard - Read float registers
        91. Fuzz ModbusTCP - FC68 - non standard - Read float registers
        92. Fuzz ModbusTCP - FC70 - non standard - Write single float registers
        93. Fuzz ModbusTCP - FC80 - Non standard - Write multible float registers
        - - - - - - - - - - - - - - - - - - - 
        0. Exit
```

### ⏳ Time to Wait
Grab a coffee ☕☕☕☕ while the fuzzer runs

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Impair Process Control | Unauthorized Command Message | [T0855](https://attack.mitre.org/techniques/T0855/) | Adversaries may send malformed or unexpected commands to disrupt control |
| Impact | Denial of Service | [T0814](https://attack.mitre.org/techniques/T0814/) | Adversaries may crash or disrupt services through malformed input |

**Why this matters:** Protocol fuzzing reveals how ICS devices handle unexpected or malformed input. Many PLCs and industrial devices have limited error handling and can crash or behave unpredictably when receiving invalid data. Understanding these weaknesses helps both attackers (to find exploitable bugs) and defenders (to test device resilience before deployment).

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Protocol Metadata Anomaly Detection | [D3-PMAD](https://d3fend.mitre.org/technique/d3f:ProtocolMetadataAnomalyDetection/) | Detecting malformed protocol messages |
| Input Validation | [D3-IV](https://d3fend.mitre.org/technique/d3f:InputValidation/) | Validating input to prevent exploitation |
| Application Exception Monitoring | [D3-AEM](https://d3fend.mitre.org/technique/d3f:ApplicationExceptionMonitoring/) | Monitoring for crashes and exceptions caused by fuzzing |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-10, SI-17 | Information input validation and fail-safe procedures |
| **System and Communications Protection (SC)** | SC-5 | Denial of service protection |
| **Risk Assessment (RA)** | RA-5 | Vulnerability scanning including protocol fuzzing |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.7 addresses the need for input validation (SI-10) in OT systems. Many legacy devices were designed for trusted environments and lack proper input validation. RA-5 (Vulnerability Scanning) recommends testing systems for robustness, including protocol fuzzing—but only in controlled environments. SI-17 (Fail-Safe Procedures) ensures that when devices do fail, they fail safely without causing dangerous conditions.

</details>

## 🔍 Solution

<details>
  <summary><span style="color:orange;font-weight: 900">Click to expand</span></summary>

  After completion, use the following flag:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(modbus_fuzzing_complete)
  </div>

</details>
