"""The landing page's side of CybICS-mgmt, the optional central server.

modules/cybics_mgmt.py is the CybICS-mgmt reference client, vendored unchanged
and tested in that repository. What is CybICS' own is the glue in
utils/mgmt.py and modules/mgmt_routes.py: the strict progress read the join
baseline depends on, the device description, the heartbeat status, the job
handlers and their banners, the enrolment on the default network cybics-mgmt,
the settings routes and the file exchange with hwio-raspberry. That is tested
here, plus one round trip of the vendored client against a minimal in-process
server, wired the way app.py wires it, with a signed job.

None of this needs a running stack.
"""
import hashlib
import json
import os
import random
import re
import stat
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")
sys.path.insert(0, LANDING)

from modules import cybics_mgmt  # noqa: E402
from modules.cybics_mgmt import MgmtClient, MgmtClientError  # noqa: E402
from utils import mgmt  # noqa: E402
from utils.restart import RestartError  # noqa: E402

VERSION_H = os.path.join(ROOT, "software", "stm32", "src", "version.h")
VENDORED = os.path.join(LANDING, "modules", "cybics_mgmt.py")


# ---------- the vendored client ----------

def _mgmt_client_source():
    """client/cybics_mgmt_client.py of a CybICS-mgmt checkout, if one is around."""
    candidates = [os.environ.get("CYBICS_MGMT_REPO")]
    parent = os.path.dirname(ROOT)
    candidates += [os.path.join(parent, name) for name in ("CybICS-mgmt", "CybICS-CTF")]
    for repo in filter(None, candidates):
        path = os.path.join(repo, "client", "cybics_mgmt_client.py")
        if os.path.isfile(path):
            return path
    return None


def test_vendored_client_is_a_verbatim_copy():
    """Never edit modules/cybics_mgmt.py here; change it in CybICS-mgmt and copy it."""
    source = _mgmt_client_source()
    if source is None:
        pytest.skip("no CybICS-mgmt checkout next to this one; set CYBICS_MGMT_REPO to compare")
    with open(source, "rb") as theirs, open(VENDORED, "rb") as ours:
        assert hashlib.sha256(ours.read()).hexdigest() == hashlib.sha256(theirs.read()).hexdigest(), \
            f"{VENDORED} differs from {source}"


def test_landing_offers_exactly_the_client_actions():
    handlers = mgmt.make_handlers(lambda: "x", mgmt.Banners(), lambda: None, lambda: None,
                                  lambda s: None, lambda: "")
    assert set(handlers) == set(cybics_mgmt.ACTIONS)


# ---------- progress ----------

def test_no_progress_file_means_no_solves(tmp_path):
    assert mgmt.read_progress_strict(str(tmp_path / "missing.json")) == []


def test_progress_is_read(tmp_path):
    path = tmp_path / "ctf_progress.json"
    path.write_text(json.dumps({"solved_challenges": ["scanning", "opcua"], "total_points": 300}))
    assert mgmt.read_progress_strict(str(path)) == ["scanning", "opcua"]


@pytest.mark.parametrize("content", ['{"solved_chall', '[]', '{}'])
def test_unreadable_progress_raises(tmp_path, content):
    """An empty list here would become the join baseline, and every old
    solve on a reused board would be reported as new."""
    path = tmp_path / "ctf_progress.json"
    path.write_text(content)
    with pytest.raises(Exception):
        mgmt.read_progress_strict(str(path))


def test_joining_refuses_unreadable_progress(tmp_path):
    progress = tmp_path / "ctf_progress.json"
    progress.write_text('{"half')
    client = MgmtClient(str(tmp_path / "cybics_mgmt.json"),
                        local_solves=lambda: mgmt.read_progress_strict(str(progress)))
    client.state.update({"enabled": True, "token": "tok", "server_url": "http://127.0.0.1:9"})
    with pytest.raises(MgmtClientError) as error:
        client.join_event("CODE", "Team", "password1")
    assert error.value.code == "progress_unreadable"


# ---------- device description ----------

def test_version_comes_from_the_firmware_header(monkeypatch):
    monkeypatch.delenv("CYBICS_RELEASE", raising=False)
    with open(VERSION_H, encoding="utf-8") as fh:
        header = fh.read()
    expected = ".".join(re.search(rf"FIRMWARE_VERSION_{p}\s+(\d+)", header).group(1)
                        for p in ("MAJOR", "MINOR", "PATCH"))
    assert mgmt.read_version(VERSION_H) == expected


