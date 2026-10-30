"""Restarting one container from the stats page (/stats).

The buttons call POST /api/stats/containers/<service>/restart, which hands
the name to restart_service() in software/landing/utils/restart.py. These
check that the page offers it, that nothing outside the CybICS compose
project can be restarted through it, and that a real restart of the IDS
neither breaks it nor hands out the IDS Evasion flag: the evasion window
lives in the IDS process, so a restart must end an attempt, not pass it.
"""
import time

import pytest
import requests

from conftest import NGINX_PROXY_PORT, READ_TIMEOUT, SERVER_IP

pytestmark = pytest.mark.usefixtures("stack_ready")

BASE = f"http://{SERVER_IP}:{NGINX_PROXY_PORT}"
IDS = f"http://{SERVER_IP}:8443"


def restart(service, **kwargs):
    kwargs.setdefault("timeout", 120)
    return requests.post(f"{BASE}/api/stats/containers/{service}/restart", **kwargs)


def test_stats_page_offers_a_restart_per_container():
    page = requests.get(f"{BASE}/stats", timeout=READ_TIMEOUT).text
    assert "/api/stats/containers/" in page
    assert "data-restart" in page


@pytest.mark.parametrize("service", ["sshd", "virtual-nope-1", "landing-1 && id", "registry"])
def test_only_containers_of_the_own_project_restart(service):
    response = restart(service)
    assert response.status_code == 404, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "That is not a running container of this CybICS installation."


def test_a_restart_needs_a_post():
    response = requests.get(f"{BASE}/api/stats/containers/ids/restart", timeout=READ_TIMEOUT)
    assert response.status_code == 405


def _ids_running(timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if requests.get(f"{IDS}/api/status", timeout=3).json().get("active"):
                return True
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1)
    return False


def test_restarting_the_ids_ends_an_evasion_attempt():
    assert _ids_running(), "the IDS is not running before the test"
    started = requests.post(f"{IDS}/api/evasion/start", timeout=READ_TIMEOUT).json()
    assert started["success"], started

    response = restart("ids")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True and body["self"] is False
    assert body["message"].startswith("restarted ") and "ids" in body["message"]

    assert _ids_running(), "the IDS did not come back after the restart"
    check = requests.get(f"{IDS}/api/evasion/check", timeout=READ_TIMEOUT).json()
    assert check["active"] is False and not check.get("success"), check
    assert "flag" not in check
