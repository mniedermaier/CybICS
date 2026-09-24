# OPC-UA

**OPC Unified Architecture (OPC-UA)** is the modern, vendor-neutral standard for industrial data exchange, on port **4840**. Unlike Modbus and classic S7comm it was designed with security in the protocol: sessions, user identities, certificates, signing and encryption. It is the one protocol on this plant you *can* secure.

Which is a different statement from "it is secure". Everything below was measured against the server running in this testbed, and most of what makes it interesting is where the configuration and the standard pull in opposite directions.

## The handshake decides nothing until the last step

A client does not simply connect and read. It opens a **secure channel**, creates a **session**, and then *activates* that session with a user identity. Four exchanges, and only the last one asks who you are.

<figure>
<style>
/* Two clocks that stay in phase: the four messages replay every 8 s and the
   identity cycles through three over 24 s. 24 is an exact multiple of 8, so a
   run never starts mid-sequence. */
.article figure {overflow-x: auto;}
.article figure svg.ua-h {min-width: 428px;}
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
<figcaption>The first three exchanges run identically for everybody, including a client that will be thrown out a moment later. Watch where the three runs differ: not at the channel, at step 4. That is the shape of the whole protocol &mdash; transport security and identity are separate decisions, and the identity one is made last.</figcaption>
</figure>

This matters because the two halves are genuinely independent. You can have an encrypted channel carrying an anonymous user, or a completely unencrypted channel carrying an administrator's certificate. "We use OPC-UA with encryption" answers only one of the two questions.

On this server the roles come from `SimpleRoleRuleset`, whose own docstring is the clearest statement of the model: *admins alone can write, admins and users can read, and anonymous users can't do anything*. That last clause is not a formality. An anonymous client here does not get a read-only view. Its `CreateSession` succeeds &mdash; the server hands it a session &mdash; and then `ActivateSession` is refused with `BadUserAccessDenied`, so it holds a session it can never use. Connecting anonymously against the running server returns exactly that.

`software/opcua/opcua.py` offers two channel policies, `NoSecurity` and `Basic256Sha256_SignAndEncrypt`, and three identity tokens, `Anonymous`, `Username` and `Basic256Sha256` (certificate). Anonymous is on that list, so a client is free to offer it &mdash; and then `Pw_Cert_UserManager.get_user` finds no username in either database and no certificate, returns `None`, and the session is never activated. The ruleset's empty anonymous permission set is never consulted at all. Two independent parts of the configuration happen to agree here, which is a comfortable place to be and a fragile one: relax either and the other still looks like it is doing the work.

The six process nodes are mirrors, refreshed from OpenPLC over Modbus by the server's own loop every two seconds. `GST` and `HPT` come from holding registers 1124 and 1126 &mdash; the same two words the *Modbus* and *Flood &amp; Overwrite* topics are about, republished under `http://opcua.cybics.github.io` with sessions and roles in front of them. Reading a node here is reading that register, one gateway removed. Worth knowing that the gateway is a place the truth can be lost as well. Four of the six mirrors read the wrong register. `stop` and `manual` are one too high &mdash; 1129 and 1131 against the 1128 and 1130 that `%MW104` and `%MW106` map to. `systemSen` and `boSen` are not close at all: they read holding registers **2** and **3**, which the program declares nowhere and which are therefore always zero. You can watch that one: register 1132 reads 1 while the OPC-UA `systemSen` node reads 0.

## What an unencrypted channel actually leaks

The obvious conclusion is that a `None` channel hands a sniffer everything. Captured off the bridge while a client logged in with `user1`, it does not.

<figure>
<style>
.article figure svg.ua-w {min-width: 428px;}
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
<figcaption>Four fields, swept left to right, with the read-out underneath saying what each one yields. The reason is not that tokens always protect themselves. Each endpoint pairs a channel policy with a policy for each identity token, and this server's two endpoints pair them in opposite directions: on the <code>None</code> channel the <code>username</code> token carries <code>Basic256Sha256</code>, so the client encrypts the password under the server&rsquo;s certificate; on the <code>Basic256Sha256</code> channel the same token carries <code>None</code>, because the channel is already doing it. Somebody chose that. A server that leaves the token policy at <code>None</code> over a <code>None</code> channel puts the password on the wire in clear. That is a narrower hole than Modbus has, and it is still a hole: a name is half a credential, and knowing the account exists is what makes guessing worth starting.</figcaption>
</figure>

