# Writing for the Theory Path

The Theory Path is the background reading for the CybICS challenges. Its
readers are **students with little IT or OT background**: they may never have
seen a PLC, a packet capture or a hex dump. Every article has to work for
them first. Expert detail is welcome, but it goes into a collapsible
"Deep dive" so it never stands between a beginner and the main idea.

The landing app renders each article from Markdown
(`software/landing/modules/theory_manager.py`), adds the learning objectives,
the key takeaways and the quiz from the article's sidecar JSON, and mounts the
interactive widgets with `software/landing/static/js/theory.js`.

## Files

Each topic is two files next to each other:

| File | Holds |
|---|---|
| `training/theory/<section>/<name>.md` | the article body |
| `training/theory/<section>/<name>.json` | objectives, takeaways, checkpoints, quiz |

The topic itself (id, title, summary, level, prerequisites, related
challenges, order) is registered in `software/landing/theory_config.json`.
`tests/test_theory_content.py` checks all of it without a running stack.

## Where a lesson goes

The sections of the Theory Path follow the seven stages of the CTF page
(`software/landing/ctf_config.json`), from the plant to its defence, with the
case studies at the end. Each challenge names its briefing in `theory`. The
briefings sit in the section of their stage and in the same order as the
challenges, so a student who works through the CTF in order has always read
the briefing of the next challenge already. A foundation lesson (Modbus,
OPC-UA, detection) goes right before the first briefing that needs it, and a
lesson's prerequisites always come earlier. Move a lesson, not a challenge,
when the two disagree; topic ids never change, because the quiz progress is
keyed on them.

## Audience and tone

- Write for a first-year student. Explain every acronym at first use
  ("Programmable Logic Controller (PLC)") and every term a beginner would not
  know. The glossary turns the first use of each term into a definition the
  reader can click, but the text must not depend on it.
- Start from what the reader already knows. An analogy before the jargon:
  a Modbus holding register is "a numbered mailbox the PLC reads and writes".
- Short paragraphs (at most four sentences), one idea each. Use lists and
  tables where they help scanning.
- Address the reader as "you". No first person ("I sent", "my capture").
- Tie every concept to the CybICS gas plant: the gas storage tank (GST), the
  high-pressure tank (HPT), the compressor, the system valve, the blow-out
  valve, the registers and the containers the reader can actually reach.
