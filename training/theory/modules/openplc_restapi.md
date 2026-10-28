# The forgotten API

In this challenge you take over a management interface of the CybICS controller that nobody on the plant uses and nobody ever set up. You do not guess or steal a password: the interface lets the first visitor create one. It shows why a device has to be judged by every interface it offers, not only by the one the operators know.

## The idea

Many devices and programs start in a **setup mode**. They have no users yet, so the first person who connects may create the administrator account. On a workbench that is convenient. On a network it is a race: whoever arrives first becomes the owner, and the real owner may not even know that there is something to claim.

<div class="callout analogy" markdown="1">
**Analogy:** a new building has a staff entrance at the back. The keypad on it still waits for its first code, and whoever types one in sets it. The caretaker locked the front door carefully, but never walked round to the back.
</div>

Security people call this *Missing Authentication for Critical Function* (CWE-306): an action that should need a login does not ask for one, at least in some state. MITRE ATT&CK for ICS files the abuse of such a flaw in a remote service as *Exploitation of Remote Services* (T0866), and using the account it gives you afterwards as *Valid Accounts* (T0859).

## How it looks on CybICS

The CybICS PLC runs OpenPLC at `172.18.0.3`. Its web interface on port 8080 is the one you know from the password challenges. OpenPLC version 3 also starts a second web server: a **REST API** over HTTPS on port 8443. A REST API is a web interface for programs instead of people: each address under `/api` does one thing, and the answers come back as JSON text.

| Interface | Port | Users |
|---|---|---|
| Web interface | 8080 | its own database, ships with one default account |
| REST API | 8443 | a separate database that **ships empty** |

The API can report the PLC's state, show its runtime log, stop and start the PLC and replace its program. While its user database is empty, it creates an account for anyone who asks, with the name, password and role the caller chooses. After a login it hands out a JSON Web Token (JWT), a signed note your requests carry instead of the password, valid for 15 minutes.

Changing the password of the web interface does nothing here: the two interfaces do not share their users.

<div data-widget="checkpoint" data-id="separate"></div>

## How to approach it

1. **Scan beyond the ports you know.** A service scan of the PLC lists every port it answers on, with a guess at the software behind it.
2. **Talk to the unknown port.** It speaks HTTPS with a certificate the PLC made for itself, so tell your client not to check it. Ask simple questions first: what does it answer without a login?
3. **Read what the answers give away.** An interface that tells a stranger how many users it has is telling you whether it is still in setup mode.
4. **Claim it, log in and read.** Create an account, log in for a token, and use the token for harmless reads such as the PLC's status. Do not stop the PLC: the plant is shared.
5. **Prove it and give it back.** The challenge page asks for your account's name and password and checks them on the API. Afterwards delete your account, so the next student finds the API as you did.

<details class="deep-dive" markdown="1">
<summary>Deep dive: why the role field does not matter</summary>

The account request has an optional `role`, and you can ask for `admin`. OpenPLC stores it, but no route checks it: every account may call every command, including the ones that stop the PLC or upload a program. The role is a placeholder for a feature that was never finished. That is common in young interfaces, and one more reason not to leave them reachable.

</details>

## Detect and defend

The CybICS IDS sees the port scan, but nothing after it. The API's traffic is encrypted, and no IDS rule watches port 8443 on the PLC. What remains is OpenPLC's own log: every API request appears there with the address it came from, so the moment an account was created is on record for anyone who reads it.

Defences:

- **Claim it yourself.** If an interface is needed, create its first account during commissioning, with a strong password, before the device is connected to the network.
- **Switch off or block what you do not use.** CybICS does not need the REST API. A service that is off cannot be claimed; if it cannot be switched off, a firewall rule on the PLC that drops port 8443 keeps it out of reach.
- **Keep an inventory of every interface.** Compare a full scan of each device with the list of interfaces you meant to offer. The forgotten ones are the dangerous ones.
- **Watch the logs of management interfaces.** An account nobody on the team created is an incident.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The verify module logs in on 172.18.0.3:8443 with the typed credentials, reads `/api/get-users-info` and `/api/status` with the token, and passes when the account is listed; it needs a password of at least eight characters and writes nothing. The REST API's user database survives a restart of the OpenPLC container but not its re-creation. If a student leaves the API claimed, the README's *Reset* section empties the user table from the admin shell without restarting the PLC. A student with a token can stop the PLC (`/api/stop-plc`) or replace its program (`/api/upload-file`), and the IDS does not see either; `/api/start-plc` restarts it. Pairs well with the firewall challenge as a follow-up: drop 8443 on the PLC.

</details>

## Before you start

- [Network scanning](/theory/scanning) for service scans with nmap.
- [Password attacks](/theory/password_attack) for the OpenPLC web interface and its login.
- [Forged session tokens](/theory/fuxa_jwt) for what a JWT is.

Later on the path:

- [Host firewalling](/theory/defense_firewall): how a rule on the PLC closes a port.
