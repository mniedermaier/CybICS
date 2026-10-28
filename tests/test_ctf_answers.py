"""Answer-graded CTF challenges, without a stack.

A "verify" (or "defense") challenge may declare "answers" in ctf_config.json:
the page then shows text fields, POST /ctf/verify/<id> carries
{"answers": {...}}, software/landing/modules/ctf_manager.py bounds and
validates them before any module runs, and the verify module grades them
server-side as verify(answers). These tests pin that contract: limits,
backwards compatibility with verify(), no flag unless the grade passes, no
expected answer in a response or on the page, and the attempt throttle.

No container is touched. Verify modules are fakes put into sys.modules.
"""
import ast
import importlib
import json
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")
CONFIG = os.path.join(LANDING, "ctf_config.json")
CHECKS_DIR = os.path.join(LANDING, "modules", "defense_checks")

sys.path.insert(0, LANDING)

try:
    from modules import ctf_manager as cm
    from modules.defense_checks import _answers
except ImportError as error:  # markdown missing on this host
    pytest.skip(f"ctf_manager not importable here ({error})", allow_module_level=True)

SECRET = "holding register 40001"
FLAG = "CybICS(test_answer_flag)"


def challenge(**extra):
    base = {"id": "answer_test", "title": "Answer test", "points": 100,
            "type": "verify", "verify_module": "fake_answer_check", "flag": FLAG,
            "answers": [{"name": "register", "label": "Register", "max_length": 40},
                        {"name": "port", "label": "Port"}]}
    base.update(extra)
    return base


def body(obj):
    return json.dumps(obj).encode()


# --- parse_answers: what a client may send ---------------------------------

def test_a_challenge_without_fields_keeps_the_old_bodyless_call():
    legacy = challenge(answers=None)
    assert cm.parse_answers(legacy, b"") is None
    assert cm.parse_answers(legacy, b"{}") is None
    assert cm.parse_answers(legacy, body({"answers": {}})) is None


def test_answers_to_a_challenge_without_fields_are_refused():
    with pytest.raises(cm.AnswerError) as err:
        cm.parse_answers(challenge(answers=None), body({"answers": {"x": "1"}}))
    assert err.value.status == 400


def test_valid_answers_are_stripped_and_returned():
    got = cm.parse_answers(challenge(), body({"answers": {"register": "  40001 ", "port": "502"}}))
    assert got == {"register": "40001", "port": "502"}


@pytest.mark.parametrize("payload, status", [
    (b"not json", 400),
    (b"[1, 2]", 400),
    (body({}), 400),                                                    # no answers at all
    (body({"answers": "40001"}), 400),                                  # not an object
    (body({"answers": {"register": "1"}}), 400),                        # a field missing
    (body({"answers": {"register": "1", "port": "   "}}), 400),         # blank after strip
    (body({"answers": {"register": "1", "port": 502}}), 400),           # not text
    (body({"answers": {"register": "1", "port": "2", "x": "3"}}), 400),  # unknown field
    (body({"answers": {"register": "a" * 41, "port": "2"}}), 400),      # over the field's cap
    (body({"answers": {"register": "a\x00b", "port": "2"}}), 400),      # control character
    (b"{" + b" " * cm.ANSWER_BODY_LIMIT + b"}", 413),                   # over the body cap
])
def test_malformed_answers_are_refused_before_any_module_runs(payload, status):
    with pytest.raises(cm.AnswerError) as err:
        cm.parse_answers(challenge(), payload)
    assert err.value.status == status


def test_the_default_field_cap_is_the_hard_cap():
    ok = {"register": "r", "port": "p" * cm.ANSWER_MAX_LENGTH}
    assert cm.parse_answers(challenge(), body({"answers": ok}))["port"] == ok["port"]
    ok["port"] += "p"
    with pytest.raises(cm.AnswerError):
        cm.parse_answers(challenge(), body({"answers": ok}))


@pytest.mark.parametrize("spec", [
    "port",
    [{"label": "no name"}],
    [{"name": "Port"}],                                  # upper case
    [{"name": "a"}, {"name": "a"}],                      # duplicate
    [{"name": "a", "max_length": 0}],
    [{"name": "a", "max_length": cm.ANSWER_MAX_LENGTH + 1}],
    [{"name": "a", "max_length": True}],
    [{"name": f"f{i}"} for i in range(cm.ANSWER_MAX_FIELDS + 1)],
])
def test_a_misconfigured_declaration_fails_closed(spec):
    with pytest.raises(cm.AnswerError) as err:
        cm.answer_fields(challenge(answers=spec))
    assert err.value.status == 500


