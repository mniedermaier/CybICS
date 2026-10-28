# Rotate the FUXA Token Key

> **MITRE D3FEND:** `Harden` | [D3-CRO - Credential Rotation](https://d3fend.mitre.org/technique/d3f:CredentialRotation/) | [D3-ACH - Application Configuration Hardening](https://d3fend.mitre.org/technique/d3f:ApplicationConfigurationHardening/)

## Overview
In the [Forged HMI Token](../fuxa_jwt/README.md) challenge you signed an
administrator token for the FUXA HMI with the key printed in FUXA's source
code. A new password does not help against that: the forged token never went
through a login. The fix is to give FUXA a **signing key of its own**.

FUXA reads the key from `secretCode` in its configuration file
`/_appdata/settings.js`, inside the FUXA container. Once it is set to a long
random value and FUXA is restarted, every token signed with the default key,
including the ones you forged, is refused, and every user simply logs in
again.

A new key closes the forged-token attack, **not every way to an admin
session**: FUXA 1.2.6 has a second flaw that the key does not touch (see
[What the new key does not fix](#what-the-new-key-does-not-fix)).

The flag has the format `CybICS(flag)`. **Verify Defense** reveals it when

- the FUXA HMI is running with authentication switched on, and still issues
  and accepts tokens with its own key;
- tokens signed with the default key, variations of it and common words are
  all refused;
- the `secretCode` in `settings.js` is at least **32 characters** long and
  uses at least **10 different characters** (40 times `a` is long, but not
  random). The check reads only these two numbers, never the key.

## The pitfall: do not just uncomment the example

`settings.js` is not a list of options but a JavaScript program: one object
literal, `module.exports = { ... }`, whose entries are separated by commas.
Near the end it contains, commented out,

```js
    "allowedOrigins": ["http://localhost", "http://127.0.0.1", "http://192.168.*", "http://10.*"]
    ...
    //secureEnabled: true,
    //secretCode: 'frangoteam751',
```

`allowedOrigins` is the last active entry and has **no trailing comma**.
Removing the `//` in front of `secretCode` puts a new entry right after it
without a separating comma. That is a syntax error: FUXA fails to load its
settings, exits, and Docker restarts it in a loop. The HMI is gone until the
file is fixed. (Uncommenting would also restore the published default key.)

Instead, put the key on **its own line straight after `module.exports = {`**,
with a comma at its end. The first entry of an object literal never needs a
comma in front of it, so nothing else in the file changes.

## Steps

All commands run in the landing page's **admin shell** (WebShell view,
*Admin shell*), which has access to Docker. The attack shell has none. The
admin shell has no interactive terminal, so every command is a complete
`docker exec`.

1. **Find the FUXA container.**
   ```bash
   docker ps --format '{{.Names}}' | grep fuxa
   ```
   Use that name for `<fuxa>` below (`virtual-fuxa-1` in the virtual lab).

2. **Back up the settings.**
   ```bash
   docker exec <fuxa> cp /_appdata/settings.js /_appdata/settings.js.bak
   ```

3. **Generate a key and add it.** 24 random bytes are 48 hex characters:
   ```bash
   KEY=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n'); docker exec <fuxa> sed -i "/^module.exports = {/a\    secretCode: \"$KEY\"," /_appdata/settings.js
   ```
   It is one command line on purpose: the admin shell starts a new shell for
   every command, so `KEY` would be gone on the next line. The key is not
   printed; you never need to type it.

4. **Check the file before restarting.** Node loads it exactly as FUXA will:
   ```bash
   docker exec <fuxa> head -3 /_appdata/settings.js
   docker exec <fuxa> node -e "const s=require('/_appdata/settings.js'); console.log('ok, key length', s.secretCode.length)"
   ```
   You want `ok, key length 48`. A `SyntaxError` means the file is broken:
   restore the backup (`docker exec <fuxa> cp /_appdata/settings.js.bak /_appdata/settings.js`)
   and try again. Never restart FUXA with a file that does not load.

5. **Restart FUXA.**
   ```bash
   docker restart <fuxa>
   ```
   Wait until the HMI on port 1881 answers again (a few seconds). Everyone
   who was logged in has to log in again: their old tokens were signed with
   the old key.

6. **Test the attack.** From the attack shell, the token you forged in the
   Forged HMI Token challenge now gets `401`:
   ```bash
   python3 /CybICS/training/fuxa_jwt/fuxa_jwt.py
   ```

7. Click **Verify Defense**.

### Undoing it

```bash
docker exec <fuxa> cp /_appdata/settings.js.bak /_appdata/settings.js
docker restart <fuxa>
```

## What the new key does not fix

FUXA 1.2.6 has a token-refresh request (`POST /api/heartbeat`) that signs a
fresh token for whatever user name and groups the client puts in its
`x-auth-user` header. FUXA only compares that header with the token when the
token is valid; send an invalid one, any garbage, and the comparison is
skipped. So any client that can reach port 1881 can ask FUXA for an
administrator token, without a password, and FUXA signs it **with your new
key**. Rotating the key does not change that.

That is a flaw in FUXA's code, not in its configuration, so no setting in
`settings.js` closes it. What helps:

- **Limit who can reach port 1881** to the operator stations that need the
  HMI, with a firewall or network segmentation (see
  [Network Segmentation](../defense_network/README.md)). This is the
  mitigation you can apply today.
- **Upgrade or patch FUXA** once a version verifies the token before it
  refreshes it, and check the release notes of every update for such fixes.
- **Watch for it**: an administrator session for a user name that is in no
  user database, or that never logged in, is the trace it leaves.

The key is still worth rotating: it ends tokens forged offline with the
published default, which need no access to FUXA at all until they are used,
and it is the setting a later FUXA fix will rely on.

## How long the change lasts

The key lives in the FUXA container's file system.

- **Virtual lab (Docker on a PC):** `docker restart` keeps it, but recreating
  the container does not. `./cybics.sh update`, a changed image or
  `docker compose up --force-recreate` start FUXA from its image again, with
  the default key. Your admin password from the Credential Hardening
  challenge is lost the same way.
- **CybICS board (Raspberry Pi):** FUXA's `/_appdata` is a Docker volume, so
  the key survives restarts, updates and reboots.

In a real plant the key belongs in configuration management, so that a
redeployment brings the hardened setting back instead of the vendor default.

## Detect and Defend

- **Rotate after exposure.** A new key invalidates every token that exists,
  forged or stolen. Rotate it whenever a token or the settings file may have
  leaked, and when staff with access leave.
- **Protect the file.** Anyone who can read `settings.js` can forge tokens
  again. Keep it out of backups that leave the plant network and out of
  version control.
- **Length beats cleverness.** HS256 keys can be attacked offline: one
  captured token lets an attacker test millions of keys a second without
  FUXA noticing. A random key of 32 characters or more is out of reach; a
  word, a name or the default with a digit changed is not. The check tries
  several such variations.
- **Watch for sessions without a login.** Successful admin requests from an
  address that never posted to `/api/signin` deserve a look.
- **Limit access to port 1881.** It is the only defence against FUXA's
  token-refresh flaw described above.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques Defended Against

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Persistence, Lateral Movement | Insecure Credentials: Default Credentials | [T1694.001](https://attack.mitre.org/techniques/T1694/001/) | The published default signing key no longer opens the HMI |
| Collection | Data from Information Repositories | [T0811](https://attack.mitre.org/techniques/T0811/) | A session forged with the default key can no longer read FUXA's user database (the token-refresh flaw still can, see above) |

### MITRE D3FEND - Defensive Techniques Applied

| Technique | ID | Description |
|-----------|-----|-------------|
| Credential Rotation | [D3-CRO](https://d3fend.mitre.org/technique/d3f:CredentialRotation/) | Replacing the signing key invalidates every token made with the old one |
| Application Configuration Hardening | [D3-ACH](https://d3fend.mitre.org/technique/d3f:ApplicationConfigurationHardening/) | Setting `secretCode` instead of relying on the built-in default |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Identification and Authentication (IA)** | IA-5 | Authenticator management: change default authenticators, keys included |
| **System and Communications Protection (SC)** | SC-12 | Cryptographic key establishment and management |
| **Configuration Management (CM)** | CM-2, CM-6 | A baseline configuration that keeps the hardened setting across redeployments |

</details>

## Hints

<details>
  <summary>💡 Hint</summary>

The key lives in `/_appdata/settings.js` inside the FUXA container. Put it on
its own line straight after `module.exports = {` rather than uncommenting the
example further down, check the file still loads with `node`, then restart
FUXA.

</details>
