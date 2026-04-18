# Solution Writeup — Challenge 1: PLC Maintenance Auth Tool

> **Password:** `M41nt3n4nc3!`
> **Flag:** `CybICS(x0r_1s_n0t_encrypti0n_4_PLC)`

---

## Step 1 — Quick Recon with `strings`

```
$ strings plc_auth
...
Enter operator password:
[-] Authentication FAILED. Invalid operator code.
[+] Maintenance mode ACTIVE
[+] Vendor diagnostic code: %s
...
```

No plaintext password visible — the credential is obfuscated.

---

## Step 2 — Static Analysis with Ghidra / `objdump`

Disassemble `check_credentials`. You will find:

```c
static const uint8_t enc_pw[12] = {
    0x0F, 0x76, 0x73, 0x2C, 0x36, 0x71,
    0x2C, 0x76, 0x2C, 0x21, 0x71, 0x63
};

// Inside check_credentials():
for (int i = 0; i < 12; i++) {
    pw[i] = enc_pw[i] ^ 0x42;   // key = 0x42
}
return strncmp(input, pw, 13) == 0;
```

The password is XOR-encoded with the constant key `0x42`.

---

## Step 3 — Decode the Password

```python
enc_pw = [0x0F,0x76,0x73,0x2C,0x36,0x71,0x2C,0x76,0x2C,0x21,0x71,0x63]
pw = ''.join(chr(b ^ 0x42) for b in enc_pw)
print(pw)   # M41nt3n4nc3!
```

---

## Step 4 — Confirm with `ltrace`

```
$ ltrace ./plc_auth <<< "M41nt3n4nc3!"
strncmp("M41nt3n4nc3!", "M41nt3n4nc3!", 13) = 0
```

---

## Step 5 — Decode the Flag

The `print_flag` function decodes `enc_flag` with the same key `0x42`:

```python
enc_flag = [0x01,0x3B,0x20,0x0B,0x01,0x11,0x6A,0x3A,
            0x72,0x30,0x1D,0x73,0x31,0x1D,0x2C,0x72,
            0x36,0x1D,0x27,0x2C,0x21,0x30,0x3B,0x32,
            0x36,0x2B,0x72,0x2C,0x1D,0x76,0x1D,0x12,
            0x0E,0x01,0x42]
flag = ''.join(chr(b ^ 0x42) for b in enc_flag)
print(flag)   # CybICS(x0r_1s_n0t_encrypti0n_4_PLC)
```

---

## Key Takeaway

Single-byte XOR with a fixed key is trivially reversible by inspection.
In a real ICS incident, credentials stored this way in vendor maintenance tools
represent a critical vulnerability — the same binary distributed to all
installations shares the same key.
