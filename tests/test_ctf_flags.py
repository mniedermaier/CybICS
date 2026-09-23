"""Tests for CTF flag validation and for the flag data itself.

CLAUDE.md singles this area out: flags have the form `CybICS(...)`, they live
in software/landing/ctf_config.json, and the warning there is to watch for `0`
versus `O`. A malformed or duplicated flag is not a crash, it is a challenge
nobody can solve, or one that solves a different challenge.

software/landing/modules/ctf_manager.py needs no Flask and no running stack.
"""
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")
CONFIG = os.path.join(LANDING, "ctf_config.json")

if not os.path.exists(CONFIG):
    pytest.skip("landing ctf_config.json not present", allow_module_level=True)

sys.path.insert(0, LANDING)

# ctf_manager imports `markdown` at module level, only for rendering challenge
# text. The flag data tests below need nothing but json, so they must not be
# held hostage to that: the import is optional and only the submission tests
# depend on it.
try:
    from modules.ctf_manager import CTFManager
except ImportError as _error:  # pragma: no cover - depends on the environment
    CTFManager = None
    _import_error = _error
else:
    _import_error = None

needs_manager = pytest.mark.skipif(
    CTFManager is None, reason=f"ctf_manager not importable here ({_import_error})"
)

FLAG_RE = re.compile(r"^CybICS\(.+\)$")


@pytest.fixture(scope="module")
def manager():
    if CTFManager is None:
        pytest.skip(f"ctf_manager not importable here ({_import_error})")
    return CTFManager()


@pytest.fixture(scope="module")
def challenges():
    with open(CONFIG, encoding="utf-8") as fh:
        config = json.load(fh)
    out = []
    for category in config.get("categories", {}).values():
        out.extend(category.get("challenges", []))
    assert out, "ctf_config.json defines no challenges"
    return out


# --- the flag data -----------------------------------------------------------

def test_every_flag_has_the_documented_shape(challenges):
    """A flag outside CybICS(...) is rejected by submit_flag's own format check."""
    wrong = [c["id"] for c in challenges if not FLAG_RE.match(c["flag"])]
    assert not wrong, f"flags not of the form CybICS(...): {wrong}"


def test_no_two_challenges_share_a_flag(challenges):
    """A duplicate would credit whichever challenge the loop reaches first."""
    seen = {}
    for c in challenges:
        seen.setdefault(c["flag"], []).append(c["id"])
    clashes = {flag: ids for flag, ids in seen.items() if len(ids) > 1}
    assert not clashes, f"the same flag appears on several challenges: {clashes}"


def test_challenge_ids_are_unique(challenges):
    """get_challenge returns the first match, so a duplicate id hides one."""
    ids = [c["id"] for c in challenges]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"duplicate challenge ids: {sorted(duplicates)}"


def test_no_flag_has_leading_or_trailing_whitespace(challenges):
    """submit_flag strips what the user types but not what the file holds."""
    untidy = [c["id"] for c in challenges if c["flag"] != c["flag"].strip()]
    assert not untidy, f"flags with surrounding whitespace, unsolvable as typed: {untidy}"


def test_every_challenge_is_worth_points(challenges):
    bad = [c["id"] for c in challenges
           if not isinstance(c.get("points"), int) or c["points"] <= 0]
    assert not bad, f"challenges with missing or non-positive points: {bad}"


# --- submission --------------------------------------------------------------

def _first(manager):
    for category in manager.challenges.values():
        for challenge in category["challenges"]:
            return challenge
    pytest.skip("no challenges configured")


@needs_manager
def test_the_right_flag_is_accepted_and_awards_its_points(manager):
    challenge = _first(manager)
    result = manager.submit_flag(challenge["id"], challenge["flag"], {"solved_challenges": []})
    assert result["success"] is True
    assert result["points"] == challenge["points"]


@needs_manager
def test_surrounding_whitespace_is_forgiven(manager):
    """People paste flags; a trailing newline must not read as a wrong answer."""
    challenge = _first(manager)
    result = manager.submit_flag(
        challenge["id"], f"  {challenge['flag']}\n", {"solved_challenges": []}
    )
    assert result["success"] is True


@needs_manager
def test_a_solved_challenge_cannot_be_scored_twice(manager):
    challenge = _first(manager)
    result = manager.submit_flag(
        challenge["id"], challenge["flag"], {"solved_challenges": [challenge["id"]]}
    )
    assert result["success"] is False
    assert "already solved" in result["message"].lower()


@needs_manager
def test_an_unknown_challenge_is_refused_rather_than_crashing(manager):
    result = manager.submit_flag("no-such-challenge", "CybICS(x)", {"solved_challenges": []})
    assert result["success"] is False
    assert "not found" in result["message"].lower()


@needs_manager
def test_a_wrong_value_in_the_right_shape_says_so(manager):
    """Telling the two apart is the difference between 'keep going' and 'you
    are pasting the wrong thing entirely'."""
    challenge = _first(manager)
    result = manager.submit_flag(challenge["id"], "CybICS(definitely-not-it)",
                                 {"solved_challenges": []})
    assert result["success"] is False
    assert "format is right" in result["message"]


@needs_manager
def test_something_that_is_not_a_flag_gets_the_format_hint(manager):
    challenge = _first(manager)
    result = manager.submit_flag(challenge["id"], "hunter2", {"solved_challenges": []})
    assert result["success"] is False
    assert "CybICS(" in result["message"]


@needs_manager
def test_case_matters(manager):
    """Flags are compared exactly; a case-insensitive match would weaken them."""
    challenge = _first(manager)
    result = manager.submit_flag(challenge["id"], challenge["flag"].upper(),
                                 {"solved_challenges": []})
    if challenge["flag"].upper() != challenge["flag"]:
        assert result["success"] is False
