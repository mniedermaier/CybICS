#!/usr/bin/env python3
"""Pretty-print the CybICS IDS alert buffer for the training videos.

Usage: ids_alerts.py [ids_url] [--flag]
  --flag  also query the intrusion-detection flag endpoint (/api/flag)
"""
import json, sys, urllib.request

args = [a for a in sys.argv[1:] if not a.startswith("-")]
show_flag = "--flag" in sys.argv
base = args[0] if args else "http://172.18.0.1:8443"


def get(path):
    return json.load(urllib.request.urlopen(base + path, timeout=5))


data = get("/api/alerts")
alerts = data.get("alerts", [])
print(f"IDS alert buffer  ({data.get('total', len(alerts))} alert(s))")
print("-" * 64)
if not alerts:
    print("No alerts in the IDS buffer.")
for a in alerts:
    print(f"[{a.get('severity','?').upper():8}] {a.get('rule','?'):18} "
          f"{a.get('src','?')} -> {a.get('dst','?')}   {a.get('mitre','')}")
    print(f"           {a.get('message','')}")

if show_flag:
    print("-" * 64)
    f = get("/api/flag")
    print("Intrusion status:", f.get("message", ""))
    if f.get("flag"):
        print("Flag unlocked   :", f["flag"])
