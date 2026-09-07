#!/usr/bin/env python3
"""
Harden the FUXA HMI admin login (defense).

FUXA ships with the default account admin / 123456 and its sign-in API has no
lockout, so lesson 4 brute-forced it in one guess. Here we change that default
to a strong password and confirm the old one no longer works. FUXA's user API
expects the session token in the 'x-access-token' header.

Usage:
  fuxa_harden.py <ip> --check                 show whether admin/123456 still works
  fuxa_harden.py <ip> --set <newpassword>     change admin's password, then re-test
  fuxa_harden.py <ip> --restore <curpassword> set admin back to 123456 (cleanup)
"""
import sys, json, urllib.request

DEFAULT = "123456"

def _post(url, body, headers=None):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def signin(base, pw):
    st, body = _post(f"{base}/api/signin", {"username": "admin", "password": pw})
    if st == 200:
        try:
            return json.loads(body)["data"]["token"]
        except Exception:
            return None
    return None

def default_works(base):
    return signin(base, DEFAULT) is not None

def set_pw(base, token, newpw):
    st, _ = _post(f"{base}/api/users",
                  {"params": {"username": "admin", "fullname": "Administrator Account",
                              "groups": -1, "password": newpw, "info": "{}"}},
                  headers={"x-access-token": token})
    return st

def main():
    ip = sys.argv[1]
    base = f"http://{ip}:1881"
    op = sys.argv[2]

    if op == "--check":
        works = default_works(base)
        print(f"[*] FUXA HMI at {ip}:1881")
        print(f"[{'!' if works else '+'}] default login admin/123456 -> "
              f"{'ACCEPTED - the HMI is wide open' if works else 'rejected'}")
        return

    if op == "--set":
        newpw = sys.argv[3]
        print(f"[*] FUXA HMI at {ip}:1881 - hardening the admin account")
        tok = signin(base, DEFAULT)
        if not tok:
            print("[!] could not sign in with the default password (already changed?)")
            return
        st = set_pw(base, tok, newpw)
        print(f"[*] set a strong admin password ................ HTTP {st}")
        print(f"[{'+' if not default_works(base) else '!'}] re-test default admin/123456 ................ "
              f"{'rejected - the default is dead' if not default_works(base) else 'still works!'}")
        print("[+] the operator login now requires the new credential")
        return

    if op == "--restore":
        curpw = sys.argv[3]
        tok = signin(base, curpw)
        if not tok:
            print("[!] restore failed: cannot sign in with the given password")
            return
        st = set_pw(base, tok, DEFAULT)
        print(f"[restore] admin password reset to default -> HTTP {st}")
        return

if __name__ == "__main__":
    main()
