#!/usr/bin/env python3
"""
CTF setup helper – generate the initial MAC for a firmware binary.

Usage:
    python3 generate_mac.py <firmware.bin> <key_file>

The resulting hex string is the MAC that update clients will verify.
Participants receive the firmware binary and this MAC as their starting
artefacts and must perform a Length Extension Attack to forge a valid
MAC for a modified firmware.
"""

import hashlib
import sys


def generate_mac(firmware_path: str, key_path: str) -> str:
    """Return MD5(secret || firmware) as a hex string."""
    with open(firmware_path, "rb") as f:
        firmware = f.read()
    with open(key_path, "rb") as f:
        secret = f.read()
    return hashlib.md5(secret + firmware).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <firmware.bin> <key_file>", file=sys.stderr)
        sys.exit(1)
    print(generate_mac(sys.argv[1], sys.argv[2]))