# --- verify_defense: grading, flag, throttle -------------------------------

@pytest.fixture
def manager(monkeypatch):
    """A CTFManager holding only the test challenge and a fake verify module."""
    calls = []

    def verify(answers=None, *rest):
        calls.append(answers)
        ok = _answers.grade(answers, {"register": SECRET, "port": _answers.number(502)},
                            labels={"register": "Register", "port": "Port"}, feedback=True)
        # A module that tries to hand out a flag itself must not succeed at it.
        ok["flag"] = "CybICS(leaked_by_module)"
        return ok

    def legacy_verify():
        calls.append("legacy")
        return {"success": True, "message": "ok", "checks": []}

    monkeypatch.setitem(sys.modules, "modules.defense_checks.fake_answer_check",
                        types.SimpleNamespace(verify=verify))
    monkeypatch.setitem(sys.modules, "modules.defense_checks.fake_legacy_check",
                        types.SimpleNamespace(verify=legacy_verify))
    monkeypatch.setattr(cm.CTFManager, "_load_config", lambda self: {"categories": {"t": {"challenges": [
        challenge(),
        challenge(id="legacy_test", verify_module="fake_legacy_check", answers=None,
                  flag="CybICS(legacy_flag)"),
    ]}}})
    m = cm.CTFManager()
    m.calls = calls
    return m


def test_a_right_answer_reveals_the_flag(manager):
    result = manager.verify_defense("answer_test", {"register": "Holding  Register 40001", "port": "0x1F6"})
    assert result["success"] is True
    assert result["flag"] == FLAG


def test_a_wrong_answer_reveals_neither_flag_nor_expected_answer(manager):
    result = manager.verify_defense("answer_test", {"register": "coil 1", "port": "502"})
    assert result["success"] is False
    assert "flag" not in result
    text = json.dumps(result)
    assert SECRET not in text.lower() and "CybICS(" not in text and "coil 1" not in text
    assert [c["passed"] for c in result["checks"]] == [False, True]


def test_an_answer_challenge_without_answers_is_not_graded(manager):
    result = manager.verify_defense("answer_test", None)
    assert result["success"] is False and "flag" not in result
    assert manager.calls == []


def test_a_challenge_without_fields_still_calls_verify_without_arguments(manager):
    result = manager.verify_defense("legacy_test")
    assert manager.calls == ["legacy"]
    assert result["success"] is True and result["flag"] == "CybICS(legacy_flag)"


def test_module_output_is_reduced_to_what_the_page_renders(manager):
    result = manager.verify_defense("answer_test", {"register": "x", "port": "1"})
    assert set(result) == {"success", "message", "checks"}
    for check in result["checks"]:
        assert set(check) == {"name", "passed", "detail"}


def test_graded_attempts_are_throttled_per_challenge_and_client(manager):
    wrong = {"register": "x", "port": "1"}
    for _ in range(cm.ANSWER_ATTEMPTS):
        assert "retry_after" not in manager.verify_defense("answer_test", wrong, client="10.0.0.5")
    blocked = manager.verify_defense("answer_test", {"register": SECRET, "port": "502"}, client="10.0.0.5")
    assert blocked["success"] is False and blocked["retry_after"] >= 1 and "flag" not in blocked
    assert len(manager.calls) == cm.ANSWER_ATTEMPTS
    # Another host used up its own attempts, not the student's.
    student = manager.verify_defense("answer_test", {"register": SECRET, "port": "502"}, client="10.0.0.7")
    assert student["success"] is True and student["flag"] == FLAG
    # The legacy challenge has no answers and is never throttled.
    assert manager.verify_defense("legacy_test", client="10.0.0.5")["success"] is True


def test_the_throttle_window_slides(manager):
    for i in range(cm.ANSWER_ATTEMPTS):
        assert manager._take_attempt("c", "a", now=100.0 + i) == 0
    assert manager._take_attempt("c", "a", now=100.0 + cm.ANSWER_ATTEMPTS) > 0
    assert manager._take_attempt("c", "b", now=100.0 + cm.ANSWER_ATTEMPTS) == 0
    assert manager._take_attempt("c", "a", now=100.0 + cm.ANSWER_WINDOW + 0.5) == 0


