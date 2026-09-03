"""
CTF check: confirm the player compiled and loaded their own PLC program.

The plc_programming challenge asks the player to modify the ladder/ST program in
the OpenPLC Editor, compile it, and download it to the controller (MITRE ATT&CK
for ICS T0843, Program Download). This verifies that actually happened, rather
than handing out a static flag.

OpenPLC assigns every compiled program a fresh file id, so once the player
uploads and starts a program of their own, the runtime's active program file is
no longer one of the three files shipped in the seeded image. That state lives
inside the OpenPLC runtime and cannot be faked over Modbus, unlike an output
coil, so it is a sound signal that a new program was genuinely downloaded.
"""
import re

import requests

from utils.logger import logger

OPENPLC_URL = "http://172.18.0.3:8080"
DEFAULT_USER = "openplc"
DEFAULT_PASS = "openplc"

# Compiled program files present in the seeded openplc.db shipped in the image:
# the CybICS plant program, OpenPLC's Snap7 map, and the blank program. Any
# other active file means the player compiled and loaded their own program.
# Update these if the seeded database is regenerated.
BASELINE_FILES = {"424345.st", "4968.st", "blank_program.st"}


def _dashboard_state(session):
    """Return (active_file, status) parsed from the OpenPLC dashboard."""
    html = session.get(f"{OPENPLC_URL}/", timeout=10).text
    f = re.search(r"File:\s*<[^>]*>\s*([^\s<]+\.st)", html)
    s = re.search(r"Status:\s*<[^>]*>\s*(Running|Stopped|Compiling)", html, re.I)
    return (f.group(1) if f else None), (s.group(1) if s else None)


def verify():
    checks = []
    try:
        session = requests.Session()
        login = session.post(
            f"{OPENPLC_URL}/login",
            data={"username": DEFAULT_USER, "password": DEFAULT_PASS},
            allow_redirects=False, timeout=10,
        )
        if login.status_code != 302:
            checks.append({
                "name": "OpenPLC access",
                "passed": False,
                "detail": "Cannot log in with the default credentials to read the "
                          "controller state. Do this challenge before hardening the "
                          "OpenPLC password, or restore it temporarily.",
            })
            return {"success": False,
                    "message": "Cannot log into OpenPLC to verify the loaded program.",
                    "checks": checks}

        active_file, status = _dashboard_state(session)

        uploaded = active_file is not None and active_file not in BASELINE_FILES
        checks.append({
            "name": "Own program compiled and downloaded",
            "passed": uploaded,
            "detail": (f"OpenPLC is running a program you compiled ({active_file})."
                       if uploaded else
                       "OpenPLC is still running the program that shipped with the "
                       "lab. Modify the program in the editor, compile it, then "
                       "upload and start it via the web UI at port 8080."),
        })

        running = status == "Running"
        checks.append({
            "name": "Program running",
            "passed": running,
            "detail": f"Controller status: {status or 'unknown'}."
                      + ("" if running else " Start the PLC after uploading."),
        })

        success = uploaded and running
        message = ("Your program is compiled and running on the controller."
                   if success else
                   "Upload and start your own compiled program, then verify again.")
        return {"success": success, "message": message, "checks": checks}

    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot reach OpenPLC service",
                "checks": [{"name": "OpenPLC reachable", "passed": False,
                            "detail": "Cannot connect to OpenPLC at port 8080"}]}
    except Exception as e:
        logger.error(f"PLC program check error: {e}")
        return {"success": False, "message": f"Verification error: {e}", "checks": checks}
