#!/usr/bin/env python3
"""
Claim OpenPLC's REST API on port 8443, use it, and give it back.

    python3 openplc_restapi.py probe                       # is the API unclaimed?
    python3 openplc_restapi.py claim  --user U --password P # create the first account, log in, read
    python3 openplc_restapi.py release --user U --password P # delete that account again

Only the Python standard library is used. OpenPLC's certificate is
self-signed, so it is not verified. Nothing here stops, starts or
reprograms the PLC.
"""
import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request

_TLS = ssl.create_default_context()
_TLS.check_hostname = False
_TLS.verify_mode = ssl.CERT_NONE


def call(base, method, path, body=None, token=None):
    """(HTTP status, decoded JSON or text) of one API request."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=_TLS, timeout=10) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read()
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw.decode(errors="replace")


def login(base, user, password):
    status, answer = call(base, "POST", "/login", {"username": user, "password": password})
    if status != 200 or not isinstance(answer, dict) or "access_token" not in answer:
        sys.exit(f"login failed: {status} {answer}")
    return answer["access_token"]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["probe", "claim", "release"])
    parser.add_argument("--host", default="172.18.0.3")
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--user", default="")
    parser.add_argument("--password", default="")
    args = parser.parse_args()
    base = f"https://{args.host}:{args.port}/api"

    if args.action == "probe":
        for path in ("/ping", "/get-users-info"):
            print(f"GET /api{path}".ljust(26), "->", *call(base, "GET", path))
        return

    if not args.user or len(args.password) < 8:
        sys.exit("--user and a --password of at least 8 characters are needed")

    if args.action == "claim":
        status, answer = call(base, "POST", "/create-user",
                              {"username": args.user, "password": args.password})
        print("POST /api/create-user".ljust(26), "->", status, answer)
        if status not in (201, 409):
            sys.exit("the API is already claimed by someone else")
        token = login(base, args.user, args.password)
        print("POST /api/login".ljust(26), "-> 200, token of", len(token), "characters")
        for path in ("/get-users-info", "/status"):
            print(f"GET /api{path}".ljust(26), "->", *call(base, "GET", path, token=token))
        print("\nNow verify on the challenge page with this user name and password,"
              "\nthen run: python3 openplc_restapi.py release --user ... --password ...")
        return

    token = login(base, args.user, args.password)
    _, users = call(base, "GET", "/get-users-info", token=token)
    mine = [u["id"] for u in users if isinstance(u, dict) and u.get("username") == args.user]
    if not mine:
        sys.exit(f"{args.user} is not in the user list")
    path = f"/delete-user/{mine[0]}"
    print(f"DELETE /api{path}".ljust(26), "->", *call(base, "DELETE", path, token=token))
    print("GET /api/get-users-info".ljust(26), "->", *call(base, "GET", "/get-users-info"))


if __name__ == "__main__":
    main()
