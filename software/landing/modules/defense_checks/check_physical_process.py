"""
Challenge check: the student drove the plant into a blow-out (physical_process).

The blow-out valve on the high-pressure tank (HPT) opens above 220 bar and
stays open until the tank is back under 200 (thread_physical in
software/stm32/src/main.c, mirrored in hwio-virtual). The plant model writes
its state to OpenPLC every cycle: HPT pressure to holding register 1126, the
blow-out sensor to 1134. On a board, hwio-raspberry writes the same two
registers from the real sensors.

Verify passes while the blow-out is happening: every one of SAMPLES reads,
spread over about two seconds, must show the valve open with the tank above
200 bar. In manual mode with the system valve shut, the compressor on and the
supply refilling the storage tank, the compressor fills faster than the valve
vents, so the state lasts as long as the student keeps it; a single forged
Modbus write is overwritten by the plant model within one cycle.

The flag used to be hidden text on the FUXA views, shown while boSen = 1.
FUXA hands its whole project to anyone without a login (GET /api/project),
so the text was readable without touching the plant; it is now "BLOW-OUT"
and the flag comes from this check.

The registers are read over Modbus from OpenPLC. If port 502 is closed to the
board (a firewall defence challenge allows only the HMI and the plant), the
same two values are read through FUXA's /api/getTagValue, i.e. what the
operator's screen shows. Both routes only read.
"""
import time

import requests

from utils.config import PLC_HOST, PLC_MODBUS_PORT
from utils.logger import logger

HPT_REGISTER = 1126        # %MW102 hpt
BLOWOUT_REGISTER = 1134    # %MW110 boSen
RELEASE_PRESSURE = 200     # the valve stays open while the tank is above this
SAMPLES = 3
SAMPLE_GAP = 1.0           # seconds between reads

FUXA_URL = "http://172.18.0.4:1881"
# FUXA tag IDs in software/FUXA/fuxa-project.json (HPT: 1127, boSen: 1135, 1-based).
FUXA_HPT_TAG = "t_e76df10e-a85c4674"
FUXA_BLOWOUT_TAG = "t_df0b8f89-09994ce8"


def _read_modbus():
    """Read function returning (hpt, blowout) over Modbus, or None if 502 is unreachable."""
    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient(PLC_HOST, port=PLC_MODBUS_PORT, timeout=2, retries=0)
    try:
        if not client.connect():
            return None
    except Exception:  # pragma: no cover - pymodbus raises several types here
        return None

    def read():
        result = client.read_holding_registers(HPT_REGISTER, count=BLOWOUT_REGISTER - HPT_REGISTER + 1,
                                               slave=1)
        if result.isError():
            raise ConnectionError("Modbus error response")
        return result.registers[0], result.registers[-1]
    read.close = client.close
    return read


def _read_fuxa():
    def read():
        resp = requests.get(f"{FUXA_URL}/api/getTagValue",
                            params={"ids": f'["{FUXA_HPT_TAG}","{FUXA_BLOWOUT_TAG}"]'}, timeout=5)
        values = {v.get("id"): v.get("value") for v in resp.json()}
        return int(float(values[FUXA_HPT_TAG])), int(float(values[FUXA_BLOWOUT_TAG]))
    return read


def sample(read, samples=SAMPLES, gap=SAMPLE_GAP):
    """[(hpt, blowout), ...] from read(), samples reads gap seconds apart."""
    readings = []
    for i in range(samples):
        if i:
            time.sleep(gap)
        readings.append(read())
    return readings


def judge(readings, route):
    """verify() result for a list of (hpt, blowout) readings."""
    blowing = [bool(bo) and hpt > RELEASE_PRESSURE for hpt, bo in readings]
    peak = max(hpt for hpt, _ in readings)
    checks = [{
        "name": "Plant state read",
        "passed": True,
        "detail": f"{len(readings)} reads through {route}, highest HPT pressure {peak} bar",
    }, {
        "name": "Blow-out valve open",
        "passed": all(blowing),
        "detail": "The HPT blow-out valve was open on every read" if all(blowing)
        else ("The blow-out valve closed during the reads: the pressure is falling back"
              if any(blowing) else "The blow-out valve is closed"),
    }]
    if all(blowing):
        return {"success": True, "checks": checks,
                "message": "The high-pressure tank is blowing out. Every step you took was an "
                           "allowed operator action; the damage came from the combination."}
    return {"success": False, "checks": checks,
            "message": "No blow-out right now. Click Verify while the HMI shows BLOW-OUT: "
                       "keep the plant in that state until the check has passed."}


def verify():
    readings, route = None, None
    read = _read_modbus()
    if read is not None:
        try:
            readings, route = sample(read), "Modbus (OpenPLC)"
        except Exception as e:  # pymodbus raises its own exception types
            logger.debug(f"physical_process: Modbus read failed ({e}), asking FUXA")
        finally:
            read.close()
    if readings is None:
        try:
            readings, route = sample(_read_fuxa()), "the FUXA HMI"
        except (requests.exceptions.RequestException, KeyError, TypeError, ValueError):
            return {"success": False, "message": "Cannot read the plant state.",
                    "checks": [{"name": "Plant state read", "passed": False,
                                "detail": "Neither OpenPLC (Modbus 502) nor FUXA gave the "
                                          "HPT pressure and blow-out sensor"}]}
    return judge(readings, route)
