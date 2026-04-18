# 🛡️ HMI Safety Override Tool

> **MITRE ATT&CK for ICS:** `Credential Access` `Impair Process Control` | [T0893 - Theft of Operational Information](https://attack.mitre.org/techniques/T0893/) | [T0110 - Brute Force — Password Cracking](https://attack.mitre.org/techniques/T0110/) | [T0836 - Modify Parameter](https://attack.mitre.org/techniques/T0836/)

## 📋 Overview

During forensic analysis of the CybICS HMI workstation, investigators found a safety-interlock
override utility. This tool allows authorized engineers to modify the High Pressure Tank (HPT)
and Gas Storage Tank (GST) safety thresholds — configuration changes that could cause
catastrophic overpressure events if misused.

Access is gated by a 16-character authorization code. The validation algorithm is more complex
than a simple password comparison: the code is derived from the plant's configuration key using
a keyed byte transformation, making each installation's code theoretically unique.

```
############################################################
#  CybICS HMI Safety Override Tool  v2.4.1                #
#  High Pressure Tank Interlock Configuration              #
#  ** AUTHORIZED PERSONNEL ONLY **                        #
############################################################

  WARNING: This tool modifies safety-critical parameters.
  Unauthorized use may cause HPT overpressure events.
  A blowout valve activation releases TOXIC GAS.

------------------------------------------------------------
  HPT Safe Range  : 60 - 90 bar
  GST Safe Range  : 60 - 240 bar
  Blowout trigger : > 220 bar
------------------------------------------------------------

Enter 16-character authorization code: _
```

This models a realistic and dangerous ICS scenario: safety-interlock bypass tools with
authorization logic embedded in client-side binaries provide only the illusion of access
control. Anyone able to reverse engineer the validation algorithm can compute a valid code
without knowing the plant's configuration key.

## 🎯 Task

Reverse engineer `hmi_validator` to understand the authorization algorithm, derive a valid
16-character code, and retrieve the override activation key (flag).

The flag has the format `CybICS(flag)`.

1. Download the binary from the CTF server and make it executable
2. Run it to understand the interface
3. Perform static analysis to locate the validation function — use `strings` first, then a disassembler
4. Identify the key array and expected-values array in the binary, then reverse the transformation to compute a valid 16-character code
5. Enter the derived code to obtain the flag

```bash
wget http://localhost/static/challenges/hmi_validator/hmi_validator
chmod +x hmi_validator
./hmi_validator

# Static recon
file hmi_validator
strings hmi_validator
objdump -d hmi_validator | grep -A 40 'validate'
```

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Credential Access | Brute Force — Password Cracking | [T0110](https://attack.mitre.org/techniques/T0110/) | Recovering the authorization code by reversing the validation algorithm offline |
| Collection | Theft of Operational Information | [T0893](https://attack.mitre.org/techniques/T0893/) | Extracting safety threshold configuration from the binary |
| Impair Process Control | Modify Parameter | [T0836](https://attack.mitre.org/techniques/T0836/) | Using the recovered code to modify HPT/GST safety thresholds |

**Why this matters:** Client-side authorization logic is fundamentally broken as a security boundary. When the validation algorithm and its keys are embedded in a binary that is distributed to field devices, any attacker with access to that binary can compute a valid code. Safety interlock override tools are particularly high-value targets: bypassing them can directly cause physical damage, hazardous material release, or injury. The 2017 TRITON/TRISIS attack against Schneider Electric safety instrumented systems demonstrated exactly how targeting safety systems can amplify the impact of an ICS compromise.

### MITRE D3FEND — Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Software Binary Analysis | [D3-SBA](https://d3fend.mitre.org/technique/d3f:SoftwareBinaryAnalysis/) | Auditing safety tool binaries to detect client-side-only validation |
| Credential Hardening | [D3-CH](https://d3fend.mitre.org/technique/d3f:CredentialHardening/) | Moving authorization validation to a trusted server-side component |
| Authentication Event Monitoring | [D3-AEM](https://d3fend.mitre.org/technique/d3f:AuthenticationEventMonitoring/) | Logging and alerting on all safety override activations |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Identification and Authentication (IA)** | IA-2, IA-5 | Multi-factor authentication and proper authenticator management for safety-critical operations |
| **System and Communications Protection (SC)** | SC-28 | Protection of information at rest — preventing extraction of keys from deployed binaries |
| **Supply Chain Risk Management (SR)** | SR-6 | Supplier assessments — verifying that safety tools implement server-side authorization |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.9 addresses the specific challenges of securing safety instrumented systems. IA-2 requires multi-factor authentication for privileged operations — a standard that client-side binary validation cannot meet by design. SC-28 (Protection of Information at Rest) recommends key storage practices that prevent offline extraction of secrets, and SR-6 requires vendors to demonstrate that safety tools do not expose authorization logic in distributed binaries.

</details>

## 💡 Hints

There is a 4-byte key array and a 16-byte expected-values array in the binary. Find the validation loop in a disassembler and understand what transformation maps each input byte to its expected value — then invert that transformation to solve for each byte independently.

## 🔍 Solution

The validation is not a simple comparison — each input byte undergoes a keyed transformation before being checked against a pre-computed expected array. There is no library call to intercept, so the solution requires understanding the algorithm from the disassembly.

**Step 1 — Find the algorithm**

Disassemble `validate_code` in `objdump` or Ghidra:

```bash
objdump -d hmi_validator | grep -A 60 '<validate_code>'
```

The logic in the validation loop is:

```c
((input[i] ^ validate_key[i % 4]) + i) & 0xFF == expected_code[i]
```

**Step 2 — Extract the arrays**

From the disassembly, read out:

```
validate_key[]  = { 0x13, 0x37, 0x42, 0x05 }
expected_code[] = { 0x46, 0x7A, 0x10, 0x4D, 0x54, 0x81, 0x23, 0x5C,
                    0x67, 0x7D, 0x27, 0x61, 0x5E, 0x7E, 0x15, 0x33 }
```

**Step 3 — Invert the transformation**

XOR is its own inverse; subtraction undoes the addition. Solve for each byte independently:

```python
key      = [0x13, 0x37, 0x42, 0x05]
expected = [0x46, 0x7A, 0x10, 0x4D, 0x54, 0x81, 0x23, 0x5C,
            0x67, 0x7D, 0x27, 0x61, 0x5E, 0x7E, 0x15, 0x33]

code = ''.join(chr(((expected[i] - i) & 0xFF) ^ key[i % 4]) for i in range(16))
print(code)
```

Enter the resulting 16-character code to unlock the override key.

**Flag:** `CybICS(HMI_byp4ss_PLC_s4f3ty_1nt3rl0ck)`