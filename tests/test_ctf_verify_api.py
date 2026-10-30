"""POST /ctf/verify/<id> on the running landing page: the answer contract.

test_ctf_answers.py covers the grading without a stack. This checks the
deployed route: it bounds and validates a request body before any verify
module runs, refuses answers where a challenge takes none, never returns a
flag on a refusal, and still renders the plain Verify button for the existing
challenges. Every request here is refused before grading, so no challenge is
solved and the board's progress is compared before and after.
"""
import json
import os
import sys

import pytest
import requests

from conftest import NGINX_PROXY_PORT, READ_TIMEOUT, SERVER_IP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))
from modules.ctf_manager import ANSWER_BODY_LIMIT as BODY_LIMIT  # noqa: E402

pytestmark = pytest.mark.usefixtures("stack_ready")

BASE = f"http://{SERVER_IP}:{NGINX_PROXY_PORT}"
with open(os.path.join(ROOT, "software", "landing", "ctf_config.json"), encoding="utf-8") as f:
    CHALLENGES = [c for cat in json.load(f)["categories"].values() for c in cat["challenges"]]

PLAIN_VERIFY = [c for c in CHALLENGES if c.get("type") in ("verify", "defense") and not c.get("answers")]
GRADED = [c for c in CHALLENGES if c.get("answers")]


def verify(challenge_id, data=None, **kwargs):
    headers = {"Content-Type": "application/json"}
    return requests.post(f"{BASE}/ctf/verify/{challenge_id}", data=data, headers=headers,
                         timeout=READ_TIMEOUT, **kwargs)


@pytest.fixture
def progress_unchanged():
    def read():
        r = requests.get(f"{BASE}/ctf/progress", timeout=READ_TIMEOUT)
        assert r.status_code == 200
        return sorted(r.json()["solved_challenge_ids"]), r.json()["total_points"]
    before = read()
    yield
    assert read() == before, "a refused verify request changed the CTF progress"


def assert_refused(resp, status):
    assert resp.status_code == status, resp.text[:200]
    data = resp.json()
    assert data["success"] is False
    assert "flag" not in data and "CybICS(" not in resp.text


def test_an_unknown_challenge_is_404(progress_unchanged):
    assert_refused(verify("no_such_challenge"), 404)


@pytest.mark.parametrize("challenge", PLAIN_VERIFY[:1], ids=lambda c: c["id"])
def test_answers_to_a_challenge_without_fields_are_refused(challenge, progress_unchanged):
    assert_refused(verify(challenge["id"], json.dumps({"answers": {"x": "1"}})), 400)


@pytest.mark.parametrize("challenge", PLAIN_VERIFY[:1], ids=lambda c: c["id"])
def test_a_body_that_is_not_a_json_object_is_refused(challenge, progress_unchanged):
    assert_refused(verify(challenge["id"], "not json"), 400)
    assert_refused(verify(challenge["id"], "[1]"), 400)


@pytest.mark.parametrize("challenge", PLAIN_VERIFY[:1], ids=lambda c: c["id"])
def test_an_oversized_body_is_refused(challenge, progress_unchanged):
    big = json.dumps({"answers": {"x": "a" * (BODY_LIMIT + 1)}})
    assert_refused(verify(challenge["id"], big), 413)


@pytest.mark.parametrize("challenge", GRADED, ids=lambda c: c["id"])
def test_a_graded_challenge_refuses_missing_and_unknown_fields(challenge, progress_unchanged):
    assert_refused(verify(challenge["id"], json.dumps({})), 400)
    names = {f["name"]: "x" for f in challenge["answers"]}
    assert_refused(verify(challenge["id"], json.dumps({"answers": {**names, "zz_unknown": "1"}})), 400)


@pytest.mark.parametrize("challenge", PLAIN_VERIFY, ids=lambda c: c["id"])
def test_existing_challenges_keep_the_plain_verify_button(challenge):
    page = requests.get(f"{BASE}/ctf/challenge/{challenge['id']}", timeout=READ_TIMEOUT)
    assert page.status_code == 200
    if 'id="verify-button"' in page.text:  # absent once the challenge is solved
        assert "data-answer-name=" not in page.text


@pytest.mark.parametrize("challenge", GRADED, ids=lambda c: c["id"])
def test_graded_challenges_render_their_fields(challenge):
    page = requests.get(f"{BASE}/ctf/challenge/{challenge['id']}", timeout=READ_TIMEOUT)
    assert page.status_code == 200
    assert challenge["flag"] not in page.text
    if 'id="verify-button"' in page.text:
        for field in challenge["answers"]:
            assert f'data-answer-name="{field["name"]}"' in page.text
