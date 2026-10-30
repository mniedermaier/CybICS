"""The Register Map Recon challenge's verify module and sweep helper, without a stack.

software/landing/modules/defense_checks/check_register_map_recon.py grades
four answers a student works out by sampling the PLC's memory: the wire
addresses of the compressor and refill latches, the HPT value at which the
compressor latch releases and the latch's byte offset in OpenPLC's S7comm data
block DB1002. The module keeps those values as constants; these tests derive
them again from software/OpenPLC/cybICS.st and OpenPLC's Snap7 wrapper, so a
change to the PLC program cannot silently make the challenge unsolvable. They
also check the premise of the challenge, that no HMI tag, OPC-UA node or
plant write covers the latches, and the helper's classifier.

tests/test_training.py::TestRegisterMapRecon runs the challenge on a live stack.
"""
import importlib.util
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))
CTF_CONFIG = os.path.join(ROOT, "software", "landing", "ctf_config.json")
SCRIPT = os.path.join(ROOT, "training", "register_map_recon", "map_registers.py")
SNAP7 = os.path.join(ROOT, "software", "OpenPLC", "OpenPLC_v3", "utils", "snap7_src",
                     "wrapper", "oplc_snap7.cpp")

from modules.defense_checks import check_register_map_recon as check  # noqa: E402

RIGHT = {"compressor_latch": "1224", "refill_latch": "1226",
         "release_hpt": "90", "s7_offset": "400"}


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def plc_words():
    """Variable name -> %MW index for every %MW variable in the PLC program."""
    return {name: int(word) for name, word in
            re.findall(r"^\s*(\w+)\s+AT\s+%MW(\d+)\s*:", read("software", "OpenPLC", "cybICS.st"), re.M)}


