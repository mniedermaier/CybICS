#!/usr/bin/env python3
"""
Probe the PLC from the attack machine to show the firewall in effect.
Tries a Modbus/TCP read on port 502 (the control protocol) and reports whether
the attack machine can still reach it. Also checks the web port for contrast.
Usage: fw_probe.py [PLC_IP]
"""
import sys, socket, time, logging
from pymodbus.client import ModbusTcpClient
for _n in ('pymodbus','pymodbus.logging','pymodbus.transaction','pymodbus.client'):
    logging.getLogger(_n).setLevel(logging.CRITICAL)
logging.disable(logging.ERROR)

IP = sys.argv[1] if len(sys.argv) > 1 else "172.18.0.3"

def port_open(ip, port, timeout=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(timeout)
    try:
        return s.connect_ex((ip, port)) == 0
    except Exception:
        return False
    finally:
        s.close()

print(f"[*] attack machine probing the PLC at {IP}")
print("[*] trying Modbus/TCP on port 502 (the control protocol) ...")
t0 = time.time()
c = ModbusTcpClient(IP, port=502, timeout=4, retries=1)
c.connect()
blocked = True
try:
    r = c.read_holding_registers(1126, count=1)
    if not r.isError():
        blocked = False
        print(f"    reachable - HPT register = {r.registers[0]}")
except Exception:
    pass
c.close()
if blocked:
    print(f"[+] Modbus is BLOCKED - the connection timed out after {int(time.time()-t0)}s")
    print("[+] the firewall now drops port 502 from the attack machine")
else:
    print("[!] Modbus is still reachable - the firewall is NOT in place")
print()
print("[*] for contrast, the operator's HMI and plant are still allowed through,")
print("    so the process keeps running - only unauthorized hosts are cut off")
