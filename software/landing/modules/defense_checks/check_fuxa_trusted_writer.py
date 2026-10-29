"""
CTF check: the plant was stopped through the HMI, and the IDS stayed silent.

The IDS write rules (modbus_unauth_write, modbus_flood) count Modbus writes
per source and skip the trusted writers hwio and FUXA entirely. FUXA writes
whatever any of its clients asks it to, so an attacker who drives FUXA -- over
its REST API with an administrator token, or over the socket.io channel the
HMI page itself uses, which FUXA 1.2.6 accepts from guests -- makes the PLC
receive the command from 172.18.0.4, a source no rule looks at (MITRE ATT&CK
for ICS T0871 Execution through API, T1692.001 Unauthorized Message: Command
Message).

The IDS keeps a journal of the Modbus write requests it sees, FUXA's included
(GET /api/modbus/writes; no rule fires on it). Four things must hold:

* the newest journaled write that covers the stop flag (holding register
  1128 on the wire, FUXA's 1129) came from FUXA, set it to a non-zero value,
  and is at most WRITE_WINDOW seconds old. "Newest" means a stop sent
  straight from the attack machine does not count, and neither does a FUXA
  stop that something else wrote over afterwards;
* the IDS was capturing for at least QUIET_BEFORE seconds before that write;
* no alert from QUIET_BEFORE seconds before that write until now, except
  arp_spoof, which says nothing about who sent the stop and which older IDS
  versions raised after every container restart (the IDS Evasion check
  ignores it too). Brute-forcing the FUXA login, a port
  scan or a burst of direct Modbus writes all show up here;
* the stop flag is set now, read over Modbus or, when 502 is firewalled, over
  S7comm, as the S7 Side Door check does.

The IDS cannot tell an operator pressing STOP in the HMI from a script that
asks FUXA to write -- that is the point of the challenge -- so neither can
this check. The README says so.
"""
from datetime import datetime, timedelta

import requests

from modules.defense_checks.check_s7_sidedoor import _read_stop_flag as _read_stop_via_plc
from utils.config import PLC_HOST
from utils.logger import logger

IDS_URL = "http://localhost:8443"
FUXA_IP = "172.18.0.4"
STOP_REGISTER = 1128          # %MW104, wire address of FUXA's "stop" tag (1129)
WRITE_FUNCTIONS = (0x06, 0x10)
WRITE_WINDOW = 300            # seconds a FUXA stop stays valid for verify
QUIET_BEFORE = 60             # seconds before the write that must be alert-free
IGNORED_RULES = frozenset(("arp_spoof",))


def _timestamp(entry):
    try:
        return datetime.fromisoformat(entry.get("timestamp"))
    except (TypeError, ValueError, AttributeError):
        return None


def _stop_value(write):
    """The value a journaled write puts into the stop flag, or None if it misses it."""
    if not isinstance(write, dict) or write.get("dst") != PLC_HOST \
            or write.get("function") not in WRITE_FUNCTIONS:
        return None
    address, values = write.get("address"), write.get("values")
    if not isinstance(address, int) or not isinstance(values, list):
        return None
    index = STOP_REGISTER - address
    if 0 <= index < len(values) and isinstance(values[index], int):
        return values[index]
    return None


def _newest_stop_write(writes):
    """(write, value) of the newest journaled write of the stop flag, or (None, None)."""
    newest = (None, None)
    for write in sorted((w for w in writes if isinstance(w, dict)),
                        key=lambda w: w.get("id", 0)):
        value = _stop_value(write)
        if value is not None:
            newest = (write, value)
    return newest


def _ids_state():
    """(status, writes, alerts) from the IDS, or raises RequestException/ValueError."""
    status = requests.get(f"{IDS_URL}/api/status", timeout=5).json()
    writes = requests.get(f"{IDS_URL}/api/modbus/writes", timeout=5).json().get("writes", [])
    alerts = requests.get(f"{IDS_URL}/api/alerts", timeout=5).json().get("alerts", [])
    return status, writes, alerts


