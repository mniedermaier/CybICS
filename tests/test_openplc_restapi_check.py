"""The Forgotten API challenge's verify module, without a stack.

software/landing/modules/defense_checks/check_openplc_restapi.py logs in on
OpenPLC's REST API (port 8443) with the typed credentials and passes when the
authenticated user list contains the account. requests is replaced by a fake
that behaves like OpenPLC v3's webserver/restapi.py: /login returns an
access_token for a known user and password, the token unlocks
/get-users-info and /status, everything else is 401.

tests/test_training.py::TestOpenplcRestApi runs the challenge on a live stack.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

try:
    import requests
    from modules.defense_checks import check_openplc_restapi as check
except ImportError as error:  # requests missing on this host
    pytest.skip(f"REST API check not importable here ({error})", allow_module_level=True)

USER, PASSWORD = "student", "training-only-42"


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeApi:
    """OpenPLC's REST API: one user table, bearer tokens, a run state."""

    def __init__(self, users=None, status="STATUS:RUNNING"):
        self.users = dict(users if users is not None else {USER: PASSWORD})
        self.status = status
        self.calls = []

    def request(self, method, url, verify=True, timeout=None, json=None, headers=None):
        assert url.startswith("https://172.18.0.3:8443/api/"), url
        assert verify is False and timeout
        path = url.split("/api", 1)[1]
        self.calls.append((method, path))
        token = (headers or {}).get("Authorization", "")
        authed = token.startswith("Bearer tok-") and token[len("Bearer tok-"):] in self.users
        if method == "POST" and path == "/login":
            if self.users.get(json.get("username")) == json.get("password"):
                return FakeResponse(200, {"access_token": f"tok-{json['username']}"})
            return FakeResponse(401, "Wrong username or password")
        if method == "GET" and path == "/get-users-info":
            if not authed:
                return FakeResponse(200, {"msg": "Users found"})
            return FakeResponse(200, [{"id": i + 1, "username": n, "role": "user"}
                                      for i, n in enumerate(self.users)])
        if method == "GET" and path == "/status":
            return FakeResponse(200, {"status": self.status}) if authed else \
                FakeResponse(401, {"msg": "Missing Authorization Header"})
        raise AssertionError(f"the check must not call {method} {path}")


@pytest.fixture
def api(monkeypatch):
    fake = FakeApi()
    monkeypatch.setattr(check.requests, "request", fake.request)
    return fake


def names(result):
    return {c["name"]: c["passed"] for c in result["checks"]}


def test_the_account_owner_passes(api):
    result = check.verify({"username": USER, "password": PASSWORD})
    assert result["success"], result
    assert all(c["passed"] for c in result["checks"])
    assert "STATUS:RUNNING" in json.dumps(result)


def test_only_reads_are_sent(api):
    check.verify({"username": USER, "password": PASSWORD})
    assert api.calls == [("POST", "/login"), ("GET", "/get-users-info"), ("GET", "/status")]


@pytest.mark.parametrize("answers", [
    {"username": USER, "password": "x"},
    {"username": USER, "password": "1234567"},
    {"username": "", "password": PASSWORD},
    {},
    None,
])
def test_short_or_missing_input_fails_before_any_request(api, answers):
    result = check.verify(answers)
    assert not result["success"]
    assert api.calls == []


def test_a_wrong_password_fails_at_login(api):
    result = check.verify({"username": USER, "password": "wrong-password"})
    assert not result["success"]
    assert names(result)["Login on the REST API (port 8443)"] is False
    assert "8080" in json.dumps(result)          # points at the separate user database
    assert api.calls == [("POST", "/login")]


def test_the_web_interface_login_does_not_count(api):
    result = check.verify({"username": "openplc", "password": "openplc-strong"})
    assert not result["success"]


def test_an_account_missing_from_the_list_fails(api, monkeypatch):
    # A login that works while the authenticated list does not name the
    # account (for example a renamed user): no flag.
    original = api.request

    def hide(method, url, **kwargs):
        resp = original(method, url, **kwargs)
        if url.endswith("/get-users-info") and isinstance(resp.json(), list):
            return FakeResponse(200, [u for u in resp.json() if u["username"] != USER])
        return resp
    monkeypatch.setattr(check.requests, "request", hide)
    result = check.verify({"username": USER, "password": PASSWORD})
    assert not result["success"]
    assert names(result)["Account in the API's user table"] is False


def test_a_refused_status_fails(api, monkeypatch):
    original = api.request

    def refuse(method, url, **kwargs):
        if url.endswith("/status"):
            return FakeResponse(401, {"msg": "Token has been revoked"})
        return original(method, url, **kwargs)
    monkeypatch.setattr(check.requests, "request", refuse)
    result = check.verify({"username": USER, "password": PASSWORD})
    assert not result["success"]
    assert names(result)["Authenticated PLC command"] is False


def test_an_unreachable_api_fails_closed(monkeypatch):
    def down(*args, **kwargs):
        raise requests.exceptions.ConnectionError("refused")
    monkeypatch.setattr(check.requests, "request", down)
    result = check.verify({"username": USER, "password": PASSWORD})
    assert not result["success"]
    assert names(result)["REST API reachable"] is False


def test_a_non_json_answer_fails_closed(monkeypatch):
    monkeypatch.setattr(check.requests, "request",
                        lambda *a, **k: FakeResponse(200, ValueError("not json")))
    result = check.verify({"username": USER, "password": PASSWORD})
    assert not result["success"]
    assert names(result)["REST API answer"] is False


def test_the_password_is_never_echoed(api):
    for password in (PASSWORD, "wrong-password"):
        result = check.verify({"username": USER, "password": password})
        assert password not in json.dumps(result)


def test_the_flag_is_not_in_the_module():
    with open(check.__file__, encoding="utf-8") as fh:
        assert "CybICS(" not in fh.read()
