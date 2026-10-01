"""Settings -> Central CTF server, against the running landing page.

These never enrol the stack with a server: they check that the feature is
reachable, keeps the token to itself and answers bad input with a message
rather than a 500. The enrolment itself is covered by test_central_ctf.py.
"""
import pytest
import requests

from conftest import NGINX_PROXY_PORT, READ_TIMEOUT, SERVER_IP

pytestmark = pytest.mark.usefixtures("stack_ready")

# Through the reverse proxy, like test_connections: the host-networked :80 may
# sit behind a host firewall.
BASE = f"http://{SERVER_IP}:{NGINX_PROXY_PORT}"


def post(path, body):
    return requests.post(BASE + path, json=body, timeout=READ_TIMEOUT + 10)


def test_snapshot_never_contains_the_token():
    response = requests.get(BASE + "/api/settings/central", timeout=READ_TIMEOUT)
    assert response.status_code == 200
    snap = response.json()
    assert snap["platform"] in ("virtual", "physical")
    assert "enabled" in snap and "pending" in snap
    assert "token" not in snap and "baseline" not in snap


def test_settings_page_offers_the_section():
    page = requests.get(BASE + "/", timeout=READ_TIMEOUT).text
    assert 'id="centralSection"' in page
    assert requests.get(BASE + "/static/js/central.js", timeout=READ_TIMEOUT).status_code == 200


@pytest.mark.parametrize("url, code", [
    ("ftp://example.org", "invalid_url"),
    # Nothing listens on the discard port; refused straight away.
    ("http://127.0.0.1:9", "unreachable"),
])
def test_connection_test_reports_problems(url, code):
    response = post("/api/settings/central/test", {"server_url": url})
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False and body["code"] == code
    assert body["message"]


@pytest.mark.parametrize("body", [
    {},
    {"server_url": "http://127.0.0.1:9", "join_code": "X", "team_name": "T"},
    {"server_url": "http://127.0.0.1:9", "join_code": "X", "team_name": "T", "team_password": 12345678},
    {"server_url": ["x"], "join_code": None, "team_name": {}, "team_password": "password1"},
])
def test_enrol_rejects_incomplete_input(body):
    response = post("/api/settings/central/enroll", body)
    assert response.status_code in (400, 409)
    assert response.json()["success"] is False


def test_uplink_only_exists_on_a_board():
    platform = requests.get(BASE + "/api/settings/central", timeout=READ_TIMEOUT).json()["platform"]
    response = post("/api/settings/central/uplink", {"enabled": False})
    if platform == "virtual":
        assert response.status_code == 404
        assert response.json()["code"] == "not_physical"
    else:
        assert response.status_code == 200


def test_the_uplink_interface_cannot_be_captured():
    response = post("/api/network/start", {"interface": "ctfwlan0"})
    assert response.status_code == 403
    names = [i["name"] for i in requests.get(BASE + "/api/network/interfaces", timeout=READ_TIMEOUT).json()]
    assert "ctfwlan0" not in names
