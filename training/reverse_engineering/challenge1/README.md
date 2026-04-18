# 🔓 PLC Maintenance Auth Tool

> **MITRE ATT&CK for ICS:** `Credential Access` | [T0812 - Default Credentials](https://attack.mitre.org/techniques/T0812/) | [T0110 - Brute Force — Password Cracking](https://attack.mitre.org/techniques/T0110/)

## 📋 Overview

During incident response on the CybICS gas pressure control system, forensic analysts
discovered a custom maintenance utility on the OpenPLC runtime filesystem. The binary is believed
to have been left by the original equipment vendor to allow privileged operator access
without going through the standard OpenPLC web interface.

The binary prompts for an operator password and — if correct — prints a vendor diagnostic
code containing a flag hidden in the system configuration.

```
==========================================================
  CybICS PLC Maintenance Tool  v1.2.0
  Gas Pressure Control System  - Operator Access
  (c) CybICS Industrial Systems
==========================================================
  System:   HPT/GST Pressure Controller
  Protocol: Modbus TCP
  Status:   CONNECTED
----------------------------------------------------------

Enter operator password: _
```

This models a realistic supply-chain risk: vendors frequently embed hardcoded credentials in
maintenance tools shipped with field devices, often with only superficial obfuscation, leaving
them recoverable by anyone with access to the binary.

## 🎯 Task

Reverse engineer `plc_auth` to recover the operator password and obtain the flag printed
after successful authentication.

The flag has the format `CybICS(flag)`.

1. Download the binary from the CTF server and make it executable
2. Run it to understand what it does
3. Perform static analysis to recover the password — start with `strings`, then examine the comparison logic in a disassembler if needed
4. Use dynamic analysis to observe the comparison at runtime without knowing the password in advance
5. Enter the recovered password to obtain the flag

```bash
wget http://localhost/static/challenges/plc_auth/plc_auth
chmod +x plc_auth
./plc_auth

# Static recon
file plc_auth
strings plc_auth

# Dynamic analysis
ltrace ./plc_auth
```

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Initial Access | Default Credentials | [T0812](https://attack.mitre.org/techniques/T0812/) | Vendor-supplied maintenance tools with embedded operator passwords |
| Credential Access | Brute Force — Password Cracking | [T0110](https://attack.mitre.org/techniques/T0110/) | Recovering the password by analyzing the binary offline |

**Why this matters:** Hardcoded credentials in ICS maintenance binaries are a persistent supply-chain threat. An attacker with even read-only access to a field device can extract vendor tools, reverse engineer the password, and gain privileged access to the control system — entirely bypassing the authentication controls visible to operators. The 2021 Oldsmar water treatment incident highlighted how single-factor, vendor-supplied credentials can become the weakest link in an OT environment.

### MITRE D3FEND — Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Software Binary Analysis | [D3-SBA](https://d3fend.mitre.org/technique/d3f:SoftwareBinaryAnalysis/) | Auditing vendor binaries for hardcoded secrets before deployment |
| Credential Hardening | [D3-CH](https://d3fend.mitre.org/technique/d3f:CredentialHardening/) | Requiring vendors to eliminate hardcoded credentials from firmware |
| Authentication Event Monitoring | [D3-AEM](https://d3fend.mitre.org/technique/d3f:AuthenticationEventMonitoring/) | Alerting on the use of shared maintenance credentials |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Identification and Authentication (IA)** | IA-5 | Authenticator management — prohibiting embedded plaintext or weakly obfuscated credentials |
| **Supply Chain Risk Management (SR)** | SR-6 | Supplier assessments — verifying vendor tools do not contain hardcoded secrets |
| **Configuration Management (CM)** | CM-7 | Least functionality — restricting which maintenance tools may be deployed on OT systems |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.3 explicitly calls out hardcoded credentials as a critical vulnerability class in OT environments. IA-5 requires that credentials not be embedded in software, while SR-6 recommends binary analysis of vendor-supplied tools as part of procurement security reviews. This challenge demonstrates exactly the kind of finding such a review would uncover.

</details>

## 💡 Hints

The password is not stored as plaintext. Look for byte arrays and XOR operations — a single constant key is XORed against each byte. Try `strings` first, then examine the comparison logic in a disassembler if needed.

## 🔍 Solution

The password is XOR-encoded in the binary with the key `0x42`. `strings` won't reveal it directly since no byte of the encoded password falls in the printable ASCII range after XOR.

**Option 1 — GDB (dynamic)**

Run the binary under GDB and break inside `check_credentials` after the decode loop executes. The decoded password sits in the `pw[]` buffer on the stack:

```bash
gdb ./plc_auth
(gdb) break check_credentials
(gdb) run
(gdb) next
(gdb) x/s pw
```

**Option 2 — Disassembly + offline solve (static)**

Open the binary in `objdump` or Ghidra, locate the `enc_pw` byte array and the XOR key `0x42` in the comparison logic, then invert the encoding in Python:

```python
enc_pw = [0x0F, 0x76, 0x73, 0x2C, 0x36, 0x71,
          0x2C, 0x76, 0x2C, 0x21, 0x71, 0x63]
print(''.join(chr(b ^ 0x42) for b in enc_pw))
```

Enter the recovered password to print the flag.

**Flag:** `CybICS(x0r_1s_n0t_encrypti0n_4_PLC)`


