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
7. `## Before you start`: links to the foundation articles to read first, as
   `[Modbus TCP](/theory/modbus)`.

Aim for 500 to 900 words of prose. That is roughly five minutes.

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
| IDS threshold | `<div data-widget="ids-threshold"></div>` | A simulated stream of Modbus writes from a legitimate HMI and an attacker. The reader tunes the threshold and the window and sees detections and false alarms. |
| Firewall rules | `<div data-widget="firewall-rules"></div>` | The reader orders allow and deny rules and sees which CybICS connections pass. |
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
- Passing the quiz (at least 80 per cent) marks the topic as completed.

## Checking your work

```bash
pytest tests/test_theory_content.py   # no stack needed
pytest tests/test_theory_pages.py     # renders every page on a running stack
```
