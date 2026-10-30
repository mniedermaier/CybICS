"""
Defense check: FUXA no longer trusts tokens signed with a known key
(challenge defense_fuxa_jwt).

It forges administrator tokens with FUXA's published default key, variations
of it and a list of guessable keys, and asks the running FUXA for its
admin-only user list with each. Every one must be refused. FUXA must also be
up, serve its HMI, have authentication switched on and still issue and accept
tokens with its own key, so stopping FUXA, switching security off or breaking
its authentication does not pass as "rotated". Finally the key in settings.js
must be at least 32 characters long and use at least 10 different characters
(40 times "a" is long but not random); only those two numbers are read,
through the Docker socket, and the key never leaves the FUXA container.

What the check cannot judge: FUXA 1.2.6 also signs administrator tokens for
anyone through its token refresh (POST /api/heartbeat with an invalid token
and a made-up x-auth-user header, see _fuxa_jwt.fuxa_could_issue). That flaw
does not depend on the key, so rotating it does not close it; the README
says so and points at limiting access to port 1881.

No password is used, so the check works whatever the student did in the
Harden FUXA Credentials challenge. Towards FUXA it sends only GET requests and
two POST /api/heartbeat calls, which change nothing.
"""
import requests

from modules.defense_checks._fuxa_jwt import (ADMIN_GROUPS, DEFAULT_SECRET, FUXA_URL, TIMEOUT,
                                               forge, fuxa_container, get_users, own_key_round_trip,
                                               secret_stats, security_enabled)
from utils.logger import logger

MIN_KEY_LENGTH = 32
# 48 random hex digits have about 16 distinct characters; fewer than 10
# means a repeated pattern rather than a random key.
MIN_DISTINCT_CHARS = 10

# Keys a lazy fix would choose: the published default and its variations,
# then common words. Not exhaustive: the point is a long random key.
DEFAULT_VARIATIONS = ("Frangoteam751", "FRANGOTEAM751", "frangoteam", "frangoteam750",
                      "frangoteam752", "frangoteam7511", "frangoteam751!", "frangoteam_751",
                      "frangoteam-751", "751frangoteam")
COMMON_SECRETS = ("secret", "secretCode", "changeme", "password", "123456", "admin", "fuxa",
                  "cybics", "cybics-mgmt", "jwtsecret", "CybICS")
GUESSABLE_SECRETS = DEFAULT_VARIATIONS + COMMON_SECRETS


def _accepted(secret):
    """True if FUXA lets an admin token signed with secret read /api/users."""
    token = forge({"id": "cybics-check", "groups": ADMIN_GROUPS[0]}, secret)
    return get_users(token).status_code == 200


def _length_check():
    """The check entry for the key's length and variety in settings.js."""
    name = "Key long and random"
    container = fuxa_container()
    stats = secret_stats(container) if container else None
    if stats is None:
        return {"name": name, "passed": False,
                "detail": "Could not read settings.js in the FUXA container through Docker"}
    length, distinct = stats
    if length < 0:
        return {"name": name, "passed": False,
                "detail": "settings.js sets no secretCode: FUXA uses its built-in key"}
    if length < MIN_KEY_LENGTH:
        return {"name": name, "passed": False,
                "detail": f"secretCode is {length} characters long. An HS256 key can be guessed "
                          f"offline from one captured token, so use at least {MIN_KEY_LENGTH} "
                          f"random characters, for example 48 hex digits"}
    if distinct < MIN_DISTINCT_CHARS:
        return {"name": name, "passed": False,
                "detail": f"secretCode is long but uses only {distinct} different characters: "
                          f"a repeated pattern is guessed as easily as a word. Generate it from "
                          f"random bytes (at least {MIN_DISTINCT_CHARS} different characters)"}
    return {"name": name, "passed": True,
            "detail": f"secretCode in settings.js is {length} characters long with "
                      f"{distinct} different characters"}


def verify():
    checks = []
    try:
        ui = requests.get(f"{FUXA_URL}/", timeout=TIMEOUT)
        up = ui.status_code == 200
        checks.append({"name": "FUXA HMI running", "passed": up,
                       "detail": "The HMI answers on port 1881" if up
                       else f"The HMI answered {ui.status_code}"})
        if not up:
            return {"success": False, "checks": checks,
                    "message": "FUXA must be running: an HMI that is down is not hardened."}

        ok, detail = security_enabled()
        checks.append({"name": "FUXA authentication on", "passed": ok, "detail": detail})
        if not ok:
            return {"success": False, "checks": checks,
                    "message": "Keep FUXA's authentication switched on (secureEnabled)."}

        ok, detail = own_key_round_trip()
        checks.append({"name": "FUXA tokens still work", "passed": ok, "detail": detail})

        default_refused = not _accepted(DEFAULT_SECRET)
        checks.append({"name": "Default key rejected", "passed": default_refused,
                       "detail": "A token signed with FUXA's built-in key is refused" if default_refused
                       else "FUXA still accepts tokens signed with its built-in default key"})

        weak = [s for s in GUESSABLE_SECRETS if _accepted(s)]
        checks.append({"name": "Key not guessable", "passed": not weak,
                       "detail": f"None of the {len(GUESSABLE_SECRETS)} common keys and variations "
                                 f"of the default tried is accepted" if not weak
                       else "FUXA accepts a token signed with a common word or a variation of the "
                            "default key; use a long random key"})

        checks.append(_length_check())

        success = all(c["passed"] for c in checks)
        message = ("FUXA now signs its tokens with a long key of its own: tokens forged with the "
                   "default or a guessable key are refused. FUXA's token refresh still hands out "
                   "admin tokens to anyone, so keep port 1881 limited to operator stations."
                   if success else
                   "FUXA still trusts a token anyone can make, or its key is weak. Set a long random "
                   "secretCode in FUXA's settings.js and restart FUXA.")
        return {"success": success, "message": message, "checks": checks}

    except requests.exceptions.RequestException:
        checks.append({"name": "FUXA reachable", "passed": False,
                       "detail": "Cannot connect to FUXA at 172.18.0.4:1881"})
        return {"success": False, "checks": checks,
                "message": "Cannot reach FUXA. If you just restarted it, wait a few seconds."}
    except ValueError:
        checks.append({"name": "FUXA answer", "passed": False,
                       "detail": "FUXA did not answer with JSON"})
        return {"success": False, "checks": checks, "message": "FUXA gave an unexpected answer."}
    except Exception as e:  # pragma: no cover - logged, never shown with details
        logger.error(f"FUXA token key check error: {e}")
        return {"success": False, "checks": checks, "message": "Verification error, see the landing log."}