def test_version_without_a_header_is_unknown(tmp_path, monkeypatch):
    monkeypatch.delenv("CYBICS_RELEASE", raising=False)
    assert mgmt.read_version(str(tmp_path / "version.h")) is None


@pytest.mark.parametrize("content, expected", [
    ('{"device_uid": "0042001a3133"}', "0042001a3133"),
    ('{"device_uid": "0042001A3133"}', None),       # the server wants lower case
    ('{"device_uid": "abc"}', None),                # too short
    ('{"device_uid": 42}', None),
    ('[]', None),
    ('{half', None),
])
def test_device_uid(tmp_path, content, expected):
    path = tmp_path / "device.json"
    path.write_text(content)
    assert mgmt.read_device_uid(str(path)) == expected


def test_no_device_file_on_a_virtual_stack(tmp_path):
    assert mgmt.read_device_uid(str(tmp_path / "device.json")) is None


def test_device_info_names_the_board(tmp_path, monkeypatch):
    device = tmp_path / "device.json"
    device.write_text('{"device_uid": "0042001a3133"}')
    monkeypatch.setattr(mgmt, "DEVICE_STATE_FILE", str(device))
    monkeypatch.setattr(mgmt, "CYBICS_PLATFORM", "physical")
    info = mgmt.device_info()
    assert info["kind"] == "physical" and info["device_uid"] == "0042001a3133"
    monkeypatch.setattr(mgmt, "CYBICS_PLATFORM", "virtual")
    info = mgmt.device_info()
    assert info["kind"] == "virtual" and "device_uid" not in info
    assert info["hostname"]


# ---------- heartbeat status ----------

def test_status_is_small_and_names_no_participant_network():
    containers = [{"name": "openplc", "status": "running"}, {"name": "fuxa", "status": "exited"},
                  {"status": "running"}, "garbage"]
    status = mgmt.collect_status(containers, ["scanning"], cpu_percent=12.345, platform="virtual")
    assert status["services"] == {"openplc": True, "fuxa": False}
    assert status["local_solved"] == ["scanning"]
    assert status["host"]["cpu_percent"] == 12.3
    assert "board" not in status
    assert len(json.dumps(status)) < 16 * 1024
    assert not any(key in json.dumps(status) for key in ("172.18.", "10.0.0.", "wlan"))


def test_status_never_raises_and_stays_small(monkeypatch):
    huge = [{"name": f"container-{n}-" + "x" * 500, "status": "running"} for n in range(10000)]
    status = mgmt.collect_status(huge, ["c" * 1000] * 10000, cpu_percent="nan", platform="virtual")
    assert len(json.dumps(status)) <= mgmt.STATUS_MAX
    assert "cpu_percent" not in status.get("host", {})

    def broken(*_args):
        raise RuntimeError("boom")
    monkeypatch.setattr(mgmt, "host_status", broken)
    assert mgmt.collect_status([], []) == {}
    assert mgmt.collect_status(None, None, platform="virtual") == {}


def test_status_of_a_board(tmp_path, monkeypatch):
    device = tmp_path / "device.json"
    device.write_text('{"device_uid": "0042001a3133"}')
    hardware = tmp_path / "hardware.json"
    hardware.write_text('{"revision": "1.2", "description": "v1.2"}')
    (tmp_path / mgmt.UPLINK_STATUS).write_text(json.dumps({
        "present": True, "state": "connected", "ssid": "cybics-mgmt", "ip": "10.42.0.17",
        "interface": "ctfwlan0", "request": 1.0}))
    monkeypatch.setattr(mgmt, "DEVICE_STATE_FILE", str(device))
    monkeypatch.setattr(mgmt, "UPLINK_DIR", str(tmp_path))
    monkeypatch.setenv("CYBICS_HARDWARE_STATE", str(hardware))
    monkeypatch.setattr("utils.hardware.HARDWARE_STATE", str(hardware))
    board = mgmt.collect_status([], [], platform="physical")["board"]
    assert board == {"revision": "1.2", "device_uid": "0042001a3133",
                     "uplink": {"present": True, "state": "connected", "ssid": "cybics-mgmt",
                                "ip": "10.42.0.17"}}


@pytest.mark.parametrize("content, expected", [("48312\n", 48.3), ("-1500\n", -1.5), ("hot", None),
                                               ("999999", None)])
def test_cpu_temperature(tmp_path, content, expected):
    path = tmp_path / "temp"
    path.write_text(content)
    assert mgmt.read_cpu_temp(str(path)) == expected


def test_no_thermal_sensor(tmp_path):
    assert mgmt.read_cpu_temp(str(tmp_path / "missing")) is None


