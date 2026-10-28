"""
CTF check: the plant was stopped through OpenPLC's S7comm side door.

OpenPLC runs a Snap7 server on port 102 next to Modbus on 502. Data block
DB1002 is the PLC's %MW memory, two bytes per word, so the program's stop flag
%MW104 (Modbus holding register 1128) is DB1002 bytes 208-209. The challenge
asks the player to set it over S7comm, the route a Modbus-only firewall does
not close (MITRE ATT&CK for ICS T1692.001 Unauthorized Message: Command Message,
T0831 Manipulation of Control).

Two things must hold:

* the newest S7comm WriteVar to OpenPLC on port 102 that touched DB1002
  bytes 208-209, as the IDS logged it (rule s7_write), put a non-zero value
  there, and the IDS logged it within the last WRITE_WINDOW seconds. The FUXA
  HMI and any Modbus client can stop the plant too; this is what tells the
  side door apart from them. "Newest" matters: an old S7 stop followed by an
  S7 restore of 0 does not count, so a later stop by Modbus or the HMI
  cannot borrow it. The window bounds what is left: a stop write that was
  never restored over S7 expires instead of arming the challenge for good.
  The IDS logs every change of value as a new alert, so the newest alert
  always carries the value last written over S7;
* the stop flag is set now, so the write reached the PLC's memory.

The flag is read over Modbus first, which raises no IDS alert. If port 502 is
closed to this host -- the Modbus Firewall challenge does exactly that -- it is
read over S7comm instead, the same side door the player used.
"""
import socket
from datetime import datetime

import requests

from utils.config import PLC_HOST, PLC_MODBUS_PORT
from utils.logger import logger

IDS_URL = "http://localhost:8443"
S7_PORT = 102
MEMORY_DB = 1002           # OpenPLC's Snap7 map: DB1002 = %MW memory
STOP_BYTE = 208            # %MW104 -> byte offset 2 * 104
STOP_REGISTER = 1128       # the same word as a Modbus holding register (%MW104)
WRITE_WINDOW = 300         # seconds an S7 stop write stays valid for verify


def _stop_flag_written(item):
    """The bytes a decoded write item put into DB1002.DBB208-209, or None if it missed them."""
    if item.get("area") != "DB" or item.get("db") != MEMORY_DB:
        return None
    try:
        start = int(item.get("start", -1))
        data = bytes.fromhex(item.get("data", ""))
    except (TypeError, ValueError):
        return None
    covered = bytes(data[b - start] for b in (STOP_BYTE, STOP_BYTE + 1)
                    if 0 <= b - start < len(data))
    return covered or None


def _age_seconds(timestamp, now):
    """Seconds between an alert's timestamp and the IDS clock; None if unparseable."""
    try:
        return (now - datetime.fromisoformat(timestamp)).total_seconds()
    except (TypeError, ValueError):
        return None


def _s7_stop_write_seen():
    """(seen, detail, error check row or None) from the IDS alert buffer.

    The newest s7_write alert to the PLC's port 102 that covers the stop flag
    decides; it must have written a non-zero value within WRITE_WINDOW.
    """
    try:
        alerts = requests.get(f"{IDS_URL}/api/alerts", timeout=5).json().get("alerts", [])
        status = requests.get(f"{IDS_URL}/api/status", timeout=5).json()
    except (requests.exceptions.RequestException, ValueError):
        return False, None, {"name": "IDS reachable", "passed": False,
                             "detail": "Cannot reach the IDS at port 8443. It has to watch "
                                       "the network to confirm the S7comm write."}
    try:
        now = datetime.fromisoformat(status.get("now", ""))
    except (TypeError, ValueError):
        now = datetime.now()   # an IDS from before "now" was reported; same host clock
    for alert in sorted(alerts, key=lambda a: a.get("id", 0), reverse=True):
        if alert.get("rule") != "s7_write" or alert.get("dst") != PLC_HOST \
                or alert.get("dport") != S7_PORT:
            continue
        written = [w for w in map(_stop_flag_written, alert.get("s7_items") or [])
                   if w is not None]
        if not written:
            continue
        source = alert.get("src")
        if not any(written[-1]):
            return False, (f"Your newest S7comm write of the stop flag (from {source}) "
                           "put 0 back. Set it over S7comm again; a Modbus write or "
                           "the HMI's stop button does not count."), None
        age = _age_seconds(alert.get("timestamp"), now)
        if age is None or age > WRITE_WINDOW:
            return False, (f"The newest S7comm write of the stop flag (from {source}) "
                           f"is older than {WRITE_WINDOW // 60} minutes. Write it again "
                           "over S7comm and verify right after."), None
        return True, (f"The IDS saw {source} write the stop flag through the S7comm "
                      f"server on {PLC_HOST}:{S7_PORT}."), None
    if not status.get("active", False):
        return False, None, {"name": "IDS capturing", "passed": False,
                             "detail": "The IDS is not capturing, so it cannot see your "
                                       "write. Start it on its dashboard (port 8443) and "
                                       "write again."}
    return False, ("No S7comm write of the stop flag seen yet. A Modbus write or "
                   "the HMI's stop button does not count."), None


