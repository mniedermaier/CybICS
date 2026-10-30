"""The HMI Project Recon challenge's verify module and solution, without a stack.

software/landing/modules/defense_checks/check_hmi_project_recon.py grades
four answers a student reads out of FUXA's project: the PLC endpoint, the
wire address of the register the STOP / SHUTDOWN buttons write, the wire
coil the SystemView "Comp." button toggles and the FUXA tag ID of HPT. The
module keeps the expected values as constants, because the landing container
does not carry software/FUXA. These tests derive them again from
software/FUXA/fuxa-project.json, the file FUXA imports at first start, so a
re-export from the FUXA UI that changes a tag cannot silently make the
challenge unsolvable. They also run the solution script's parser on that file.

tests/test_training.py::TestHmiProjectRecon runs the challenge on a live stack.
"""
import importlib.util
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))
PROJECT_FILE = os.path.join(ROOT, "software", "FUXA", "fuxa-project.json")
CTF_CONFIG = os.path.join(ROOT, "software", "landing", "ctf_config.json")
SCRIPT = os.path.join(ROOT, "training", "hmi_project_recon", "hmi_recon.py")

from modules.defense_checks import check_hmi_project_recon as check  # noqa: E402


def load_project():
    with open(PROJECT_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_script():
    spec = importlib.util.spec_from_file_location("hmi_recon", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def answers_from(project):
    """The four answers, worked out from a FUXA project the way the README does."""
    recon = load_script()
    plc = [d for d in project["devices"].values() if d.get("type") == "ModbusTCP"]
    assert len(plc) == 1, "expected exactly one Modbus device in the HMI project"
    tags = recon.tag_index(project)

    def written_by(caption, view=None):
        hits = {tag_id for v, text, _, tag_id in recon.button_writes(project)
                if text == caption and (view is None or v == view)}
        assert len(hits) == 1, f"button {caption!r} writes {hits}, expected one tag"
        return tags[hits.pop()][1]

    stop = written_by("STOP / SHUTDOWN")
    comp = written_by("Comp.", "SystemView")
    assert stop["memaddress"] == "400000" and comp["memaddress"] == "000000"
    hpt = [t for _, t in tags.values() if t.get("name") == "HPT"]
    assert len(hpt) == 1
    return {
        "plc": plc[0]["property"]["address"],
        "stop_register": str(recon.wire_address(stop)),
        "compressor_coil": str(recon.wire_address(comp)),
        "hpt_tag_id": hpt[0]["id"],
    }


RIGHT = {"plc": "openplc:502", "stop_register": "1128",
         "compressor_coil": "1", "hpt_tag_id": "t_e76df10e-a85c4674"}


# --- the module's constants are what the shipped project says --------------

def test_the_expected_answers_match_the_shipped_hmi_project():
    derived = answers_from(load_project())
    assert derived == RIGHT
    assert derived["plc"] in check.PLC_ENDPOINTS
    assert int(derived["stop_register"]) == check.STOP_REGISTER
    assert int(derived["compressor_coil"]) == check.COMPRESSOR_COIL
    assert derived["hpt_tag_id"] == check.HPT_TAG_ID


def test_the_wire_addresses_match_the_plc_program():
    """stop is %MW104 (1024 + 104) and compressor %QX0.1 (coil 1) in cybICS.st."""
    with open(os.path.join(ROOT, "software", "OpenPLC", "cybICS.st"), encoding="utf-8") as f:
        source = f.read()
    stop = re.search(r"^\s*stop\s+AT\s+%MW(\d+)", source, re.M)
    comp = re.search(r"^\s*compressor\s+AT\s+%QX0\.(\d+)", source, re.M)
    assert stop and 1024 + int(stop.group(1)) == check.STOP_REGISTER
    assert comp and int(comp.group(1)) == check.COMPRESSOR_COIL


# --- grading ---------------------------------------------------------------

def test_the_right_answers_pass():
    result = check.verify(dict(RIGHT))
    assert result["success"] is True
    assert [c["passed"] for c in result["checks"]] == [True]


@pytest.mark.parametrize("variant", [
    {"plc": "172.18.0.3:502"},
    {"plc": "OpenPLC:502"},
    {"stop_register": "0x468"},
    {"hpt_tag_id": "T_E76DF10E-A85C4674"},
])
def test_equivalent_spellings_pass(variant):
    assert check.verify({**RIGHT, **variant})["success"] is True


@pytest.mark.parametrize("wrong", [
    {"plc": "openplc"},                     # no port
    {"plc": "172.18.0.4:1881"},             # the HMI itself
    {"stop_register": "1129"},              # FUXA's 1-based address
    {"stop_register": "104"},               # %MW offset, not the register
    {"compressor_coil": "2"},               # FUXA's 1-based address
    {"compressor_coil": "0"},               # the heartbeat coil
    {"hpt_tag_id": "t_8d116167-9c4d477a"},  # the stop tag's ID
    {"hpt_tag_id": "d_ce5e29f3-e7a14f6e"},  # the device ID
], ids=lambda w: f"{next(iter(w))}={next(iter(w.values()))}")
def test_any_single_wrong_answer_fails_the_whole_grade(wrong):
    result = check.verify({**RIGHT, **wrong})
    assert result["success"] is False
    # One all-or-nothing check: the page does not say which field was wrong.
    assert len(result["checks"]) == 1 and result["checks"][0]["passed"] is False


def test_missing_answers_fail():
    assert check.verify(None)["success"] is False
    assert check.verify({})["success"] is False


def test_a_failed_grade_gives_nothing_away():
    text = json.dumps(check.verify({**RIGHT, "compressor_coil": "2"}))
    for secret in ("1128", "t_e76df10e", "openplc:502", "CybICS("):
        assert secret not in text


def test_the_challenge_is_declared_with_these_fields():
    with open(CTF_CONFIG, encoding="utf-8") as f:
        config = json.load(f)
    entry = next(c for cat in config["categories"].values() for c in cat["challenges"]
                 if c["id"] == "hmi_project_recon")
    assert entry["verify_module"] == "check_hmi_project_recon"
    assert [a["name"] for a in entry["answers"]] == list(RIGHT)
    for field in entry["answers"]:
        assert len(RIGHT[field["name"]]) <= field["max_length"]
    # Expected values live only in the module, never in the config the page sees.
    blob = json.dumps(entry)
    for value in ("1128", "t_e76df10e", "openplc:502"):
        assert value not in blob


# --- the solution script ---------------------------------------------------

def test_the_solution_script_lists_every_button_that_writes(capsys):
    recon = load_script()
    project = load_project()
    recon.print_devices(project)
    recon.print_tags(project)
    recon.print_views(project)
    out = capsys.readouterr().out
    assert "openplc:502" in out and "t_e76df10e-a85c4674" in out
    assert re.search(r"SystemView\s+Comp\.\s+onToggleValue\s+-> OpenPLC/compressor \(coil 1\)", out)
    assert re.search(r"STOP / SHUTDOWN\s+onToggleValue\s+-> OpenPLC/stop \(holding register 1128\)", out)
    # It prints the map, not the screens' SVG.
    assert "CybICS(" not in out


# --- no other flag in the project --------------------------------------------

# The project used to carry the Password Attack and Physical Process flags as
# hidden SVG text, so doing this challenge handed out both. They now come from
# verify modules (tests/test_hmi_flags.py); this keeps the recon challenge
# from ever pointing at another challenge's flag again.
def test_the_hmi_project_carries_no_other_challenges_flag():
    with open(CTF_CONFIG, encoding="utf-8") as f:
        config = json.load(f)
    flags = {c["flag"] for cat in config["categories"].values() for c in cat["challenges"]}
    with open(PROJECT_FILE, encoding="utf-8") as f:
        text = f.read()
    leaked = sorted(flag for flag in flags if flag in text)
    assert not leaked, f"the anonymous HMI project contains {leaked}"
