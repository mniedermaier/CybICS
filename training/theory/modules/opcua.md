# Attacking OPC-UA

In this challenge you log in to the CybICS OPC-UA server twice: first as an ordinary user whose password you have to guess, then as an administrator whose certificate has leaked. OPC-UA is the modern industrial protocol that *does* have security built in, so this module shows the uncomfortable truth behind it: the protection is only as good as the passwords and keys an operator configures.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="An OPC-UA client opens a session as a user or as an admin. The user tier can read the userFLAG node; only the admin tier can unlock the adminFLAG node.">
  <rect x="20" y="30" width="110" height="44" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="75" y="57" text-anchor="middle" font-size="11" fill="#1a1a1a">client</text>
  <defs><marker id="ou" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <line x1="130" y1="45" x2="360" y2="45" stroke="#ff6b00" stroke-width="2" marker-end="url(#ou)"/>
  <text x="245" y="39" text-anchor="middle" font-size="11">session as user / admin</text>
  <g font-size="11" text-anchor="middle">
    <rect x="362" y="24" width="140" height="26" rx="4" fill="currentColor" opacity="0.2" stroke="currentColor"/>
    <text x="432" y="41">userFLAG (user tier)</text>
    <rect x="362" y="58" width="140" height="26" rx="4" fill="#ff6b00" opacity="0.5"/>
    <text x="432" y="75" fill="#1a1a1a">adminFLAG (admin tier)</text>
  </g>
  <text x="20" y="108" font-size="11" opacity="0.7">The tier you reach depends on how you authenticate.</text>
</svg>
<figcaption>Different nodes need different privileges. Which one you reach depends on the identity you log in with, not on the protocol itself.</figcaption>
</figure>

## The idea

Think of an OPC-UA server as an office building with a reception desk. Before you get in, reception asks who you are. You can show nothing (an **anonymous** visitor), give a name and a password, or show an ID card, which in OPC-UA is an **X.509 certificate**: a digital ID card signed with a secret **private key** that only its owner should hold.

Once you are inside, your badge decides which doors open. A normal user may look at the values but not change them; an administrator may change them too. This is called **role-based access**.

An attacker does not need to break the encryption to get past reception. It is enough to:

- guess a weak password, because nobody stops you from trying thousands of them, or
- find a copy of someone else's ID card together with its private key.

Both are mistakes of configuration and handling, not of the protocol. That is the lesson: security features only protect you if they are switched on and the secrets behind them stay secret.

## How it looks on CybICS

The OPC-UA server runs in the `opcua` container at `172.18.0.5` and listens on TCP port **4840**, the standard OPC-UA port. It copies the plant values (GST, HPT and a few status values) from the PLC over Modbus and publishes them as nodes in a folder called `CybICS Variables`, next to the challenge nodes.

| What the server offers | What it means for you |
|---|---|
| Security policies `None` and `Basic256Sha256` | You can connect without encryption. Your requests, the values and your user name then travel readable; the password itself is still encrypted with the server's key, because this server asks for that. |
| Identity tokens: anonymous, username/password, certificate | All three are advertised, but the server refuses anonymous sessions. You must prove who you are. |
| Roles: user and admin | A user can browse and read; only an admin can write. |

<div class="callout cybics" markdown="1">
**On CybICS:** the endpoint advertising "anonymous" does not mean anonymous login works. Reading what a server *offers* and testing what it *accepts* are two different steps, and attackers do both.
</div>

<div data-widget="opcua-security"></div>

<div data-widget="checkpoint" data-id="anonymous"></div>

## How to approach it

1. **Find and fingerprint the server.** Confirm port 4840 is open on the OPC-UA container and ask the server for its endpoints. The answer lists its security policies and the login types it accepts.
2. **Try the cheap doors first.** Check whether an anonymous session is accepted. On CybICS it is not, so move on.
3. **Guess a password.** The challenge folder ships a list of common username and password pairs. The Metasploit OPC-UA modules from COMSYS (`opcua_hello`, `opcua_login`) try each pair against the username login for you; in the attack shell, without Metasploit, the folder's `opcua_login.py` does the same.
4. **Log in and browse.** Connect with a graphical client such as `opcua-client` using the account you found. Walk the address space and read what a user may read. Try to write a value and notice what happens.
5. **Look for a better identity.** Investigate the server's security configuration, then think about where certificates and keys live on a real site: engineering laptops, project folders, backups, code repositories. A certificate *with its private key* is all a client needs to log in as its owner.
6. **Log in as that identity** with the client's certificate options and see which nodes become writable.

<details class="deep-dive" markdown="1">
<summary>Deep dive: security policy versus identity token</summary>

OPC-UA has two separate layers. The **secure channel** decides whether messages are signed and encrypted; its security policy (`None`, `Basic256Sha256` and others) is negotiated with the server's application certificate. The **session** then carries a user identity token: anonymous, username and password, or an X.509 user certificate.

The two are independent. A client can open an unencrypted channel and still present a password. Whether that password crosses the network readable depends on the endpoint's token policy: the CybICS server asks clients to encrypt it with the server's public key, so a capture shows the user name but not the password. A server configured differently would expose both, see [OPC-UA](/theory/opcua-protocol). A client can also use a certificate as its user identity; the server maps that certificate to a role. Disabling the `None` policy and rejecting passwords on unencrypted channels closes the first gap; protecting private keys closes the second.

</details>

## Detect and defend

A password-guessing run is loud. Every attempt is a new connection to port 4840 from the same host, and the server sees each failed login.

- **Network monitoring.** The CybICS IDS raises `opcua_access` whenever a host that is not one of the plant's own services talks OPC-UA, so your attack machine shows up on the IDS dashboard.
- **Authentication monitoring.** Log failed logins and alert on bursts of them; lock out or slow down an account after a few failures.
- **Strong credentials.** Long, unique passwords make a word list useless.
- **Turn off what you do not need.** Remove the `None` security policy and the anonymous token from production servers.
- **Guard the keys.** Keep private keys out of shared folders and repositories, keep a trust list of allowed client certificates, and revoke any certificate that has leaked.

In MITRE ATT&CK for ICS this is **T0859 Valid Accounts**: once you hold a working password or certificate, you are using a legitimate identity rather than an exploit.

## Before you start

- [OPC-UA](/theory/opcua-protocol): nodes, sessions, security policies and certificates.

Later on the path:

- [Password attacks](/theory/password_attack): how guessing with a word list works.
- [Detection and monitoring](/theory/detection-monitoring): how the IDS notices you.