# ---------- banners and job handlers ----------

class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_banners_expire():
    clock = Clock()
    banners = mgmt.Banners(clock)
    banners.show("hello", 10)
    banners.show("x" * 1000, 300, kind="identify")
    active = banners.active()
    assert [b["text"] for b in active] == ["hello", "x" * 500]
    assert active[0]["remaining"] == 10 and active[1]["kind"] == "identify"
    clock.now += 11
    assert [b["text"] for b in banners.active()] == ["x" * 500]
    clock.now += 300
    assert banners.active() == []


class Recorder:
    """Stand-ins for the restart, reset and logs functions app.py injects."""

    def __init__(self, restart_error=None):
        self.calls = []
        self.restart_error = restart_error

    def reset_progress(self):
        self.calls.append("reset")

    def restart_all(self):
        if self.restart_error:
            raise RestartError(self.restart_error)
        self.calls.append("restart all")
        return "virtual", ["virtual-openplc-1", "virtual-fuxa-1"], "virtual-landing-1"

    def restart_service(self, name):
        if self.restart_error:
            raise RestartError(self.restart_error)
        self.calls.append(f"restart {name}")
        return f"restarted {name}"

    def logs(self):
        return "Container: virtual-openplc-1\nall good\n"


def handlers_for(recorder, label="Board 7", clock=None):
    banners = mgmt.Banners(clock or Clock())
    return banners, mgmt.make_handlers(lambda: label, banners, recorder.reset_progress,
                                       recorder.restart_all, recorder.restart_service, recorder.logs)


@pytest.mark.parametrize("seconds, shown", [(30, 30), (1, 5), (100000, 600), ("abc", 60), (None, 60)])
def test_identify_shows_the_label(seconds, shown):
    banners, handlers = handlers_for(Recorder())
    assert handlers["identify"]({"seconds": seconds}) == f"banner shown for {shown} s"
    [banner] = banners.active()
    assert banner["text"] == "This is Board 7" and banner["kind"] == "identify"
    assert banner["remaining"] == shown


def test_identify_falls_back_to_the_hostname():
    class NoLabel:
        def snapshot(self):
            return {"device": None}
    assert mgmt.device_label(NoLabel()) == mgmt.socket.gethostname()

    class Labelled:
        def snapshot(self):
            return {"device": {"label": "cybics-0042001a3133"}}
    assert mgmt.device_label(Labelled()) == "cybics-0042001a3133"


def test_message_is_shown_for_a_few_minutes():
    banners, handlers = handlers_for(Recorder())
    assert handlers["message"]({"text": "  Lunch at noon  "}) == "message shown"
    [banner] = banners.active()
    assert banner["text"] == "Lunch at noon" and banner["remaining"] == mgmt.MESSAGE_SECONDS
    with pytest.raises(MgmtClientError):
        handlers["message"]({"text": "   "})
    with pytest.raises(MgmtClientError):
        handlers["message"]({})


def test_restart_all_and_one_service():
    recorder = Recorder()
    _, handlers = handlers_for(recorder)
    assert handlers["restart"]({"service": "all"}) == "restarting 3 containers of virtual"
    assert handlers["restart"]({"service": "openplc"}) == "restarted openplc"
    assert handlers["restart"]({}) == "restarting 3 containers of virtual"
    assert recorder.calls == ["restart all", "restart openplc", "restart all"]


def test_a_refused_restart_fails_the_job_with_its_reason():
    _, handlers = handlers_for(Recorder(restart_error="'sshd' is not a running container of virtual"))
    with pytest.raises(MgmtClientError) as error:
        handlers["restart"]({"service": "sshd"})
    assert error.value.message == "'sshd' is not a running container of virtual"


def test_reset_progress_and_collect_logs():
    recorder = Recorder()
    _, handlers = handlers_for(recorder)
    assert handlers["reset_progress"]({}) == "local CTF progress reset"
    assert recorder.calls == ["reset"]
    logs = handlers["collect_logs"]({})
    assert isinstance(logs, str) and "virtual-openplc-1" in logs


def test_reset_progress_clears_the_progress_file(tmp_path, monkeypatch):
    """The handler app.py registers is CTFManager.reset_progress, the same as /ctf/reset."""
    pytest.importorskip("markdown")
    from modules import ctf_manager
    progress = tmp_path / "ctf_progress.json"
    progress.write_text(json.dumps({"solved_challenges": ["scanning"], "total_points": 100}))
    monkeypatch.setattr(ctf_manager, "PROGRESS_FILE", str(progress))
    manager = ctf_manager.CTFManager()
    handlers = mgmt.make_handlers(lambda: "x", mgmt.Banners(), manager.reset_progress,
                                  None, None, None)
    handlers["reset_progress"]({})
    assert mgmt.read_progress_strict(str(progress)) == []


