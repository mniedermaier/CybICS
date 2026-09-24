# OPC-UA

**OPC Unified Architecture (OPC-UA)** is the modern, vendor-neutral standard for industrial data exchange, on port **4840**. Unlike Modbus and classic S7comm it was designed with security in the protocol: sessions, user identities, certificates, signing and encryption. It is the one protocol on this plant you *can* secure.

Which is a different statement from "it is secure". Everything below was measured against the server running in this testbed, and most of what makes it interesting is where the configuration and the standard pull in opposite directions.

## The handshake decides nothing until the last step

A client does not simply connect and read. It opens a **secure channel**, creates a **session**, and then *activates* that session with a user identity. Four exchanges, and only the last one asks who you are.

<figure>
<style>
/* Two clocks that stay in phase: the four messages replay every 6 s, the
   identity being offered changes every 6 s as well but cycles through three
   over 18 s. 18 is an exact multiple of 6, so a run never starts mid-sequence. */
.article figure {overflow-x: auto;}
.article figure svg.ua-h {min-width: 520px;}
.ua-h {--m: 6s; --i: 18s;}
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
@keyframes ua-m1 {0%,4.9%{opacity:0}  5%,100%{opacity:1}}
@keyframes ua-m2 {0%,24.9%{opacity:0} 25%,100%{opacity:1}}
@keyframes ua-m3 {0%,44.9%{opacity:0} 45%,100%{opacity:1}}
@keyframes ua-m4 {0%,64.9%{opacity:0} 65%,100%{opacity:1}}
@keyframes ua-vd {0%,81.9%{opacity:0} 82%,100%{opacity:1}}
@keyframes ua-A {0%,33.32%{opacity:1} 33.33%,100%{opacity:0}}
@keyframes ua-B {0%,33.32%{opacity:0} 33.33%,66.65%{opacity:1} 66.66%,100%{opacity:0}}
@keyframes ua-C {0%,66.65%{opacity:0} 66.66%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) {
  /* Everything meaningful is already in the base rules above, so this only
     has to stop the motion. */
  .ua-h * {animation:none !important;}
}
</style>
<svg class="ua-h" viewBox="0 0 520 252" role="img"
     aria-label="An OPC-UA session being established four messages at a time. Hello and Acknowledge, then OpenSecureChannel, then CreateSession, all of which succeed for every client. The fourth message, ActivateSession, carries the user identity, and only there is the client accepted or refused. An anonymous identity is refused with BadUserAccessDenied; the username user1 is accepted with the User role, which may read but not write; the registered admin certificate is accepted with the Admin role, which may also write.">
  <rect x="10" y="12" width="104" height="40" rx="6" fill="#ff6b00"/>
  <text x="62" y="37" text-anchor="middle" font-size="13" font-weight="bold" style="fill:#1a1a1a">Client</text>
  <rect x="406" y="12" width="104" height="40" rx="6" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="458" y="31" text-anchor="middle" font-size="13" font-weight="bold">CybICS server</text>
  <text x="458" y="46" text-anchor="middle" font-size="12" opacity="0.85">:4840</text>
  <defs>
    <marker id="ua-a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff6b00"/></marker>
  </defs>
  <g font-size="12">
    <g class="m1">
      <line x1="114" y1="82" x2="404" y2="82" stroke="#ff6b00" stroke-width="2" marker-end="url(#ua-a)"/>
      <text x="259" y="76" text-anchor="middle">1. HEL / ACK &mdash; agree on buffer sizes</text>
    </g>
    <g class="m2">
      <line x1="114" y1="114" x2="404" y2="114" stroke="#ff6b00" stroke-width="2" marker-end="url(#ua-a)"/>
      <text x="259" y="108" text-anchor="middle">2. OpenSecureChannel &mdash; pick a policy</text>
    </g>
    <g class="m3">
      <line x1="114" y1="146" x2="404" y2="146" stroke="#ff6b00" stroke-width="2" marker-end="url(#ua-a)"/>
      <text x="259" y="140" text-anchor="middle">3. CreateSession &mdash; still nobody has said who they are</text>
    </g>
    <g class="m4">
      <line x1="114" y1="182" x2="404" y2="182" stroke="#ff6b00" stroke-width="3" marker-end="url(#ua-a)"/>
      <text x="259" y="176" text-anchor="middle" font-weight="bold">4. ActivateSession &mdash; the identity travels here</text>
      <g font-size="12" font-weight="bold">
        <text class="idA" x="259" y="200" text-anchor="middle" fill="#ff6b00">identity: Anonymous</text>
        <text class="idB" x="259" y="200" text-anchor="middle" fill="#ff6b00">identity: user1 + password</text>
        <text class="idC" x="259" y="200" text-anchor="middle" fill="#ff6b00">identity: the admin certificate</text>
      </g>
    </g>
  </g>
  <g class="vd" font-size="12">
    <g class="vA">
      <rect x="86" y="216" width="348" height="26" rx="4" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
      <text x="260" y="234" text-anchor="middle" font-weight="bold">refused here: BadUserAccessDenied &mdash; no session at all</text>
    </g>
    <g class="vB">
      <rect x="86" y="216" width="348" height="26" rx="4" fill="#ff6b00"/>
      <text x="260" y="234" text-anchor="middle" font-weight="bold" style="fill:#1a1a1a">role User &mdash; may read every node, may write none</text>
    </g>
    <g class="vC">
      <rect x="86" y="216" width="348" height="26" rx="4" fill="#ff6b00"/>
      <text x="260" y="234" text-anchor="middle" font-weight="bold" style="fill:#1a1a1a">role Admin &mdash; may read and write</text>
    </g>
  </g>
