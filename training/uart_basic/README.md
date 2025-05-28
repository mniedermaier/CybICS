# 🔌 UART Training Guide

## 📋 Overview
This guide covers how to connect to the CybICS system using UART (Universal Asynchronous Receiver-Transmitter) communication.

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

## 🎯 Find the flag
The flag has the format `CybICS(flag)`.

**💡 Hint**: The flag appears after successful login on the HMI.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>
  
  Run the script:
  ```bash
  python3 bruteforce_login.py /dev/serial0
  ```

  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(U#RT)
  </div>
</details>
