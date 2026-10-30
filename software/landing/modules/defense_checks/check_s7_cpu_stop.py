"""
CTF check: an S7comm CPU STOP that the PLC accepts and the plant ignores.

OpenPLC's S7comm server (Snap7) understands the PLC STOP job (function 0x29)
and PLC Control (0x28, warm or cold restart). It acknowledges a STOP and
reports the CPU as stopped in its system status list (SZL 0x0424), but
nothing in OpenPLC reads that status: the scan cycle keeps running, and so
does the plant. The challenge asks the player to send the STOP, see the PLC
claim it stopped, and prove from the plant that it did not (MITRE ATT&CK for
ICS T0858 Change Operating Mode).

Three things must hold when Verify is clicked:

* the newest S7comm CPU control request to OpenPLC on port 102, as the IDS
  logged it (rule s7_cpu_control), is a STOP, logged within the last
  STOP_WINDOW seconds. A later warm or cold restart cancels it, and the
  window keeps a STOP somebody forgot to undo from handing the flag to
  everyone who comes after;
* the CPU status list read over S7comm says STOP, so the request landed.
  Nothing else on the plant network puts Snap7 into STOP;
* the PLC's scan cycle still runs: the heartbeat output %QX0.0 changes
  within HEARTBEAT_SAMPLE seconds. It is read over Modbus (coil 0), which
  raises no IDS alert, and over S7comm (process outputs, byte 0) when port
  502 is firewalled.

The status read and the S7 fallback raise an s7_enumeration alert from the
board itself (172.18.0.1); they are reads and never touch the CPU's mode.
"""
import socket
import time
from datetime import datetime

import requests

from modules.defense_checks.check_s7_sidedoor import (
    IDS_URL, S7_PORT, WRITE_WINDOW, _age_seconds, _recv_tpkt)
from utils.config import PLC_HOST, PLC_MODBUS_PORT
from utils.logger import logger

STOP_WINDOW = WRITE_WINDOW     # seconds an S7 STOP stays valid for verify (5 minutes)
HEARTBEAT_SAMPLE = 3.0         # the heartbeat toggles about once a second
HEARTBEAT_COIL = 0             # %QX0.0
CPU_RUN, CPU_STOP = 0x08, 0x04

_COTP_CR = bytes.fromhex("0300001611e00000000100c1020100c2020101c0010a")
_SETUP = bytes.fromhex("0300001902f08032010000000100080000f0000001000101e0")
# Userdata request: CPU functions (group 4), read SZL (subfunction 1),
# SZL-ID 0x0424 index 0 -- the CPU's operating mode and its last change.
_READ_SZL_0424 = bytes.fromhex(
    "0300002102f080" "32070000000200080008" "0001120411440100" "ff09000404240000")
# Read Var job: one byte of the process image of outputs (area 0x82), byte 0.
_READ_PA0 = bytes.fromhex(
    "0300001f02f080" "320100000003000e0000" "0401120a10020001000082000000")


def _newest_cpu_control():
    """(passed, detail, error check row or None) from the IDS alert buffer."""
    try:
        alerts = requests.get(f"{IDS_URL}/api/alerts", timeout=5).json().get("alerts", [])
        status = requests.get(f"{IDS_URL}/api/status", timeout=5).json()
    except (requests.exceptions.RequestException, ValueError):
        return False, None, {"name": "IDS reachable", "passed": False,
                             "detail": "Cannot reach the IDS at port 8443. It has to watch "
                                       "the network to confirm the S7comm STOP."}
    try:
        now = datetime.fromisoformat(status.get("now", ""))
    except (TypeError, ValueError):
        now = datetime.now()
    for alert in sorted(alerts, key=lambda a: a.get("id", 0), reverse=True):
        if alert.get("rule") != "s7_cpu_control" or alert.get("dst") != PLC_HOST \
                or alert.get("dport") != S7_PORT:
            continue
        source = alert.get("src")
        action = alert.get("s7_control")
        if action != "stop":
            if action in ("warm_start", "cold_start"):
                return False, (f"The newest S7comm CPU control request (from {source}) "
                               "restarted the CPU. Send the STOP again and verify "
                               "before you restart it."), None
            continue   # some other PI service: neither stops nor starts the CPU
        age = _age_seconds(alert.get("timestamp"), now)
        if age is None or age > STOP_WINDOW:
            return False, (f"The newest S7comm STOP (from {source}) is older than "
                           f"{STOP_WINDOW // 60} minutes. Send it again and verify "
                           "right after."), None
        return True, (f"The IDS saw {source} send a PLC STOP to the S7comm server "
                      f"on {PLC_HOST}:{S7_PORT}."), None
    if not status.get("active", False):
        return False, None, {"name": "IDS capturing", "passed": False,
                             "detail": "The IDS is not capturing, so it cannot see your "
                                       "STOP. Start it on its dashboard (port 8443) and "
                                       "send the STOP again."}
    return False, ("No S7comm STOP to the PLC seen yet. Stopping the plant with the "
                   "stop flag or the HMI is a different thing and does not count."), None


def _s7_session():
    sock = socket.create_connection((PLC_HOST, S7_PORT), timeout=3)
    try:
        sock.sendall(_COTP_CR)
        _recv_tpkt(sock)
        sock.sendall(_SETUP)
        _recv_tpkt(sock)
    except Exception:
        sock.close()
        raise
    return sock


