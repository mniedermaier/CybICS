# The ICS attack lifecycle

A burglar does not walk up to a house and immediately open the safe. First they watch the street, then find an unlocked window, look around inside, and only at the end take what they came for. Attacks on plants work the same way: they are campaigns made of stages, and each stage is a chance for a defender to notice.

## Why think in stages

News reports on a plant attack usually describe only the end: a power cut or a damaged machine. The weeks before, where most of the work happened, stay invisible.

Thinking in stages helps you in two ways:

- **As an attacker** (in the CTF), it tells you what to do next. You cannot overwrite a register before you know which host holds it.
- **As a defender**, it tells you where to look. Every stage leaves traces, and catching an early one stops the dangerous final stage.

<div class="callout analogy" markdown="1">
**Analogy:** a stage model is like the chapters of a crime novel. Knowing that "the break-in" comes before "the getaway" lets the detective set a trap at the right chapter.
</div>

## The ICS Cyber Kill Chain

A *kill chain* is a military term: a sequence of steps that must all succeed for an attack to work. Break any link and the chain fails. In 2015, Michael Assante and Robert M. Lee adapted it for industrial control systems (ICS). Their **ICS Cyber Kill Chain** has two big stages:

1. **Intrusion:** the attacker gets into the company network, usually the office (IT) side, for example with a booby-trapped e-mail attachment on an engineer's laptop.
2. **ICS attack:** the attacker learns how the plant works, then builds, tests and runs an attack that fits it, such as changing a controller's setpoints so a tank overfills.

The key insight is in stage 2. To damage a physical process, an attacker has to understand *that particular* process: which controller drives which valve, and what values are dangerous. That takes time and leaves traces, which is good news for defenders.

## MITRE ATT&CK for ICS

For day-to-day work, defenders use a more detailed catalogue: **MITRE ATT&CK for ICS** (Adversarial Tactics, Techniques and Common Knowledge), published free at attack.mitre.org by MITRE, a US non-profit that records how real attackers behave.

ATT&CK uses two words you need to keep apart:

- A **tactic** is the attacker's *goal* at that moment: "find out what is on the network" (Discovery) or "change how the process behaves" (Impair Process Control).
- A **technique** is *how* they reach that goal. Each one has an ID, for example **T0846 Remote System Discovery**, so that defenders everywhere mean exactly the same thing.

There are twelve ICS tactics. You do not need to memorise them, only recognise the names:

Initial Access, Execution, Persistence, Privilege Escalation, Evasion, Discovery, Lateral Movement, Collection, Command and Control, Inhibit Response Function, Impair Process Control, Impact.

The last two make ICS special. *Impair Process Control* means manipulating the physical process; *Impact* is the real-world result: lost production, damaged equipment or a safety incident.

<div data-widget="checkpoint" data-id="tactic-technique"></div>

## The arc on CybICS

Doing the CybICS challenges in order walks you through one campaign against the gas plant.

| Tactic | CybICS challenge |
|---|---|
| Discovery | [Service Scanning](/ctf/challenge/scanning), [S7comm Scanning](/ctf/challenge/scanning2), [Wireshark Capture](/ctf/challenge/wireshark_capture) |
| Collection | [Man-in-the-Middle](/ctf/challenge/mitm) |
| Lateral Movement, Persistence | [OpenPLC](/ctf/challenge/password_openplc) and [FUXA](/ctf/challenge/password_attack) password attacks, [PLC Programming](/ctf/challenge/plc_programming) |
| Impair Process Control | [Flood & Overwrite](/ctf/challenge/flood_overwrite) |
| Impact | [Physical Process](/ctf/challenge/physical_process) |

Read the table as a story. You scan the network from the attack machine and find the PLC. You listen to its Modbus traffic and learn which register carries the high-pressure tank (HPT) value. You log in to the web interface with a guessed password. Finally, you change values the controller relies on, and the compressor does things the operator never asked for.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the technique behind each challenge</summary>

| Tactic | Technique | CybICS challenge |
|---|---|---|
| Discovery | T0846 Remote System Discovery, T0840 Network Connection Enumeration | [Service Scanning](/ctf/challenge/scanning) |
| Discovery | T0888 Remote System Information Discovery | [S7comm Scanning](/ctf/challenge/scanning2) |
| Discovery | T0842 Network Sniffing | [Wireshark Capture](/ctf/challenge/wireshark_capture) |
| Collection | T0830 Adversary-in-the-Middle | [Man-in-the-Middle](/ctf/challenge/mitm) |
| Persistence, Lateral Movement | T0859 Valid Accounts | [OpenPLC](/ctf/challenge/password_openplc) and [FUXA](/ctf/challenge/password_attack) password attacks |
| Lateral Movement, Persistence | T0843 Program Download, T0889 Modify Program | [PLC Programming](/ctf/challenge/plc_programming) |
| Impair Process Control | T0806 Brute Force I/O, T1692.001 Unauthorized Message: Command Message | [Flood & Overwrite](/ctf/challenge/flood_overwrite) |
| Impact | T0831 Manipulation of Control | [Physical Process](/ctf/challenge/physical_process) |

