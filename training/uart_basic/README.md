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

## 🎯 Task
The flag has the format `CybICS(flag)`.

### Steps
1. Connect to the CybICS Raspberry Pi via SSH
2. Install picocom if not already available
3. Connect to the UART interface using picocom at 115200 baud on /dev/serial0
4. Observe the login prompt on the UART console
5. Run the brute-force script to discover the 3-character lowercase password
6. Log in with the discovered password to retrieve the flag

The flag appears after a successful login on the UART console. When you connect via picocom, you will be presented with a login prompt that requires a password.

### Password Constraints
- The password is **3 characters long**
- It contains **only lowercase letters** (a-z)

This means there are only 26^3 = 17,576 possible combinations, making brute-forcing a viable approach.

### Brute-Force Approach
Given the small keyspace, you can automate the login attempts using the provided `bruteforce_login.py` script, which systematically tries all lowercase 3-character combinations over the serial connection. At approximately 1-2 passwords per second, expect the process to take up to a few hours in the worst case.

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


## 💡 Hints

Run `python3 bruteforce_login.py /dev/serial0 3 3` to brute-force the 3-character lowercase password over the UART serial connection.

## 🔍 Solution

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

**Flag:** `CybICS(U#RT)`
