# Password attacks

In this briefing you prepare for two challenges: guessing your way into the FUXA HMI and into the OpenPLC web interface with a dictionary attack. Weak and default passwords are still one of the most common ways into industrial systems, and once an attacker holds a valid login, everything they do looks like normal operator work.

## The idea

Imagine a padlock with a four-digit code. Trying every code from 0000 to 9999 takes a while. But if you know that people love 1234, 0000 and their birth year, you try those first and are often done in minutes. A **dictionary attack** works the same way: instead of trying every possible password, it tries a list of passwords that real people actually use.

Such lists exist because of real data breaches. The best known, `rockyou.txt`, holds about 14 million passwords from a 2009 breach. Tools such as `ffuf`, `hydra` or Burp Suite take a list, send one login attempt per entry, and report which attempt got a different answer.

Industrial systems are especially exposed. Devices often ship with **default credentials**, the same user name and password on every unit, printed in the manual, and many are never changed. MITRE ATT&CK for ICS lists this as *Insecure Credentials: Default Credentials* (T1694.001), and the use of any stolen or guessed login as *Valid Accounts* (T0859).

Why does a list beat trying everything? Compare the two below, and see what a default password costs the attacker.

<div data-widget="keyspace"></div>

## How it looks on CybICS

Two web interfaces have a login:

| Target | Address | How the login is sent |
|---|---|---|
| OpenPLC | 172.18.0.3, port 8080, `/login` | An HTML form, sent as a form-encoded POST |
| FUXA HMI | 172.18.0.4, port 1881, `/api/signin` | A JSON request to the HMI's API |

Each target is its own challenge. For OpenPLC you read the flag in the account you broke into; for FUXA you enter the user name and password you found on the challenge page, which checks them. The Kali attack machine already has `ffuf` and the `rockyou` wordlist in `/usr/share/wordlists/`; the attack shell has `ffuf` and a shorter list of common passwords, `/usr/share/wordlists/passwords.txt`.

<figure class="wide">
<svg viewBox="0 0 520 150" role="img" aria-label="ffuf takes one password after another from a wordlist and sends each as a login request to the OpenPLC or FUXA login. Most answers are failures and look the same; the one answer that differs in size or content marks the correct password.">
  <defs><marker id="pw-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="40" width="120" height="52" rx="6" fill="#ff6b00"/>
  <text x="80" y="62" text-anchor="middle" font-size="12" style="fill:#1a1a1a" font-weight="bold">ffuf</text>
  <text x="80" y="78" text-anchor="middle" font-size="11" style="fill:#1a1a1a">+ wordlist</text>
  <g font-size="11">
    <line x1="140" y1="56" x2="370" y2="46" stroke="#ff6b00" stroke-width="1.5" marker-end="url(#pw-arrow)"/>
    <line x1="140" y1="66" x2="370" y2="66" stroke="#ff6b00" stroke-width="1.5" marker-end="url(#pw-arrow)"/>
    <line x1="140" y1="76" x2="370" y2="86" stroke="#ff6b00" stroke-width="1.5" marker-end="url(#pw-arrow)"/>
    <text x="180" y="34">one login attempt per word</text>
  </g>
  <rect x="376" y="40" width="124" height="52" rx="6" fill="currentColor" fill-opacity="0.15" stroke="currentColor"/>
  <text x="438" y="62" text-anchor="middle" font-size="11">login page</text>
  <text x="438" y="78" text-anchor="middle" font-size="11">:8080 or :1881</text>
  <g font-family="monospace" font-size="11">
    <text x="20" y="118" opacity="0.8">fail  size 4561   fail  size 4561   fail  size 4561</text>
    <text x="20" y="136" fill="#ff6b00" font-weight="bold">different answer &rarr; the password that worked</text>
  </g>
</svg>
<figcaption>Every wrong password produces the same answer. A dictionary attack therefore hides the typical failure, by its size or by a word it contains, and shows only the answer that is different.</figcaption>
</figure>

## How to approach it

1. **Study one login by hand.** Open the login page, open your browser's developer tools (F12), go to the *Network* tab and log in with a wrong password. Note the URL, the method (POST), the content type and the exact field names in the request body.
2. **Learn what failure looks like.** Note the status code, the size of the answer and any error text. That is what you will filter out.
3. **Build the ffuf command.** ffuf replaces the word `FUZZ` in your request with each entry of the wordlist. Copy the request you saw: URL with `-u`, method with `-X`, body with `-d`, content type with `-H`, wordlist with `-w`.
4. **Filter the failures.** Use `-fs` to hide answers of the failure size, or `-fr` to hide answers that contain the error text. Without a filter you will see thousands of identical lines.
5. **Run it and log in.** When one word survives the filter, log in with it in the browser and look around the account.
6. **Repeat for the other target.** The second login is sent differently, so step 1 matters again.

<div data-widget="checkpoint" data-id="filter"></div>

<div class="callout tip" markdown="1">
**Tip:** Test your command with a tiny wordlist of three entries first, one of them a password you know is wrong. If the wrong one is not filtered out, your filter is wrong, and a run over 14 million words will not fix it.
</div>

## Detect and defend

Guessing is noisy: it produces many failed logins from one source in a short time. The CybICS IDS has an `http_brute_force` rule that counts POST requests to port 8080 or 1881 whose first bytes mention `login` or `auth`. Five within thirty seconds from one source raise a high-severity alert. OpenPLC's login form matches; FUXA's `/api/signin` contains neither word, so guessing at FUXA raises no alert from this rule. Web servers usually log failed logins too, which gives a second place to look.

Defences, roughly from most to least important:

- **Change default passwords** before a device goes into service, and use long, unique passwords. That is the [Hardening credentials](/theory/defense_password) challenge.
- **Limit who can reach the login.** An HMI login does not need to be reachable from every network. See [Network segmentation](/theory/defense_network).
- **Slow attackers down.** Rate limiting and growing delays after failures make a dictionary attack take years instead of minutes.
- **Lock out with care.** Locking an account after a few failures stops guessing, but in a plant it can also lock out an operator during an emergency. OT sites often prefer delays and alerts.
- **Add a second factor** for remote and administrative access.

## Before you start

- [HMI and SCADA](/theory/hmi-scada) for what FUXA is and why its login matters.
- [The ICS attack lifecycle](/theory/attack-lifecycle) for where initial access fits.

Later on the path:

- [Ukraine power grid (2015, 2016, 2022)](/theory/ukraine-grid) for what attackers did with stolen operator logins.