</svg>
<figcaption>The first three exchanges run identically for everybody, including a client that will be thrown out a moment later. Watch where the three runs differ: not at the channel, at step 4. That is the shape of the whole protocol &mdash; transport security and identity are separate decisions, and the identity one is made last.</figcaption>
</figure>

This matters because the two halves are genuinely independent. You can have an encrypted channel carrying an anonymous user, or a completely unencrypted channel carrying an administrator's certificate. "We use OPC-UA with encryption" answers only one of the two questions.

On this server the roles come from `SimpleRoleRuleset`, whose own docstring is the clearest statement of the model: *admins alone can write, admins and users can read, and anonymous users can't do anything*. That last clause is not a formality. An anonymous client here does not get a read-only view; it is refused at `ActivateSession` with `BadUserAccessDenied` and never holds a session. Connecting anonymously against the running server returns exactly that.

`software/opcua/opcua.py` offers two channel policies, `NoSecurity` and `Basic256Sha256_SignAndEncrypt`, and three identity tokens, `Anonymous`, `Username` and `Basic256Sha256` (certificate). Anonymous is accepted as a *token* and then denied every *action*, which is why the failure arrives one step later than you might expect.

## What an unencrypted channel actually leaks

The obvious conclusion is that a `None` channel hands a sniffer everything. Captured off the bridge while a client logged in with `user1`, it does not.

<figure>
<style>
.article figure svg.ua-w {min-width: 520px;}
.ua-w {--w: 12s;}
/* The playhead sweeps the four fields of the identity token in turn; the
   read-out underneath says what a sniffer gets from the field it is over. */
.ua-w .ph {animation: uw-ph var(--w) steps(4,end) infinite;}
.ua-w .r1 {opacity:0; animation: uw-r1 var(--w) steps(1,end) infinite;}
.ua-w .r2 {opacity:0; animation: uw-r2 var(--w) steps(1,end) infinite;}
.ua-w .r3 {opacity:1; animation: uw-r3 var(--w) steps(1,end) infinite;}
.ua-w .r4 {opacity:0; animation: uw-r4 var(--w) steps(1,end) infinite;}
.ua-w .f1 {animation: uw-f1 var(--w) steps(1,end) infinite;}
.ua-w .f2 {animation: uw-f2 var(--w) steps(1,end) infinite;}
.ua-w .f3 {animation: uw-f3 var(--w) steps(1,end) infinite;}
.ua-w .f4 {animation: uw-f4 var(--w) steps(1,end) infinite;}
/* Base state is the third field, the password -- the one the figure exists
   to make a point about. */
