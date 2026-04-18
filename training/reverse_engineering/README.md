# 🔓 Reverse Engineering — CTF Challenges

> **MITRE ATT&CK for ICS:** `Credential Access` `Collection` | [T0812 - Default Credentials](https://attack.mitre.org/techniques/T0812/) | [T0893 - Theft of Operational Information](https://attack.mitre.org/techniques/T0893/) | [T0110 - Brute Force — Password Cracking](https://attack.mitre.org/techniques/T0110/)

## 📋 Overview

Vendors and system integrators often embed credentials or authorization logic directly in compiled
binaries — sometimes with minimal obfuscation — leaving them exposed to anyone with access to the
firmware or filesystem.

Two maintenance utilities were recovered from CybICS field devices during an incident response
exercise. Both binaries are compiled for Linux/x86-64. Your task is to reverse engineer each one,
recover the embedded credentials or authorization code, and retrieve the hidden diagnostic flag.

These challenges model a realistic ICS threat scenario: hardcoded secrets in maintenance tools
are a persistent problem in OT environments, where firmware updates are rare and security audits
even rarer.

---

## 🎯 Challenges

### Challenge 1 — PLC Maintenance Auth Tool (`plc_auth`) · 150 pts · Easy

A maintenance binary found on the OpenPLC runtime filesystem.
It prompts for an operator password before revealing a diagnostic code.

**Goal:** Find the password → get the flag.

→ See [challenge1/README.md](challenge1/README.md)

---

### Challenge 2 — HMI Safety Override Tool (`hmi_validator`) · 200 pts · Medium

A safety-interlock override utility recovered from the HMI workstation.
It validates a 16-character authorization code using a keyed transformation.

**Goal:** Derive a valid authorization code → get the flag.

→ See [challenge2/README.md](challenge2/README.md)

---

## 🛠️ Getting the Binaries

Download the challenge binaries from the CTF server:

```bash
# Challenge 1
wget http://localhost/static/challenges/plc_auth/plc_auth
chmod +x plc_auth

# Challenge 2
wget http://localhost/static/challenges/hmi_validator/hmi_validator
chmod +x hmi_validator
```

---

## 🧰 Recommended Tools

| Tool        | Purpose                           |
|-------------|-----------------------------------|
| `strings`   | Quick plaintext extraction        |
| `ltrace`    | Trace library calls (strcmp etc.) |
| `strace`    | Trace syscalls                    |
| `gdb`       | Dynamic analysis / breakpoints    |
| `ghidra`    | Full decompilation (recommended)  |
| `radare2`   | Disassembly + scripting           |
| `objdump`   | Quick disassembly                 |
| `python3`   | Solve encoding math offline       |

---

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Initial Access | Default Credentials | [T0812](https://attack.mitre.org/techniques/T0812/) | Credentials embedded in vendor maintenance tools |
| Collection | Theft of Operational Information | [T0893](https://attack.mitre.org/techniques/T0893/) | Extracting configuration and diagnostic data from ICS binaries |
| Credential Access | Brute Force — Password Cracking | [T0110](https://attack.mitre.org/techniques/T0110/) | Recovering passwords through analysis or offline cracking |

**Why this matters:** Hardcoded credentials in ICS maintenance tools are a well-documented supply-chain risk. An attacker with physical or network access to a field device can extract these tools and recover credentials that grant privileged access to the wider control system — bypassing all authentication controls on the management interface.

### MITRE D3FEND — Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Software Binary Analysis | [D3-SBA](https://d3fend.mitre.org/technique/d3f:SoftwareBinaryAnalysis/) | Analyzing binaries to detect embedded secrets before deployment |
| Credential Hardening | [D3-CH](https://d3fend.mitre.org/technique/d3f:CredentialHardening/) | Eliminating hardcoded credentials from software and firmware |
| Authentication Event Monitoring | [D3-AEM](https://d3fend.mitre.org/technique/d3f:AuthenticationEventMonitoring/) | Monitoring for use of shared or vendor maintenance credentials |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------| 
| **Identification and Authentication (IA)** | IA-5 | Authenticator management — prohibiting hardcoded credentials |
| **Supply Chain Risk Management (SR)** | SR-6, SR-11 | Supplier assessment and component authenticity verification |
| **Configuration Management (CM)** | CM-7 | Least functionality — restricting maintenance tool deployment |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.3 explicitly calls out hardcoded credentials as a critical risk in OT environments. IA-5 (Authenticator Management) requires that credentials not be embedded in software, while SR-6 (Supplier Assessments) recommends auditing vendor-supplied tools for exactly this type of vulnerability before deployment. These challenges demonstrate why binary analysis of vendor tools should be part of every ICS security assessment.

</details>

---

## 🔍 Solutions

Full solution writeups are in `challengeN/solution/writeup.md`.
**Do not open these before attempting the challenge yourself.**
