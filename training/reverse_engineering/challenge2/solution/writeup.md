# Solution Writeup — Challenge 2: HMI Safety Override Tool

> **Authorization code:** `UNLOCK_PLC_SAFE!`
> **Flag:** `CybICS(HMI_byp4ss_PLC_s4f3ty_1nt3rl0ck)`

---

## Step 1 — Identify the Validation Logic

In Ghidra or `objdump`, locate `validate_code`. The core loop is:

```c
static const uint8_t validate_key[4]    = { 0x13, 0x37, 0x42, 0x05 };
static const uint8_t expected_code[16]  = {
    0x46, 0x7A, 0x10, 0x4D, 0x54, 0x81, 0x23, 0x5C,
    0x67, 0x7D, 0x27, 0x61, 0x5E, 0x7E, 0x15, 0x33
};

for (int i = 0; i < 16; i++) {
    uint8_t t = ((uint8_t)input[i] ^ validate_key[i % 4]) + (uint8_t)i;
    if (t != expected_code[i]) return 0;
}
```

Each byte of the input is:
1. XORed with `validate_key[i % 4]`
2. Added to `i` (mod 256)
3. Compared to `expected_code[i]`

---

## Step 2 — Invert the Algorithm

Both operations are independently reversible:

```
expected[i] == ((input[i] ^ key[i%4]) + i) mod 256
→ input[i]   = ((expected[i] - i) mod 256) ^ key[i%4]
```

```python
validate_key  = [0x13, 0x37, 0x42, 0x05]
expected_code = [0x46,0x7A,0x10,0x4D, 0x54,0x81,0x23,0x5C,
                 0x67,0x7D,0x27,0x61, 0x5E,0x7E,0x15,0x33]

code = ''.join(
    chr((expected_code[i] - i) & 0xFF ^ validate_key[i % 4])
    for i in range(16)
)
print(code)   # UNLOCK_PLC_SAFE!
```

---

## Step 3 — Confirm

```
$ ./hmi_validator <<< "UNLOCK_PLC_SAFE!"
[+] Authorization ACCEPTED
[+] Override activation key: CybICS(HMI_byp4ss_PLC_s4f3ty_1nt3rl0ck)
```

---

## Step 4 — Decode the Flag Independently

The flag is XOR-encoded with the constant `0x37`:

```python
enc_flag = [0x74,0x4E,0x55,0x7E,0x74,0x64,0x1F,0x7F,
            0x7A,0x7E,0x68,0x55,0x4E,0x47,0x03,0x44,
            0x44,0x68,0x67,0x7B,0x74,0x68,0x44,0x03,
            0x51,0x04,0x43,0x4E,0x68,0x06,0x59,0x43,
            0x04,0x45,0x5B,0x07,0x54,0x5C,0x1E]
flag = ''.join(chr(b ^ 0x37) for b in enc_flag)
print(flag)   # CybICS(HMI_byp4ss_PLC_s4f3ty_1nt3rl0ck)
```

---

## Key Takeaway

The rolling-key transformation (`XOR key[i%4] + i`) is marginally harder than
single-byte XOR but equally invertible given the binary. In real ICS deployments,
authorization codes for safety-interlock overrides must never be derived from
static data embedded in a distributed binary. Hardware security modules or
one-time codes tied to an online authorization service are required for
safety-critical parameter changes.
