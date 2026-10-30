"""POST /ctf/verify/<id> through Flask's test client, without a stack.

software/landing/modules/ctf_routes.py is the HTTP layer of answer-graded
challenges: the 413 from Content-Length, the mapping of AnswerError and of the
throttle to status codes (429 with Retry-After), the "already solved"
short-circuit before anything is graded, and saving a solve. No challenge in
ctf_config.json declares answers yet, so this is also the end-to-end graded
solve: a real CTFManager with a test challenge and a fake verify module, its
progress file in tmp_path.

No container is touched and the board's progress file is never opened.
"""
import json
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")
sys.path.insert(0, LANDING)

flask = pytest.importorskip("flask")
try:
    from modules import ctf_manager as cm
    from modules.ctf_routes import register_verify_route
    from modules.defense_checks import _answers
except ImportError as error:  # markdown missing on this host
    pytest.skip(f"landing modules not importable here ({error})", allow_module_level=True)

FLAG = "CybICS(route_test_flag)"
LEGACY_FLAG = "CybICS(route_legacy_flag)"
RIGHT = {"register": "40001", "function_code": "0x06"}


@pytest.fixture
def stack_free(monkeypatch, tmp_path):
    """A Flask app with only the verify route, a CTFManager over two test challenges."""
    calls, solves = [], []

    def graded_verify(answers):
        calls.append(answers)
        return _answers.grade(answers, {"register": _answers.number(40001),
                                        "function_code": _answers.one_of("6", "0x06")})

    def legacy_verify():
        calls.append("legacy")
        return {"success": True, "message": "Defense in place.", "checks": []}

    monkeypatch.setitem(sys.modules, "modules.defense_checks.fake_route_graded",
                        types.SimpleNamespace(verify=graded_verify))
    monkeypatch.setitem(sys.modules, "modules.defense_checks.fake_route_legacy",
                        types.SimpleNamespace(verify=legacy_verify))
    monkeypatch.setattr(cm, "PROGRESS_FILE", str(tmp_path / "ctf_progress.json"))
    monkeypatch.setattr(cm.CTFManager, "_load_config", lambda self: {"categories": {"t": {"challenges": [
        {"id": "graded", "title": "Graded", "points": 100, "type": "verify",
         "verify_module": "fake_route_graded", "flag": FLAG,
         "answers": [{"name": "register", "label": "Register", "max_length": 20},
                     {"name": "function_code", "label": "Function code", "max_length": 20}]},
        {"id": "legacy", "title": "Legacy", "points": 50, "type": "defense",
         "verify_module": "fake_route_legacy", "flag": LEGACY_FLAG},
    ]}}})
    manager = cm.CTFManager()

    app = flask.Flask(__name__)
    app.secret_key = "test"
    register_verify_route(app, manager, lambda cid, flag: solves.append((cid, flag)))
    client = app.test_client()
    return types.SimpleNamespace(client=client, manager=manager, calls=calls, solves=solves,
                                 progress=lambda: manager.load_progress())


def post(env, challenge_id, payload=None, raw=None, addr="10.0.0.5", **kwargs):
    data = raw if raw is not None else (json.dumps(payload) if payload is not None else None)
    return env.client.post(f"/ctf/verify/{challenge_id}", data=data, content_type="application/json",
                           environ_base={"REMOTE_ADDR": addr}, **kwargs)


def refused(resp, status):
    assert resp.status_code == status, resp.get_data(as_text=True)
    body = resp.get_json()
    assert body["success"] is False and "flag" not in body
    assert "CybICS(" not in resp.get_data(as_text=True)
    return body


def test_a_right_answer_solves_the_challenge_and_saves_it(stack_free):
    resp = post(stack_free, "graded", {"answers": RIGHT})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True and body["flag"] == FLAG and body["points"] == 100
    assert stack_free.calls == [RIGHT]
    assert stack_free.progress() == {"solved_challenges": ["graded"], "total_points": 100}
    assert stack_free.solves == [("graded", FLAG)]


