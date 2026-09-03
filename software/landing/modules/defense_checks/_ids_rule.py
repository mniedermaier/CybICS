"""
Shared helper for CTF checks that confirm an attack was actually carried out.

The IDS sniffs all lab traffic and raises a named alert for each attack
signature. A verified offensive challenge passes when its signature has fired,
so the flag is earned by performing the attack rather than by reading a static
string. This keeps the plant model untouched and reuses detection that already
exists.
"""
import requests

from utils.logger import logger

IDS_URL = "http://localhost:8443"


def rule_fired(rule_names):
    """Whether any of the given IDS rules has an alert.

    Returns (fired, error_message, error_checks). On success error_message is
    "" and error_checks is []; on an IDS problem fired is False, error_message
    explains it, and error_checks holds a check row to surface to the player.
    """
    if isinstance(rule_names, str):
        rule_names = [rule_names]
    try:
        resp = requests.get(f"{IDS_URL}/api/rules/stats", timeout=5)
        stats = resp.json()
    except requests.exceptions.ConnectionError:
        return (False, "Cannot reach the IDS service",
                [{"name": "IDS reachable", "passed": False,
                  "detail": "Cannot reach the IDS at port 8443"}])
    except Exception as e:
        logger.error(f"IDS rule check error: {e}")
        return False, f"Verification error: {e}", []

    fired = any(stats.get(r, {}).get("count", 0) for r in rule_names)
    return fired, "", []
