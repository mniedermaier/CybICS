#!/usr/bin/env python3
"""Pretty-print the CybICS IDS alert buffer for the training videos.

Usage: ids_alerts.py [ids_url]   (default http://172.18.0.1:8443)
"""
import json, sys, urllib.request

base = sys.argv[1] if len(sys.argv) > 1 else "http://172.18.0.1:8443"
data = json.load(urllib.request.urlopen(base + "/api/alerts", timeout=5))
alerts = data.get("alerts", [])
if not alerts:
    print("No alerts in the IDS buffer.")
    sys.exit(0)
print(f"IDS alert buffer  ({data.get('total', len(alerts))} alert(s))")
print("-" * 64)
for a in alerts:
    print(f"[{a.get('severity','?').upper():8}] {a.get('rule','?'):16} "
          f"{a.get('src','?')} -> {a.get('dst','?')}   {a.get('mitre','')}")
    print(f"           {a.get('message','')}")