Measured, not assumed: in a capture of a full `user1` login taken on the container bridge, the string `user1` appears in clear text inside the `ActivateSessionRequest`, the password `test` appears **zero** times anywhere in the capture, and the token carries `http://www.w3.org/2001/04/xmlenc#rsa-oaep` immediately after it. The channel in the same capture negotiated `http://opcfoundation.org/UA/SecurityPolicy#None`.

This is why the *OPC-UA* challenge brute-forces logins against the live server rather than cracking a captured hash: there is no captured hash. Every guess costs a round trip, and every round trip is visible.

## The admin flag is written, not read

The user-tier flag is an ordinary variable; a `User` session reads it directly. The admin-tier one is not a value sitting in the address space waiting to be found. On a running server it holds a prompt &mdash; `set the correct variable > 0` &mdash; which that same two-second loop rewrites on every pass, and goes on holding it until the trigger variable is above zero.

<figure>
<style>
.article figure svg.ua-f {min-width: 388px;}
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
  <text class="fl1" x="222" y="136" text-anchor="middle" font-size="13" font-weight="bold">CybICS(&hellip;)</text>
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
<figcaption>Two writes to the same variable, one refused and one accepted, and then a pause before anything visible happens. That pause is the lesson: the write lands on a trigger, and the server's own loop &mdash; <code>await asyncio.sleep(2)</code> &mdash; is what replaces the flag text on its next pass. A client that writes the trigger and reads back immediately sees the old value and concludes it failed. With motion switched off the figure holds the moment after the accepted write and before the loop has noticed.</figcaption>
</figure>

Reaching `Admin` is not a matter of a better password. `admin_db` in `software/opcua/user_manager.py` is empty &mdash; its only entry is commented out &mdash; so no username and password combination reaches the admin role at all. Admin is bound to one certificate, registered at start-up by `add_admin("certificates/trusted/cert_admin.der", name='test_admin')`, and that certificate and its private key are both in the repository. The challenge is a leaked-key exercise wearing the clothes of a password exercise, which is the more realistic of the two: keys leak more quietly than passwords, and nothing expires them here.

## Where it goes wrong in general

- **SecurityPolicy None** &mdash; the channel is neither signed nor encrypted. Reads, writes and node names are all in the clear, and a sniffer learns the address space for free. Whether the password survives it is a separate setting, not a separate guarantee: this server attaches `Basic256Sha256` to the username token on that endpoint, and a server that does not puts the credential in the clear alongside everything else.
- **Anonymous access** &mdash; refused outright here, because the user manager returns no user at all for it, and dangerous on a server that admits it with read access, which is the common default.
- **Certificates trusted too broadly, or leaked.** A certificate in a repository is a credential in a repository.

## Detection

The IDS has a rule for this, and it is deliberately blunt: **rule 9, `opcua_access`**, fires on any TCP payload of eight bytes or more to port 4840 whose source is not one of four named services &mdash; `hwio`, `fuxa`, `openplc` and `opcua` itself. That list is narrower than the IDS's general `KNOWN_SERVICES` table on purpose; exempting every service meant traffic from the attack box went unnoticed.

It does not try to tell a login from a read, or a good certificate from a bad one. It asks one question &mdash; is this host supposed to be speaking OPC-UA at all &mdash; and any answer of "no" is a low-severity alert mapped to **T0846 Remote System Discovery**. Repeats from the same source are collapsed to one alert per thirty seconds, so a brute-force run of hundreds of attempts produces a slow trickle rather than a flood. Two probes from a host thirty-one seconds apart produced exactly two alerts in the IDS log, which is the cooldown doing its job.

That is the trade every rule on this plant makes. A rule this blunt cannot be evaded by being careful on the wire, only by coming from an address that belongs there &mdash; which is the same lesson the *Network Segmentation* and *IDS Evasion* modules arrive at from the other side.
