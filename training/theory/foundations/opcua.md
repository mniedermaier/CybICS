# OPC-UA

**OPC Unified Architecture (OPC-UA)** is the modern, vendor-neutral standard for exchanging industrial data. Unlike [Modbus](/theory/modbus) and classic [S7comm](/theory/s7comm), it was designed with security built in: logins, certificates, signing and encryption. It is the one protocol on the CybICS plant that *can* be secured, and this article shows why "can" is not the same as "is".

## Two separate questions

When a client connects to an OPC-UA server, two different things are decided. It helps to keep them apart from the start:

1. **Is the line protected?** This is the **security policy** of the *secure channel*, the connection between client and server. With policy `None` everything travels in readable form. With a policy like `Basic256Sha256` and the mode *SignAndEncrypt*, every message is **signed** (the receiver can tell whether it was changed) and **encrypted** (an eavesdropper sees only scrambled bytes).
2. **Who are you?** This is the **user identity token** the client presents. It can be *Anonymous* (no identity at all), a *username and password*, or an *X.509 certificate*, a digital ID card backed by a secret key that only its owner holds.

<div class="callout analogy" markdown="1">
**Analogy:** the security policy is the envelope: open postcard or sealed, tamper-evident letter. The identity token is the ID card you show at the door. A sealed envelope tells you nothing about who wrote the letter, and showing an ID card does not stop anyone from reading your postcard.
</div>

The two are independent. You can have an encrypted channel carrying an anonymous user, or an unencrypted channel carrying an administrator's certificate. So "we use OPC-UA with encryption" answers only the first question.

The CybICS server (`software/opcua/opcua.py`, port **4840**) offers:

| Question | What the server offers |
|---|---|
| Security policy | `None`, and `Basic256Sha256` with SignAndEncrypt |
| Identity token | Anonymous, Username and password, Certificate |

Offering a token type is not the same as accepting every client who uses it. Which identities are actually let in is decided by the server's user manager (`software/opcua/user_manager.py`), as the next section shows.

## The handshake

A client does not simply connect and read. It opens the secure channel, creates a **session**, and then *activates* that session with its identity. Only that last step asks who you are.

<figure class="wide">
<style>
/* Two clocks that stay in phase: the four messages replay every 8 s and the
   identity cycles through three over 24 s. 24 is an exact multiple of 8, so a
   run never starts mid-sequence. */
.ua-h {--m: 8s; --i: 24s;}
/* The base state is a complete run, not an empty diagram: a browser that drops
   animations (a print, a preview, a screenshot) gets the middle case, which is
   the one the challenge actually walks. */
.ua-h .m1,.ua-h .m2,.ua-h .m3,.ua-h .m4,.ua-h .vd {opacity:1;}
.ua-h .idA,.ua-h .idC,.ua-h .vA,.ua-h .vC {opacity:0;}
.ua-h .idB,.ua-h .vB {opacity:1;}
.ua-h .m1 {animation: ua-m1 var(--m) steps(1,end) infinite;}
.ua-h .m2 {animation: ua-m2 var(--m) steps(1,end) infinite;}
.ua-h .m3 {animation: ua-m3 var(--m) steps(1,end) infinite;}
.ua-h .m4 {animation: ua-m4 var(--m) steps(1,end) infinite;}
.ua-h .vd {animation: ua-vd var(--m) steps(1,end) infinite;}
.ua-h .idA,.ua-h .vA {animation: ua-A var(--i) steps(1,end) infinite;}
.ua-h .idB,.ua-h .vB {animation: ua-B var(--i) steps(1,end) infinite;}
.ua-h .idC,.ua-h .vC {animation: ua-C var(--i) steps(1,end) infinite;}
/* The verdict is the only thing in this figure the prose cannot also tell
   you, and it used to be on screen for 1.08 s in every 18. The four messages
   are compressed into the first 46% of an 8 s cycle so the verdict gets the
   remaining 4.3 s -- enough to read a 51-character line once. */
