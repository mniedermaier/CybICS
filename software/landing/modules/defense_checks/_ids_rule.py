"""
Shared helper for CTF checks that confirm an attack was actually carried out.

The IDS sniffs all lab traffic and raises a named alert for each attack
signature. A verified offensive challenge passes when its signature has fired
recently, so the flag is earned by performing the attack rather than by reading
a static string. This keeps the plant model untouched and reuses detection that
already exists.

"Recently" matters: the IDS keeps its alert buffer across CTF resets, so
without a window an attack run once -- by an instructor's demo, the test suite
or an earlier student on the same board -- would hand the flag to everyone
afterwards. The IDS repeats an alert every 30 s while an attack keeps going,
so a running attack always counts.
"""
from datetime import datetime

import requests

from utils.logger import logger

IDS_URL = "http://localhost:8443"
ATTACK_WINDOW = 600  # seconds an alert vouches for an attack


def _age(last_seen, now):
    """Seconds between two IDS timestamps, or None if either is unreadable."""
    try:
        return (datetime.fromisoformat(now) - datetime.fromisoformat(last_seen)).total_seconds()
    except (TypeError, ValueError):
        return None


def rule_fired(rule_names, max_age=ATTACK_WINDOW):
    """Whether any of the given IDS rules raised an alert in the last max_age seconds.

    The age is measured on the IDS's own clock (/api/status "now"), so the
    landing container's clock and time zone do not matter. max_age=None
    accepts any alert in the buffer.

    Returns (fired, error_message, error_checks). On success error_message is
    "" and error_checks is []; on an IDS problem fired is False, error_message
    explains it, and error_checks holds a check row to surface to the player.
    """
    if isinstance(rule_names, str):
        rule_names = [rule_names]
    try:
        stats = requests.get(f"{IDS_URL}/api/rules/stats", timeout=5).json()
        now = None
        if max_age is not None:
            now = requests.get(f"{IDS_URL}/api/status", timeout=5).json().get("now")
    except requests.exceptions.ConnectionError:
        return (False, "Cannot reach the IDS service",
                [{"name": "IDS reachable", "passed": False,
                  "detail": "Cannot reach the IDS at port 8443"}])
    except Exception as e:
        logger.error(f"IDS rule check error: {e}")
        return False, f"Verification error: {e}", []

    for rule in rule_names:
        entry = stats.get(rule, {})
        if not entry.get("count", 0):
            continue
        if max_age is None:
            return True, "", []
        age = _age(entry.get("last_seen"), now)
        if age is not None and age <= max_age:
            return True, "", []
    return False, "", []
