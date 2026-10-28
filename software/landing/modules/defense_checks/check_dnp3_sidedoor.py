"""
CTF check: the plant was stopped through OpenPLC's DNP3 side door.

OpenPLC runs a DNP3 outstation on port 20000 next to Modbus on 502. It maps an
Analog Output at index 1024 + n onto %MWn, so the program's stop flag %MW104
(Modbus holding register 1128) is analog output 1128. The challenge asks the
player to set it with a DNP3 operate -- a command a Modbus firewall and the
Modbus IDS rules never see (MITRE ATT&CK for ICS T1692.001 Unauthorized
Message: Command Message, T0831 Manipulation of Control).

Two things must hold:

* the newest DNP3 operate on analog output 1128 that the IDS logged (rule
  dnp3_operate) went to OpenPLC's port 20000, wrote a non-zero value, was
  logged within the last WRITE_WINDOW seconds -- and the outstation confirmed
  it. The IDS files the outstation's reply under the request whose points it
  echoes, and only when exactly one request seen on that connection fits and
  the connection carried nothing the IDS could not read in full (a response
  does not name the function it answers, so a SELECT's reply must not stand
  in for a dropped operate); otherwise it marks the request "unattributed". The
  check takes the value from that echo, with control status 00, not from the
  request. For an operate that is the outstation's own word that it carried
  it out, so this check does not have to second-guess which frames
  opendnp3 accepts. A frame it drops (wrong link addresses, wrong direction
  bit, a transport or application header it does not take) gets no reply, and
  one it refuses (an OPERATE without its SELECT, an index out of range) gets a
  non-zero status; neither counts, else a dropped frame followed by a Modbus
  stop would pass. A DIRECT OPERATE NO ACK (06) is never answered, so it
  cannot be confirmed either.

  "Newest" matters: a DNP3 stop followed by a DNP3 restore of 0 does not
  count, so a later stop by Modbus or the HMI cannot borrow it; the window
  keeps a stop that was never restored over DNP3 from arming the challenge for
  good. A restore cancels the stop unless the outstation explicitly refused
  it, because an 06 restore does write 0 without a reply;
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
STOP_INDEX = 1128          # analog output 1024 + 104 -> %MW104
OPERATE_FUNCTIONS = (0x04, 0x05, 0x06)
NO_ACK = 0x06              # DIRECT OPERATE NO ACK: the outstation never answers
WRITE_WINDOW = 300         # seconds a DNP3 stop stays valid for verify
UNATTRIBUTED = -1          # the IDS saw a reply but could not tell which request it answers
# opendnp3 CommandStatus values a student is likely to meet
STATUS_NAMES = {1: "TIMEOUT", 2: "NO_SELECT", 3: "FORMAT_ERROR", 4: "NOT_SUPPORTED",
                5: "ALREADY_ACTIVE", 6: "HARDWARE_ERROR", 7: "LOCAL", 8: "TOO_MANY_OPS",
                9: "NOT_AUTHORIZED", 12: "OUT_OF_RANGE"}


def _stop_value(request):
    """The value a decoded DNP3 request carries for analog output 1128, or None."""
    values = [o.get("value") for o in request.get("objects") or []
              if isinstance(o, dict) and o.get("group") == 41 and o.get("variation") == 2
              and o.get("index") == STOP_INDEX and isinstance(o.get("value"), int)]
    return values[-1] if values else None


def _echo(request):
    """(status, value) the outstation's reply echoed for analog output 1128.

    None without a reply. A reply that does not echo the point is a refusal
    of the whole request (the IIN bits say why), so it gives status 0xFF. The
    value is taken from the echo, not from the request: for an operate it is
    what the outstation says it wrote.
    """
    reply = request.get("reply")
    if not isinstance(reply, dict):
        return None
    if reply.get("unattributed"):
        return UNATTRIBUTED, None
    points = [o for o in reply.get("objects") or []
              if isinstance(o, dict) and o.get("group") == 41 and o.get("variation") == 2
              and o.get("index") == STOP_INDEX and isinstance(o.get("status"), int)
              and isinstance(o.get("value"), int)]
    if not points:
        return 0xFF, None
    return points[-1]["status"], points[-1]["value"]


def _reply_status(request):
    echo = _echo(request)
    return None if echo is None else echo[0]


def _timestamp(alert):
    try:
        return datetime.fromisoformat(alert.get("timestamp"))
    except (TypeError, ValueError):
        return None


def _stop_writes(alerts):
    """(newest confirmed stop-flag write, newest unconfirmed one after it).

    The first is (alert, value) for the newest operate on the stop flag the
    outstation answered with status 00, the second (alert, request) for a
    later stop it did not confirm; each None if there is none.
    """
    effective, unconfirmed = None, None
    for alert in sorted(alerts, key=lambda a: a.get("id", 0)):
        if alert.get("rule") != "dnp3_operate" or alert.get("dst") != PLC_HOST \
                or alert.get("dport") != DNP3_PORT:
            continue
        for request in alert.get("dnp3") or []:
            if not isinstance(request, dict) or request.get("function") not in OPERATE_FUNCTIONS:
                continue
            value = _stop_value(request)
            if value is None:
                continue
            echo = _echo(request)
            status = None if echo is None else echo[0]
            if status == 0:
                effective, unconfirmed = (alert, echo[1]), None
            elif value == 0 and status in (None, UNATTRIBUTED):
                # A restore with no reply, or one the IDS could not tie to
                # it, may still have written 0 (an 06 never gets a reply), so
                # it cancels an earlier stop.
                effective, unconfirmed = None, None
            elif value != 0:
                unconfirmed = (alert, request)
    return effective, unconfirmed


def _unconfirmed_detail(request):
    function, status = request.get("function"), _reply_status(request)
    if function == NO_ACK:
        return ("Your newest DNP3 stop was a Direct Operate No Ack (06). The outstation "
                "never answers it, so nothing confirms it was carried out. Use a Direct "
                "Operate (05), or a SELECT followed by an OPERATE.")
    if status == UNATTRIBUTED:
        return ("The outstation answered, but the IDS could not tell which of your "
                "requests the answer was for: another request on the same connection "
                "fits it too (a SELECT with the same sequence number and point, say), "
                "the connection carried something it could not read in full, or the "
                "IDS did not follow it from its start without a gap. Send the operate "
                "on its own, as one frame, on a new connection.")
    if status is None:
        return ("The IDS saw your newest DNP3 operate on the stop flag, but the outstation "
                "never answered it: it dropped the frame. Check the link control byte and "
                "addresses, the transport header and the application control byte against "
                "the tables.")
    name = STATUS_NAMES.get(status, "no echo of the point" if status == 0xFF else "")
    hint = (" An OPERATE (04) only works right after a SELECT (03) with the same objects "
            "and the previous sequence number; a Direct Operate (05) needs none."
            if status == 2 else "")
    return (f"The outstation refused your newest DNP3 operate on the stop flag with "
            f"control status {status:02X}{f' ({name})' if name else ''} and wrote "
            f"nothing.{hint}")


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
        effective, unconfirmed = _stop_writes(alerts)
    except (AttributeError, TypeError):
        effective, unconfirmed = None, None
    if effective is not None and effective[1] != 0:
        # A later operate the outstation did not confirm cannot undo this one.
        when = _timestamp(effective[0])
        age = (now - when).total_seconds() if when is not None else None
        if age is not None and age <= WRITE_WINDOW:
            return True, (f"The outstation on {PLC_HOST}:{DNP3_PORT} confirmed your DNP3 "
                          "operate on the stop flag with control status 00."), None
        if unconfirmed is None:
            return False, (f"The newest confirmed DNP3 stop is older than "
                           f"{WRITE_WINDOW // 60} minutes. Send it again and verify right "
                           "after."), None
    if unconfirmed is not None:
        return False, _unconfirmed_detail(unconfirmed[1]), None
    if effective is not None:
        return False, ("The newest confirmed DNP3 operate on the stop flag put 0 back. "
                       "Set it over DNP3 again; a Modbus write or the HMI's stop button "
                       "does not count."), None
    if not status.get("active", False):
        return False, None, {"name": "IDS capturing", "passed": False,
                             "detail": "The IDS is not capturing, so it cannot see your "
                                       "command. Start it on its dashboard (port 8443) "
                                       "and send it again."}
    return False, ("No DNP3 operate that sets the stop flag seen yet. A Modbus write or "
                   "the HMI's stop button does not count."), None


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