# ---------- enrolment on the default network ----------

class FakeClient:
    """What AutoEnrol and the settings routes use of MgmtClient."""

    def __init__(self, enabled=False, revoked=False, fail=None):
        self.state = {"enabled": enabled, "revoked": revoked, "server_url": None,
                      "device": None, "allowed": []}
        self.fail = fail
        self.calls = []

    def _maybe_fail(self):
        if self.fail:
            raise MgmtClientError(self.fail[0], self.fail[1], 403, True)

    def snapshot(self):
        return dict(self.state, history=[], available=sorted(cybics_mgmt.ACTIONS),
                    key_fingerprint="ab" * 32, ctf={"joined": False, "pending": 0})

    def test_connection(self, url):
        self.calls.append(("test", url))
        self._maybe_fail()
        return {"service": "cybics-mgmt", "name": "Workshop", "version": "0.1.0"}

    def enroll(self, url, code, label=None):
        self.calls.append(("enroll", url, code, label))
        self._maybe_fail()
        self.state.update({"enabled": True, "server_url": url, "device": {"label": label}})
        return {"device": {"label": label}}

    def join_event(self, join_code, team_name, team_password):
        self.calls.append(("join", join_code, team_name, team_password))
        self._maybe_fail()
        return {"event": {"slug": "ws"}, "team": {"name": team_name}}

    def leave_event(self):
        self.calls.append(("leave_event",))

    def set_allowed(self, actions):
        self.calls.append(("allowed", list(actions)))
        self.state["allowed"] = sorted(a for a in actions if a in cybics_mgmt.ACTIONS)
        return self.state["allowed"]

    def leave(self):
        self.calls.append(("leave",))
        self.state.update({"enabled": False})


class Uplink:
    def __init__(self, state="connected", ssid="cybics-mgmt", ip="10.42.0.17"):
        self.status = {"present": True, "state": state, "ssid": ssid, "ip": ip}

    def __call__(self):
        return {"available": True, "pending": False, "status": self.status}


def auto(client, tmp_path, uplink=None, platform="physical", uid="0042001a3133"):
    return mgmt.AutoEnrol(client, platform=platform, uplink=uplink or Uplink(),
                          device_uid=lambda: uid, optout_path=str(tmp_path / "optout"))


def test_a_board_on_the_default_network_enrols_itself(tmp_path):
    client = FakeClient()
    assert auto(client, tmp_path).check() == "enrolled_now"
    assert client.calls == [("enroll", "http://10.42.0.1", "CYBICS-BOARDS", "cybics-0042001a3133")]
    # Only once: an enrolled board is left alone.
    assert auto(client, tmp_path).check() == "enrolled"
    assert len(client.calls) == 1


def test_defaults_come_from_the_config():
    from utils import config
    assert (config.MGMT_DEFAULT_SSID, config.MGMT_DEFAULT_URL, config.MGMT_DEFAULT_CODE) == \
        ("cybics-mgmt", "http://10.42.0.1", "CYBICS-BOARDS")


@pytest.mark.parametrize("uplink", [
    Uplink(ssid="cybics-mgmt-guest"),
    Uplink(ssid="EventWifi"),
    Uplink(ssid="CYBICS-MGMT"),
    Uplink(state="disconnected"),
    Uplink(state="connecting (getting IP configuration)"),
    Uplink(ip=None),
])
def test_only_on_the_default_network(tmp_path, uplink):
    client = FakeClient()
    assert auto(client, tmp_path, uplink=uplink).check() == "not_on_default_network"
    assert client.calls == []


def test_without_an_uplink_status_nothing_happens(tmp_path):
    client = FakeClient()
    enrol = mgmt.AutoEnrol(client, platform="physical", uplink=lambda: {"status": None},
                           device_uid=lambda: "0042001a3133", optout_path=str(tmp_path / "o"))
    assert enrol.check() == "not_on_default_network"
    broken = mgmt.AutoEnrol(client, platform="physical", uplink=lambda: 1 / 0,
                            optout_path=str(tmp_path / "o"))
    assert broken.check() == "error"
    assert client.calls == []


def test_a_virtual_instance_never_enrols_itself(tmp_path):
    client = FakeClient()
    assert auto(client, tmp_path, platform="virtual").check() == "virtual"
    assert client.calls == []