@keyframes ua-m1 {0%,3.9%{opacity:0}  4%,100%{opacity:1}}
@keyframes ua-m2 {0%,13.9%{opacity:0} 14%,100%{opacity:1}}
@keyframes ua-m3 {0%,25.9%{opacity:0} 26%,100%{opacity:1}}
@keyframes ua-m4 {0%,37.9%{opacity:0} 38%,100%{opacity:1}}
@keyframes ua-vd {0%,45.9%{opacity:0} 46%,100%{opacity:1}}
@keyframes ua-A {0%,33.32%{opacity:1} 33.33%,100%{opacity:0}}
@keyframes ua-B {0%,33.32%{opacity:0} 33.33%,66.65%{opacity:1} 66.66%,100%{opacity:0}}
@keyframes ua-C {0%,66.65%{opacity:0} 66.66%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) {
  /* Everything meaningful is already in the base rules above, so this only
     has to stop the motion. */
  .ua-h * {animation:none !important;}
}
</style>
<svg class="ua-h" viewBox="0 0 400 252" role="img"
     aria-label="An OPC-UA session being established four messages at a time. Hello and Acknowledge, then OpenSecureChannel, then CreateSession, all of which succeed for every client. The fourth message, ActivateSession, carries the user identity, and only there is the client accepted or refused. An anonymous identity is refused with BadUserAccessDenied; the username user1 is accepted with the User role, which may read but not write; the registered admin certificate is accepted with the Admin role, which may also write.">
  <rect x="8" y="12" width="88" height="40" rx="6" fill="#ff6b00"/>
  <text x="52" y="37" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">Client</text>
  <rect x="296" y="12" width="96" height="40" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="344" y="31" text-anchor="middle" font-size="12" font-weight="bold">CybICS server</text>
  <text x="344" y="46" text-anchor="middle" font-size="12" opacity="0.85">:4840</text>
  <defs>
    <marker id="ua-a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff6b00"/></marker>
  </defs>
  <g font-size="12">
    <g class="m1">
      <line x1="96" y1="82" x2="294" y2="82" stroke="#ff6b00" stroke-width="2" marker-end="url(#ua-a)"/>
      <text x="198" y="76" text-anchor="middle">1. HEL / ACK &mdash; agree on buffer sizes</text>
    </g>
    <g class="m2">
      <line x1="96" y1="114" x2="294" y2="114" stroke="#ff6b00" stroke-width="2" marker-end="url(#ua-a)"/>
      <text x="198" y="108" text-anchor="middle">2. OpenSecureChannel &mdash; pick a policy</text>
    </g>
    <g class="m3">
      <line x1="96" y1="146" x2="294" y2="146" stroke="#ff6b00" stroke-width="2" marker-end="url(#ua-a)"/>
      <text x="198" y="140" text-anchor="middle">3. CreateSession &mdash; nobody has said who they are yet</text>
    </g>
    <g class="m4">
      <line x1="96" y1="182" x2="294" y2="182" stroke="#ff6b00" stroke-width="3" marker-end="url(#ua-a)"/>
      <text x="198" y="176" text-anchor="middle" font-weight="bold">4. ActivateSession &mdash; the identity travels here</text>
      <g font-size="12" font-weight="bold">
        <text class="idA" x="198" y="200" text-anchor="middle" fill="#ff6b00">identity: Anonymous</text>
        <text class="idB" x="198" y="200" text-anchor="middle" fill="#ff6b00">identity: user1 + password</text>
        <text class="idC" x="198" y="200" text-anchor="middle" fill="#ff6b00">identity: the admin certificate</text>
      </g>
    </g>
  </g>
  <g class="vd" font-size="12">
    <g class="vA">
      <rect x="28" y="216" width="344" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
      <text x="200" y="234" text-anchor="middle" font-weight="bold">refused at step 4 &mdash; BadUserAccessDenied</text>
    </g>
    <g class="vB">
      <rect x="28" y="216" width="344" height="26" rx="4" fill="#ff6b00"/>
      <text x="200" y="234" text-anchor="middle" font-weight="bold" style="fill:#1a1a1a">role User &mdash; may read every node, may write none</text>
    </g>
    <g class="vC">
      <rect x="28" y="216" width="344" height="26" rx="4" fill="#ff6b00"/>
      <text x="200" y="234" text-anchor="middle" font-weight="bold" style="fill:#1a1a1a">role Admin &mdash; may read and write</text>
    </g>
  </g>
