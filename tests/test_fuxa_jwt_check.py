"""The two FUXA token challenges' verify modules, without a stack.

software/landing/modules/defense_checks/_fuxa_jwt.py signs HS256 tokens with
the standard library and decides whether FUXA could have issued a token
itself; check_fuxa_jwt.py grades a pasted token and check_fuxa_jwt_secret.py
judges the defence. FUXA's HTTP API and the Docker calls are replaced by a
fake that behaves like FUXA 1.2.6 (api/jwt-helper.js): a token whose
signature matches the current key is trusted, its groups decide admin, and
an invalid token counts as a guest.

tests/test_training.py::TestFuxaJwt runs both challenges on a live stack.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

try:
    from modules.defense_checks import _fuxa_jwt as jwt
    from modules.defense_checks import check_fuxa_jwt as attack
    from modules.defense_checks import check_fuxa_jwt_secret as defense
except ImportError as error:  # requests missing on this host
    pytest.skip(f"FUXA token checks not importable here ({error})", allow_module_level=True)

DEFAULT = "frangoteam751"
STRONG = "4f1c9a7be2d84c06a3e5f7918b2d6c40e1a9f3b75d28c6e4"
USERS = ["admin", "viewer", "operator"]


# --- the signer -----------------------------------------------------------

def test_forge_matches_the_well_known_hs256_example():
    # The HS256 example token of jwt.io, signed with "your-256-bit-secret".
    expected = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4g"
                "RG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c")
    token = jwt.forge({"sub": "1234567890", "name": "John Doe", "iat": 1516239022},
                      "your-256-bit-secret")
    assert token == expected
    assert "=" not in token


def test_forge_matches_a_token_fuxa_signed():
    # A real FUXA 1.2.6 guest token, signed with the default key.
    real = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Imd1ZXN0IiwiZ3JvdXBzIjpbImd1ZXN0Il0s"
            "ImlhdCI6MTc5MzIwNjExNSwiZXhwIjoxNzkzMjA5NzE1fQ.y0yutHYb2IJ8wybIYMB_6DWvajeowcKYDjG0XOsMAZE")
    assert jwt.signed_with(real, DEFAULT)
    assert not jwt.signed_with(real, STRONG)
    payload = jwt.decode(real)[1]
    assert jwt.forge(payload, DEFAULT) == real


def test_signed_with_rejects_garbage():
    assert not jwt.signed_with("not a token", DEFAULT)
    assert not jwt.signed_with(None, DEFAULT)


# --- decoding and the FUXA-issued shape -----------------------------------

@pytest.mark.parametrize("token", [
    "", "abc", "a.b", "a.b.c.d", "a b.c.d",
    "eyJhIjox.eyJiIjox.sig",                                 # truncated base64/JSON
    jwt._b64(b"[1]") + "." + jwt._b64(b"{}") + ".x",          # header not an object
    jwt._b64(b"{}") + "." + jwt._b64(b'"text"') + ".x",       # payload not an object
    jwt._b64(b"{}") + "." + jwt._b64(b"\xff\xfe") + ".x",     # not UTF-8
])
def test_decode_refuses_what_is_not_a_jwt(token):
    assert jwt.decode(token) is None


@pytest.mark.parametrize("payload, could", [
    ({"id": "ghost", "groups": -1, "iat": 1000, "exp": 1000 + 3600}, True),
    ({"id": "ghost", "groups": -1, "iat": 1000, "exp": 1000 + 900}, True),
    ({"id": "ghost", "groups": -1, "iat": 1000, "exp": 1000 + 10800}, True),
    ({"id": "ghost", "groups": -1, "iat": 1000, "exp": 1000 + 86400}, True),
    ({"id": "ghost", "groups": -1}, False),                              # no expiry
    ({"id": "ghost", "groups": -1, "iat": 1000, "exp": 1000 + 7200}, False),
    ({"id": "ghost", "groups": -1, "exp": 4600}, False),                 # no iat
    ({"id": "ghost", "groups": -1, "iat": 1000, "exp": 4600, "x": 1}, False),
    ({"id": "ghost", "groups": -1, "iat": "1000", "exp": 4600}, False),
    ({"id": "ghost", "groups": -1, "iat": True, "exp": 3601}, False),
])
def test_fuxa_could_issue(payload, could):
    assert jwt.fuxa_could_issue(payload) is could


# --- a fake FUXA ----------------------------------------------------------

class _Resp:
    def __init__(self, status, body=None):
        self.status_code = status
        self._body = body

    def json(self):
        if self._body is None:
            raise ValueError("no JSON")
        return self._body


class FakeFuxa:
    """Answers like FUXA 1.2.6 for the requests the checks make."""

    def __init__(self, key=DEFAULT, secure=True, up=True, broken_own_tokens=False):
        self.key, self.secure, self.up = key, secure, up
        self.broken_own_tokens = broken_own_tokens
        self.length = len(key) if key != DEFAULT else -1
        self.distinct = None   # None: the distinct characters of self.key

    def _claims(self, token):
        if not token or not jwt.signed_with(token, self.key):
            return None
        return jwt.decode(token)[1]

    def get(self, url, headers=None, timeout=None):
        if not self.up:
            raise jwt.requests.exceptions.ConnectionError("down")
        path = url.split(":1881", 1)[1]
        if path == "/":
            return _Resp(200)
        if path == "/api/settings":
            return _Resp(200, {"secureEnabled": self.secure})
        if path == "/api/users":
            claims = self._claims((headers or {}).get("x-access-token"))
            if not self.secure or (claims and claims.get("groups") in (-1, 255)):
                return _Resp(200, [{"username": u} for u in USERS])
            return _Resp(401, {"error": "unauthorized_error"})
        raise AssertionError(f"unexpected GET {url}")

    def post(self, url, json=None, headers=None, timeout=None):
        assert url.endswith("/api/heartbeat"), url
        headers = headers or {}
        token = headers.get("x-access-token")
        if token is None:
            guest = jwt.forge({"id": "guest", "groups": ["guest"], "iat": 1, "exp": 3601},
                              "other key" if self.broken_own_tokens else self.key)
            return _Resp(200, {"message": "guest", "token": guest})
        claims = self._claims(token)
        if claims and "x-auth-user" in headers:
            return _Resp(403)
        return _Resp(200, {"message": "guest"})


@pytest.fixture
def fuxa(monkeypatch):
    fake = FakeFuxa()
    monkeypatch.setattr(jwt.requests, "get", fake.get)
    monkeypatch.setattr(jwt.requests, "post", fake.post)
    monkeypatch.setattr(defense, "fuxa_container", lambda: "virtual-fuxa-1")
    monkeypatch.setattr(defense, "secret_stats", lambda container: (
        fake.length, len(set(fake.key)) if fake.distinct is None else fake.distinct))
    return fake


# --- the attack check -----------------------------------------------------

def _paste(token):
    return attack.verify({"token": token})


def test_forged_ghost_admin_token_passes(fuxa):
    result = _paste(jwt.forge({"id": "ghost", "groups": -1}))
    assert result["success"], result
    assert all(c["passed"] for c in result["checks"])


def test_group_255_and_own_lifetime_pass(fuxa):
    assert _paste(jwt.forge({"id": "nobody", "groups": 255, "iat": 10, "exp": 7210}))["success"]


@pytest.mark.parametrize("token, needle", [
    ("garbage", "Token format"),
    (jwt.forge({"user": "ghost", "groups": -1}), "FUXA claims"),
    (jwt.forge({"id": "ghost"}), "FUXA claims"),
    (jwt.forge({"id": "", "groups": -1}), "FUXA claims"),
    (jwt.forge({"id": "ghost", "groups": -1, "iat": 10, "exp": 3610}), "Not a token FUXA issues itself"),
    (jwt.forge({"id": "ghost", "groups": 1}), "Accepted as administrator"),          # viewer role
    (jwt.forge({"id": "ghost", "groups": -1}, "wrong key"), "Accepted as administrator"),
    (jwt.forge({"id": "admin", "groups": -1}), "User that does not exist"),          # real account
    (jwt.forge({"id": "Admin", "groups": -1}), "User that does not exist"),          # case variant
    (jwt.forge({"id": " admin ", "groups": -1}), "User that does not exist"),
    # What FUXA's heartbeat refresh signs for anyone (24 h lifetime in CybICS).
    (jwt.forge({"id": "ghost", "groups": -1, "iat": 10, "exp": 86410}), "Not a token FUXA issues itself"),
])
def test_attack_check_fails_closed(fuxa, token, needle):
    result = _paste(token)
    assert not result["success"], result
    failed = [c["name"] for c in result["checks"] if not c["passed"]]
    assert failed == [needle], result


def test_attack_check_needs_authentication_on(fuxa):
    fuxa.secure = False
    result = _paste(jwt.forge({"id": "ghost", "groups": -1}))
    assert not result["success"]
    assert "authentication" in result["message"]


def test_attack_check_with_rotated_key_fails(fuxa):
    fuxa.key = STRONG
    result = _paste(jwt.forge({"id": "ghost", "groups": -1}))
    assert not result["success"]


def test_attack_check_never_echoes_the_token(fuxa):
    token = jwt.forge({"id": "ghost", "groups": -1}, "wrong key")
    assert token not in json.dumps(_paste(token))


def test_attack_check_survives_fuxa_down(fuxa):
    fuxa.up = False
    result = _paste(jwt.forge({"id": "ghost", "groups": -1}))
    assert not result["success"]
    assert "reach" in result["message"].lower()


# --- the defence check ----------------------------------------------------

def _failed(result):
    return [c["name"] for c in result["checks"] if not c["passed"]]


def test_default_key_fails_the_defence(fuxa):
    result = defense.verify()
    assert not result["success"]
    assert {"FUXA tokens still work", "Default key rejected", "Key long and random"} <= set(_failed(result))


def test_long_random_key_passes(fuxa):
    fuxa.key, fuxa.length = STRONG, len(STRONG)
    result = defense.verify()
    assert result["success"], result
    assert len(result["checks"]) == 6


@pytest.mark.parametrize("key", ["Frangoteam751", "frangoteam752", "frangoteam751!", "changeme",
                                 "secret", "cybics"])
def test_guessable_keys_fail(fuxa, key):
    fuxa.key, fuxa.length = key, len(key)
    result = defense.verify()
    assert not result["success"]
    assert "Key not guessable" in _failed(result)


def test_guess_list_holds_the_default_and_its_variations():
    assert defense.DEFAULT_SECRET == "frangoteam751"
    variations = [k for k in defense.GUESSABLE_SECRETS if "frangoteam" in k.lower()]
    assert len(variations) >= 8
    assert len(set(defense.GUESSABLE_SECRETS)) == len(defense.GUESSABLE_SECRETS)


def test_short_random_key_fails_with_its_length(fuxa):
    fuxa.key = fuxa_key = "Xk3q9Zr2Lw"
    fuxa.length = len(fuxa_key)
    result = defense.verify()
    assert _failed(result) == ["Key long and random"]
    detail = next(c["detail"] for c in result["checks"] if c["name"] == "Key long and random")
    assert "10 characters" in detail and "32" in detail
    assert fuxa_key not in json.dumps(result)


def test_long_repetitive_key_fails(fuxa):
    fuxa.key = "a" * 40
    fuxa.length = 40
    result = defense.verify()
    assert _failed(result) == ["Key long and random"]
    detail = next(c["detail"] for c in result["checks"] if c["name"] == "Key long and random")
    assert "1 different characters" in detail
    assert fuxa.key not in json.dumps(result)


def test_random_hex_key_has_enough_distinct_characters():
    assert len(set(STRONG)) >= defense.MIN_DISTINCT_CHARS


def test_unreadable_settings_fail_closed(fuxa, monkeypatch):
    fuxa.key, fuxa.length = STRONG, len(STRONG)
    monkeypatch.setattr(defense, "fuxa_container", lambda: None)
    assert _failed(defense.verify()) == ["Key long and random"]


def test_broken_authentication_does_not_pass_as_rotated(fuxa):
    # FUXA refuses the default key, but also its own tokens.
    fuxa.key, fuxa.length, fuxa.broken_own_tokens = STRONG, len(STRONG), True
    result = defense.verify()
    assert not result["success"]
    assert _failed(result) == ["FUXA tokens still work"]


def test_security_off_does_not_pass(fuxa):
    fuxa.key, fuxa.length, fuxa.secure = STRONG, len(STRONG), False
    result = defense.verify()
    assert not result["success"]
    assert _failed(result) == ["FUXA authentication on"]


def test_fuxa_down_does_not_pass(fuxa):
    fuxa.up = False
    result = defense.verify()
    assert not result["success"]
    assert "reach" in result["message"].lower()


def test_secret_stats_parses_node_output(monkeypatch):
    class Done:
        def __init__(self, out, code=0):
            self.stdout, self.returncode = out, code

    monkeypatch.setattr(jwt.subprocess, "run", lambda *a, **k: Done("48 16"))
    assert jwt.secret_stats("c") == (48, 16)
    monkeypatch.setattr(jwt.subprocess, "run", lambda *a, **k: Done("-1 0"))
    assert jwt.secret_stats("c") == (-1, 0)
    monkeypatch.setattr(jwt.subprocess, "run", lambda *a, **k: Done("", 1))   # SyntaxError
    assert jwt.secret_stats("c") is None
    monkeypatch.setattr(jwt.subprocess, "run", lambda *a, **k: Done("oops"))
    assert jwt.secret_stats("c") is None
    monkeypatch.setattr(jwt.subprocess, "run", lambda *a, **k: Done("48"))
    assert jwt.secret_stats("c") is None
