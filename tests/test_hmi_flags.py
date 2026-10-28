"""No challenge flag in the FUXA project, and the two checks that replaced it.

FUXA answers GET /api/project without a login, because the HMI page needs the
project to draw its views, and FUXA 1.2.6 sends hidden and admin-only items
along (it only marks them hidden). Two flags used to be SVG text in that
project: Password Attack's on the admin-only Flag view and Physical Process's
on three views, shown while the blow-out sensor was 1. One grep of the
anonymous download gave both away. The texts now say "Admin login works" and
"BLOW-OUT"; the flags come from verify modules:

* check_fuxa_login grades the FUXA administrator login the student recovered;
* check_physical_process reads the HPT pressure and blow-out sensor and passes
  only while the blow-out valve is open.

These tests need no stack. tests/test_training.py::TestFlagsOffTheHmi runs
both checks and the anonymous download against a live one.
"""
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))
PROJECT = os.path.join(ROOT, "software", "FUXA", "fuxa-project.json")
CONFIG = os.path.join(ROOT, "software", "landing", "ctf_config.json")
PLC_PROGRAM = os.path.join(ROOT, "software", "OpenPLC", "cybICS.st")

try:
    from modules.defense_checks import check_fuxa_login as login
    from modules.defense_checks import check_physical_process as process
except ImportError as error:  # requests or pymodbus missing on this host
    pytest.skip(f"landing check modules not importable here ({error})", allow_module_level=True)


def _project_text():
    with open(PROJECT, encoding="utf-8") as fh:
        return fh.read()


def _project():
    return json.loads(_project_text())


def _challenges():
    with open(CONFIG, encoding="utf-8") as fh:
        return {c["id"]: c for cat in json.load(fh)["categories"].values() for c in cat["challenges"]}


def _tags():
    return {t["name"]: t for d in _project()["devices"].values() for t in d.get("tags", {}).values()}


# --- the project ------------------------------------------------------------

def test_the_fuxa_project_carries_no_flag():
    text = _project_text()
    leaked = sorted(c["id"] for c in _challenges().values() if c["flag"] in text)
    assert not leaked, f"fuxa-project.json, which FUXA serves without a login, holds the flags of {leaked}"
    assert not re.search(r"CybICS\(", text), "fuxa-project.json holds something shaped like a flag"


def test_the_blowout_banner_still_follows_the_sensor():
    bo_tag = _tags()["boSen"]["id"]
    banners = 0
    for view in _project()["hmi"]["views"]:
        for match in re.finditer(r'<text[^>]*id="(svg_[^"]+)"[^>]*>BLOW-OUT</text>', view["svgcontent"]):
            item = view["items"][match.group(1)]
            actions = {(a["type"], a["range"]["min"], a["variableId"]) for a in item["property"]["actions"]}
            assert {("show", 1, bo_tag), ("hide", 0, bo_tag)} <= actions, view["name"]
            banners += 1
    assert banners == 3, "Overview, Pressure and SystemView each show BLOW-OUT"


def test_the_flag_view_is_still_admin_only():
    nav = _project()["hmi"]["layout"]["navigation"]["items"]
    flag_view = next(item for item in nav if item["text"] == "Flag")
    assert flag_view["permission"] == 128
    view = next(v for v in _project()["hmi"]["views"] if v["id"] == flag_view["view"])
    assert ">Admin login works</text>" in view["svgcontent"]


# --- check_physical_process -------------------------------------------------

def test_the_process_check_reads_the_registers_and_tags_the_plant_writes():
    with open(PLC_PROGRAM, encoding="utf-8") as fh:
        program = fh.read()
    # %MWn is Modbus holding register 1024 + n in OpenPLC.
    for name, register in (("hpt", process.HPT_REGISTER), ("boSen", process.BLOWOUT_REGISTER)):
        word = int(re.search(rf"\b{name} AT %MW(\d+)", program).group(1))
        assert 1024 + word == register, name
    tags = _tags()
    for name, tag_id, register in (("HPT", process.FUXA_HPT_TAG, process.HPT_REGISTER),
                                   ("boSen", process.FUXA_BLOWOUT_TAG, process.BLOWOUT_REGISTER)):
        assert tags[name]["id"] == tag_id
        assert int(tags[name]["address"]) == register + 1   # FUXA counts from 1