.ua-w .ph {transform: translateX(216px);}
.ua-w .f3 {stroke-width:3;}
@keyframes uw-ph {0%{transform:translateX(0)} 100%{transform:translateX(432px)}}
@keyframes uw-f1 {0%,24.9%{stroke-width:3} 25%,100%{stroke-width:0}}
@keyframes uw-f2 {0%,24.9%{stroke-width:0} 25%,49.9%{stroke-width:3} 50%,100%{stroke-width:0}}
@keyframes uw-f3 {0%,49.9%{stroke-width:0} 50%,74.9%{stroke-width:3} 75%,100%{stroke-width:0}}
@keyframes uw-f4 {0%,74.9%{stroke-width:0} 75%,100%{stroke-width:3}}
@keyframes uw-r1 {0%,24.9%{opacity:1} 25%,100%{opacity:0}}
@keyframes uw-r2 {0%,24.9%{opacity:0} 25%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes uw-r3 {0%,49.9%{opacity:0} 50%,74.9%{opacity:1} 75%,100%{opacity:0}}
@keyframes uw-r4 {0%,74.9%{opacity:0} 75%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .ua-w * {animation:none !important;} }
</style>
<svg class="ua-w" viewBox="0 0 520 186" role="img"
     aria-label="The four fields of an OPC-UA username identity token as they appear on an unencrypted channel. The policy identifier reads username in clear text. The user name reads user1 in clear text. The password is an RSA-OAEP ciphertext and reveals nothing. The fourth field names the algorithm, rsa-oaep, in clear text. A sniffer therefore harvests account names but not passwords.">
  <text x="10" y="22" font-size="13" font-weight="bold">UserNameIdentityToken, channel policy None</text>
  <g font-size="12">
    <rect class="f1" x="10" y="38" width="108" height="40" rx="4" fill="#ff6b00" stroke="#1a1a1a" stroke-width="0"/>
    <text x="64" y="55" text-anchor="middle" style="fill:#1a1a1a" font-size="11">policyId</text>
    <text x="64" y="71" text-anchor="middle" style="fill:#1a1a1a" font-weight="bold">"username"</text>
    <rect class="f2" x="126" y="38" width="108" height="40" rx="4" fill="#ff6b00" stroke="#1a1a1a" stroke-width="0"/>
    <text x="180" y="55" text-anchor="middle" style="fill:#1a1a1a" font-size="11">userName</text>
    <text x="180" y="71" text-anchor="middle" style="fill:#1a1a1a" font-weight="bold">"user1"</text>
    <rect class="f3" x="242" y="38" width="140" height="40" rx="4" fill="currentColor" fill-opacity="0.18" stroke="#ff6b00" stroke-width="0"/>
    <text x="312" y="55" text-anchor="middle" font-size="11" opacity="0.85">password</text>
    <text x="312" y="71" text-anchor="middle" font-weight="bold" font-family="monospace">b7 2d 22 8f 3a &hellip;</text>
    <rect class="f4" x="390" y="38" width="120" height="40" rx="4" fill="#ff6b00" stroke="#1a1a1a" stroke-width="0"/>
    <text x="450" y="55" text-anchor="middle" style="fill:#1a1a1a" font-size="11">encryptionAlgorithm</text>
    <text x="450" y="71" text-anchor="middle" style="fill:#1a1a1a" font-weight="bold">rsa-oaep</text>
  </g>
  <g class="ph"><path d="M 6 84 L 14 84 L 10 92 Z" fill="#ff6b00"/><line x1="10" y1="92" x2="10" y2="100" stroke="#ff6b00" stroke-width="2"/></g>
  <text x="10" y="126" font-size="13" font-weight="bold" opacity="0.85">what a capture gives you:</text>
  <g font-size="13" font-weight="bold">
    <text class="r1" x="10" y="148" fill="#ff6b00">the token type &mdash; this client is using a password</text>
    <text class="r2" x="10" y="148" fill="#ff6b00">the account name &mdash; "user1", in clear text</text>
    <text class="r3" x="10" y="148" fill="#ff6b00">nothing: RSA-OAEP under the server's public key</text>
    <text class="r4" x="10" y="148" fill="#ff6b00">the algorithm that protected it</text>
  </g>
  <text x="10" y="172" font-size="12" opacity="0.85">Channel policy: None throughout. The password still never appeared.</text>
</svg>
<figcaption>Four fields, swept left to right, with the read-out underneath saying what each one yields. The token encrypts its own password with the server's certificate whatever the channel does, so an unencrypted OPC-UA session leaks account names and leaks no passwords. That is a narrower hole than Modbus has, and it is still a hole: a name is half a credential, and knowing the account exists is what makes guessing worth starting.</figcaption>
</figure>

Measured, not assumed: in a capture of a full `user1` login taken on the container bridge, the string `user1` appears in clear text inside the `ActivateSessionRequest`, the password `test` appears **zero** times anywhere in the capture, and the token carries `http://www.w3.org/2001/04/xmlenc#rsa-oaep` immediately after it. The channel in the same capture negotiated `http://opcfoundation.org/UA/SecurityPolicy#None`.

This is why the *OPC-UA* challenge brute-forces logins against the live server rather than cracking a captured hash: there is no captured hash. Every guess costs a round trip, and every round trip is visible.

## The admin flag is written, not read

The user-tier flag is an ordinary variable; a `User` session reads it directly. The admin-tier one is not a value sitting in the address space waiting to be found &mdash; it is empty until the server puts it there.

<figure>
<style>
.article figure svg.ua-f {min-width: 520px;}
.ua-f {--f: 14s;}
.ua-f .sweep {transform-origin: 72px 84px; animation: uf-sweep 2s linear infinite;}
.ua-f .wr   {opacity:0; animation: uf-wr var(--f) steps(1,end) infinite;}
.ua-f .z0   {opacity:0; animation: uf-z0 var(--f) steps(1,end) infinite;}
.ua-f .z1   {opacity:1; animation: uf-z1 var(--f) steps(1,end) infinite;}
.ua-f .fl0  {opacity:0; animation: uf-fl0 var(--f) steps(1,end) infinite;}
.ua-f .fl1  {opacity:1; animation: uf-fl1 var(--f) steps(1,end) infinite;}
.ua-f .deny {opacity:0; animation: uf-deny var(--f) steps(1,end) infinite;}
@keyframes uf-sweep {to {transform: rotate(360deg);}}
/* A User write is refused at 20%; the Admin write lands at 50%; the server's
   own loop notices on its next pass, at 57%, and replaces the value. The gap
   between 50% and 57% is the point -- nothing the client did changed the flag
   node, the loop did. */
@keyframes uf-deny{0%,19.9%{opacity:0} 20%,39.9%{opacity:1} 40%,100%{opacity:0}}
@keyframes uf-wr  {0%,49.9%{opacity:0} 50%,69.9%{opacity:1} 70%,100%{opacity:0}}
@keyframes uf-z0  {0%,49.9%{opacity:1} 50%,100%{opacity:0}}
@keyframes uf-z1  {0%,49.9%{opacity:0} 50%,100%{opacity:1}}
@keyframes uf-fl0 {0%,56.9%{opacity:1} 57%,100%{opacity:0}}
@keyframes uf-fl1 {0%,56.9%{opacity:0} 57%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .ua-f * {animation:none !important;} }
</style>
<svg class="ua-f" viewBox="0 0 520 210" role="img"
     aria-label="The server's own loop drives the admin flag. A User session's write to the trigger variable is refused with BadUserAccessDenied. An Admin session's write sets the trigger from zero to one. On its next pass the server loop reads the trigger, finds it above zero, and replaces the admin flag node's text with the flag. The client never writes the flag node itself.">
  <circle cx="72" cy="84" r="34" fill="none" stroke="currentColor" stroke-opacity="0.65" stroke-width="2"/>
  <path class="sweep" d="M 72 50 A 34 34 0 0 1 106 84" fill="none" stroke="#ff6b00" stroke-width="3"/>
  <text x="72" y="80" text-anchor="middle" font-size="12" font-weight="bold">server</text>
  <text x="72" y="95" text-anchor="middle" font-size="12" font-weight="bold">loop</text>
  <text x="72" y="140" text-anchor="middle" font-size="12" opacity="0.85">polls every pass</text>

  <rect x="168" y="46" width="164" height="44" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="250" y="64" text-anchor="middle" font-size="11" opacity="0.85">"Set &gt; 0 to obtain flag!"</text>
  <text class="z0" x="250" y="82" text-anchor="middle" font-size="14" font-weight="bold" fill="#ff6b00">0</text>
  <text class="z1" x="250" y="82" text-anchor="middle" font-size="14" font-weight="bold" fill="#ff6b00">1</text>

  <rect x="358" y="46" width="152" height="44" rx="5" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-opacity="0.7"/>
  <text x="434" y="64" text-anchor="middle" font-size="11" opacity="0.85">adminFLAG</text>
  <text class="fl0" x="434" y="82" text-anchor="middle" font-size="12">set the correct variable</text>
  <text class="fl1" x="434" y="82" text-anchor="middle" font-size="12" font-weight="bold" fill="#ff6b00">CybICS(&hellip;)</text>

  <defs><marker id="ua-b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <line x1="108" y1="68" x2="164" y2="68" stroke="currentColor" stroke-opacity="0.65" stroke-width="2" marker-end="url(#ua-b)"/>
  <line x1="336" y1="68" x2="354" y2="68" stroke="currentColor" stroke-opacity="0.65" stroke-width="2" marker-end="url(#ua-b)"/>
  <text x="250" y="116" text-anchor="middle" font-size="11" opacity="0.85">the loop reads this &hellip;</text>
  <text x="434" y="116" text-anchor="middle" font-size="11" opacity="0.85">&hellip; and writes this</text>

  <g class="wr">
    <line x1="250" y1="172" x2="250" y2="96" stroke="#ff6b00" stroke-width="3" marker-end="url(#ua-b)"/>
    <text x="264" y="168" font-size="13" font-weight="bold" fill="#ff6b00">Admin writes 1</text>
  </g>
  <g class="deny">
    <line x1="250" y1="172" x2="250" y2="140" stroke="currentColor" stroke-opacity="0.7" stroke-width="3"/>
    <path d="M 240 138 L 260 122 M 240 122 L 260 138" stroke="currentColor" stroke-opacity="0.85" stroke-width="3"/>
    <text x="264" y="162" font-size="13" font-weight="bold">User writes 1:</text>
    <text x="264" y="177" font-size="13" font-weight="bold">BadUserAccessDenied</text>
  </g>
  <text x="10" y="200" font-size="12" opacity="0.85">The client never touches the flag node &mdash; it sets one integer and waits.</text>
</svg>
<figcaption>Two writes to the same variable, one refused and one accepted, and then a pause before anything visible happens. That pause is the lesson: the write lands on a trigger, and the server's own loop is what replaces the flag text on its next pass. A client that writes the trigger and reads back instantly sees the old value and concludes it failed.</figcaption>
</figure>

Reaching `Admin` is not a matter of a better password. `admin_db` in `software/opcua/user_manager.py` is empty &mdash; its only entry is commented out &mdash; so no username and password combination reaches the admin role at all. Admin is bound to one certificate, registered at start-up by `add_admin("certificates/trusted/cert_admin.der")`, and that certificate and its private key are both in the repository. The challenge is a leaked-key exercise wearing the clothes of a password exercise, which is the more realistic of the two: keys leak more quietly than passwords, and nothing expires them here.

## Where it goes wrong in general

- **SecurityPolicy None** &mdash; the channel is neither signed nor encrypted. Reads, writes and node names are all in the clear, and a sniffer learns the address space for free. The password token is a separate mechanism and survives this; nothing else does.
- **Anonymous access** &mdash; harmless on this server because the ruleset gives anonymous no permissions, and dangerous on a server that gives it read access, which is the common default.
- **Certificates trusted too broadly, or leaked.** A certificate in a repository is a credential in a repository.

## Detection

The IDS has a rule for this, and it is deliberately blunt: **rule 9, `opcua_access`**, fires on any TCP payload of eight bytes or more to port 4840 whose source is not one of four named services &mdash; `hwio`, `fuxa`, `openplc` and `opcua` itself. That list is narrower than the IDS's general `KNOWN_SERVICES` table on purpose; exempting every service meant traffic from the attack box went unnoticed.

It does not try to tell a login from a read, or a good certificate from a bad one. It asks one question &mdash; is this host supposed to be speaking OPC-UA at all &mdash; and any answer of "no" is a low-severity alert mapped to **T0846 Remote System Discovery**. Repeats from the same source are collapsed to one alert per thirty seconds, so a brute-force run of hundreds of attempts produces a slow trickle rather than a flood. Two probes from a host thirty-one seconds apart produced exactly two alerts in the IDS log, which is the cooldown doing its job.

That is the trade every rule on this plant makes. A rule this blunt cannot be evaded by being careful on the wire, only by coming from an address that belongs there &mdash; which is the same lesson the *Network Segmentation* and *IDS Evasion* modules arrive at from the other side.
