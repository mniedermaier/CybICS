# Flash Dump Analysis

> **MITRE ATT&CK for ICS:** `Collection` | [T0893 - Data from Local System](https://attack.mitre.org/techniques/T0893/) | [T0811 - Data from Information Repositories](https://attack.mitre.org/techniques/T0811/)

## Overview

During a physical security assessment of an industrial controller, you gained access to the device's **debug port (JTAG/SWD)**. Using this access you dumped the entire flash memory of the device.

The manufacturer claims the firmware is protected by full-disk encryption. Your goal: **prove this protection is useless**, because the device must boot without user input — meaning the decryption key has to be stored unencrypted on the device itself.

You are given:
- `flash_dump.bin` — raw flash memory dump (download below)

The flag is hidden inside the encrypted firmware partition.

---

## Task

Analyse the flash dump, find and reverse-engineer the unlock binary embedded in it, extract the encryption key, and decrypt the firmware partition to read the flag.

---

### Phase 1: Reconnaissance

Download `flash_dump.bin` and run `binwalk` to get an overview of what is inside:


```bash
binwalk flash_dump.bin
```

You should see two interesting structures at specific offsets. Note them down — you will need them in the next phases.

<details>
<summary>Hint</summary>

Look for a **Linux EXT filesystem** and a **LUKS encrypted container**. Ignore false-positive hits from binwalk.

</details>

---

### Phase 2: Extract and Mount the Filesystem

Create a loop device for the EXT2 filesystem region and mount it read-only:

```bash
sudo losetup -f --show -o $((0x10000)) flash_dump.bin
# note the loop device, e.g. /dev/loop0

sudo mkdir -p /mnt/flash_ext2
sudo mount -o ro /dev/loop0 /mnt/flash_ext2
```

Browse the filesystem and find the unlock binary:

```bash
sudo tree -a /mnt/flash_ext2
cp /mnt/flash_ext2/usr/sbin/unlock_firmware ./unlock_firmware
```

Cleanup when done:

```bash
sudo umount /mnt/flash_ext2
sudo losetup -d /dev/loop0
```

---

### Phase 3: Reverse Engineer the Binary

Analyse `unlock_firmware` to find where it reads the decryption key from.

Start with a quick inspection:

```bash
strings unlock_firmware
```

What device path does it reference? What does it call to unlock the partition?

Now open it in **Ghidra** (or `objdump -d unlock_firmware`) and find the `main()` function. Look for the `lseek()` call — its second argument is the byte offset where the key is stored in the flash.

<details>
<summary>Hint</summary>

The binary seeks to a constant called `BASE_INIT` before reading 32 bytes. Find the numeric value of this constant in the disassembly — it is the second argument passed to `lseek()`.

</details>

<details>
<summary>Solution</summary>

The `lseek()` call uses the immediate value `0x80` (decimal 128) as the seek offset. This means the 32-byte LUKS key is stored at byte offset `0x80` in the flash dump.

</details>

---

### Phase 4: Extract the Key

Use `dd` to extract the 32-byte key from the dump at the offset you found:

```bash
dd if=flash_dump.bin bs=1 skip=$((0x80)) count=32 of=key.bin
xxd key.bin    # verify it looks like 32 bytes of random data
```

---

### Phase 5: Open the LUKS Container

Create a loop device for the LUKS region and open it with the extracted key:

```bash
sudo losetup -f --show -o $((0x200000)) flash_dump.bin
# note the loop device, e.g. /dev/loop1

sudo cryptsetup open --type luks2 --key-file key.bin /dev/loop1 flash_challenge_luks
```

Mount the decrypted container and read the flag:

```bash
sudo mkdir -p /mnt/flash_luks
sudo mount /dev/mapper/flash_challenge_luks /mnt/flash_luks

cat /mnt/flash_luks/firmware/flag.txt
```

---

### Cleanup

```bash
sudo umount /mnt/flash_luks
sudo cryptsetup close flash_challenge_luks
sudo losetup -d /dev/loop1
rm key.bin
```

---

## 🛡️ Security Framework References

<details>
<summary>Click to expand</summary>

### MITRE ATT&CK for ICS — Techniques Applied

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Collection | Data from Local System | [T0893](https://attack.mitre.org/techniques/T0893/) | Reading key material directly from device storage |
| Collection | Data from Information Repositories | [T0811](https://attack.mitre.org/techniques/T0811/) | Extracting firmware from encrypted partition |
| Initial Access | Exploit Public-Facing Application | [T0819](https://attack.mitre.org/techniques/T0819/) | Debug port access to dump flash memory |

### MITRE CWE — Weaknesses Exploited

| CWE | Name | Description |
|-----|------|-------------|
| [CWE-321](https://cwe.mitre.org/data/definitions/321.html) | Use of Hard-coded Cryptographic Key | Decryption key stored in plaintext at a fixed offset |
| [CWE-312](https://cwe.mitre.org/data/definitions/312.html) | Cleartext Storage of Sensitive Information | Key is readable by anyone with physical flash access |
| [CWE-693](https://cwe.mitre.org/data/definitions/693.html) | Protection Mechanism Failure | Encryption provides no real security when key is co-located |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------| 
| **System and Communications Protection (SC)** | SC-12, SC-28 | Cryptographic key management, protection of data at rest |
| **Physical and Environmental Protection (PE)** | PE-3 | Physical access controls to prevent debug port access |
| **Configuration Management (CM)** | CM-6 | Secure configuration — debug interfaces should be disabled in production |

**Why this matters in ICS:** NIST 800-82r3 Section 6.2 highlights that embedded ICS devices frequently store credentials and keys in unprotected flash memory. SC-12 requires proper key management — keys must never be stored adjacent to the data they protect without additional protection mechanisms such as a TPM or secure enclave.

</details>