def test_a_wrong_answer_says_neither_which_field_nor_the_flag(stack_free):
    body = refused(post(stack_free, "graded", {"answers": {"register": "40001", "function_code": "16"}}), 200)
    assert len(body["checks"]) == 1 and "40001" not in json.dumps(body)
    assert stack_free.progress()["solved_challenges"] == []


def test_a_solved_challenge_is_not_graded_again(stack_free):
    post(stack_free, "graded", {"answers": RIGHT})
    again = post(stack_free, "graded", {"answers": {"register": "1", "function_code": "1"}})
    assert again.status_code == 200 and again.get_json()["message"] == "Challenge already solved!"
    assert "flag" not in again.get_json()
    assert len(stack_free.calls) == 1
    assert stack_free.progress()["total_points"] == 100


def test_an_unknown_challenge_is_404(stack_free):
    refused(post(stack_free, "nope"), 404)


def test_a_declared_oversized_body_is_413_before_it_is_read(stack_free):
    big = json.dumps({"answers": {"register": "a" * (cm.ANSWER_BODY_LIMIT + 1)}})
    refused(post(stack_free, "graded", raw=big), 413)
    assert stack_free.calls == []


@pytest.mark.parametrize("payload", [None, {}, {"answers": {"register": "40001"}},
                                     {"answers": {**RIGHT, "extra": "1"}}])
def test_malformed_answers_are_400_and_never_graded(stack_free, payload):
    refused(post(stack_free, "graded", payload), 400)
    assert stack_free.calls == []


def test_too_many_attempts_are_429_with_retry_after(stack_free):
    wrong = {"answers": {"register": "1", "function_code": "1"}}
    for _ in range(cm.ANSWER_ATTEMPTS):
        assert post(stack_free, "graded", wrong).status_code == 200
    blocked = post(stack_free, "graded", {"answers": RIGHT})
    refused(blocked, 429)
    assert 1 <= int(blocked.headers["Retry-After"]) <= int(cm.ANSWER_WINDOW) + 1
    assert stack_free.progress()["solved_challenges"] == []
    # A different address is not locked out by the first one.
    assert post(stack_free, "graded", {"answers": RIGHT}, addr="10.0.0.7").get_json()["success"] is True


def test_a_challenge_without_fields_still_verifies_without_a_body(stack_free):
    resp = post(stack_free, "legacy")
    assert resp.status_code == 200 and resp.get_json()["flag"] == LEGACY_FLAG
    assert stack_free.calls == ["legacy"]
    refused(post(stack_free, "legacy", {"answers": {"x": "1"}}), 400)


# --- the AI assistant's verify tool ------------------------------------------

def _agent_training(monkeypatch):
    """software/cybicsagent/tools/training.py alone, without the agent's other tools."""
    import importlib.util
    agent = os.path.join(ROOT, "software", "cybicsagent")
    monkeypatch.syspath_prepend(agent)
    monkeypatch.delitem(sys.modules, "config", raising=False)
    spec = importlib.util.spec_from_file_location("agent_training_under_test",
                                                  os.path.join(agent, "tools", "training.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("status, message, expect", [
    (404, "Challenge not found", "Challenge not found"),
    (400, "Please fill in the answer fields", "typed answer"),
    (429, "Too many attempts. Try again in 30 seconds.", "Too many attempts"),
])
def test_the_assistant_passes_on_why_landing_refused(monkeypatch, status, message, expect):
    requests = pytest.importorskip("requests")
    training = _agent_training(monkeypatch)

    class Resp:
        status_code = status

        def json(self):
            return {"success": False, "message": message, "checks": []}

        def raise_for_status(self):
            raise requests.HTTPError(str(status))

    monkeypatch.setattr(training.requests, "post", lambda *a, **k: Resp())
    result = training.verify_defense_challenge("some_challenge")
    assert expect in result["error"]
