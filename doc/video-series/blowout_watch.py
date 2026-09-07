#!/usr/bin/env python3
"""
Watch the CybICS safety system while the overpressure attack drives the tank up.
Polls only the blow-out valve sensor (register 1134) until it trips - a single
read per poll keeps out of the way of the attack's own Modbus traffic - then
reports the unsafe state. Exits as soon as the blow-out is detected (or TIMEOUT).
Usage: blowout_watch.py [PLC_IP] [TIMEOUT_SECONDS]
"""
import sys, time, logging
from pymodbus.client import ModbusTcpClient
for _n in ('pymodbus','pymodbus.logging','pymodbus.transaction','pymodbus.client'):
    logging.getLogger(_n).setLevel(logging.CRITICAL)
logging.disable(logging.ERROR)

IP = sys.argv[1] if len(sys.argv) > 1 else "172.18.0.3"
TIMEOUT = int(sys.argv[2]) if len(sys.argv) > 2 else 120

c = ModbusTcpClient(IP, port=502, timeout=3, retries=2); c.connect()

def _fresh():
    cl = ModbusTcpClient(IP, port=502, timeout=3, retries=2)
    cl.connect(); return cl

def rd(a):
    global c
    try:
        r = c.read_holding_registers(a, count=1)
        if r.isError():
            raise IOError("modbus error")
        return r.registers[0]
    except Exception:
        try:
            c.close(); c = _fresh()
        except Exception:
            pass
        return -1

print("[*] monitoring the safety system on the OpenPLC controller")
print("[*] blow-out valve sensor = register 1134   (the relief valve opens above 220 bar)\n")
t0 = time.time()
tripped = False
last = -2
while time.time() - t0 < TIMEOUT:
    bo = rd(1134)
    el = int(time.time() - t0)
    if bo == 1:
        ss = rd(1132)
        print(f"\n*** BLOW-OUT *** the mechanical relief valve has opened  (boSen = 1)")
        print(f"    system-operational flag  sysSen = {ss}   (0 = the plant has tripped out)")
        print("\n[+] the process has been forced into an unsafe state - impact achieved")
        tripped = True
        break
    if bo == 0:
        print(f"    t={el:3}s   pressure climbing ...   blow-out valve still closed (boSen=0)", flush=True)
    time.sleep(3)
c.close()
if not tripped:
    print("[!] timeout reached without a blow-out")
