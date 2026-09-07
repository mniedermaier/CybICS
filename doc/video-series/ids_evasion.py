#!/usr/bin/env python3
"""Query the CybICS IDS evasion-challenge status for the training videos.

Usage: ids_evasion.py [ids_url]
"""
import json, sys, urllib.request

base = sys.argv[1] if len(sys.argv) > 1 else "http://172.18.0.1:8443"
d = json.load(urllib.request.urlopen(base + "/api/evasion/check", timeout=5))
print("IDS evasion check")
print("-" * 48)
print(f"  Modbus writes detected : {d.get('modbus_writes_detected')}")
print(f"  new IDS alerts raised  : {d.get('new_alerts')}")
print(f"  status                 : {d.get('message','')}")
if d.get("flag"):
    print(f"  flag                   : {d['flag']}")
