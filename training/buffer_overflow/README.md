# Stack Smashing the PLC Diagnostics Service

> **MITRE ATT&CK for ICS:** `Execution` | [T0807 - Command-Line Interface](https://attack.mitre.org/techniques/T0807/) | [T0862 - Supply Chain Compromise](https://attack.mitre.org/techniques/T0862/)

## Overview

A forgotten **internal maintenance binary** (`plc_diagnostics`) has been discovered on the attack machine. It was written years ago by a field engineer and never audited for security. The binary contains a classic **stack-based buffer overflow** — user input is copied into a fixed-size stack buffer without any length check, allowing an attacker to overwrite the return address and redirect execution.

This technique is called **ret2win**: you overflow the buffer until you reach the return address on the stack, then replace it with the address of a hidden function that prints the flag.

```
Stack frame of run_diagnostic():

  [ cmd_buffer (64 bytes) ][ saved RBP (8 bytes) ][ return address (8 bytes) ]
   ←────── overflow with padding ───────────────────→ ← overwrite with target →

Goal: replace the return address with the address of maintenance_shell()
```

## Prerequisites

- Access to the attack machine (`http://localhost:6081/vnc.html`) or the webshell
- The challenge files are located at `/opt/challenges/buffer_overflow/` on the attack machine
- Tools required: `gcc`, `pwndbg`, `python3`, `nm`, `checksec`

## Task

Analyse the binary, find the vulnerability, determine the exact overflow offset, and redirect execution to the hidden `maintenance_shell()` function to capture the flag.

The flag has the format `CybICS(flag)`.

---

### Phase 1: Setup & Reconnaissance

- Copy the challenge files to your working directory and compile the binary:

```bash
cp -r /opt/challenges/buffer_overflow ~/Desktop/bof_challenge
cd ~/Desktop/bof_challenge
make
```

- Run the binary normally to understand its behaviour:

```bash
./plc_diagnostics
```

   Enter an input when prompted and observe the output.

- Check what security protections are active:

   ```bash
   checksec --file=./plc_diagnostics
   ```

   You should see: **No canary**, **No PIE**, **NX disabled** — ideal conditions for a stack overflow.


   <details>
   <summary>Binary Compiler Flags</summary>

   <ul style="padding-left: 40px;">
    <li><code>-fno-stack-protector</code> → disables stack canaries</li>
    <li><code>-no-pie</code> → disables PIE, resulting in fixed addresses</li>
    <li><code>-z execstack</code> → marks the stack as executable</li>
    <li>
   <a href="https://caiorss.github.io/C-Cpp-Notes/compiler-flags-options.html">
      Learn more about C compiler flags
   </a>
    </li>
  </ul>

   </details>


- List all function symbols and their addresses:

   ```bash
   nm ./plc_diagnostics | grep -E "maintenance|run_diag|main"
   ```

   **Write down the address of `maintenance_shell`** — this is your target jump address.

- Read the source code and find the vulnerability:

   ```bash
   cat plc_diagnostics.c
   ```

   What makes this binary exploitable?

   <details>
   <summary>Hint</summary>

   <ul style="padding-left: 40px;">
      <li>C has some unsafe functions. Look for one.</li> 
      <li><a href="https://dwheeler.com/secure-programs/Secure-Programs-HOWTO/dangers-c.html">
      Learn more about unsafe functions
   </a></li>
  </ul>

   </details>

   <details>
   <summary>Solution</summary>

   <div style="padding: 10px;">
   Look for the unsafe `strcpy()` call inside `run_diagnostic()`. Unlike `strncpy()`, `strcpy()` copies until it hits a null byte with no regard for the destination buffer size.
   </div>

   </details>


### Phase 2: Find the Overflow Offset

You need to know exactly how many bytes of padding are required before you reach the return address on the stack.

- Open the binary in pwndbg:

   ```bash
   pwndbg ./plc_diagnostics
   ```

- Generate a cyclic pattern with pwndbg. Every 8-byte subsequence in this pattern is unique, which lets you pinpoint the exact offset after a crash:

   ```
   pwndbg> cyclic <charLength>
   ```

   Try different input lengths.

   <details>
   <summary>Hint</summary>

   <div style="padding: 10px;">
   Try it with a length of 100
   </div>

   </details>



- Run the program and paste the full character pattern when prompted:

   ```
   pwndbg> run
   ```

   If the cyclic pattern is long enough, the program will crash with a **Segmentation Fault**.

- If a **Segmentation Fault** is triggered, find the unique cyclic pattern value that was written as the return address on the stack.

   <details>
   <summary>Hint</summary>

   <div style="padding: 10px;">
   Try to find a command in pwndbg that allows you to read the stack value that the stack pointer (RSP) points to.
   </div>

   </details>

   <details>
   <summary>Solution</summary>

   <div style="padding: 10px;">
   Use the following command to extract the pattern that was written to the return address on the stack:
   </div>

   ```bash
   x/1gx $rsp
   ```

   </details>

- If the cyclic pattern is found, try to get the offset for the return address which cyclic

   <details>
   <summary>Solution</summary>

   <div style="padding: 10px;">
   Use following command to extract the offset of the return address with the previous found return address pattern.
   </div>

   ```bash
      cyclic -l <unique_pattern>
   ```
   
   <div style="padding: 10px;">
   The result is your offset — it should be **72** (64 bytes for `cmd_buffer` + 8 bytes for saved RBP on x86-64).
   </div>

   </details>


### Phase 3: Craft and Send the Exploit

Use the standalone exploit script `exploit.py` to obtain the flag:

   Update `<MAINTENANCE_ADDR>` with the real address and `<OFFSET>` with the offset, then run:

   ```bash
   python3 exploit.py
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