def test_the_opt_out_is_respected(tmp_path):
    client = FakeClient()
    mgmt.set_opted_out(True, str(tmp_path / "optout"))
    assert mgmt.opted_out(str(tmp_path / "optout"))
    assert auto(client, tmp_path).check() == "opted_out"
    mgmt.set_opted_out(False, str(tmp_path / "optout"))
    assert not mgmt.opted_out(str(tmp_path / "optout"))
    assert auto(client, tmp_path).check() == "enrolled_now"


def test_a_retired_board_does_not_come_back_by_itself(tmp_path):
    client = FakeClient(revoked=True)
    assert auto(client, tmp_path).check() == "revoked"
    assert client.calls == []


def test_without_a_board_id_it_waits(tmp_path):
    client = FakeClient()
    assert auto(client, tmp_path, uid=None).check() == "no_device_uid"
    assert client.calls == []


@pytest.mark.parametrize("code", ["code_disabled", "invalid_code", "unreachable"])
def test_no_retry_after_a_refusal_until_the_uplink_reconnects(tmp_path, code):
    client = FakeClient(fail=(code, "The enrolment code is disabled."))
    uplink = Uplink()
    enrol = auto(client, tmp_path, uplink=uplink)
    assert enrol.check() == "refused"
    for _ in range(5):
        assert enrol.check() == "refused_before"
    assert len(client.calls) == 1

    # A new address is a new connection.
    uplink.status["ip"] = "10.42.0.99"
    assert enrol.check() == "refused"
    assert len(client.calls) == 2

    # Dropping off the network and coming back is one too.
    uplink.status["state"] = "disconnected"
    assert enrol.check() == "not_on_default_network"
    uplink.status["state"] = "connected"
    client.fail = None
    assert enrol.check() == "enrolled_now"
    assert len(client.calls) == 3


def test_a_restart_of_landing_tries_again(tmp_path):
    client = FakeClient(fail=("code_disabled", "Disabled."))
    assert auto(client, tmp_path).check() == "refused"
    client.fail = None
    assert auto(client, tmp_path).check() == "enrolled_now"


def test_run_stops(tmp_path):
    client = FakeClient()
    enrol = auto(client, tmp_path, uplink=Uplink(ssid="other"))
    thread = threading.Thread(target=enrol.run, kwargs={"interval": 0.01}, daemon=True)
    thread.start()
    enrol.stop()
    thread.join(2)
    assert not thread.is_alive()


# ---------- settings routes ----------

@pytest.fixture
def routes(tmp_path, monkeypatch):
    flask = pytest.importorskip("flask")
    from modules import mgmt_routes
    monkeypatch.setattr(mgmt, "MGMT_OPTOUT_FILE", str(tmp_path / "optout"))
    monkeypatch.setattr(mgmt, "UPLINK_DIR", str(tmp_path / "uplink"))
    monkeypatch.setattr(mgmt_routes, "CYBICS_PLATFORM", "virtual")
    monkeypatch.setattr(mgmt_routes, "device_info", lambda: {"kind": "virtual", "hostname": "h"})
    app = flask.Flask(__name__)
    client = FakeClient()
    banners = mgmt.Banners()
    mgmt_routes.register_mgmt_routes(app, client, banners)
    return app.test_client(), client, banners, mgmt_routes, tmp_path


def test_snapshot_route(routes):
    http, _, _, _, _ = routes
    snap = http.get("/api/settings/mgmt").get_json()
    assert snap["platform"] == "virtual" and snap["enabled"] is False
    assert snap["opted_out"] is False and "uplink" not in snap
    assert "token" not in snap


def test_test_route_shows_the_server_message_unchanged(routes):
    http, client, _, _, _ = routes
    assert http.post("/api/settings/mgmt/test", json={"server_url": "http://x"}).get_json()["success"]
    client.fail = ("not_a_mgmt_server", "That address is not a CybICS-mgmt server.")
    response = http.post("/api/settings/mgmt/test", json={"server_url": "http://x"})
    assert response.status_code == 400
    assert response.get_json() == {"success": False, "code": "not_a_mgmt_server",
                                   "message": "That address is not a CybICS-mgmt server."}


