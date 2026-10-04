"""Settings -> CybICS-mgmt, against the running landing page.

These never connect the stack to a server: they check that the feature is
reachable, keeps the token to itself and answers bad input with a message
rather than a 500. Connecting, joining and jobs are covered by
test_cybics_mgmt.py.
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
    response = requests.get(BASE + "/api/settings/mgmt", timeout=READ_TIMEOUT)
    assert response.status_code == 200
    snap = response.json()
    assert snap["platform"] in ("virtual", "physical")
    assert "enabled" in snap and "pending" in snap["ctf"]
    assert sorted(snap["available"]) == ["collect_logs", "identify", "message", "reset_progress", "restart"]
    assert "token" not in snap and "signing_key" not in snap and "baseline" not in snap["ctf"]


def test_banners_are_served():
    response = requests.get(BASE + "/api/mgmt/banners", timeout=READ_TIMEOUT)
    assert response.status_code == 200
    assert isinstance(response.json()["banners"], list)


def test_settings_page_offers_the_section():
    page = requests.get(BASE + "/settings", timeout=READ_TIMEOUT).text
    assert 'id="section-mgmt"' in page and 'id="connectForm"' in page and 'id="joinForm"' in page
    assert requests.get(BASE + "/static/js/mgmt.js", timeout=READ_TIMEOUT).status_code == 200


@pytest.mark.parametrize("url, code", [
    ("ftp://example.org", "invalid_url"),
    # Nothing listens on the discard port; refused straight away.
    ("http://127.0.0.1:9", "unreachable"),
])
def test_connection_test_reports_problems(url, code):
    response = post("/api/settings/mgmt/test", {"server_url": url})
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False and body["code"] == code
    assert body["message"]


@pytest.mark.parametrize("body", [
    {},
    {"server_url": "http://127.0.0.1:9"},
    {"server_url": ["x"], "code": None, "label": {}},
])
def test_connect_rejects_incomplete_input(body):
    response = post("/api/settings/mgmt/connect", body)
    assert response.status_code in (400, 409)
    assert response.json()["success"] is False


def test_join_needs_a_team():
    response = post("/api/settings/mgmt/join", {"join_code": "X", "team_name": "T"})
    assert response.status_code == 400
    assert response.json()["success"] is False


def test_uplink_only_exists_on_a_board():
    platform = requests.get(BASE + "/api/settings/mgmt", timeout=READ_TIMEOUT).json()["platform"]
    response = post("/api/settings/mgmt/uplink", {"enabled": False})
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
