"""
CTF check: the plant was stopped through OpenPLC's DNP3 side door.

OpenPLC runs a DNP3 outstation on port 20000 next to Modbus on 502. It maps an
Analog Output at index 1024 + n onto %MWn, so the program's stop flag %MW104
(Modbus holding register 1128) is analog output 1128. The challenge asks the
player to set it with a DNP3 operate -- a command a Modbus firewall and the
Modbus IDS rules never see (MITRE ATT&CK for ICS T1692.001 Unauthorized
Message: Command Message, T0831 Manipulation of Control).

Two things must hold:

* the newest DNP3 operate on analog output 1128 that the outstation carried
  out, as reconstructed from the IDS log (rule dnp3_operate), went to
  OpenPLC's port 20000 with the link addresses the outstation accepts, wrote a
  non-zero value, and was logged within the last WRITE_WINDOW seconds.

  The IDS logs requests, not what the outstation made of them, so this check
  replays the outstation's own acceptance rules on the logged requests. The
  IDS already drops frames with a bad CRC or a malformed object header, and
  wrong link addresses are filtered here. A DIRECT OPERATE (0x05) or DIRECT
  OPERATE NO ACK (0x06) acts at once. A plain OPERATE (0x04) acts only as the
  second half of select-before-operate: opendnp3 (ControlState::
  ValidateSelection) runs it only if the last SELECT carried the previous
  application sequence number and byte-identical objects and came less than
  selectTimeout (10 s, OpenPLC's dnp3.cfg does not change it) before. Anything
  else gets control status 02 NO_SELECT or 01 TIMEOUT and writes nothing, so
  it must not earn the flag either -- else a refused OPERATE followed by a
  Modbus stop would pass.

  "Newest" matters: a DNP3 stop followed by a DNP3 restore of 0 does not
  count, so a later stop by Modbus or the HMI cannot borrow it; the window
  keeps a stop that was never restored over DNP3 from arming the challenge for
  good. The IDS logs every change of value as a new alert, so the newest one
  carries the last value;
* the stop flag is set now, so the write reached the PLC's memory. It is read
  over Modbus, or over S7comm when 502 is firewalled, as the S7 Side Door
  check does.
"""
from datetime import datetime

import requests

from modules.defense_checks.check_s7_sidedoor import _read_stop_flag as _read_stop_via_plc
from utils.config import PLC_HOST
from utils.logger import logger

IDS_URL = "http://localhost:8443"
DNP3_PORT = 20000
OUTSTATION = 10            # OpenPLC dnp3.cfg local_address
MASTER = 1                 # dnp3.cfg remote_address: the only master it answers
STOP_INDEX = 1128          # analog output 1024 + 104 -> %MW104
SELECT = 0x03
OPERATE = 0x04             # acts only after a matching SELECT
DIRECT_OPERATE_FUNCTIONS = (0x05, 0x06)
SELECT_TIMEOUT = 10        # opendnp3 OutstationParams::selectTimeout default
WRITE_WINDOW = 300         # seconds a DNP3 stop stays valid for verify


def _stop_value(request):
    """The value a decoded DNP3 request carries for analog output 1128, or None."""
    values = [o.get("value") for o in request.get("objects") or []
              if isinstance(o, dict) and o.get("group") == 41 and o.get("variation") == 2
              and o.get("index") == STOP_INDEX and isinstance(o.get("value"), int)]
    return values[-1] if values else None


def _timestamp(alert):
    try:
        return datetime.fromisoformat(alert.get("timestamp"))
    except (TypeError, ValueError):
        return None


def _stop_writes(alerts):
    """(newest stop-flag write the outstation carried out, refused OPERATE after it).

    Each is the IDS alert that logged it, or None; the first comes with the
    value written. Walks the logged requests to the outstation in order and
    keeps the select-before-operate state the way opendnp3 does.
    """
    effective, refused = None, None
    selection = None   # (expected sequence number, objects CRC, time of the SELECT)
    for alert in sorted(alerts, key=lambda a: a.get("id", 0)):
        if alert.get("rule") != "dnp3_operate" or alert.get("dst") != PLC_HOST \
                or alert.get("dport") != DNP3_PORT:
            continue
        when = _timestamp(alert)
        for request in alert.get("dnp3") or []:
            if not isinstance(request, dict) or request.get("link_dst") != OUTSTATION \
                    or request.get("link_src") != MASTER:
                continue   # the outstation drops it without a reply
            function, seq = request.get("function"), request.get("seq")
            crc = request.get("objects_crc")
            if function == SELECT:
                selection = ((seq + 1) & 0x0F, crc, when) \
                    if isinstance(seq, int) and when is not None else None
                continue
            value = _stop_value(request)
            if function in DIRECT_OPERATE_FUNCTIONS:
                acted = True
            elif function == OPERATE:
                acted = (selection is not None and when is not None
                         and isinstance(seq, int) and seq == selection[0]
                         and crc is not None and crc == selection[1]
                         and 0 <= (when - selection[2]).total_seconds() < SELECT_TIMEOUT)
            else:
                continue
            if value is None:
                continue
            if acted:
                effective, refused = (alert, value), None
            else:
                refused = alert
    return effective, refused