def read_cpu_mode():
    """The mode byte of SZL 0x0424 (0x08 RUN, 0x04 STOP), read over S7comm."""
    with _s7_session() as sock:
        sock.sendall(_READ_SZL_0424)
        return mode_from_reply(_recv_tpkt(sock))


def mode_from_reply(reply):
    """The mode byte from a TPKT frame answering _READ_SZL_0424."""
    s7 = reply[7:]                                    # past TPKT (4) and COTP (3)
    if len(s7) < 10 or s7[0] != 0x32 or s7[1] != 0x07:
        raise ConnectionError("not an S7 userdata reply")
    par_len = int.from_bytes(s7[6:8], "big")
    data = s7[10 + par_len:]
    # return code, transport size, length (2), SZL-ID, index, LENTHDR, N_DR
    if len(data) < 12 or data[0] != 0xFF:
        raise ConnectionError("SZL read refused")
    if int.from_bytes(data[4:6], "big") != 0x0424 or int.from_bytes(data[10:12], "big") < 1:
        raise ConnectionError("unexpected SZL in the reply")
    record = data[12:12 + int.from_bytes(data[8:10], "big")]
    if len(record) < 4:
        raise ConnectionError("SZL record too short")
    # Record of SZL 0x0424: event id (2), event class (1), then the mode (1)
    return record[3]


def _heartbeat_modbus(client):
    result = client.read_coils(HEARTBEAT_COIL, count=1, slave=1)
    if result.isError():
        raise ConnectionError("Modbus error response")
    return bool(result.bits[0])


def _heartbeat_s7(sock):
    sock.sendall(_READ_PA0)
    return heartbeat_from_reply(_recv_tpkt(sock))


def heartbeat_from_reply(reply):
    """%QX0.0 from a TPKT frame answering _READ_PA0."""
    item = reply[21:]
    if len(item) < 5 or item[0] != 0xFF:
        raise ConnectionError("S7 read refused")
    return bool(item[4] & 0x01)


def _sample(read):
    seen = set()
    deadline = time.monotonic() + HEARTBEAT_SAMPLE
    while True:
        seen.add(read())
        if len(seen) > 1 or time.monotonic() >= deadline:
            return len(seen) > 1
        time.sleep(0.2)


def scan_cycle_running():
    """(running, route): does the heartbeat output change within the sample?"""
    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient(PLC_HOST, port=PLC_MODBUS_PORT, timeout=2, retries=0)
    try:
        if client.connect():
            return _sample(lambda: _heartbeat_modbus(client)), "Modbus"
    except Exception as e:
        logger.debug(f"s7_cpu_stop: Modbus heartbeat read failed ({e}), trying S7comm")
    finally:
        client.close()
    with _s7_session() as sock:
        return _sample(lambda: _heartbeat_s7(sock)), "S7comm"


def verify():
    checks = []
    try:
        seen, detail, error = _newest_cpu_control()
        if error:
            checks.append(error)
            detail = "No S7comm STOP confirmed."
        checks.append({"name": "CPU STOP sent over S7comm", "passed": seen, "detail": detail})

        try:
            mode = read_cpu_mode()
            claims_stop = mode == CPU_STOP
            checks.append({
                "name": "PLC reports STOP",
                "passed": claims_stop,
                "detail": ("The PLC's status list (SZL 0x0424) says the CPU is in STOP."
                           if claims_stop else
                           f"The PLC's status list (SZL 0x0424) reports mode 0x{mode:02X}, "
                           "not STOP (0x04). Send the STOP and verify before you restart "
                           "the CPU."),
            })
        except Exception as e:
            logger.error(f"s7_cpu_stop: cannot read the CPU status: {e}")
            claims_stop = False
            checks.append({"name": "PLC reports STOP", "passed": False,
                           "detail": "Cannot read the PLC's status list over S7comm "
                                     "from the board."})

        try:
            running, route = scan_cycle_running()
            checks.append({
                "name": "Plant still running",
                "passed": running,
                "detail": (f"The heartbeat output kept toggling (read over {route}): the "
                           "PLC program never stopped."
                           if running else
                           f"The heartbeat output did not change for {HEARTBEAT_SAMPLE:.0f} s "
                           f"(read over {route}). Is the OpenPLC runtime running?"),
            })
        except Exception as e:
            logger.error(f"s7_cpu_stop: cannot read the heartbeat: {e}")
            running = False
            checks.append({"name": "Plant still running", "passed": False,
                           "detail": "Cannot read the PLC's heartbeat over Modbus or "
                                     "S7comm from the board."})

        success = seen and claims_stop and running
        message = ("The PLC acknowledged your STOP and says it is stopped, yet its program "
                   "is still running the plant. Now restart the CPU (warm restart) so the "
                   "next player finds it in RUN."
                   if success else
                   "Send an S7comm CPU STOP to the PLC, check its status, and verify "
                   "while it still reports STOP.")
        return {"success": success, "message": message, "checks": checks}
    except Exception as e:
        logger.error(f"s7_cpu_stop check error: {e}")
        return {"success": False, "message": "Verification error, see the landing log.",
                "checks": checks}