def test_stale_throttle_buckets_are_dropped(manager):
    for i in range(cm.ANSWER_MAX_BUCKETS + 1):
        manager._take_attempt("c", f"10.1.{i // 256}.{i % 256}", now=0.0)
    manager._take_attempt("c", "fresh", now=cm.ANSWER_WINDOW + 1)
    assert len(manager._attempts) == 1


# --- the grading helpers ----------------------------------------------------

def test_normalize_ignores_case_and_spacing():
    assert _answers.matches("  Modbus\tTCP ", "modbus tcp")
    assert not _answers.matches("modbustcp", "modbus tcp")


def test_one_of_and_number():
    fc = _answers.one_of("6", "0x06", "write single register")
    assert fc("0X06") and fc("Write Single Register") and not fc("16")
    port = _answers.number(502)
    assert port("502") and port("0x1f6") and port("502.0") and not port("503") and not port("five")
    assert _answers.number(3.3, tolerance=0.1)("3.25")


def test_grade_by_default_does_not_say_which_field_is_wrong():
    result = _answers.grade({"a": "1", "b": "x"}, {"a": "1", "b": "2"})
    assert result["success"] is False
    assert len(result["checks"]) == 1
    assert _answers.grade({"a": "1", "b": "2"}, {"a": "1", "b": "2"})["success"] is True


def test_per_field_feedback_is_opt_in():
    result = _answers.grade({"a": "1", "b": "x"}, {"a": "1", "b": "2"}, feedback=True)
    assert [c["passed"] for c in result["checks"]] == [True, False]


def test_grade_needs_every_field():
    assert not _answers.grade({}, {"a": "1"})["success"]
    assert not _answers.grade({"a": "1"}, {"a": "1", "b": "2"})["success"]


@pytest.mark.parametrize("expected", [{}, {"port": 502}, {"port": None}, {"port": []},
                                      {"port": ["502", 502]}, "502"])
def test_an_expected_value_grade_cannot_compare_is_a_clear_type_error(expected):
    # Raised before any answer is looked at, so even an empty submission trips it.
    with pytest.raises(TypeError):
        _answers.grade({}, expected)


# --- ctf_config.json and the page -------------------------------------------

def _challenges():
    with open(CONFIG, encoding="utf-8") as fh:
        config = json.load(fh)
    return [c for cat in config["categories"].values() for c in cat["challenges"]]


def _verify_takes_an_argument(module_name):
    with open(os.path.join(CHECKS_DIR, module_name + ".py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "verify":
            return bool(node.args.args or node.args.vararg)
    return False


def test_every_declared_answer_set_is_wellformed_and_graded_by_its_module():
    for chall in _challenges():
        fields = cm.answer_fields(chall)  # raises on a malformed declaration
        if not fields:
            continue
        assert chall.get("type") in ("verify", "defense"), chall["id"]
        assert chall.get("verify_module"), chall["id"]
        assert _verify_takes_an_argument(chall["verify_module"]), \
            f"{chall['id']}: {chall['verify_module']}.verify() must accept the answers"
        # Grade a wrong answer for real: a bad expected value in the module
        # (502 instead of number(502)) raises TypeError here, at test time,
        # instead of a generic internal error on the board. A graded module
        # must not touch the stack, so this needs none.
        module = importlib.import_module(f"modules.defense_checks.{chall['verify_module']}")
        wrong = {f["name"]: "x" for f in fields}
        result = module.verify(wrong)
        assert isinstance(result, dict) and result.get("success") is False, chall["id"]
        assert "flag" not in result and chall["flag"] not in json.dumps(result), chall["id"]


def test_the_page_shows_the_fields_and_nothing_to_grade_with():
    flask = pytest.importorskip("flask")
    app = flask.Flask(__name__, template_folder=os.path.join(LANDING, "templates"))
    chall = challenge()
    with app.test_request_context("/ctf/challenge/answer_test"):
        html = flask.render_template("challenge.html", challenge=chall, category={"name": "t"},
                                     training_content="", solved=False, challenge_type="verify",
                                     answer_fields=cm.answer_fields(chall))
        legacy = flask.render_template("challenge.html", challenge=chall, category={"name": "t"},
                                       training_content="", solved=False, challenge_type="verify",
                                       answer_fields=[])
    assert 'data-answer-name="register"' in html and 'maxlength="40"' in html
    assert 'data-answer-name="port"' in html and f'maxlength="{cm.ANSWER_MAX_LENGTH}"' in html
    assert FLAG not in html and SECRET not in html
    assert 'id="verify-button"' in legacy and "data-answer-name=" not in legacy
