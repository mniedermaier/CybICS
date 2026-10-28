"""
Grading helpers for answer-graded challenges.

A challenge that declares "answers" in ctf_config.json gets the student's text
as verify(answers), a dict {field name: stripped text} already bounded by
ctf_manager.parse_answers. Its verify module keeps the expected values and
grades with grade() below, so they never reach the browser:

    from modules.defense_checks._answers import grade, number, one_of

    def verify(answers):
        return grade(answers, {
            "port": number(502),
            "function_code": one_of("6", "0x06", "write single register"),
        }, labels={"port": "Modbus port", "function_code": "Function code"})

By default the result holds a single check, "all correct" or not, so a field
with few possible values (a function code, a register type) cannot be solved
one field at a time. Pass feedback=True for per-field checks only where every
field has many possible values. Checks never say what the right answer is and
never echo what was typed.
"""
import hmac
import re

__all__ = ["normalize", "one_of", "number", "matches", "grade"]


def normalize(value):
    """Case-insensitive, whitespace-collapsed form used for comparisons."""
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def _same(a, b):
    return hmac.compare_digest(normalize(a).encode("utf-8"), normalize(b).encode("utf-8"))


def one_of(*accepted):
    """Accept any of several spellings, compared after normalize()."""
    if not accepted:
        raise ValueError("one_of() needs at least one accepted answer")

    def check(value):
        # Compare against every spelling, so the time taken does not depend on which matched.
        hits = [_same(value, candidate) for candidate in accepted]
        return any(hits)
    return check


def number(expected, tolerance=0):
    """Accept a number (decimal or 0x-hex) within an absolute tolerance."""
    def check(value):
        text = normalize(value).replace(" ", "")
        try:
            got = int(text, 16) if text.startswith("0x") else float(text)
        except ValueError:
            return False
        return abs(got - expected) <= tolerance
    return check


def _check_spec(name, expected):
    """Refuse an expected value matches() cannot compare, naming the field."""
    if callable(expected) or isinstance(expected, str):
        return
    if isinstance(expected, (list, tuple, set, frozenset)) and expected \
            and all(isinstance(item, str) for item in expected):
        return
    raise TypeError(f"answer '{name}': expected a string, a non-empty list of strings or a "
                    f"checker such as number() or one_of(), got {type(expected).__name__} "
                    f"(write number(502), not 502)")


def matches(value, expected):
    """True if value satisfies expected: a string, an iterable of strings or a callable."""
    _check_spec("?", expected)
    if callable(expected):
        return bool(expected(value))
    if isinstance(expected, str):
        return _same(value, expected)
    return one_of(*expected)(value)


def grade(answers, expected, labels=None, feedback=False,
          success_message="All answers are correct!",
          failure_message="Not all answers are correct yet."):
    """Grade answers against expected and build a verify() result.

    expected maps every field name to what matches() accepts; a value it
    cannot compare raises TypeError before anything is graded. By default
    the result holds a single check, so a student cannot solve the fields one
    at a time. feedback=True gives one check per field; use it only where
    every field has many possible values.
    """
    if not isinstance(expected, dict) or not expected:
        raise TypeError("grade() needs a non-empty dict {field name: expected value}")
    for name, want in expected.items():
        _check_spec(name, want)
    labels = labels or {}
    answers = answers if isinstance(answers, dict) else {}
    results = {name: matches(answers.get(name, ""), want) if answers.get(name) else False
               for name, want in expected.items()}
    success = bool(results) and all(results.values())

    if feedback:
        checks = [{"name": labels.get(name, name),
                   "passed": ok,
                   "detail": "Correct" if ok else "Not correct yet"}
                  for name, ok in results.items()]
    else:
        checks = [{"name": "Answers",
                   "passed": success,
                   "detail": "All correct" if success else "At least one answer is not correct yet"}]

    return {"success": success,
            "message": success_message if success else failure_message,
            "checks": checks}