@pytest.mark.parametrize("readings, passes", [
    ([(255, 1), (255, 1), (254, 1)], True),
    ([(221, 1), (222, 1), (223, 1)], True),
    ([(205, 1), (201, 1), (200, 1)], False),   # vented back to the release pressure
    ([(255, 1), (255, 0), (255, 1)], False),   # a single forged sensor value
    ([(255, 0), (255, 0), (255, 0)], False),   # full tank, valve closed
    ([(70, 1), (70, 1), (70, 1)], False),      # sensor written by hand on a normal tank
    ([(70, 0), (71, 0), (72, 0)], False),
])
def test_the_blowout_must_last_through_every_read(readings, passes):
    result = process.judge(readings, "test")
    assert result["success"] is passes
    assert "flag" not in result


def _fake_modbus(readings):
    values = iter(readings)

    def read():
        return next(values)
    read.close = lambda: None
    return read


def test_the_process_check_samples_modbus_first(monkeypatch):
    monkeypatch.setattr(process.time, "sleep", lambda s: None)
    monkeypatch.setattr(process, "_read_modbus", lambda: _fake_modbus([(255, 1)] * 3))
    monkeypatch.setattr(process, "_read_fuxa", lambda: pytest.fail("FUXA asked although Modbus answered"))
    result = process.verify()
    assert result["success"] and "Modbus" in result["checks"][0]["detail"]


def test_the_process_check_falls_back_to_fuxa(monkeypatch):
    monkeypatch.setattr(process.time, "sleep", lambda s: None)
    monkeypatch.setattr(process, "_read_modbus", lambda: None)            # port 502 closed
    monkeypatch.setattr(process, "_read_fuxa", lambda: _fake_modbus([(255, 1)] * 3))
    result = process.verify()
    assert result["success"] and "FUXA" in result["checks"][0]["detail"]

    def broken():
        raise ConnectionError("reset")
    broken.close = lambda: None
    monkeypatch.setattr(process, "_read_modbus", lambda: broken)          # 502 drops mid-read
    assert process.verify()["success"]


def test_the_process_check_fails_closed_when_nothing_answers(monkeypatch):
    import requests
    monkeypatch.setattr(process.time, "sleep", lambda s: None)
    monkeypatch.setattr(process, "_read_modbus", lambda: None)

    def unreachable():
        def read():
            raise requests.exceptions.ConnectionError("down")
        return read
    monkeypatch.setattr(process, "_read_fuxa", unreachable)
    result = process.verify()
    assert result["success"] is False and result["checks"][0]["passed"] is False


# --- check_fuxa_login -------------------------------------------------------

def test_the_shipped_login_is_the_documented_one():
    with open(os.path.join(ROOT, "software", "FUXA", "README.md"), encoding="utf-8") as fh:
        readme = fh.read()
    assert re.search(rf"\|\s*{login.USERNAME}\s*\|\s*{login.PASSWORD}\s*\|", readme)


@pytest.mark.parametrize("username, password, passes", [
    ("admin", "123456", True),
    ("Admin", "123456", True),          # FUXA user names: case does not matter here
    ("operator", "operator", False),    # a real login, but not the administrator
    ("admin", "1234567", False),
    ("admin", "", False),
    ("", "123456", False),
])
def test_the_login_check_grades_the_admin_credentials(username, password, passes):
    result = login.verify({"username": username, "password": password})
    assert result["success"] is passes
    assert len(result["checks"]) == 1                     # all or nothing
    assert "123456" not in json.dumps(result)


def test_the_two_challenges_are_verify_challenges():
    challenges = _challenges()
    assert challenges["physical_process"]["verify_module"] == "check_physical_process"
    assert "answers" not in challenges["physical_process"]
    assert challenges["password_attack"]["verify_module"] == "check_fuxa_login"
    assert [f["name"] for f in challenges["password_attack"]["answers"]] == ["username", "password"]
    for cid in ("physical_process", "password_attack"):
        assert challenges[cid]["type"] == "verify"


def test_the_readmes_no_longer_print_the_two_flags():
    # Both pages render their README; the flag now comes from Verify only.
    challenges = _challenges()
    for cid in ("physical_process", "password_attack"):
        with open(os.path.join(ROOT, challenges[cid]["training_content"]), encoding="utf-8") as fh:
            assert challenges[cid]["flag"] not in fh.read(), cid