def _write_check(status, writes):
    """(check row, time of the FUXA write or None)."""
    name = "Stop flag written by the HMI"
    write, value = _newest_stop_write(writes)
    if write is None:
        return {"name": name, "passed": False,
                "detail": "The IDS has not seen any write of the stop flag (holding "
                          f"register {STOP_REGISTER} on {PLC_HOST}). Make FUXA write it."}, None
    source = write.get("src")
    if source != FUXA_IP:
        return {"name": name, "passed": False,
                "detail": f"The newest write of the stop flag came from {source}, not "
                          f"from the HMI ({FUXA_IP}). The IDS logged your own host as "
                          "the writer. Let FUXA send it."}, None
    if value == 0:
        return {"name": name, "passed": False,
                "detail": "The newest write of the stop flag came from FUXA but put 0 "
                          "back. Stop the plant through FUXA again."}, None
    when = _timestamp(write)
    try:
        now = datetime.fromisoformat(status.get("now", ""))
    except (TypeError, ValueError):
        now = datetime.now()
    age = (now - when).total_seconds() if when is not None else None
    if age is None or age > WRITE_WINDOW:
        return {"name": name, "passed": False,
                "detail": f"FUXA's stop write is older than {WRITE_WINDOW // 60} minutes. "
                          "Send it again and verify right after."}, None
    return {"name": name, "passed": True,
            "detail": f"The IDS journal shows FUXA ({FUXA_IP}) writing {value} to the "
                      f"stop flag, function 0x{write.get('function'):02X}, "
                      f"{int(age)} s ago. No write rule looks at that source."}, when


def _quiet_check(status, alerts, when):
    name = "IDS stayed silent"
    started = None
    try:
        started = datetime.fromisoformat((status.get("stats") or {}).get("started_at") or "")
    except (TypeError, ValueError):
        pass
    since = when - timedelta(seconds=QUIET_BEFORE)
    if started is None or started > since:
        return {"name": name, "passed": False,
                "detail": f"The IDS started capturing less than {QUIET_BEFORE} s before "
                          "FUXA's write, so it cannot vouch for the time before it. "
                          "Keep it running and stop the plant again."}
    loud = [a for a in alerts if isinstance(a, dict)
            and a.get("rule") not in IGNORED_RULES
            and (_timestamp(a) or datetime.min) >= since]
    if loud:
        seen = sorted({f"{a.get('rule')} from {a.get('src')}" for a in loud})
        return {"name": name, "passed": False,
                "detail": f"The IDS raised {len(loud)} alert(s) between {QUIET_BEFORE} s "
                          f"before FUXA's write and now: {', '.join(seen[:4])}. Wait a "
                          "minute without scans, login guessing or direct Modbus writes, "
                          "then stop the plant through FUXA again."}
    return {"name": name, "passed": True,
            "detail": f"No alert from {QUIET_BEFORE} s before the write until now "
                      "(ARP noise from container restarts aside)."}


def verify():
    checks = []
    try:
        try:
            status, writes, alerts = _ids_state()
        except (requests.exceptions.RequestException, ValueError, AttributeError):
            checks.append({"name": "IDS reachable", "passed": False,
                           "detail": "Cannot reach the IDS at port 8443. It has to watch "
                                     "the network to confirm who wrote the stop flag."})
            return {"success": False, "message": "Start the IDS and try again.",
                    "checks": checks}
        if not status.get("active", False):
            checks.append({"name": "IDS capturing", "passed": False,
                           "detail": "The IDS is not capturing. Start it on its dashboard "
                                     "(port 8443), then stop the plant through FUXA."})
            return {"success": False, "message": "Start the IDS and try again.",
                    "checks": checks}

        row, when = _write_check(status, writes)
        checks.append(row)
        quiet = False
        if when is not None:
            quiet_row = _quiet_check(status, alerts, when)
            quiet = quiet_row["passed"]
            checks.append(quiet_row)

        try:
            value, route = _read_stop_via_plc()
            stopped = value != 0
            checks.append({
                "name": "Plant stopped",
                "passed": stopped,
                "detail": (f"The PLC's stop flag is set (read over {route}); compressor "
                           "and system valve are held off."
                           if stopped else
                           f"The PLC's stop flag is 0 (read over {route}), so the plant "
                           "is running. Stop it, then verify before you restore it."),
            })
        except Exception as e:
            logger.error(f"fuxa_trusted_writer: cannot read the stop flag: {e}")
            stopped = False
            checks.append({"name": "Plant stopped", "passed": False,
                           "detail": "Cannot read the PLC's stop flag over Modbus or "
                                     "S7comm from the board."})

        success = row["passed"] and quiet and stopped
        message = ("Trusted writer confirmed: the PLC took the stop from the HMI and the "
                   "IDS said nothing. Now restore the plant the same way: write 0 "
                   "through FUXA."
                   if success else
                   "Stop the plant by making FUXA write the stop flag, without raising "
                   "an IDS alert, keep it stopped and verify again.")
        return {"success": success, "message": message, "checks": checks}
    except Exception as e:
        logger.error(f"fuxa_trusted_writer check error: {e}")
        return {"success": False, "message": "Verification error, see the landing log.",
                "checks": checks}