</svg>
<figcaption>The first three steps run the same for every client, even one that is refused a moment later. Identity is checked only at step 4, ActivateSession. Channel security and identity are separate decisions, and the identity decision comes last.</figcaption>
</figure>

## Roles: what each identity may do

Once a session is active, every request is checked against the user's **role**. CybICS uses the library's standard rule set (`SimpleRoleRuleset`), which has three levels:

| Identity | Result on CybICS | Role | May read | May write |
|---|---|---|---|---|
| Anonymous | refused at ActivateSession | none | no | no |
| Username `user1` with the right password | accepted | User | yes | no |
| The registered admin certificate | accepted | Admin | yes | yes |

The anonymous case deserves a closer look. The server *advertises* the Anonymous token, so a client may offer it, and the first three steps succeed. Then the user manager finds no username and no certificate, returns no user, and `ActivateSession` fails with `BadUserAccessDenied`. An anonymous client gets no read-only view; it gets nothing.

No username and password reaches the Admin role: the admin password list in `user_manager.py` is empty. The only way to Admin is a certificate that the server registered as an administrator when it started. A certificate is only as safe as its private key, so the key file must never leave the machine that owns it.

<div data-widget="checkpoint" data-id="roles"></div>

## In CybICS: the address space

OPC-UA organises data as **nodes** in a tree, the **address space**, much like files in folders. The CybICS server has one folder, `CybICS Variables`, with these nodes:

- `GST` and `HPT`: the two tank pressures. Every two seconds the server reads holding registers 1124 and 1126 from OpenPLC over Modbus and copies them into these nodes. Reading `HPT` over OPC-UA is reading Modbus register 1126 through a gateway that adds logins in front.
- `systemSen`, `boSen`, `STOP` and `manual`: more plant values copied the same way.
- `userFLAG`: readable by any User session.
- A trigger variable named `Set > 0 to obtain flag!`, and `adminFLAG`, which only changes after that trigger has been written.

The admin part of the challenge is therefore a *write*, and only an Admin may write:

<figure class="wide">
<style>
.ua-f {--f: 14s;}
.ua-f .sweep {transform-origin: 52px 74px; animation: uf-sweep 2s linear infinite;}
/* Base state shows the accepted write, the trigger at 1 and the flag still
   holding its prompt -- cause before effect, which is the frame that matches
   the caption. Switching the animations off used to leave a populated flag
   with no write anywhere on screen. */
.ua-f .wr   {opacity:1; animation: uf-wr var(--f) steps(1,end) infinite;}
.ua-f .deny {opacity:0; animation: uf-deny var(--f) steps(1,end) infinite;}
.ua-f .z0   {opacity:0; animation: uf-z0 var(--f) steps(1,end) infinite;}
.ua-f .z1   {opacity:1; animation: uf-z1 var(--f) steps(1,end) infinite;}
.ua-f .fl0  {opacity:1; animation: uf-fl0 var(--f) steps(1,end) infinite;}
.ua-f .fl1  {opacity:0; animation: uf-fl1 var(--f) steps(1,end) infinite;}
@keyframes uf-sweep {to {transform: rotate(360deg);}}
/* A User write is refused at 20%. The Admin write lands at 50%. The loop
   notices on its next pass -- `await asyncio.sleep(2)` -- and the flag changes
   at 57%, one second of a 14 s loop later. That gap is the figure. */