def _read_stop_flag():
    return _read_stop_via_plc()


def _dnp3_stop_seen():
    """(seen, detail, error check row or None) from the IDS alert buffer."""
    try:
        alerts = requests.get(f"{IDS_URL}/api/alerts", timeout=5).json().get("alerts", [])
        status = requests.get(f"{IDS_URL}/api/status", timeout=5).json()
    except (requests.exceptions.RequestException, ValueError):
        return False, None, {"name": "IDS reachable", "passed": False,
                             "detail": "Cannot reach the IDS at port 8443. It has to watch "
                                       "the network to confirm the DNP3 command."}
    try:
        now = datetime.fromisoformat(status.get("now", ""))
    except (TypeError, ValueError):
        now = datetime.now()
    try:
        effective, refused = _stop_writes(alerts)
    except (AttributeError, TypeError):
        effective, refused = None, None
    if effective is not None:
        alert, value = effective
        source = alert.get("src")
        if value == 0:
            return False, (f"Your newest DNP3 operate on the stop flag (from {source}) "
                           "put 0 back. Set it over DNP3 again; a Modbus write or the "
                           "HMI's stop button does not count."), None
        when = _timestamp(alert)
        age = (now - when).total_seconds() if when is not None else None
        if age is None or age > WRITE_WINDOW:
            return False, (f"The newest DNP3 operate on the stop flag (from {source}) is "
                           f"older than {WRITE_WINDOW // 60} minutes. Send it again and "
                           "verify right after."), None
        return True, (f"The IDS saw {source} set the stop flag through the DNP3 "
                      f"outstation on {PLC_HOST}:{DNP3_PORT}."), None
    if refused is not None:
        return False, (f"The IDS saw an OPERATE (function 04) on the stop flag from "
                       f"{refused.get('src')}, but no matching SELECT right before it, so "
                       "the outstation refused it (control status 02, NO_SELECT) and "
                       "wrote nothing. Use a Direct Operate (05), or a SELECT followed "
                       f"within {SELECT_TIMEOUT} s by an OPERATE with the same objects "
                       "and the next sequence number."), None
    if not status.get("active", False):
        return False, None, {"name": "IDS capturing", "passed": False,
                             "detail": "The IDS is not capturing, so it cannot see your "
                                       "command. Start it on its dashboard (port 8443) "
                                       "and send it again."}
    return False, ("No DNP3 operate that sets the stop flag seen yet. The outstation "
                   "only acts on a frame with correct CRCs, a well-formed object "
                   "header and the link addresses it is configured for, and so does "
                   "this check. A Modbus write or the HMI's stop button does not "
                   "count."), None


def verify():
    checks = []
    try:
        seen, detail, error = _dnp3_stop_seen()
        if error:
            checks.append(error)
            detail = "No DNP3 operate on the stop flag confirmed."
        checks.append({"name": "Stop flag set over DNP3", "passed": seen, "detail": detail})

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
            logger.error(f"dnp3_sidedoor: cannot read the stop flag: {e}")
            stopped = False
            checks.append({"name": "Plant stopped", "passed": False,
                           "detail": "Cannot read the PLC's stop flag over Modbus or "
                                     "S7comm from the board."})

        success = seen and stopped
        message = ("Side door confirmed: you stopped the plant over DNP3. Now restore "
                   "it: operate the same point with 0."
                   if success else
                   "Stop the plant through OpenPLC's DNP3 outstation, keep it stopped, "
                   "and verify again.")
        return {"success": success, "message": message, "checks": checks}
    except Exception as e:
        logger.error(f"dnp3_sidedoor check error: {e}")
        return {"success": False, "message": "Verification error, see the landing log.",
                "checks": checks}
