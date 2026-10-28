"""
Challenge check: a forged FUXA administrator token (challenge fuxa_jwt).

The student pastes a JSON Web Token. It passes when the running FUXA accepts
it as an administrator (GET /api/users answers 200), the token names a user
FUXA does not have, and its claims are not ones FUXA could have signed
itself. The last check matters: FUXA 1.2.6 signs an administrator token for
any name, for any client and without a password, through its token refresh in
POST /api/heartbeat (see _fuxa_jwt.fuxa_could_issue). That route works
whatever the key is, so it proves nothing about the key. Every FUXA-issued
token carries exactly id, groups, iat and exp with one of FUXA's lifetimes,
so a token with any other claim set or lifetime can only come from someone
who holds the signing key: the default key from FUXA's source code.

The check asks FUXA itself rather than recomputing the signature, so it also
holds if the key is ever changed. It sends only GET requests and never echoes
the token, the user list or the password hashes FUXA returns.
"""
import requests

from modules.defense_checks._fuxa_jwt import decode, fuxa_could_issue, get_users, security_enabled
from utils.logger import logger


def _fail(checks, message):
    return {"success": False, "message": message, "checks": checks}


def verify(answers=None):
    token = ((answers or {}).get("token") or "").strip()
    checks = []

    decoded = decode(token)
    checks.append({
        "name": "Token format",
        "passed": decoded is not None,
        "detail": "Three base64url parts with a JSON header and payload" if decoded
        else "Not a JSON Web Token: expected header.payload.signature in base64url",
    })
    if decoded is None:
        return _fail(checks, "Paste the complete token, three base64url parts separated by dots.")
    _header, payload = decoded
    user_id = payload.get("id")
    if not isinstance(user_id, str) or not user_id or "groups" not in payload:
        checks.append({"name": "FUXA claims", "passed": False,
                       "detail": "FUXA reads the claims 'id' (a user name) and 'groups'"})
        return _fail(checks, "The payload needs the two claims FUXA reads: 'id' and 'groups'.")
    checks.append({"name": "FUXA claims", "passed": True,
                   "detail": "The payload carries 'id' and 'groups'"})

    own = fuxa_could_issue(payload)
    checks.append({
        "name": "Not a token FUXA issues itself",
        "passed": not own,
        "detail": "Its claims are not the set FUXA signs (id, groups, iat, exp with a "
                  "FUXA lifetime)" if not own
        else "id, groups, iat and exp with a lifetime of 15 min, 1 h, 3 h or 1 day is exactly "
             "what FUXA signs at login or token refresh, so it proves nothing about the key. "
             "Leave out iat/exp, or choose your own lifetime",
    })
    if own:
        return _fail(checks, "This could be a token FUXA signed itself. Forge one FUXA would never issue.")

    try:
        ok, detail = security_enabled()
        checks.append({"name": "FUXA authentication on", "passed": ok, "detail": detail})
        if not ok:
            return _fail(checks, "FUXA must run with authentication switched on to judge a token.")

        resp = get_users(token)
        accepted = resp.status_code == 200 and isinstance(resp.json(), list)
        checks.append({
            "name": "Accepted as administrator",
            "passed": accepted,
            "detail": "FUXA returned its user list for this token" if accepted
            else f"FUXA answered {resp.status_code}: wrong key, expired, or not an admin group",
        })
        if not accepted:
            return _fail(checks, "FUXA does not accept this token as an administrator.")

        # Case-insensitive and ignoring surrounding blanks: "Admin" or " admin"
        # is not a clearly fictitious user.
        usernames = {u.get("username").strip().casefold() for u in resp.json()
                     if isinstance(u, dict) and isinstance(u.get("username"), str)}
        ghost = user_id.strip().casefold() not in usernames
        checks.append({
            "name": "User that does not exist",
            "passed": ghost,
            "detail": "No FUXA account has this name: no login could have issued it" if ghost
            else "The token names a real FUXA account (names are compared ignoring case), "
                 "which a stolen or logged-in session could also give you",
        })
        if not ghost:
            return _fail(checks, "Forge it for a user name FUXA has never heard of.")

        return {"success": True,
                "message": "FUXA accepted an administrator token for a user that does not exist. "
                           "Only the signing key can make one.",
                "checks": checks}

    except requests.exceptions.RequestException:
        checks.append({"name": "FUXA reachable", "passed": False,
                       "detail": "Cannot connect to FUXA at 172.18.0.4:1881"})
        return _fail(checks, "Cannot reach FUXA.")
    except ValueError:
        checks.append({"name": "FUXA answer", "passed": False,
                       "detail": "FUXA did not answer with JSON"})
        return _fail(checks, "FUXA gave an unexpected answer.")
    except Exception as e:  # pragma: no cover - logged, never shown with details
        logger.error(f"FUXA token check error: {e}")
        return _fail(checks, "Verification error, see the landing log.")