def test_connect_and_disconnect_toggle_the_opt_out(routes):
    http, client, _, _, tmp_path = routes
    mgmt.set_opted_out(True, str(tmp_path / "optout"))
    response = http.post("/api/settings/mgmt/connect",
                         json={"server_url": " http://10.42.0.1 ", "code": "ABC", "label": "Table 4"})
    assert response.status_code == 200 and response.get_json()["snapshot"]["enabled"]
    assert client.calls[-1] == ("enroll", "http://10.42.0.1", "ABC", "Table 4")
    assert not mgmt.opted_out(str(tmp_path / "optout"))

    response = http.post("/api/settings/mgmt/disconnect")
    assert response.status_code == 200 and not response.get_json()["snapshot"]["enabled"]
    assert client.calls[-1] == ("leave",)
    assert mgmt.opted_out(str(tmp_path / "optout"))
    assert http.get("/api/settings/mgmt").get_json()["opted_out"] is True


def test_a_refused_connect_keeps_the_opt_out(routes):
    http, client, _, _, tmp_path = routes
    mgmt.set_opted_out(True, str(tmp_path / "optout"))
    client.fail = ("invalid_code", "Unknown code.")
    response = http.post("/api/settings/mgmt/connect", json={"server_url": "http://x", "code": "NOPE"})
    assert response.status_code == 400 and response.get_json()["message"] == "Unknown code."
    assert mgmt.opted_out(str(tmp_path / "optout"))


@pytest.mark.parametrize("body", [{}, {"server_url": "http://x"}, {"code": "X"},
                                  {"server_url": ["x"], "code": {}}])
def test_connect_needs_address_and_code(routes, body):
    http, client, _, _, _ = routes
    response = http.post("/api/settings/mgmt/connect", json=body)
    assert response.status_code == 400 and response.get_json()["code"] == "invalid_input"
    assert client.calls == []


def test_a_board_without_an_id_cannot_connect(routes, monkeypatch):
    http, client, _, mgmt_routes, _ = routes
    monkeypatch.setattr(mgmt_routes, "device_info", lambda: {"kind": "physical"})
    response = http.post("/api/settings/mgmt/connect", json={"server_url": "http://x", "code": "X"})
    assert response.status_code == 409 and response.get_json()["code"] == "no_device_uid"
    assert client.calls == []


def test_join_and_leave_event(routes):
    http, client, _, _, _ = routes
    response = http.post("/api/settings/mgmt/join",
                         json={"join_code": "EV", "team_name": " Red ", "team_password": " pass word "})
    assert response.status_code == 200
    assert client.calls[-1] == ("join", "EV", "Red", " pass word ")
    assert http.post("/api/settings/mgmt/leave-event").status_code == 200
    assert client.calls[-1] == ("leave_event",)


@pytest.mark.parametrize("body", [
    {}, {"join_code": "X", "team_name": "T"},
    {"join_code": "X", "team_name": "T", "team_password": 12345678},
])
def test_join_rejects_incomplete_input(routes, body):
    http, client, _, _, _ = routes
    assert http.post("/api/settings/mgmt/join", json=body).status_code == 400
    assert client.calls == []


def test_allowed_actions(routes):
    http, client, _, _, _ = routes
    response = http.post("/api/settings/mgmt/allowed", json={"actions": ["identify", "shell"]})
    assert response.get_json()["allowed"] == ["identify"]
    assert http.post("/api/settings/mgmt/allowed", json={"actions": []}).get_json()["allowed"] == []
    for bad in ({}, {"actions": "identify"}, {"actions": [1]}):
        assert http.post("/api/settings/mgmt/allowed", json=bad).status_code == 400


def test_uplink_only_on_a_board(routes, monkeypatch):
    http, _, _, mgmt_routes, tmp_path = routes
    response = http.post("/api/settings/mgmt/uplink", json={"enabled": False})
    assert response.status_code == 404 and response.get_json()["code"] == "not_physical"

    monkeypatch.setattr(mgmt_routes, "CYBICS_PLATFORM", "physical")
    (tmp_path / "uplink").mkdir()
    response = http.post("/api/settings/mgmt/uplink",
                         json={"enabled": True, "ssid": "cybics-mgmt", "psk": "cybics-mgmt"})
    assert response.status_code == 200 and response.get_json()["uplink"]["pending"] is True
    snap = http.get("/api/settings/mgmt").get_json()
    assert snap["uplink"]["default_ssid"] == "cybics-mgmt"
    response = http.post("/api/settings/mgmt/uplink", json={"enabled": True, "ssid": "x", "psk": "short"})
    assert response.status_code == 400


def test_banner_route(routes):
    http, _, banners, _, _ = routes
    assert http.get("/api/mgmt/banners").get_json() == {"banners": []}
    banners.show("This is Board 7", 30, kind="identify")
    [banner] = http.get("/api/mgmt/banners").get_json()["banners"]
    assert banner["text"] == "This is Board 7" and banner["kind"] == "identify"


