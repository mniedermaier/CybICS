# Forged session tokens

In this challenge you become an administrator of the CybICS Human-Machine Interface (HMI) without knowing any password. The HMI trusts a signed note instead of checking who you are, and the key that signs those notes was never changed from the one in its public source code. It shows why a default secret is as dangerous as a default password.

## The idea

Websites do not ask for your password on every click. After you log in, the server hands your browser a **session token**, and every later request carries it. Many modern applications use a **JSON Web Token (JWT)** for this: a short piece of text that says who you are and what you may do, plus a signature.

<div class="callout analogy" markdown="1">
**Analogy:** a festival wristband. The guard at the gate checks your ticket once and gives you a band with a stamp. Inside, nobody checks tickets again, only the stamp. Whoever owns a copy of the stamp can make bands for people who never bought a ticket.
</div>

A JWT has three parts separated by dots: a **header**, a **payload** with the *claims* (for example the user name and the role) and a **signature**. The header and payload are only encoded, not encrypted, so anyone can read them. The signature is what the server checks. With the common method HS256 it is computed from the header, the payload and a secret **signing key**. The same key creates and checks signatures.

So the security of every session rests on one secret. If an attacker knows the key, they can write any claims they like, sign them, and the server accepts the result as genuine. No login is involved, so a strong password does not help.

<figure>
<svg viewBox="0 0 520 150" role="img" aria-label="A JSON Web Token has a header, a payload with the user name and role, and a signature computed from both with a secret key. The server recomputes the signature with its key and trusts the claims if both match.">
  <rect x="10" y="20" width="110" height="44" rx="6" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.7"/>
  <rect x="130" y="20" width="170" height="44" rx="6" fill="#ff6b00" fill-opacity="0.12" stroke="#ff6b00" stroke-width="2"/>
  <rect x="310" y="20" width="110" height="44" rx="6" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.7"/>
  <g font-size="13" text-anchor="middle" fill="currentColor">
    <text x="65" y="40" font-weight="bold">header</text>
    <text x="65" y="56" opacity="0.85">HS256</text>
    <text x="215" y="40" font-weight="bold">payload</text>
    <text x="215" y="56" opacity="0.85">user name, role</text>
    <text x="365" y="40" font-weight="bold">signature</text>
    <text x="365" y="56" opacity="0.85">needs the key</text>
    <text x="260" y="110">server: same key, same signature? then trust the payload</text>
  </g>
  <path d="M365 70 v22" stroke="currentColor" stroke-width="2"/>
  <circle cx="470" cy="42" r="18" fill="none" stroke="#ff6b00" stroke-width="2"/>
  <text x="470" y="47" font-size="12" text-anchor="middle" fill="currentColor">key</text>
  <path d="M452 42 h-26" stroke="#ff6b00" stroke-width="2"/>
</svg>
<figcaption>Anyone can read the payload. Only the signature, made with the secret key, stops someone from changing it.</figcaption>
</figure>

## How it looks on CybICS

| Host | Address | What matters here |
|---|---|---|
| FUXA | `172.18.0.4`, port 1881 | the HMI; signs JWTs with the HS256 method |

FUXA puts two claims of its own into every token: `id`, the user name, and `groups`, the role. Some group numbers mean administrator. The user list is a request only an administrator may make; without a valid administrator token FUXA refuses it.

FUXA reads its signing key from its settings file. When the file sets none, FUXA falls back to a built-in default. FUXA is open-source software, so that default is published for everyone to read. On CybICS nobody has set a key yet.

<div data-widget="checkpoint" data-id="readable"></div>

MITRE ATT&CK for ICS lists using a manufacturer's default secret as *Insecure Credentials: Default Credentials* (T1694.001). Reading the user database with the forged session is *Data from Information Repositories* (T0811).

## How to approach it

1. **Look at a real token.** Log in as a user with few rights and decode the middle part. Note which claims FUXA writes.
2. **Confirm the door is locked.** Ask for the user list with no token and with the low-rights token. Both should be refused.
3. **Find the key.** Read FUXA's source code where it handles tokens, and look for the value it uses when the settings give none.
4. **Write your own claims.** Choose a user name that has no account and an administrator role, and sign them with the key. Your token does not need an expiry time.
5. **Test it** against the user list, then hand it to the challenge page.

The challenge accepts a token only if it is one FUXA could never have issued itself, so a token obtained through FUXA's own login or refresh does not count. Change nothing in the HMI: reading is enough.

<details class="deep-dive" markdown="1">
<summary>Deep dive: why HS256 keys must be long</summary>

HS256 is HMAC with the SHA-256 hash. Checking a guess at the key needs one captured token and a few microseconds of computing, and the server never learns that someone is guessing. A single graphics card tries hundreds of millions of guesses a second, so a word, a name or a default with one digit changed falls quickly. A key of 32 or more random characters is out of reach. Asymmetric methods such as RS256 sign with a private key and check with a public one, so the servers that only check tokens never hold a key that could sign.

</details>

## Detect and defend

The forged token travels in an ordinary HTTP header of an ordinary request. The CybICS IDS sees nothing unusual, and FUXA's request log shows only that the user list was read, not by whom.

- **Set your own key.** A long random key in FUXA's settings makes every token signed with the default worthless. That is the [Rotate the FUXA Token Key](/ctf/challenge/defense_fuxa_jwt) challenge.
- **Log the user behind a request.** A session for a user name that exists in no user database is a clear sign of forgery.
- **Watch for sessions without a login.** Administrator requests from an address that never logged in deserve a look.
- **Limit who can reach the HMI.** A web interface only operator stations can reach cannot be attacked from elsewhere.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

FUXA 1.2.6 falls back to the key in api/jwt-helper.js when settings.js has no secretCode; the solution is in training/fuxa_jwt/README.md. The verify module asks the running FUXA whether the pasted token reads /api/users, requires an id that no FUXA account has, and refuses tokens whose claims are exactly id, groups, iat and exp with a lifetime of 15 min, 1 h, 3 h or 1 day. That closes a side route that needs neither the key nor a password: in FUXA 1.2.6, verifyToken skips its x-auth-user groups comparison when the token is invalid, and POST /api/heartbeat with {"params": true} then signs {id, groups} straight from x-auth-user. So x-access-token: garbage plus x-auth-user: {"user":"ghost","groups":-1} returns a FUXA-signed administrator token for any client, on the default key and after the defence rotated it. Those tokens have FUXA's exact claim set and lifetime and are refused here. The route is a good candidate for a separate, later challenge (unauthenticated token refresh, CWE-287/CWE-306), with port restriction as its defence; until then, mention it when discussing the defence, because rotating the key does not close it. A token with exactly FUXA's claims and a FUXA lifetime forged with the key is also refused; the README tells students to leave out iat and exp.

</details>

## Before you start

- [HMI and SCADA](/theory/hmi-scada): what the HMI is and why it is a target
- [Password attacks](/theory/password_attack): the login this attack walks around

Later on the path:

- [Rotating a signing key](/theory/defense_fuxa_jwt): the defence for this attack
