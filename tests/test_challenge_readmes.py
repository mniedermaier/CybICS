"""
A challenge README must not give its flag away before the student asks for it.

The challenge page (software/landing/templates/challenge.html) shows the
README as cards, one per H2 section. Overview, Task and plain content cards
are open when the page loads; only sections whose heading names a solution
(or "Flag:") are collapsed and marked as such. A flag anywhere else is on
screen the moment the student opens the challenge: the OpenPLC Password
Attack flag once sat in the always-open Task section of its README.

No stack needed.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "software" / "landing" / "ctf_config.json"


def _challenges():
    config = json.loads(CONFIG.read_text())
    return [ch for cat in config["categories"].values() for ch in cat["challenges"]]


def _all_flags():
    return {ch["flag"] for ch in _challenges()}


def _is_solution(heading):
    """challenge.html's detectType() for the sections it collapses as solutions."""
    h = heading.lower()
    if "task" in h or "hint" in h:
        return False
    return "solution" in h or "flag:" in h


def _sections(markdown):
    """(H2 heading, line) for every line outside code fences' own headings."""
    heading, fenced = "", False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"## (?!#)", line):
            heading = line[3:].strip()
            continue
        yield heading, line


READMES = sorted({ch["training_content"] for ch in _challenges() if ch.get("training_content")})


@pytest.mark.parametrize("readme", READMES)
def test_flags_only_in_solution_sections(readme):
    text = (ROOT / readme).read_text()
    flags = _all_flags()
    leaks = [f"[{heading or 'preamble'}] {line.strip()[:80]}"
             for heading, line in _sections(text)
             if not _is_solution(heading) and any(flag in line for flag in flags)]
    assert not leaks, (
        f"{readme} shows a flag in a section the challenge page opens by default; "
        f"move it under a '## Solution' heading:\n" + "\n".join(leaks))