# ---------- uplink hand-over to hwio-raspberry ----------

@pytest.mark.parametrize("ssid, psk, ok", [
    ("cybics-mgmt", "cybics-mgmt", True),
    ("", "12345678", False),
    ("x" * 33, "12345678", False),
    ("cybics-mgmt", "1234567", False),
    ("cybics-mgmt", "p" * 64, False),
    ("cybics-mgmt", "pässwörter", False),
])
def test_uplink_validation(ssid, psk, ok):
    assert (mgmt.validate_uplink(ssid, psk) is None) is ok


def test_uplink_request_is_private(tmp_path):
    mgmt.request_uplink(True, "event-wifi", "secret-pass", directory=str(tmp_path))
    path = tmp_path / mgmt.UPLINK_REQUEST
    assert json.loads(path.read_text())["psk"] == "secret-pass"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert mgmt.uplink_status(str(tmp_path))["pending"] is True


def test_disabling_the_uplink_carries_no_credentials(tmp_path):
    mgmt.request_uplink(False, "event-wifi", "secret-pass", directory=str(tmp_path))
    assert "secret-pass" not in (tmp_path / mgmt.UPLINK_REQUEST).read_text()


def test_uplink_needs_the_shared_volume(tmp_path):
    with pytest.raises(OSError):
        mgmt.request_uplink(True, "event-wifi", "secret-pass", directory=str(tmp_path / "missing"))
    assert mgmt.uplink_status(str(tmp_path / "missing"))["available"] is False


# ---------- round trip with the vendored client ----------