Some techniques belong to more than one tactic: a stolen password (T0859 Valid Accounts) lets an attacker both move to a new machine and come back later. ATT&CK is a catalogue, not a strict timeline.

</details>

Now try it yourself. Each step below needs something the one before it found out, so only one order works.

<div data-widget="sequence" data-id="arc"></div>

## Why the order matters for defenders

Early stages are quiet and cheap to stop; late stages are loud and expensive. Notice a port scan, and you block one address before anything is harmed. Notice only when the HPT pressure is already climbing, and the operators are fighting the attack in real time.

So defenders try to **detect as far left in the chain as possible**. Two limits keep this honest:

- Some stages cannot be seen on the network at all. A host that only *listens* (passive sniffing, T0842) sends nothing for an IDS to notice.
- Some stages look exactly like normal work. An engineer uploading a new PLC program and an attacker doing the same produce very similar traffic.

That is why a single control is never enough, and why the next articles cover both [detection](/theory/detection-monitoring) and [Defence in depth](/theory/defense-hardening). On the small CybICS Intrusion Detection System (IDS), most stages of the campaign above raise alerts; the program download is the quiet one.

<details class="deep-dive" markdown="1">
<summary>Deep dive: which alert each stage raises on the CybICS IDS</summary>

The figure walks one campaign past the IDS, stage by stage, from the attack machine (172.18.0.100) to the PLC (172.18.0.3). The details of every rule are in [Detection and monitoring](/theory/detection-monitoring).

<figure class="wide">
<style>
.al-w {--w: 20s;}
/* One marker, five stages, and the alert each stage produces. The stage
   highlight and the alert row share one clock. */
.al-w .mk {animation: aw-mk var(--w) steps(1,end) infinite;}
.al-w .s1 {animation: aw-s1 var(--w) steps(1,end) infinite;}
.al-w .s2 {animation: aw-s2 var(--w) steps(1,end) infinite;}
.al-w .s3 {animation: aw-s3 var(--w) steps(1,end) infinite;}
.al-w .s4 {animation: aw-s4 var(--w) steps(1,end) infinite;}
.al-w .s5 {animation: aw-s5 var(--w) steps(1,end) infinite;}
.al-w .a1 {opacity:0; animation: aw-o1 var(--w) steps(1,end) infinite;}
.al-w .a2 {opacity:0; animation: aw-o2 var(--w) steps(1,end) infinite;}
.al-w .a3 {opacity:0; animation: aw-o3 var(--w) steps(1,end) infinite;}
.al-w .a4 {opacity:0; animation: aw-o4 var(--w) steps(1,end) infinite;}
.al-w .a5 {opacity:0; animation: aw-o5 var(--w) steps(1,end) infinite;}
/* Base state is stage 4, the quiet one: the frame worth landing on when
   animation is switched off. */
.al-w .s4 {stroke-width:3;}
.al-w .s1,.al-w .s2,.al-w .s3,.al-w .s5 {stroke-width:0;}
.al-w .a4 {opacity:1;}
.al-w .mk {transform: translateX(228px);}
@keyframes aw-mk {0%,19.9%{transform:translateX(0)}    20%,39.9%{transform:translateX(76px)}
                  40%,59.9%{transform:translateX(152px)} 60%,79.9%{transform:translateX(228px)}
                  80%,100%{transform:translateX(304px)}}