- Be precise. Every fact about CybICS must match the code in this repository;
  check it there, not from memory. Every MITRE ATT&CK for ICS technique ID
  must match the current catalogue (https://attack.mitre.org/techniques/ics/).
- Teach, do not review. Bugs in CybICS, criticism of a design choice and
  simulation statistics do not belong in the reading text. When an instructor
  needs to know about one, put it in an instructor note (see below).
- Never give away a CTF flag or a complete challenge solution. Explain the
  concept and the approach; the challenge page and its hints do the rest.

## Article structure

The template renders the title bar, objectives, key takeaways, quiz and
"Put it into practice" links. The Markdown body therefore starts with the
`# Title` and contains only the teaching text.

### Foundation articles

1. `# Title`
2. A short hook (two or three sentences): why this matters, in plain words.
3. Core sections as `##` headings. They form the table of contents, so give
   them short, descriptive names. Three to six sections.
4. A section that shows the concept on CybICS (`## In CybICS` or a more
   specific heading).
5. At least one interactive widget or checkpoint where it fits the topic.
6. Optional deep dives for the expert material.

### Module articles (one per challenge)

Every module article uses the same section headings, in this order:

1. `# Title`
2. One paragraph: what you will do in the challenge and why it matters.
3. `## The idea`: the concept in plain words, with an analogy.
4. `## How it looks on CybICS`: the containers, ports, registers or files
   involved, and what the reader will see.
5. `## How to approach it`: the mental model and the tools, as steps, without
   the solution.
6. `## Detect and defend`: how a defender notices it and what stops it.
7. `## Before you start`: links to the articles to read first, as
   `[Modbus TCP](/theory/modbus)`. They must come earlier on the path; links
   to lessons that come later go after a line `Later on the path:`.

Aim for 500 to 900 words of prose. That is roughly five minutes.

The reading time on a page counts the text outside deep dives (170 words a
minute, plus half a minute per figure or widget); deep dives show as extra
optional minutes. Keep every lesson at eight minutes or less, and a lesson on
the core path at seven (six where possible); tests enforce both caps: move
detail, numbers that only matter in a challenge, and source paths into deep
dives rather than into the main text.

## Building blocks

All of these are plain HTML in the Markdown. Leave a blank line before and
after each block, and add `markdown="1"` to any block whose content is
Markdown.

### Callouts

```html
<div class="callout tip" markdown="1">
**Tip:** text
</div>
```

The kinds are `tip`, `warning`, `cybics` (how this applies to the plant) and
`analogy`.

### Deep dives

```html
<details class="deep-dive" markdown="1">
<summary>Deep dive: how the MBAP length field is counted</summary>

Markdown content.

</details>
```

### Instructor notes

```html
<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

Known limitations of the lab, design trade-offs, things to watch for in class.

</details>
```

Instructor notes are **never rendered**: the renderer cuts them out before
the page is built, because some of them say how a challenge can be passed
without doing it. They are not secret, though: they stay in the Markdown in
this public repository and in the copy of `training/` inside the landing
container, where instructors read them. Anything a student must know belongs
in the text or a callout, not in a note. Do not
nest another `<details>` inside one.

### Figures

Keep the existing SVG figures; they are accurate and accessible. Every `<svg>`
needs `role="img"` and an `aria-label` that describes what it shows, and every
figure a `<figcaption>`. A figure that must keep its scale on a phone and
scroll instead of shrinking gets `class="wide"`:

```html
<figure class="wide">
<svg viewBox="0 0 520 260" role="img" aria-label="...">...</svg>
<figcaption>...</figcaption>
</figure>
```

Animations go in a `<style>` block in the article. **Every selector in it must
start with a class that belongs to that figure** (for example `.mb-x .pkt`).
Selectors that start with `.article`, `figure`, `svg`, `html`, `body` or any
bare element would restyle the whole page and are rejected by the tests.
Respect `prefers-reduced-motion`. `<script>` and event handler attributes are
stripped by the sanitiser.

### Widgets

Widgets are empty `div`s; `theory.js` fills them in. All of them work without
a running stack except `plant-live`, which says so when the plant cannot be
reached.

| Widget | Markup | What it does |
|---|---|---|
| Live plant | `<div data-widget="plant-live" data-fields="gst,hpt,compressor"></div>` | Live values the PLC holds, polled once a second. Fields: `gst`, `hpt`, `sysSen`, `boSen`, `heartbeat`, `compressor`, `systemValve`, `gstSig`. Without `data-fields` it shows all of them. |
| Modbus frame builder | `<div data-widget="modbus-frame" data-fc="6" data-address="1126" data-value="90"></div>` | Edit the fields of a Modbus TCP request and see the bytes, or paste bytes and see the fields. Every byte is explained. All attributes are optional. |
| S7 layers | `<div data-widget="s7-layers" data-sample="szl"></div>` | A real S7comm request taken apart layer by layer (TPKT, COTP, S7). Samples: `setup` (Setup Communication), `szl` (read SZL 0x0011). |
| Register decoder | `<div data-widget="register-decoder" data-values="18533,27756,28416"></div>` | Turns 16-bit register values into hex bytes and ASCII text step by step. Never use real flag registers as the example. |
| Purdue explorer | `<div data-widget="purdue-explorer"></div>` | The CybICS network on the Purdue levels. Click a host to see its IP, ports, protocols, the attacks that target it and the IDS rules that watch it. |
| Scan cycle | `<div data-widget="scan-cycle"></div>` | Steps through read inputs, run logic, write outputs with the CybICS compressor rule. The reader changes the HPT pressure and watches the PLC decide. |
| IDS threshold | `<div data-widget="ids-threshold" data-scenario="flood" data-n="50" data-w="5"></div>` | A simulated stream of Modbus writes from the engineering workstation (legitimate, but not an expected writer) and an attacker: a short burst, a real flood or low and slow. The reader tunes the threshold and the window and sees detections and false alarms. All attributes are optional. |
| Firewall rules | `<div data-widget="firewall-rules"></div>` | The reader orders allow and deny rules and sees which CybICS connections pass. |
| ARP spoofing | `<div data-widget="arp-spoof"></div>` | Steps through poisoning FUXA's and the PLC's ARP caches, with the path of the frames, IP forwarding, rewriting a reading and the IDS `arp_spoof` rule. |
| Keyspace | `<div data-widget="keyspace"></div>` | How long guessing a password takes: random characters (set and length), a leaked list or a default password, against online and offline attackers. |
| Alert log | `<div data-widget="alert-log"></div>` | A made-up morning of CybICS IDS alerts to filter and count, with four triage questions. Not the data of the IDS Forensics challenge. |
| OPC-UA security | `<div data-widget="opcua-security"></div>` | Choose the channel policy and the identity; shows what the CybICS server accepts, the role, what a listener sees and what the IDS reports. |
| Sequence | `<div data-widget="sequence" data-id="attack"></div>` | Put the steps of a story in order and label each one (an ATT&CK tactic, an incident-response phase). The steps come from `exercises` in the sidecar. |
| Plant prediction | `<div data-widget="plant-predict"></div>` | The reader predicts from the live compressor and valve state whether the HPT will rise, fall or stay over 20 seconds, then the live plant answers. Read-only; needs the stack. |
| Plant sandbox | `<div data-widget="plant-sandbox"></div>` | The plant model (the same rules as hwio and the firmware) and the PLC's automatic mode in the browser, one tick at a time. The reader sets the start pressures, the mode (automatic, manual with frozen outputs, stop) and an attacker who forges the HPT the PLC reads in one scan or in a share of the scans, and sees the pressures, the ticks in which the compressor really moved gas (in the current run and since the start), a chart and a log of what changed on which tick, from the start state on. `tests/test_plant_model_parity.py` keeps its constants in step with the firmware. |
| Rate planner | `<div data-widget="rate-planner"></div>` | Plan a number of Modbus writes and their spacing against the two write rules of the IDS over a two-minute window, with imprecise timing and a stray scan as options. |
| UART frame | `<div data-widget="uart-frame"></div>` | One character as start bit, eight data bits (lowest first) and stop bit, and what a receiver at the wrong baud rate reads instead. |
| Checkpoint | `<div data-widget="checkpoint" data-id="frame"></div>` | One question in the middle of the text, taken from `checkpoints` in the sidecar. |

## The sidecar JSON

```json
{
  "level": "beginner",
  "objectives": [
    "Explain what a Modbus register is and how a client reads it",
    "Read the bytes of a Modbus TCP request"
  ],
  "takeaways": [
    "Modbus has no authentication: anyone who can reach port 502 can write.",
    "..."
  ],
  "checkpoints": [
    {
      "id": "frame",
      "question": "Which field tells the PLC what to do?",
      "options": ["Transaction ID", "Function code", "Unit ID"],
      "answer": 1,
      "explanation": "The function code (for example 03 = read holding registers) selects the operation."
    }
  ],
  "quiz": [
    {
      "type": "single",
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "answer": 2,
      "explanation": "Why the right answer is right, and why the tempting wrong one is wrong."
    },
    {
      "type": "multi",
      "question": "Which of these are write function codes? (Select all that apply)",
      "options": ["03", "05", "06", "16"],
      "answer": [1, 2, 3],
      "explanation": "..."
    }
  ]
}
```

A lesson with a `sequence` widget also has an `exercises` object, keyed by
the widget's `data-id`:

```json
"exercises": {
  "attack": {
    "type": "sequence",
    "title": "Put the attack in order",
    "intro": "What the reader has to do, in one or two sentences.",
    "labels": ["Initial Access", "Discovery", "Impact"],
    "steps": [
      {"text": "One short sentence", "label": "Initial Access", "explain": "Why it comes here and has this label."}
    ]
  }
}
```

The steps are listed in the right order; the widget shuffles them. With
`"order": false` the widget becomes a matching exercise: the items keep
their place and only the labels are graded, which suits "which protocol is
this?" or "normal or attack?". Three to
eight steps, none of which may give its position away ("first", "then"), and
every one of them stated in the article. `labels` is optional; offer at most
one label that no step uses.

- `level` is `beginner`, `intermediate` or `advanced`.
- A topic marked `"core": true` in `theory_config.json` is on the short core
  path; its prerequisites must be core topics too.
- Two to four objectives, phrased as things the reader can do afterwards
  ("Explain", "Identify", "Decode"), not as topics.
- Three to five takeaways, one sentence each.
- Four to six quiz questions. `single` has exactly one answer (an index);
  `multi` has a list of indices. True/false is a `single` with the options
  `["True", "False"]`. Ask about understanding and application ("What happens
  if...", "Which field would you change to..."), not about trivia. Every
  question needs an explanation that also addresses the most tempting wrong
  answer.
- Passing the quiz (at least 80 per cent) marks the topic as completed. The
  page carries only the questions and options; the board grades an attempt,
  records it and only then returns the answers and explanations. Checkpoints
  are practice and carry their answers in the page.
- Progress is stored on the board, one record for everyone who uses it. It
  is a learning aid for self-study, not an exam: it does not tell students
  apart, and anyone on the board can reset it.

## Checking your work

```bash
pytest tests/test_theory_content.py   # no stack needed
pytest tests/test_theory_pages.py     # renders every page on a running stack
```