def load_script():
    spec = importlib.util.spec_from_file_location("map_registers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- the expected values follow from the sources ---------------------------------

def test_the_latch_addresses_match_the_plc_program():
    words = plc_words()
    assert words["compressorState"] == check.COMPRESSOR_LATCH_MW
    assert words["gstState"] == check.REFILL_LATCH_MW
    assert check.COMPRESSOR_LATCH == check.OPENPLC_MW_BASE + words["compressorState"] == 1224
    assert check.REFILL_LATCH == check.OPENPLC_MW_BASE + words["gstState"] == 1226
    # The same base the OPC-UA mirror and test_register_map.py rely on.
    assert words["hpt"] + check.OPENPLC_MW_BASE == 1126


def test_the_release_value_matches_the_compressor_rule():
    source = read("software", "OpenPLC", "cybICS.st")
    seal_in = re.search(r"ELSIF\s+hpt\s*<\s*(\d+)\s+AND\s+compressorState\s*=\s*1", source)
    assert seal_in, "the compressor's seal-in branch changed shape"
    assert int(seal_in.group(1)) == check.RELEASE_HPT


def test_the_s7_offset_matches_openplcs_snap7_mapping():
    assert check.S7_OFFSET == 2 * plc_words()["compressorState"] == 400
    if not os.path.exists(SNAP7):
        pytest.skip("OpenPLC_v3 submodule not checked out")
    with open(SNAP7, encoding="utf-8") as f:
        source = f.read()
    # DB1002 is backed by int_memory (%MW), word by word, addressed in bytes.
    assert re.search(r"if \(int_memory\[c\] == NULL\) int_memory\[c\] = &DB1002\[c\];", source)
    case = re.search(r"case 1002:(.*?)break;", source, re.S)
    assert case and "getBytesFromWordArray(int_memory" in case.group(1)


# --- the premise: nothing on a screen or in the docs maps the latches ------------

def test_no_hmi_tag_opcua_node_or_plant_write_covers_the_latches():
    project = json.loads(read("software", "FUXA", "fuxa-project.json"))
    for device in project["devices"].values():
        for tag in (device.get("tags") or {}).values():
            if tag.get("memaddress") == "400000":
                # FUXA counts from 1.
                assert int(tag["address"]) - 1 not in (check.COMPRESSOR_LATCH, check.REFILL_LATCH), tag
    opcua = read("software", "opcua", "opcua.py")
    hwio = read("software", "hwio-virtual", "hardwareAbstraction.py")
    for address in (check.COMPRESSOR_LATCH, check.REFILL_LATCH):
        assert not re.search(rf"\(\s*{address}\b", opcua)
        assert not re.search(rf"write_registers?\(\s*{address}\b", hwio)


def test_no_challenge_readme_or_lesson_hands_out_the_s7_offset():
    """The README and lesson teach the translation; only the collapsed solution gives it."""
    readme = read("training", "register_map_recon", "README.md")
    before_solution = readme.split("## Solution", 1)[0]
    for value in ("1224", "1226", "DBW400", "offset 400", "%MW200"):
        assert value not in before_solution, value
    lesson = read("training", "theory", "modules", "register_map_recon.md")
    rendered = re.sub(r'<details class="instructor".*?</details>', "", lesson, flags=re.S)
    for value in ("1224", "1226", "400", "%MW200", "%MW202", "compressorState", "gstState"):
        assert value not in rendered, value


# --- grading ---------------------------------------------------------------------

def test_the_right_answers_pass():
    result = check.verify(dict(RIGHT))
    assert result["success"], result
    assert [c["passed"] for c in result["checks"]] == [True]


@pytest.mark.parametrize("variant", [
    {"release_hpt": "89"}, {"release_hpt": "91"}, {"release_hpt": "90.0"},
    {"s7_offset": "DBW400"}, {"s7_offset": "DB1002.DBW400"}, {"s7_offset": "db1002.dbb400"},
    {"s7_offset": "DB1002 DBW 400"}, {"compressor_latch": "0x4C8"}, {"refill_latch": " 1226 "},
])
def test_equivalent_spellings_pass(variant):
    assert check.verify({**RIGHT, **variant})["success"], variant


@pytest.mark.parametrize("wrong", [
    {"compressor_latch": "1226", "refill_latch": "1224"},   # swapped
    {"compressor_latch": "1225"},                           # FUXA's 1-based number
    {"compressor_latch": "200"},                            # %MW index, not the wire
    {"refill_latch": "1227"},
    {"release_hpt": "60"},                                  # the switch-on value
    {"release_hpt": "92"},
    {"s7_offset": "200"},                                   # forgot two bytes per word
    {"s7_offset": "1224"},
    {"s7_offset": "DB1001.DBW400"},
    {"s7_offset": "404"},                                   # the refill latch
])
def test_any_single_wrong_answer_fails_the_whole_grade(wrong):
    result = check.verify({**RIGHT, **wrong})
    assert not result["success"]
    assert [c["passed"] for c in result["checks"]] == [False]


def test_missing_answers_fail():
    assert not check.verify(None)["success"]
    assert not check.verify({k: v for k, v in RIGHT.items() if k != "s7_offset"})["success"]


def test_a_failed_grade_gives_nothing_away():
    text = json.dumps(check.verify({**RIGHT, "s7_offset": "200"}))
    for value in ("1224", "1226", "90", "400", "200"):
        assert value not in text, value


def test_the_challenge_is_declared_with_these_fields():
    config = json.loads(read("software", "landing", "ctf_config.json"))
    challenge = next(c for cat in config["categories"].values() for c in cat["challenges"]
                     if c["id"] == "register_map_recon")
    assert challenge["type"] == "verify" and challenge["verify_module"] == "check_register_map_recon"
    assert [a["name"] for a in challenge["answers"]] == list(RIGHT)
    assert re.fullmatch(r"CybICS\([^)O]+\)", challenge["flag"]), "flag format (and no letter O)"
    assert os.path.exists(os.path.join(ROOT, challenge["training_content"]))
    declared = json.dumps(challenge)
    for value in ("1224", "1226", "400"):
        assert value not in declared, value


# --- the sweep helper -----------------------------------------------------------

def test_the_helper_classifies_words_by_behaviour():
    helper = load_script()
    assert helper.classify([0, 0, 0]) == "zero"
    assert helper.classify([17273] * 5) == "constant"
    assert helper.classify([1, 1, 1]) == "constant"     # a latch that never switched in the window
    assert helper.classify([0, 1, 1, 0]) == "flag"
    assert helper.classify([58, 60, 75, 90]) == "analog"


def test_the_helper_translates_like_the_check():
    helper = load_script()
    assert helper.translate(check.COMPRESSOR_LATCH) == ("%MW200", f"DB1002.DBW{check.S7_OFFSET}")
    assert helper.translate(1128) == ("%MW104", "DB1002.DBW208")    # s7_sidedoor's stop flag
    assert helper.translate(1023) == ("", "")
    assert helper.OPENPLC_MW_BASE == check.OPENPLC_MW_BASE and helper.S7_MW_DB == check.S7_DB


def test_the_helper_only_reads():
    source = read("training", "register_map_recon", "map_registers.py")
    assert not re.search(r"\.write_\w+\(", source)