/* The panels animate stroke-width only, so their dark labels stay legible. */
@keyframes aw-s1 {0%,19.9%{stroke-width:3} 20%,100%{stroke-width:0}}
@keyframes aw-s2 {0%,19.9%{stroke-width:0} 20%,39.9%{stroke-width:3} 40%,100%{stroke-width:0}}
@keyframes aw-s3 {0%,39.9%{stroke-width:0} 40%,59.9%{stroke-width:3} 60%,100%{stroke-width:0}}
@keyframes aw-s4 {0%,59.9%{stroke-width:0} 60%,79.9%{stroke-width:3} 80%,100%{stroke-width:0}}
@keyframes aw-s5 {0%,79.9%{stroke-width:0} 80%,100%{stroke-width:3}}
@keyframes aw-o1 {0%,19.9%{opacity:1} 20%,100%{opacity:0}}
@keyframes aw-o2 {0%,19.9%{opacity:0} 20%,39.9%{opacity:1} 40%,100%{opacity:0}}
@keyframes aw-o3 {0%,39.9%{opacity:0} 40%,59.9%{opacity:1} 60%,100%{opacity:0}}
@keyframes aw-o4 {0%,59.9%{opacity:0} 60%,79.9%{opacity:1} 80%,100%{opacity:0}}
@keyframes aw-o5 {0%,79.9%{opacity:0} 80%,100%{opacity:1}}
@media (prefers-reduced-motion: reduce) { .al-w * {animation:none !important;} }
</style>
<svg class="al-w" viewBox="0 0 400 214" role="img"
     aria-label="Five stages of a campaign against the CybICS plant, walked in order. Scanning raises a port scan alert and an S7 enumeration alert, both medium severity. Man in the middle raises an ARP spoofing alert at critical severity. Guessing the OpenPLC password raises an HTTP brute force alert at high severity after five attempts in thirty seconds. Downloading a modified PLC program raises nothing, because no rule looks at program uploads. Flooding a Modbus register raises a Modbus flood alert at critical severity. Four stages make noise; the quiet one is where the attacker changes the logic.">
  <text x="8" y="18" font-size="12" font-weight="bold">one campaign, five stages</text>
  <g font-size="11" text-anchor="middle">
    <rect class="s1" x="8"   y="30" width="68" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="42" y="48" style="fill:#1a1a1a" font-weight="bold">scan</text><text x="42" y="62" style="fill:#1a1a1a">find the ports</text>
    <rect class="s2" x="84"  y="30" width="68" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="118" y="48" style="fill:#1a1a1a" font-weight="bold">MitM</text><text x="118" y="62" style="fill:#1a1a1a">sit on the wire</text>
    <rect class="s3" x="160" y="30" width="68" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="194" y="48" style="fill:#1a1a1a" font-weight="bold">creds</text><text x="194" y="62" style="fill:#1a1a1a">guess a login</text>
    <rect class="s4" x="236" y="30" width="68" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="270" y="48" style="fill:#1a1a1a" font-weight="bold">program</text><text x="270" y="62" style="fill:#1a1a1a">change the logic</text>
    <rect class="s5" x="312" y="30" width="80" height="40" rx="5" fill="#ff6b00" stroke="#1a1a1a"/>
    <text x="352" y="48" style="fill:#1a1a1a" font-weight="bold">flood</text><text x="352" y="62" style="fill:#1a1a1a">pin the register</text>
  </g>
  <g class="mk"><path d="M 34 82 L 50 82 L 42 92 Z" fill="#ff6b00"/></g>

  <text x="8" y="116" font-size="12" font-weight="bold" opacity="0.85">what the IDS hears:</text>
  <g font-size="12" font-weight="bold">
    <text class="a1" x="8" y="140" fill="#ff6b00">port_scan &mdash; medium &nbsp;&middot;&nbsp; s7_enumeration &mdash; medium</text>
    <text class="a2" x="8" y="140" fill="#ff6b00">arp_spoof &mdash; critical</text>
    <text class="a3" x="8" y="140" fill="#ff6b00">http_brute_force &mdash; high</text>
    <text class="a4" x="8" y="140">&mdash; silence &mdash;</text>
    <text class="a5" x="8" y="140" fill="#ff6b00">modbus_flood &mdash; critical</text>
  </g>
  <g font-size="11" opacity="0.85">
    <text class="a1" x="8" y="160">Five ports in ten seconds, and any S7 payload to port 102.</text>
    <text class="a2" x="8" y="160">One IP address claiming two hardware (MAC) addresses.</text>
    <text class="a3" x="8" y="160">Five login attempts on OpenPLC in thirty seconds.</text>
    <text class="a4" x="8" y="160">No rule looks at a program upload.</text>
    <text class="a5" x="8" y="160">Fifty writes in five seconds from an unexpected host.</text>
  </g>
  <text x="8" y="190" font-size="11" opacity="0.85">Four stages make noise. The quiet one is where the attacker</text>
  <text x="8" y="206" font-size="11" opacity="0.85">changes what the controller does.</text>
</svg>
<figcaption>The alerts each stage raises on the CybICS IDS, from the rules in <code>software/ids/rules.py</code>. A program download is a normal engineering action over the web interface, so no network rule flags it; catching it needs a different control, such as comparing the running program with a known-good copy.</figcaption>
</figure>

</details>

<div data-widget="checkpoint" data-id="earliest"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: technique IDs change over time</summary>

ATT&CK is a living catalogue. MITRE publishes new versions, merges techniques and occasionally renumbers them. Several older ICS IDs you will still find in tools and reports now redirect to new entries:

| Older ID | Name then | Current entry |
|---|---|---|
| T0855 | Unauthorized Command Message | T1692.001 Unauthorized Message: Command Message |
| T0856 | Spoof Reporting Message | T1692.002 Unauthorized Message: Reporting Message |
| T0812 | Default Credentials | T1694.001 Insecure Credentials: Default Credentials |

The habit to build: when an alert or a report cites a technique ID, look it up on attack.mitre.org before you rely on it. An ID is a promise about what the alert means, and the promise is only as good as the catalogue version behind it.

</details>

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

- The IDS (`software/ids/rules.py`) still labels its alerts with the older IDs T0855, T0856 and T0812. Students who look them up will be redirected to the T1692/T1694 entries; the deep dive above prepares them for that.
- The `http_brute_force` rule only counts POSTs whose request contains `login` or `auth`. OpenPLC's `/login` matches; FUXA's sign-in route (`/api/signin` on port 1881) does not, so a FUXA password attack raises no brute-force alert. A good class discussion on how signature rules fail.

</details>
