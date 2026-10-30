"""
Challenge check: the student claimed OpenPLC's forgotten REST API (openplc_restapi).

Next to its web interface on 8080, OpenPLC v3 runs a second management API
over HTTPS on port 8443 (webserver/restapi.py). It has a user database of its
own, separate from the web interface's, and it ships empty. While it is
empty, POST /api/create-user needs no authentication and the caller chooses
the account and its role: whoever finds the port first owns the API, and
with it start-plc, stop-plc, runtime-logs and upload-file (replace and
compile the PLC program). CWE-306, Missing Authentication for Critical
Function.

The student types the user name and password of the account they created.
The check logs in with them (POST /api/login), uses the token it gets for an
authenticated read of the user list and the PLC status, and passes when the
user list contains that name. It writes nothing: no account is created,
changed or deleted, and the PLC is not started or stopped. The token is
discarded; it expires on its own after 15 minutes.

The password must have at least MIN_PASSWORD characters. An account on a
management API with a one-letter password is not a claim worth the name, and
the length test lets a wrong answer fail before anything is sent to the PLC.
"""
import warnings

import requests
from urllib3.exceptions import InsecureRequestWarning

from utils.config import PLC_HOST
from utils.logger import logger

REST_PORT = 8443
REST_URL = f"https://{PLC_HOST}:{REST_PORT}/api"
MIN_PASSWORD = 8
TIMEOUT = 10


def _fail(checks, message):
    return {"success": False, "message": message, "checks": checks}


def _request(method, path, **kwargs):
    """One request to the REST API. OpenPLC generates a self-signed
    certificate at first start, so there is nothing to verify it against."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InsecureRequestWarning)
        return requests.request(method, f"{REST_URL}{path}", verify=False,
                                timeout=TIMEOUT, **kwargs)


def verify(answers=None):
    answers = answers or {}
    username = (answers.get("username") or "").strip()
    password = answers.get("password") or ""
    checks = []

    long_enough = len(password) >= MIN_PASSWORD
    checks.append({
        "name": "Password length",
        "passed": long_enough,
        "detail": f"At least {MIN_PASSWORD} characters" if long_enough
        else f"Claim the API with a password of at least {MIN_PASSWORD} characters. "
             "If your account has a shorter one, change it with PUT "
             "/api/password-change/<id> or delete the account and create it again",
    })
    if not username or not long_enough:
        return _fail(checks, "Enter the user name and password of the account you created "
                             f"on the REST API (port {REST_PORT}).")

    try:
        resp = _request("POST", "/login", json={"username": username, "password": password})
        token = None
        if resp.status_code == 200:
            token = (resp.json() or {}).get("access_token")
        checks.append({
            "name": f"Login on the REST API (port {REST_PORT})",
            "passed": bool(token),
            "detail": "POST /api/login returned an access token" if token
            else f"POST /api/login answered {resp.status_code}. The REST API has its own "
                 "user database: the web interface's login on port 8080 does not work here",
        })
        if not token:
            return _fail(checks, "These credentials do not log in to OpenPLC's REST API.")
        auth = {"Authorization": f"Bearer {token}"}

        users = _request("GET", "/get-users-info", headers=auth)
        listed = users.status_code == 200 and isinstance(users.json(), list)
        names = {u.get("username") for u in users.json()} if listed else set()
        claimed = username in names
        checks.append({
            "name": "Account in the API's user table",
            "passed": claimed,
            "detail": f"The authenticated user list holds {len(names)} account(s), yours among them"
            if claimed else f"GET /api/get-users-info answered {users.status_code} without your account",
        })
        if not claimed:
            return _fail(checks, "The REST API does not list your account.")

        status = _request("GET", "/status", headers=auth)
        state = (status.json() or {}).get("status") if status.status_code == 200 else None
        checks.append({
            "name": "Authenticated PLC command",
            "passed": bool(state),
            "detail": f"GET /api/status answered {state}" if state
            else f"GET /api/status answered {status.status_code}",
        })
        if not state:
            return _fail(checks, "The token from your login was not accepted for a PLC command.")

        return {"success": True,
                "message": "You own OpenPLC's management API: an account nobody was asked to "
                           "approve, with a token that can stop or reprogram the PLC. Give it "
                           "back now: delete your account (README, last step) so the next "
                           "student finds the API unclaimed.",
                "checks": checks}

    except requests.exceptions.RequestException:
        checks.append({"name": "REST API reachable", "passed": False,
                       "detail": f"Cannot connect to {PLC_HOST}:{REST_PORT}"})
        return _fail(checks, "Cannot reach OpenPLC's REST API.")
    except (ValueError, AttributeError):
        checks.append({"name": "REST API answer", "passed": False,
                       "detail": "The REST API did not answer with the expected JSON"})
        return _fail(checks, "OpenPLC's REST API gave an unexpected answer.")
    except Exception as e:  # pragma: no cover - logged, never shown with details
        logger.error(f"OpenPLC REST API check error: {e}")
        return _fail(checks, "Verification error, see the landing log.")
