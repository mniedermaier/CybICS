# Hardening credentials

In these two challenges you change the default passwords of the PLC's web interface and of the Human-Machine Interface (HMI), the screen operators use to run the plant. It is the cheapest security control there is, and one of the most often skipped. Once it is done, a default login that anyone can look up in a manual stops working.

## The idea

A new front door often comes with a key that opens every door of the same model. If nobody changes the lock after moving in, anyone who owns that model can walk in. **Default credentials** are that shared key: a username and password set at the factory and printed in the manual for everyone to read.

Industrial devices are installed for decades and often configured once, in a hurry, during commissioning. Defaults survive surprisingly often. MITRE ATT&CK for ICS lists using them as its own technique, Insecure Credentials: Default Credentials (T1694.001), and a login that works stays useful to an attacker later as Valid Accounts (T0859).

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Before hardening, the default login is accepted and a dictionary attack succeeds. After hardening with a strong, unique password, the default login is rejected.">
  <rect x="20" y="30" width="210" height="60" rx="6" fill="#ff6b00" fill-opacity="0.12" stroke="#ff6b00" stroke-width="2"/>
  <rect x="290" y="30" width="210" height="60" rx="6" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.7"/>
  <g font-size="13" text-anchor="middle" fill="currentColor">
    <text x="125" y="55" font-weight="bold">before: factory default</text>
    <text x="125" y="75" opacity="0.85">default login accepted</text>
    <text x="395" y="55" font-weight="bold">after: strong and unique</text>
    <text x="395" y="75" opacity="0.85">default login rejected</text>
  </g>
  <path d="M240 60 h38" stroke="currentColor" stroke-width="2"/><path d="M272 54 l8 6 l-8 6" fill="none" stroke="currentColor" stroke-width="2"/>
</svg>
<figcaption>Changing the defaults makes a published or guessed password worthless. The challenge check tries the old default and passes only when it is refused.</figcaption>
</figure>

## How it looks on CybICS

Two web logins guard the plant, and both start with well-known defaults that are part of the training scenario:

| System | Address | Account the check tries |
|---|---|---|
| OpenPLC web interface | `172.18.0.3`, port 8080 | `openplc` with its default password |
| FUXA HMI | `172.18.0.4`, port 1881 | `admin` with its default password |

When you press **Verify Defense**, the CybICS landing page logs in with the old default. OpenPLC answers a successful login with a redirect to its dashboard; FUXA answers with user data. If the old login still works, the check fails.

<div class="callout cybics" markdown="1">
**On CybICS:** OpenPLC has more than one user. The check only tests the `openplc` account, but a real hardening pass covers every account, including the one you cracked in the [Password attacks](/theory/password_attack) module. Look at the full user list while you are logged in.
</div>

<div data-widget="checkpoint" data-id="check"></div>

## How to approach it

1. **List the accounts.** Log in to each web interface and find where users are managed. In OpenPLC that is the Users page; in FUXA it is in the user settings of the top-right menu.
2. **Pick a strong password.** Length beats cleverness: a passphrase of four or five unrelated words resists the wordlist attacks you used earlier. Never reuse a password across systems.
3. **Change it, keep the username.** The checks expect the same usernames.
4. **Write it down safely.** If you forget it, the only way back in the lab is to reset the container. In a plant, store it in a password manager or a sealed record.
5. **Verify.** Log out, try the old password yourself, then press Verify Defense.

Try it: compare an eight-character password of random letters with a passphrase of four words (about 25 lower-case letters).

<div data-widget="keyspace"></div>

<div class="callout warning" markdown="1">
**Watch out:** In a plant, locking out operators can be as dangerous as an attacker. Coordinate a password change with everyone who uses the account, and never change one in the middle of a running operation.
</div>

## Detect and defend

A changed password stops the easy guess. These measures stop the rest:

- **Monitor logins.** The CybICS IDS rule `http_brute_force` watches login requests to ports 8080 and 1881 and alerts when one source sends five within 30 seconds. A burst of failed logins is a clear signal.
- **Slow guessing down.** Rate limits or short delays after failed attempts make wordlist attacks impractical. Full account lockout is used carefully in OT, because it can lock out an operator during an emergency.
- **Remove what you do not need.** Delete unused accounts and give each person their own login, so actions can be traced back.
- **Limit who can reach the login.** A web interface that only the engineering network can reach cannot be guessed at from elsewhere; see [Host firewalling](/theory/defense_firewall).

Standards say the same. NIST SP 800-82 points to control IA-5 (Authenticator Management), which requires changing default authenticators when a system is installed. In MITRE D3FEND this is Strong Password Policy (D3-SPP).

## Before you start

- [HMI and SCADA](/theory/hmi-scada): what the HMI is and why its login matters
- [Password attacks](/theory/password_attack): the attack this module defends against
- [Defense in depth](/theory/defense-hardening): where credentials fit among other controls
