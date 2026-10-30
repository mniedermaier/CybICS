# HMI Project Recon

> **MITRE ATT&CK for ICS:** `Collection` | [T0811 - Data from Information Repositories](https://attack.mitre.org/techniques/T0811/) | [T0861 - Point & Tag Identification](https://attack.mitre.org/techniques/T0861/) | [T0801 - Monitor Process State](https://attack.mitre.org/techniques/T0801/)

## Overview
An attacker who wants to stop a plant needs to know *which* value to change.
A raw Modbus scan gives you numbered registers and coils, but not what they
mean. The engineers who built the Human-Machine Interface (HMI) already
answered that question: the HMI project names the PLC, every tag (a named
process value), the address behind each tag and which button on which screen
writes it. It is the blueprint of the plant.

FUXA, the HMI at **172.18.0.4:1881**, keeps that project on its server and
sends it to every browser that opens the HMI, because the browser needs it to
draw the screens. A login is not required to get it.

Your goal is to **download FUXA's project without logging in and rebuild the
plant's I/O map from it**: which PLC the HMI talks to, which address the
STOP button writes, which coil the compressor button switches, and the tag ID
you need to read live values through the HMI itself.

## Background

### What is in an HMI project

| Part of the project | What it tells an attacker |
|---|---|
| `devices` | Every system the HMI talks to: protocol (`ModbusTCP`), address and port |
| `devices.<id>.tags` | Every process value: name, data type, Modbus area and address, and the tag's ID |
| `hmi.views` | Every screen, drawn as SVG, with its buttons and indicators |
| events on view items | Which button writes which tag when it is clicked |

Nothing in it is a password, so it is easy to treat as harmless. But it
turns "holding register 1130" into "the switch between manual and automatic mode".
That is the step from network access to a targeted attack.

### FUXA's Modbus addresses

FUXA stores a Modbus tag as an area (`memaddress`) and an address:

| `memaddress` | Modbus area |
|---|---|
| `000000` | coils (single bits the PLC drives, such as a motor on/off) |
| `100000` | discrete inputs |
| `300000` | input registers |
| `400000` | holding registers (16-bit values) |

FUXA numbers addresses **from 1**, the way many engineering tools and
datasheets do. On the wire, a Modbus request numbers them **from 0**. FUXA's
own driver subtracts one before it sends a request, so a tag at FUXA address
`1127` is holding register `1126` in the packet. Whenever you move an address
from one tool to another, check which convention each one uses.

## Where to run it

From the **attack shell** (WebShell view of the landing page, 172.18.0.100)
or the Kali attack machine. You need `curl` and Python's standard library;
the attack shell also has `pymodbus` for the optional cross-check in step 5.

## Task

The flag has the format `CybICS(flag)`. Enter four answers on the challenge
page and click **Verify**:

1. the PLC endpoint the HMI polls, as `host:port`;
2. the holding register the **STOP / SHUTDOWN** button writes, as a wire
   address (from 0);
3. the coil the **Comp.** button on the SystemView screen toggles, as a wire
   address (from 0);
4. the FUXA tag ID of the **HPT** tag (high-pressure tank).

All four have to be right at once; the page does not say which one is wrong.

### Steps

1. **Watch the HMI load.** Open `http://<board>:1881` in a browser with the
   developer tools open (F12, *Network* tab). Do not log in. Among the first
   requests is one to `/api/project`. Look at its size.

2. **Fetch it yourself, without a token.**
   ```bash
   curl -s -o project.json -w '%{http_code} %{size_download} bytes\n' \
        http://172.18.0.4:1881/api/project
   ```
   A `200` and about a hundred kilobytes: the whole project, anonymously.
   FUXA does have authentication switched on (try `GET /api/users`, it answers
   `401`), it just does not protect this request.

3. **List the devices and tags.**
   ```bash
   python3 - <<'EOF'
   import json
   p = json.load(open("project.json"))
   for dev in p["devices"].values():
       print(dev["name"], dev["type"], (dev.get("property") or {}).get("address"))
       for t in (dev.get("tags") or {}).values():
           print("   ", t["id"], t["name"], t.get("memaddress"), t.get("address"))
   EOF
   ```
   Note the PLC's address, the area and address of every tag, and the ID of
   the HPT tag. Turn each FUXA address into a wire address.

4. **Find out what the buttons do.** The screens are in `p["hmi"]["views"]`.
   Each view has `items`; a button's caption is in `property.text` (or, if
   that is empty, in the item's `name`), and its `property.events` lists what
   a click does. A click with the action `onToggleValue` flips a tag, and the
   event's `actoptions.variable.variableId` is that tag's ID. Find the STOP / SHUTDOWN
   button (it is on every screen) and the *Comp.* button on SystemView, and
   follow each to its tag and its wire address. While you are there, count
   how many different PLC values an operator can change from the HMI.

5. **Check your map against the plant (optional, read-only).**
   ```bash
   python3 -c "from pymodbus.client import ModbusTcpClient as C; c=C('172.18.0.3'); c.connect(); print(c.read_holding_registers(<wire address of HPT>, count=1).registers); c.close()"
   ```
   The right address returns the tank pressure; one off returns `0`. The HMI
   can also read it for you, without any Modbus connection of your own:
   ```bash
   curl -s -G --data-urlencode 'ids=["<HPT tag ID>"]' http://172.18.0.4:1881/api/getTagValue
   ```
   This is a second unauthenticated door: the HMI reads the PLC on behalf of
   anyone who knows a tag's ID, even from a host that cannot reach port 502.

6. **Verify.** Enter the four answers on the challenge page.

`hmi_recon.py` in this directory does steps 2 to 5 and prints the map
(`python3 hmi_recon.py --help`).

Only read. Do not click the buttons on the HMI, log in or write to the
PLC: the plant is shared with everyone else on the board.

## Detect and Defend

### Detection
- The CybICS IDS does **not** flag this. It is ordinary HTTP to the HMI, and
  every operator's browser makes exactly the same request each time it opens
  the HMI. A project download cannot be told apart from a page load.
- FUXA logs each request (`GET /api/project 200 110273`) but not the client
  address. A reverse proxy in front of the HMI that logs source addresses
  would show requests from hosts that are not operator stations, and
  `/api/project` or `/api/getTagValue` from a script (no browser
  `User-Agent`, no static files around it) stands out.

### Defense
- **Limit who can reach the HMI.** Only operator and engineering stations
  need port 1881. Anything that can reach it can read the project; see
  [Network Segmentation](../defense_network/README.md) and
  [Modbus Firewall Rules](../defense_firewall/README.md) for the same idea on
  the PLC.
- **Require a login before the HMI, not inside it.** FUXA's own permissions
  do not help here: for a user without permission, FUXA 1.2.6 marks a view
  item hidden or disables its button, but still sends the item, every device
  and every tag. An authenticating reverse proxy in front of port 1881 keeps
  the whole project from anyone without an account. Treat "view only" as a
  role that still needs one.
- **Keep secrets out of the project.** Anything the HMI may display at some
  point (a hidden label, an instruction, a password on a maintenance screen)
  is sent to every browser in advance. Hidden is not secret.
- **Treat engineering files as sensitive.** HMI projects, PLC programs and
  their backups are a complete plan of the plant. Store and share them like
  the network diagrams they effectively are.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Collection | Data from Information Repositories | [T0811](https://attack.mitre.org/techniques/T0811/) | The HMI server is a repository of engineering data, and it hands its project to anyone who asks |
| Collection | Point & Tag Identification | [T0861](https://attack.mitre.org/techniques/T0861/) | The project names every tag, its address and the controls that write it |
| Collection | Monitor Process State | [T0801](https://attack.mitre.org/techniques/T0801/) | `/api/getTagValue` returns live process values through the HMI without a login |

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Isolation | [D3-NI](https://d3fend.mitre.org/technique/d3f:NetworkIsolation/) | Only operator stations can reach the HMI |
| Application Configuration Hardening | [D3-ACH](https://d3fend.mitre.org/technique/d3f:ApplicationConfigurationHardening/) | No secrets in views; anonymous access to the HMI switched off by a login in front of it |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Access Control (AC)** | AC-3, AC-14 | Enforce access to HMI data; no actions without identification beyond what is truly needed |
| **System and Communications Protection (SC)** | SC-7 | Boundary protection around the HMI |
| **Configuration Management (CM)** | CM-7 | Least functionality: no anonymous engineering data on a production HMI |

</details>

## Hints

<details>
  <summary>💡 Hint 1</summary>

The HMI page in your browser starts empty and fills in its screens a moment
later. Where does it get them from? The browser's Network tab shows it.

</details>

<details>
  <summary>💡 Hint 2</summary>

If your register answer is off, compare FUXA's address with what a Modbus
read at that number returns. FUXA counts from 1, the wire from 0.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

From the attack shell:

```bash
cd /CybICS/training/hmi_project_recon
python3 hmi_recon.py --live
```

The device list shows the PLC at `openplc:502` (172.18.0.3). The STOP /
SHUTDOWN buttons toggle the tag `stop`, FUXA holding register 1129, wire
address **1128**. *Comp.* toggles `compressor`, FUXA coil 2, wire address
**1**. The HPT tag's ID is in the tag table. Enter the four values on the
challenge page.

</details>