@keyframes uf-deny{0%,19.9%{opacity:0} 20%,39.9%{opacity:1} 40%,100%{opacity:0}}
@keyframes uf-wr  {0%,49.9%{opacity:0} 50%,69.9%{opacity:1} 70%,100%{opacity:0}}
@keyframes uf-z0  {0%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes uf-z1  {0%,49.9%{opacity:0} 50%,100%{opacity:1}}
@keyframes uf-fl0 {0%,56.9%{opacity:1} 57%,100%{opacity:0}}
@keyframes uf-fl1 {0%,56.9%{opacity:0} 57%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .ua-f * {animation:none !important;} }
</style>
<svg class="ua-f" viewBox="0 0 360 248" role="img"
     aria-label="The server's own loop drives the admin flag. A User session's write to the trigger variable is refused with BadUserAccessDenied. An Admin session's write sets the trigger from zero to one. Up to two seconds later, on its next pass, the loop reads the trigger, finds it above zero, and replaces the admin flag node's text with the flag. The client never writes the flag node itself.">
  <defs><marker id="ua-b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <circle cx="52" cy="74" r="34" fill="none" stroke="currentColor" stroke-opacity="0.65" stroke-width="2"/>
  <path class="sweep" d="M 52 40 A 34 34 0 0 1 86 74" fill="none" stroke="#ff6b00" stroke-width="3"/>
  <text x="52" y="70" text-anchor="middle" font-size="12" font-weight="bold">server</text>
  <text x="52" y="85" text-anchor="middle" font-size="12" font-weight="bold">loop</text>
  <text x="52" y="128" text-anchor="middle" font-size="12" opacity="0.85">every 2 s</text>

  <rect x="118" y="26" width="228" height="44" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="222" y="44" text-anchor="middle" font-size="11" opacity="0.85">"Set &gt; 0 to obtain flag!"</text>
  <text class="z0" x="222" y="62" text-anchor="middle" font-size="14" font-weight="bold">0</text>
  <text class="z1" x="222" y="62" text-anchor="middle" font-size="14" font-weight="bold">1</text>
  <line x1="88" y1="48" x2="114" y2="48" stroke="currentColor" stroke-opacity="0.65" stroke-width="2" marker-end="url(#ua-b)"/>
  <text x="352" y="20" text-anchor="end" font-size="11" opacity="0.85">the loop reads this &hellip;</text>

  <rect x="118" y="100" width="228" height="48" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="222" y="118" text-anchor="middle" font-size="11" opacity="0.85">adminFLAG</text>
  <text class="fl0" x="222" y="136" text-anchor="middle" font-size="12">"set the correct variable &gt; 0"</text>
  <text class="fl1" x="222" y="136" text-anchor="middle" font-size="13" font-weight="bold">the admin flag</text>
  <line x1="88" y1="122" x2="114" y2="122" stroke="currentColor" stroke-opacity="0.65" stroke-width="2" marker-end="url(#ua-b)"/>
  <text x="352" y="164" text-anchor="end" font-size="11" opacity="0.85">&hellip; and writes this, up to 2 s later</text>

  <g class="wr">
    <path d="M 222 216 L 104 216 L 104 60 L 114 60" fill="none" stroke="#ff6b00" stroke-width="3" marker-end="url(#ua-b)"/>
    <text x="222" y="232" text-anchor="middle" font-size="13" font-weight="bold" fill="#ff6b00">Admin writes 1</text>
  </g>
  <g class="deny">
    <line x1="222" y1="216" x2="222" y2="190" stroke="currentColor" stroke-opacity="0.7" stroke-width="3"/>
    <path d="M 212 188 L 232 172 M 212 172 L 232 188" stroke="currentColor" stroke-opacity="0.85" stroke-width="3"/>
    <text x="222" y="228" text-anchor="middle" font-size="13" font-weight="bold">User writes 1:</text>
    <text x="222" y="243" text-anchor="middle" font-size="13" font-weight="bold">BadUserAccessDenied</text>
  </g>
</svg>
<figcaption>Two writes to the same trigger variable: a User session is refused, an Admin session is accepted. The flag text does not change at once. The server's own loop checks the trigger every two seconds and only then fills in <code>adminFLAG</code>, so read it again after a moment. With motion switched off, the figure shows the moment after the accepted write.</figcaption>
</figure>

## What an unencrypted channel leaks

You might expect a `None` channel to hand an eavesdropper everything, passwords included. On this server it does not, and the reason teaches you something about OPC-UA.

<figure class="wide">
<style>
.ua-w {--w: 12s;}
/* The playhead sweeps the four fields of the identity token in turn; the
   read-out underneath says what a sniffer gets from the field it is over. */
.ua-w .ph {animation: uw-ph var(--w) steps(1,end) infinite;}
.ua-w .r1 {opacity:0; animation: uw-r1 var(--w) steps(1,end) infinite;}
.ua-w .r2 {opacity:0; animation: uw-r2 var(--w) steps(1,end) infinite;}
.ua-w .r3 {opacity:1; animation: uw-r3 var(--w) steps(1,end) infinite;}
.ua-w .r4 {opacity:0; animation: uw-r4 var(--w) steps(1,end) infinite;}

/* Base state is the third field, the password -- the one the figure exists
   to make a point about. */
.ua-w .ph {transform: translateX(249px);}

/* The marker apex is at x=10, so a translate of t puts it at 10+t; the four
   field centres are 55, 155, 259 and 354, so each translate is that minus
   ten. An even four-step sweep put the marker under the wrong box for three
   of the four steps and never reached the last box at all. */
@keyframes uw-ph {0%,24.9%{transform:translateX(45px)}  25%,49.9%{transform:translateX(145px)}
                  50%,74.9%{transform:translateX(249px)} 75%,100%{transform:translateX(344px)}}

@keyframes uw-r1 {0%,24.9%{opacity:1} 25%,100%{opacity:0}}
@keyframes uw-r2 {0%,24.9%{opacity:0} 25%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes uw-r3 {0%,49.9%{opacity:0} 50%,74.9%{opacity:1} 75%,100%{opacity:0}}
@keyframes uw-r4 {0%,74.9%{opacity:0} 75%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .ua-w * {animation:none !important;} }
</style>
<svg class="ua-w" viewBox="0 0 400 186" role="img"
     aria-label="The four fields of an OPC-UA username identity token as they appear on an unencrypted channel. The policy identifier reads username in clear text. The user name reads user1 in clear text. The password is an RSA-OAEP ciphertext and reveals nothing. The fourth field names the algorithm, rsa-oaep, in clear text. A sniffer therefore harvests account names but not passwords.">
  <text x="8" y="22" font-size="13" font-weight="bold">UserNameIdentityToken, channel policy None</text>
  <g font-size="12">
    <rect class="f1" x="8" y="38" width="94" height="40" rx="4" fill="#ff6b00"/>
    <text x="55" y="55" text-anchor="middle" style="fill:#1a1a1a" font-size="11">policyId</text>
    <text x="55" y="71" text-anchor="middle" style="fill:#1a1a1a" font-weight="bold">"username"</text>
    <rect class="f2" x="108" y="38" width="94" height="40" rx="4" fill="#ff6b00"/>
    <text x="155" y="55" text-anchor="middle" style="fill:#1a1a1a" font-size="11">userName</text>
    <text x="155" y="71" text-anchor="middle" style="fill:#1a1a1a" font-weight="bold">"user1"</text>
    <rect class="f3" x="208" y="38" width="102" height="40" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
    <text x="259" y="55" text-anchor="middle" font-size="11" opacity="0.85">password</text>
    <text x="259" y="71" text-anchor="middle" font-weight="bold" font-family="monospace">b7 2d 22 &hellip;</text>
    <rect class="f4" x="316" y="38" width="76" height="40" rx="4" fill="#ff6b00"/>
    <text x="354" y="55" text-anchor="middle" style="fill:#1a1a1a" font-size="11">algorithm</text>
    <text x="354" y="71" text-anchor="middle" style="fill:#1a1a1a" font-weight="bold">rsa-oaep</text>
  </g>
  <g class="ph"><path d="M 6 84 L 14 84 L 10 92 Z" fill="#ff6b00"/><line x1="10" y1="92" x2="10" y2="100" stroke="#ff6b00" stroke-width="2"/></g>
  <text x="8" y="126" font-size="13" font-weight="bold" opacity="0.85">what a capture gives you:</text>
  <g font-size="13" font-weight="bold">
    <text class="r1" x="8" y="148" fill="#ff6b00">the token type &mdash; this client is using a password</text>
    <text class="r2" x="8" y="148" fill="#ff6b00">the account name &mdash; "user1", in clear text</text>
    <text class="r3" x="8" y="148" fill="#ff6b00">nothing: RSA-OAEP under the server's public key</text>
    <text class="r4" x="8" y="148" fill="#ff6b00">the algorithm that protected it</text>
  </g>
  <text x="8" y="172" font-size="12" opacity="0.85">Channel policy None throughout. The password never appeared.</text>
</svg>
<figcaption>The four fields of a username token on an unencrypted channel. The token type, the user name and the algorithm are readable; the password is encrypted with the server's public key because this endpoint's token policy asks for it. A server whose token policy is also <code>None</code> would send the password in readable form.</figcaption>
</figure>

Each endpoint can attach its own security policy to the identity token, separate from the channel. On the CybICS `None` endpoint the username token asks for `Basic256Sha256`, so a well-behaved client encrypts the password with the server's public key before sending it. The user name, however, travels in readable form. On the encrypted endpoint the channel already protects everything, so the token needs no extra policy.

That is still a gap: a captured user name is half of a credential, and a server configured differently would put the password in readable form too. It also explains why the *OPC-UA* challenge guesses passwords against the live server instead of cracking a captured one. Every guess is a round trip the network can see.

## Detect and defend

The CybICS IDS watches OPC-UA with one simple rule. **Rule 9** (`opcua_access`) raises a low-severity alert when a host other than `hwio`, `fuxa`, `openplc` or `opcua` itself sends traffic to port 4840. It does not try to tell a login from a read, or a good certificate from a bad one. It only asks: is this host supposed to speak OPC-UA at all? Like the other rules it reports each source at most once every 30 seconds, so a long password-guessing run shows up as a slow trickle of alerts.

To defend a real OPC-UA server:

- Offer only signed and encrypted security policies, and disable `None`.
- Disable the Anonymous token, rather than relying on the user manager to refuse it.
- Use strong passwords and lock accounts after repeated failures, so guessing does not scale.
- Protect private keys like passwords, and revoke a certificate the moment its key may have leaked.

In MITRE ATT&amp;CK for ICS, logging in with a guessed password or a stolen certificate is **T0859 Valid Accounts**: the attacker uses a real identity the server accepts. The IDS rule maps OPC-UA access from an unexpected host to **T0846 Remote System Discovery**. The [Defence and hardening](/theory/defense-hardening) article covers these measures in more depth.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

- The OPC-UA mirrors of some plant values do not match the PLC: `systemSen` and `boSen` are read from holding registers 2 and 3 (not 1132 and 1134) and stay at 0, and `STOP` and `manual` are read from 1129 and 1131 rather than 1128 and 1130 (`%MW104`, `%MW106`). `GST` and `HPT` are correct. Students comparing OPC-UA with Modbus may notice this.
- `training/opcua/README.md` says the passwords of the brute-force run can be read in plaintext in Wireshark. With the asyncua server used here, the `None` endpoint asks clients to encrypt the password, so whether it appears depends on the client honouring the token policy. Let students check their own capture.
- `training/README.md` maps the challenge to T0859 and T0866. T0859 fits well; T0866 (Exploitation of Remote Services) describes exploiting a software flaw, which the challenge does not do.

</details>
