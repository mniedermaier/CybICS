# Password attacks

Default and weak credentials are the most common way into ICS web interfaces. A dictionary
attack tries a wordlist against a login until one works. CybICS has two targets: the OpenPLC
web UI and the FUXA HMI.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Dictionary attack">
  <defs><marker id="pw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="34" width="120" height="52" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="80" y="56" text-anchor="middle" font-size="11" fill="#1a1a1a">ffuf + wordlist</text>
  <text x="80" y="72" text-anchor="middle" font-size="9" fill="#1a1a1a">rockyou.txt</text>
  <g font-size="9" text-anchor="middle">
    <line x1="140" y1="52" x2="380" y2="40" stroke="#ff6b00" stroke-width="1.3" marker-end="url(#pw)"/>
    <line x1="140" y1="60" x2="380" y2="60" stroke="#ff6b00" stroke-width="1.3" marker-end="url(#pw)"/>
    <line x1="140" y1="68" x2="380" y2="80" stroke="#ff6b00" stroke-width="1.3" marker-end="url(#pw)"/>
    <text x="250" y="30">admin : password?</text>
  </g>
  <rect x="382" y="40" width="118" height="40" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="441" y="64" text-anchor="middle" font-size="11">login :8080 / :1881</text>
</svg>
<figcaption>A dictionary attack submits each candidate password and watches the response length to spot a success.</figcaption>
</figure>

## The skill

Analyse the login request, then run `ffuf` with a wordlist, filtering by response size or
content. OpenPLC uses form-encoded POST at `/login`; FUXA uses a JSON API at `/api/signin`.
Each yields its own flag.

> **MITRE ATT&CK for ICS:** T0812 Default Credentials, T0859 Valid Accounts. Defence: the
> *harden credentials* module.
