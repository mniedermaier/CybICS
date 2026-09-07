#!/usr/bin/env python3
"""
Probe the segmented targets from the attack machine.
After network segmentation, the attack machine should be dropped by BOTH the
controller (OpenPLC web + Modbus) and the OPC-UA server. We try each and report.
Usage: seg_probe.py
"""
import socket, time, logging
logging.disable(logging.CRITICAL)

TARGETS = [
    ("OpenPLC web UI", "172.18.0.3", 8080),
    ("OpenPLC Modbus", "172.18.0.3", 502),
    ("OPC-UA server",  "172.18.0.5", 4840),
]

def reachable(ip, port, timeout=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(timeout)
    try:
        return s.connect_ex((ip, port)) == 0
    except Exception:
        return False
    finally:
        s.close()

print("[*] attack machine probing the segmented ICS targets ...\n")
blocked_all = True
for name, ip, port in TARGETS:
    t0 = time.time()
    ok = reachable(ip, port)
    dt = int(time.time() - t0)
    if ok:
        print(f"    {name:16} {ip}:{port:<5}  ->  REACHABLE  (segmentation missing!)")
        blocked_all = False
    else:
        print(f"    {name:16} {ip}:{port:<5}  ->  blocked (timed out after {dt}s)")
print()
if blocked_all:
    print("[+] every target drops traffic from the attack machine")
    print("[+] the attacker is isolated - reconnaissance and every earlier attack now fail")
else:
    print("[!] at least one target is still reachable - segmentation incomplete")