def _read_stop_modbus():
    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient(PLC_HOST, port=PLC_MODBUS_PORT, timeout=2, retries=0)
    try:
        if not client.connect():
            raise ConnectionError("Modbus port closed")
        result = client.read_holding_registers(STOP_REGISTER, count=1, slave=1)
        if result.isError():
            raise ConnectionError("Modbus error response")
        return result.registers[0]
    finally:
        client.close()


def _recv_tpkt(sock):
    head = b""
    while len(head) < 4:
        chunk = sock.recv(4 - len(head))
        if not chunk:
            raise ConnectionError("S7 connection closed")
        head += chunk
    body = b""
    size = int.from_bytes(head[2:4], "big") - 4
    while len(body) < size:
        chunk = sock.recv(size - len(body))
        if not chunk:
            raise ConnectionError("S7 connection closed")
        body += chunk
    return head + body


def _read_stop_s7():
    """Read DB1002.DBW208 with a minimal S7comm client (connect, setup, read var)."""
    cotp_cr = bytes.fromhex("0300001611e00000000100c1020100c2020101c0010a")
    setup = bytes.fromhex("0300001902f08032010000000100080000f0000001000101e0")
    read = (bytes.fromhex("0300001f02f080320100000002000e00000401120a10020002")
            + MEMORY_DB.to_bytes(2, "big") + b"\x84" + (STOP_BYTE * 8).to_bytes(3, "big"))
    with socket.create_connection((PLC_HOST, S7_PORT), timeout=3) as sock:
        sock.sendall(cotp_cr)
        _recv_tpkt(sock)
        sock.sendall(setup)
        _recv_tpkt(sock)
        sock.sendall(read)
        reply = _recv_tpkt(sock)
    # TPKT (4) + COTP (3) + Ack_Data header (12) + parameters (2) = data item
    item = reply[21:]
    if len(item) < 6 or item[0] != 0xFF:
        raise ConnectionError("S7 read refused")
    return int.from_bytes(item[4:6], "big")


def _read_stop_flag():
    """(value, route) of the stop flag, Modbus first and S7comm if 502 is closed."""
    try:
        return _read_stop_modbus(), "Modbus"
    except Exception as e:
        logger.debug(f"s7_sidedoor: Modbus read failed ({e}), trying S7comm")
    return _read_stop_s7(), "S7comm"


def verify():
    checks = []
    try:
        seen, detail, error = _s7_stop_write_seen()
        if error:
            checks.append(error)
            detail = "No S7comm write of the stop flag confirmed."
        checks.append({"name": "Stop flag written over S7comm", "passed": seen,
                       "detail": detail})

        try:
            value, route = _read_stop_flag()
            stopped = value != 0
            checks.append({
                "name": "Plant stopped",
                "passed": stopped,
                "detail": (f"The PLC's stop flag is set (read over {route}); compressor "
                           "and system valve are held off."
                           if stopped else
                           f"The PLC's stop flag is 0 (read over {route}), so the plant "
                           "is running. Set it, then verify before you restore it."),
            })
        except Exception as e:
            logger.error(f"s7_sidedoor: cannot read the stop flag: {e}")
            stopped = False
            checks.append({"name": "Plant stopped", "passed": False,
                           "detail": "Cannot read the PLC's stop flag over Modbus or "
                                     "S7comm from the board."})

        success = seen and stopped
        message = ("Side door confirmed: you stopped the plant through S7comm. Now "
                   "restore it: write 0 back to the same word."
                   if success else
                   "Stop the plant through OpenPLC's S7comm server, keep it stopped, "
                   "and verify again.")
        return {"success": success, "message": message, "checks": checks}
    except Exception as e:
        logger.error(f"s7_sidedoor check error: {e}")
        return {"success": False, "message": "Verification error, see the landing log.",
                "checks": checks}