def _probable_prime(n, rng):
    for p in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97):
        if n % p == 0:
            return False
    d, r = n - 1, 0
    while d % 2 == 0:
        d, r = d // 2, r + 1
    for _ in range(16):
        x = pow(rng.randrange(2, n - 2), d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _prime(bits, rng):
    while True:
        candidate = rng.getrandbits(bits) | (3 << (bits - 2)) | 1
        if _probable_prime(candidate, rng):
            return candidate


@pytest.fixture(scope="module")
def signing_key():
    """An RSA-3072 key, like the server's (test-only, generated per run)."""
    rng = random.Random(3072)
    e = 65537
    while True:
        p, q = _prime(1536, rng), _prime(1536, rng)
        phi = (p - 1) * (q - 1)
        if p != q and phi % e and (p * q).bit_length() == 3072:
            return p * q, e, pow(e, -1, phi)


def _sign(key, job):
    n, _, d = key
    size = (n.bit_length() + 7) // 8
    digest_info = cybics_mgmt._SHA256_DIGEST_INFO + hashlib.sha256(cybics_mgmt.job_message(job)).digest()
    block = b"\x00\x01" + b"\xff" * (size - len(digest_info) - 3) + b"\x00" + digest_info
    return format(pow(int.from_bytes(block, "big"), d, n), "x").zfill(2 * size)


class FakeServer(BaseHTTPRequestHandler):
    """The calls the client makes, answered the way CybICS-mgmt does."""
    received = []
    jobs = []
    solved = []
    key = None

    def log_message(self, *args):
        pass

    def _reply(self, code, body=None):
        raw = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/v1/info":
            self._reply(200, {"service": "cybics-mgmt", "name": "Test", "version": "0", "api_version": 1})
        else:
            self._reply(404, {"error": {"code": "not_found", "message": "nope"}})

    def do_DELETE(self):
        FakeServer.received.append((self.path, None, self.headers.get("Authorization")))
        self._reply(204)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeServer.received.append((self.path, body, self.headers.get("Authorization")))
        event = {"name": "Workshop", "slug": "ws", "state": "running", "created_at": 1.0}
        team = {"id": 1, "name": "Team"}
        if self.path == "/api/v1/enroll":
            n, e, _ = FakeServer.key
            self._reply(201, {"device_id": "dev-1", "token": "tok",
                              "device": {"id": "dev-1", "label": body["label"], "group": None},
                              "signing_key": {"n": format(n, "x"), "e": e}, "heartbeat_interval": 30})
        elif self.path == "/api/v1/ctf/join":
            self._reply(201, {"instance_id": "i-1", "event": event, "team": team})
        elif self.path == "/api/v1/heartbeat":
            self._reply(200, {"device": {"id": "dev-1", "label": "Board 7", "group": "Room 2"},
                              "jobs": FakeServer.jobs, "heartbeat_interval": 30,
                              "ctf": {"instance_id": "i-1", "event": event,
                                      "team": dict(team, score=0, rank=1, teams=1),
                                      "solved": list(FakeServer.solved), "catalog_version": "v1",
                                      "announcements": [],
                                      "announcement_ids": []}})
        elif self.path == "/api/v1/solves":
            FakeServer.solved.append(body["challenge_id"])
            self._reply(200, {"result": "accepted"})


@pytest.fixture
def server(signing_key):
    FakeServer.received, FakeServer.jobs, FakeServer.solved, FakeServer.key = [], [], [], signing_key
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), FakeServer)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_round_trip(tmp_path, server, signing_key):
    """Old progress stays local, new solves are reported with their flag, a
    signed job runs only once allowed, and the token never reaches the page."""
    progress = tmp_path / "ctf_progress.json"
    progress.write_text(json.dumps({"solved_challenges": ["physical_process"], "total_points": 100}))
    flags = {"physical_process": "CybICS(Bl0w0ut)", "scanning": "CybICS(scanning_d0ne)"}
    banners = mgmt.Banners()
    recorder = Recorder()
    holder = {}
    client = MgmtClient(str(tmp_path / "cybics_mgmt.json"),
                        device_info=lambda: {"kind": "virtual", "hostname": "test"},
                        local_solves=lambda: mgmt.read_progress_strict(str(progress)),
                        flag_for=flags.get,
                        status=lambda: mgmt.collect_status([], mgmt.read_progress_strict(str(progress)),
                                                           platform="virtual"),
                        handlers=mgmt.make_handlers(lambda: mgmt.device_label(holder["client"]), banners,
                                                    recorder.reset_progress, recorder.restart_all,
                                                    recorder.restart_service, recorder.logs))
    holder["client"] = client

    # Not connected: report_solve is a no-op and nothing is sent.
    client.report_solve("scanning", flags["scanning"])
    assert FakeServer.received == [] and client.snapshot()["ctf"]["pending"] == 0

    assert client.test_connection(server)["service"] == "cybics-mgmt"
    client.enroll(server, "CYBICS-BOARDS", label="cybics-0042001a3133")
    assert FakeServer.received[0][1]["label"] == "cybics-0042001a3133"
    snap = client.snapshot()
    assert "token" not in snap and "signing_key" not in snap
    assert snap["allowed"] == [] and snap["available"] == sorted(cybics_mgmt.ACTIONS)
    assert snap["key_fingerprint"] == cybics_mgmt.key_fingerprint(signing_key[0], signing_key[1])

    client.join_event("EV", "Team", "password1")
    progress.write_text(json.dumps({"solved_challenges": ["physical_process", "scanning"],
                                    "total_points": 200}))
    client.report_solve("scanning", flags["scanning"])
    assert client.sync_once() is True
    solves = [body for path, body, _ in FakeServer.received if path == "/api/v1/solves"]
    assert [s["challenge_id"] for s in solves] == ["scanning"]
    assert solves[0]["flag"] == "CybICS(scanning_d0ne)"
    heartbeat = next(body for path, body, _ in FakeServer.received if path == "/api/v1/heartbeat")
    assert heartbeat["status"]["host"] is not None and "local_solved" in heartbeat["status"]

    # A signed identify job: refused while not allowed, run once allowed.
    def job(seq):
        body = {"id": f"job-{seq}", "device": "dev-1", "seq": seq, "action": "identify",
                "params": {"seconds": 30}}
        return dict(body, signature=_sign(signing_key, body))
    FakeServer.jobs = [job(1)]
    assert client.sync_once() is True
    assert client.snapshot()["history"][-1]["state"] == "refused"
    assert banners.active() == []

    client.set_allowed(["identify"])
    FakeServer.jobs = [job(2)]
    assert client.sync_once() is True
    assert client.run_next_job() is True
    assert client.snapshot()["history"][-1]["state"] == "done"
    assert [b["text"] for b in banners.active()] == ["This is Board 7"]

    # A forged job is dropped and reported as such.
    forged = job(3)
    forged["params"] = {"seconds": 600}
    FakeServer.jobs = [forged]
    client.sync_once()
    assert client.snapshot()["last_error"]["code"] == "bad_signature"
    assert client.run_next_job() is False

    assert all(auth == "Bearer tok" for path, _, auth in FakeServer.received
               if path not in ("/api/v1/enroll",))
    state = tmp_path / "cybics_mgmt.json"
    assert stat.S_IMODE(state.stat().st_mode) == 0o600

    client.leave()
    assert FakeServer.received[-1][0] == "/api/v1/device"
    assert client.snapshot()["enabled"] is False
