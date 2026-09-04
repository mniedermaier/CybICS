# Hardening credentials

The first control every ICS needs is to remove default and weak passwords. This module has
you change the OpenPLC and FUXA logins so the earlier dictionary attack no longer works.

<figure>
<svg viewBox="0 0 520 110" role="img" aria-label="Default versus changed credentials">
  <rect x="20" y="30" width="210" height="50" rx="6" fill="#ff6b00" opacity="0.2" stroke="#ff6b00"/>
  <text x="125" y="52" text-anchor="middle" font-size="11">before: admin / default</text>
  <text x="125" y="70" text-anchor="middle" font-size="10" opacity="0.8">dictionary attack succeeds</text>
  <text x="250" y="60" font-size="16" fill="#ff6b00">&rarr;</text>
  <rect x="290" y="30" width="210" height="50" rx="6" fill="currentColor" opacity="0.15" stroke="currentColor"/>
  <text x="395" y="52" text-anchor="middle" font-size="11">after: strong, unique</text>
  <text x="395" y="70" text-anchor="middle" font-size="10" opacity="0.8">default login rejected</text>
</svg>
<figcaption>Changing the defaults makes stolen or guessed default credentials worthless. The check confirms the old password no longer works.</figcaption>
</figure>

## The skill

Change the OpenPLC and FUXA passwords through their web UIs, then verify. The check logs in
with the old defaults and passes only when they are rejected.

> **IEC 62443** SR 1.1; **NIST SP 800-82 / 800-53** IA-5 Authenticator Management. Detection
> counterpart: HTTP brute-force alerting.
