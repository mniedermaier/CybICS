# 🔍 Detection Training - Override

> **MITRE D3FEND:** `Detect` | [D3-NTA - Network Traffic Analysis](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | [D3-OPM - Operational Process Monitoring](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/)

## 📋 Overview
One common attack is Modbus TCP register flooding, where an attacker sends a continuous stream of malicious Modbus commands to overwrite or spoof register values.
This can disrupt processes, cause equipment failure, or provide incorrect data to operators.
This training focuses on how to detect this type of attack by analyzing network traffic and monitoring system behavior.

## 🎯 Indicators of Modbus Flooding Attacks
Detecting Modbus flooding and register overwriting attacks requires understanding how normal Modbus traffic behaves and recognizing anomalies in the communication pattern. Key indicators include:

### 1. 📈 High Frequency of Modbus Write Requests
Modbus systems typically have a stable frequency of write operations. A sudden spike in write requests, particularly to the same registers, is a sign of flooding. Monitor for:
- Unusual write frequencies: Multiple write commands to the same register in a short time span
- Repeated overwrites: The same register being modified continuously

### 2. 🔄 Unexplained Process Values Changes
When a Modbus register is being spoofed, the values stored in registers might change frequently without corresponding physical events. For example:
- A temperature sensor reports fluctuating values despite stable environmental conditions
- Equipment parameters (e.g., pressure, motor speed) are altered without operator action

### 3. 🚫 Unusual Source IPs or Unauthorized Devices
Flooding may come from unauthorized IP addresses or devices not normally involved in the communication. Look for:
- Write commands originating from unknown sources
- Devices sending Modbus traffic that do not typically perform write operations

### 4. 📊 Network Traffic Abnormalities
Flooding often generates a high volume of packets, potentially leading to congestion or delays in legitimate traffic. Watch for:
- Unusually high Modbus traffic: A sharp increase in Modbus TCP packets on the network
- Packet loss: Legitimate Modbus traffic may be delayed or dropped due to the attack

## ❓ Training Questions
1. What is happening with the physical process?
2. What can you observe within the network capture?

## ⚠️ Important Note
***!!! Execute the python script without looking into it !!!***

```sh
python3 override.py <DEVICE_IP>
```

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Detected Techniques

This training focuses on **detecting** the following adversary techniques:

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Impair Process Control | Modify Parameter | [T0836](https://attack.mitre.org/techniques/T0836/) | Modifying process parameters to affect operation |
| Impair Process Control | Unauthorized Command Message | [T0855](https://attack.mitre.org/techniques/T0855/) | Sending unauthorized commands to ICS devices |
| Impair Process Control | Brute Force I/O | [T0806](https://attack.mitre.org/techniques/T0806/) | Repeatedly overwriting I/O values |

**Why this matters:** Detecting ongoing attacks is more challenging than detecting reconnaissance. Register flooding attacks actively manipulate the process while you're trying to detect them. This training simulates the pressure of real incident response—you must identify the attack, understand its impact, and gather evidence while the attack continues.

### MITRE D3FEND - Defensive Techniques (Primary Focus)

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Analyzing Modbus traffic for anomalies |
| Operational Process Monitoring | [D3-OPM](https://d3fend.mitre.org/technique/d3f:OperationalProcessMonitoring/) | Monitoring process values for unexpected changes |
| Message Analysis | [D3-MA](https://d3fend.mitre.org/technique/d3f:MessageAnalysis/) | Analyzing message content to identify malicious commands |
| Baseline Deviation Detection | [D3-BDD](https://d3fend.mitre.org/technique/d3f:BaselineDeviationDetection/) | Detecting deviations from normal traffic baselines |

**Detection indicators to look for:**
- Abnormally high frequency of Modbus write commands (Function Code 6 or 16)
- Repeated writes to the same register address
- Write commands from unexpected source IPs
- Process values that don't match expected physics (e.g., pressure changing faster than physically possible)

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-4, SI-7 | System monitoring and software/information integrity |
| **Audit and Accountability (AU)** | AU-3, AU-6 | Detailed audit records and automated review |
| **Incident Response (IR)** | IR-4, IR-5 | Incident handling and monitoring |
| **System and Communications Protection (SC)** | SC-5, SC-7 | Denial of service protection and boundary protection |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.7 recommends both network-based and process-based monitoring for comprehensive detection. SI-4 (System Monitoring) should include industrial protocol-aware intrusion detection systems (IDS) that understand Modbus semantics. SC-5 (Denial of Service Protection) recommends rate limiting and anomaly detection for industrial protocols. This training teaches you to correlate network observations (high write frequency) with process observations (unexpected pressure changes)—the hallmark of effective OT security monitoring.

</details>

## 🔍 Solution

<details>
  <summary><span style="color:orange;font-weight: 900">Click to expand</span></summary>

  ### 🔍 Wireshark Analysis

  #### 📡 Modbus Filter
  To filter only Modbus traffic, use the following filter in Wireshark:
  ```sh
  tcp.port == 502
  ```

  #### ✍️ Identifying Excessive Write Requests
  Apply a filter for Modbus function codes responsible for writing registers:
  ```sh
  modbus.func_code == 6 || modbus.func_code == 16
  ```
  Look for a large number of write requests to the same register (e.g., modbus.reference_num indicates the register address).

  #### 📊 IO Graphs
  Use Wireshark's IO Graphs to visualize the traffic over time. A spike in the number of write requests is a strong indicator of flooding.

  After completion, use the following flag:
  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(detection_evasion_complete)
  </div>
</details>