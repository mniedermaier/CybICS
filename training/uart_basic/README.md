# 🔌 UART Training Guide (Hardware Required)

> **MITRE ATT&CK for ICS:** `Initial Access` | [T0812 - Default Credentials](https://attack.mitre.org/techniques/T0812/) | [T0822 - External Remote Services](https://attack.mitre.org/techniques/T0822/)

## 📋 Overview
This guide covers how to connect to the CybICS micro controller using UART (Universal Asynchronous Receiver-Transmitter) communication.

## 🔗 Connecting to the System

### 🔐 SSH Connection
1. Connect to the Raspberry Pi:
   ```bash
   ssh pi@cybics
   ```
   - 🔑 Default password: `raspberry`
   - 🌐 If using a different hostname, replace 'cybics' with the correct IP address

### 📡 UART Communication
1. Install picocom if not already installed:
   ```bash
   sudo apt-get install picocom
   ```

2. Connect to the UART interface:
   ```bash
   picocom -b 115200 /dev/serial0
   ```

3. Common picocom commands:
   - `Ctrl+A Ctrl+X`: Exit picocom

## 🎯 Find the Flag
The flag has the format `CybICS(flag)`.

**💡 Hint**: The flag appears after successful login on the UART.

**🔑 Password Hint**: The password is 3 characters long and contains only out of lowercase letters.

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Initial Access | Default Credentials | [T0812](https://attack.mitre.org/techniques/T0812/) | Adversaries may leverage default or weak credentials on embedded devices |
| Initial Access | External Remote Services | [T0822](https://attack.mitre.org/techniques/T0822/) | Adversaries may use serial/debug interfaces as entry points |

**Why this matters:** Hardware interfaces like UART, JTAG, and SWD are often overlooked attack vectors in ICS environments. Embedded devices (PLCs, RTUs, sensors) frequently have debug interfaces with weak or no authentication. Physical access to these interfaces can bypass all network security controls. This training demonstrates that ICS security must include physical security and hardware hardening.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Physical Access Control | [D3-PAC](https://d3fend.mitre.org/technique/d3f:PhysicalAccessControl/) | Restricting physical access to devices and interfaces |
| Hardware Component Inventory | [D3-HCI](https://d3fend.mitre.org/technique/d3f:HardwareComponentInventory/) | Tracking devices with exposed debug interfaces |
| Authentication Event Monitoring | [D3-AEM](https://d3fend.mitre.org/technique/d3f:AuthenticationEventMonitoring/) | Logging serial console access attempts |
| Strong Password Policy | [D3-SPP](https://d3fend.mitre.org/technique/d3f:StrongPasswordPolicy/) | Enforcing strong credentials on all interfaces |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Physical and Environmental Protection (PE)** | PE-3, PE-4, PE-5 | Physical access control, access control for transmission, and access control for output devices |
| **Identification and Authentication (IA)** | IA-2, IA-5 | User identification and authenticator management for all interfaces |
| **Media Protection (MP)** | MP-7 | Media use restrictions including serial interfaces |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.9 addresses physical security for OT environments. PE-3 (Physical Access Control) should include control cabinet locks and tamper detection. PE-5 (Access Control for Output Devices) specifically mentions serial/console ports as interfaces requiring protection. Many organizations focus on network security while leaving debug interfaces wide open—this training demonstrates why PE controls are just as important as SC (System and Communications Protection) controls.

</details>

## 🔍 Solution

<details>
  <summary><span style="color:orange;font-weight: 900">Click to expand</span></summary>

  Run the script:
  ```bash
  python3 bruteforce_login.py /dev/serial0 3 3
  ```

   The output should look like this:
  ```bash
   [*] Using password length range: 3-3
   2025-06-05 14:07:30 - INFO - Connected to /dev/serial0
   2025-06-05 14:07:30 - INFO - Results will be saved to bruteforce_results.txt
   2025-06-05 14:07:30 - INFO - Starting bruteforce attack...
   2025-06-05 14:07:30 - INFO - Total combinations to try: 17,576
   2025-06-05 14:07:30 - INFO - Trying 3 character combinations...
   [*] Current: cyb | Rate: 1.6 p/s | Attempts: 1,978 | Elapsed: 20.1m | Remaining: 2.6h2025-06-05 14:27:33 - INFO -
   [+] Password found: cyb
   [+] Attempts: 1,978
   [+] Time taken: 20.1m
   [+] Average rate: 1.6 passwords/second
   2025-06-05 14:27:33 - INFO - Disconnected
  ```

  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(U#RT)
  </div>
</details>
