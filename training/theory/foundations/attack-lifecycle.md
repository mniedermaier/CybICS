# The ICS attack lifecycle

Real ICS intrusions are not single tricks; they are campaigns with stages. The
**MITRE ATT&CK for ICS** knowledge base names the tactics an adversary moves through. The
CybICS challenges are arranged along the same arc, so the CTF is a guided walk through a
real attack.

<figure>
<svg viewBox="0 0 560 150" role="img" aria-label="ICS attack lifecycle stages">
  <defs><marker id="l" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <g font-size="11" text-anchor="middle">
    <rect x="10" y="40" width="95" height="46" rx="6" fill="#ff6b00" opacity="0.35"/>
    <text x="57" y="60">Recon</text><text x="57" y="76" font-size="9">scan, enumerate</text>
    <rect x="125" y="40" width="95" height="46" rx="6" fill="#ff6b00" opacity="0.5"/>
    <text x="172" y="60">Access</text><text x="172" y="76" font-size="9">creds, MITM</text>
    <rect x="240" y="40" width="95" height="46" rx="6" fill="#ff6b00" opacity="0.65"/>
    <text x="287" y="60">Manipulate</text><text x="287" y="76" font-size="9">write, program</text>
    <rect x="355" y="40" width="95" height="46" rx="6" fill="#ff6b00" opacity="0.8"/>
    <text x="402" y="60" fill="#1a1a1a">Inhibit</text><text x="402" y="76" font-size="9" fill="#1a1a1a">evade, flood</text>
    <rect x="470" y="40" width="80" height="46" rx="6" fill="#ff6b00"/>
    <text x="510" y="60" fill="#1a1a1a">Impact</text><text x="510" y="76" font-size="9" fill="#1a1a1a">blowout</text>
  </g>
  <line x1="105" y1="63" x2="123" y2="63" stroke="#ff6b00" stroke-width="2" marker-end="url(#l)"/>
  <line x1="220" y1="63" x2="238" y2="63" stroke="#ff6b00" stroke-width="2" marker-end="url(#l)"/>
  <line x1="335" y1="63" x2="353" y2="63" stroke="#ff6b00" stroke-width="2" marker-end="url(#l)"/>
  <line x1="450" y1="63" x2="468" y2="63" stroke="#ff6b00" stroke-width="2" marker-end="url(#l)"/>
  <text x="280" y="120" text-anchor="middle" font-size="10" opacity="0.7">Each stage is louder than the last; detection gets easier as impact nears.</text>
</svg>
<figcaption>The stages of an ICS attack, and the CybICS challenges that live in each.</figcaption>
</figure>

## The stages, with CybICS challenges

| Stage | ATT&CK for ICS | CybICS challenge |
|---|---|---|
| Discovery | T0846 Remote System Discovery | Scanning, S7comm enumeration |
| Collection | T0802 Automated Collection | Wireshark capture |
| Initial access | T0812 Default Credentials, T0859 Valid Accounts | Password attack |
| Adversary-in-the-middle | T0830 | MITM |
| Execution / persistence | T0843 Program Download, T0889 Modify Program | PLC programming |
| Impair process control | T0836 Modify Parameter | Flood & overwrite |
| Inhibit response / evasion | T0851 Rootkit, evasion of monitoring | IDS evasion |
| Impact | T0828 Loss of Productivity, unsafe state | The blowout |

## Why the order matters for defenders

Reconnaissance is quiet; impact is obvious. The earlier you detect, the more options you
have and the less damage is done. That is the whole argument for monitoring the control
network: it turns a silent campaign into a series of alerts, which is exactly what the
detection modules practise. The defender's goal is to **shift detection left**, catching the
scan before it becomes a blowout.
