"""The settings view (/settings) against the running landing page.

Settings used to be a modal inside the dashboard; it is now a view of its
own, loaded in the dashboard's iframe like /stats and /ctf. These check the
view is wired in, leaves board-only parts out on a virtual stack, and that
its maintenance actions stay inside the CybICS compose project. Nothing here
restarts anything: the restart is only planned, never started.
"""
import re
import shutil
import subprocess

import pytest
import requests

from conftest import NGINX_PROXY_PORT, READ_TIMEOUT, SERVER_IP

pytestmark = pytest.mark.usefixtures("stack_ready")

# Through the reverse proxy, like test_landing_mgmt.
BASE = f"http://{SERVER_IP}:{NGINX_PROXY_PORT}"


def get(path, **kwargs):
    kwargs.setdefault("timeout", READ_TIMEOUT)
    return requests.get(BASE + path, **kwargs)


def test_settings_view_has_its_sections_and_assets():
    response = get("/settings")
    assert response.status_code == 200
    for section in ("mgmt", "assistant", "system"):
        assert f'<section class="section" id="section-{section}"' in response.text
    for asset in ("/static/js/settings.js", "/static/js/mgmt.js", "/static/css/settings.css"):
        assert asset in response.text
        assert get(asset).status_code == 200


def test_dashboard_opens_settings_as_a_view():
    page = get("/").text
    assert 'id="settings-iframe"' in page and 'data-src="/settings"' in page
    assert "updateView('settings')" in page
    # The old modal and its handlers are gone, not just hidden.
    assert 'id="settingsModal"' not in page and "openSettings(" not in page


def render(path):
    """The DOM of a page after its scripts ran, from headless Chrome.

    The checks above only see the HTML the server sends. A script that throws
    on load leaves that HTML intact and the view stuck on its spinners, so
    the sections are checked once more after the browser ran them.
    """
    browser = next(filter(None, map(shutil.which, (
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"))), None)
    if browser is None:
        pytest.skip("no Chrome or Chromium on this host to run the view's scripts")
    result = subprocess.run(
        [browser, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=10000", "--dump-dom", BASE + path],
        capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr[-2000:]
    return result.stdout


def test_settings_scripts_fill_the_sections():
    # mgmt.js fills the CybICS-mgmt section, settings.js the system section.
    section = render("/settings#mgmt")
    assert re.search(r'<p [^>]*id="mgmtLoading"[^>]*hidden', section), "CybICS-mgmt section stuck loading"
    system = render("/settings#system")
    assert 'id="systemFacts" aria-busy="false"' in system, "system section stuck loading"
    assert "<dt>Platform</dt>" in system


def test_board_only_parts_follow_the_platform():
    platform = get("/api/settings/mgmt").json()["platform"]
    page = get("/settings").text
    assert ('id="uplinkCard"' in page) == (platform == "physical")


def test_restart_plan_covers_only_the_own_project_with_landing_last():
    status = get("/api/settings/containers/restart", params={"plan": 1}).json()
    assert "error" not in status, status.get("error")
    assert len(status["boot_id"]) == 32 and status["running"] is False
    project, containers = status["project"], status["containers"]
    assert containers and "landing" in containers[-1]
    # Compose names containers <project>-<service>-<n>.
    assert all(name.startswith(project + "-") for name in containers), containers


def test_log_download_holds_only_the_own_project():
    plan = get("/api/settings/containers/restart", params={"plan": 1}).json()
    response = get("/api/settings/logs/download", timeout=120)
    assert response.status_code == 200
    listed = re.findall(r"^Container: (.+)$", response.text, re.M)
    assert sorted(listed) == sorted(plan["containers"])
