"""The Plant Physics Sandbox challenge: its answers and its verify module, without a stack.

The challenge asks what the plant does in three situations an attacker can
create, and which register freezes the outputs. These tests

- run each situation with the real tick of physical_process_thread() in
  software/hwio-virtual/hardwareAbstraction.py (executed, not copied) and
  the automatic-mode PLC of software/scripts/generate_physics_historian.py,
  which tests/test_physics_forensics.py checks against cybICS.st; the
  answers derived here must equal the constants in
  check_plant_physics_sandbox.py, for every random seed tried;
- show that the tempting wrong answers really are wrong (the PLC's "> 50"
  guard instead of the plant's ">= 50", an off-by-one tick, "the spoof lasts
  one scan, so the compressor runs one tick", the length of the normal cycle
  that follows, the STOP register);
- back what the README says about situation 3's control run: without the
  attacker, or with a forged 60, the consumer drains the HPT and the PLC
  starts the compressor itself a few ticks later for a slightly longer run
  up to the same cut-out;
- read the manual branch of cybICS.st and the register map, so the register
  answer cannot drift;
- check that no answer leaks into the README, the Theory lesson, its sidecar
  or ctf_config.json, and grade the module with right and wrong answers.

The browser copy of the model (PLANT_MODEL and plantTick in
theory-widgets.js) is checked against the firmware in
tests/test_plant_model_parity.py. tests/test_training.py::TestPlantPhysicsSandbox
solves the challenge on the running landing page.
"""
import importlib.util
import json
import os
import random
import re
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))
HWIO = os.path.join(ROOT, "software", "hwio-virtual", "hardwareAbstraction.py")
GENERATOR = os.path.join(ROOT, "software", "scripts", "generate_physics_historian.py")
PLC_PROGRAM = os.path.join(ROOT, "software", "OpenPLC", "cybICS.st")
CTF_CONFIG = os.path.join(ROOT, "software", "landing", "ctf_config.json")
README = os.path.join(ROOT, "training", "plant_physics_sandbox", "README.md")
LESSON = os.path.join(ROOT, "training", "theory", "modules", "plant_physics_sandbox")

from modules.defense_checks import check_plant_physics_sandbox as check  # noqa: E402

SEEDS = range(300)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def hwio_tick():
    """The simulation block of physical_process_thread(), compiled from the source."""
    with open(HWIO, encoding="utf-8") as f:
        src = f.read()
    start = src.index("    if delay > 50:", src.index("def physical_process_thread"))
    end = src.index("    # Write to OpenPLC", start)
    block = compile(textwrap.dedent(src[start:end]), "hwio-tick", "exec")

    def tick(state, coils, rng):
        env = {**state, **{k: int(v) for k, v in coils.items()}, "sysSen": 0, "heartbeat": 0,
               "delay": 51, "timer": 0, "random": rng}
        exec(block, env)
        state.update(gst=env["gst"], hpt=env["hpt"], boSen=env["boSen"])
        return state
    return tick


@pytest.fixture(scope="module")
def plc_class():
    return _load(GENERATOR, "generate_physics_historian").Plc


def frozen(hwio_tick, gst, hpt, coils, rng, ticks):
    """Manual mode: the PLC leaves the coils alone. Yields (tick, state, moved)."""
    state = {"gst": gst, "hpt": hpt, "boSen": 0}
    for t in range(1, ticks + 1):
        before = dict(state)
        hwio_tick(state, coils, rng)
        yield t, state, state["hpt"] > before["hpt"] and state["gst"] < before["gst"]


def situation_1(hwio_tick, seed):
    coils = {"compressor": 1, "systemValve": 0, "gstSig": 0}
    for t, state, _ in frozen(hwio_tick, 150, 60, coils, random.Random(seed), 300):
        pass
    return state


def situation_2(hwio_tick, seed):
    coils = {"compressor": 1, "systemValve": 0, "gstSig": 1}
    for t, state, _ in frozen(hwio_tick, 240, 90, coils, random.Random(seed), 300):
        if state["boSen"]:
            return t, state
    return None, state


def situation_3(hwio_tick, plc_class, seed, forged=40, scans_per_tick=20, started=None):
    """Automatic mode; the PLC sees `forged` instead of the HPT in exactly one
    scan (forged=None is the control run). Counts the ticks the compressor
    moved gas until the PLC switched it off. With a `started` list, appends
    the tick on which the compressor first switched on."""
    rng = random.Random(seed)
    plc = plc_class()
    state = {"gst": 200, "hpt": 62, "boSen": 0}
    used, moved, was_on = False, 0, False
    for t in range(1, 201):
        for _ in range(scans_per_tick):
            seen = state["hpt"]
            if forged is not None and not used:
                seen, used = forged, True
            coils = dict(plc.scan(state["gst"], seen, 0))
        if coils["compressor"] and not was_on and started is not None and not started:
            started.append(t)
        if was_on and not coils["compressor"]:
            return moved, state
        was_on = bool(coils["compressor"])
        before = dict(state)
        hwio_tick(state, coils, rng)
        if state["hpt"] > before["hpt"]:
            moved += 1
    return None, state


def test_situation_1_settles_where_the_gst_runs_out(hwio_tick):
    for seed in range(20):   # no random draw changes anything here
        state = situation_1(hwio_tick, seed)
        assert state["hpt"] == check.SETTLE_HPT
        assert state["gst"] < 50 and state["boSen"] == 0
    # Decoy: with the PLC's own "gst > 50" guard the answer would be one lower.
    assert (150 - 52) // 2 + 1 + 60 == check.SETTLE_HPT - 1


def test_situation_2_blow_out_tick(hwio_tick):
    ticks = set()
    for seed in SEEDS:
        tick, state = situation_2(hwio_tick, seed)
        ticks.add(tick)
        assert state["hpt"] in (220, 221)
    assert ticks == {check.BLOWOUT_TICK}


def test_situation_2_relief_valve_loses(hwio_tick):
    """What the lesson says about it: once open, the valve never gets the HPT back under 200."""
    coils = {"compressor": 1, "systemValve": 0, "gstSig": 1}
    for seed in range(30):
        lowest_after_open = None
        for t, state, _ in frozen(hwio_tick, 240, 90, coils, random.Random(seed), 600):
            if t > check.BLOWOUT_TICK:
                lowest_after_open = min(lowest_after_open or 999, state["hpt"])
        assert lowest_after_open > 200 and state["hpt"] >= 250 and state["boSen"] == 1


def test_situation_3_one_forged_scan_runs_the_compressor_to_its_cut_out(hwio_tick, plc_class):
    results = {situation_3(hwio_tick, plc_class, seed)[0] for seed in SEEDS}
    assert results == {check.SPOOF_TICKS}


def test_situation_3_control_run_is_a_normal_cycle_a_few_ticks_later(hwio_tick, plc_class):
    """The README's control run: without the attacker the open valve drains the
    HPT, the PLC starts the compressor itself after a few ticks, and it runs a
    little longer up to the same cut-out. A forged 60 changes nothing at all:
    run for run it is the control run."""
    for seed in SEEDS:
        forged_start, control_start, sixty_start = [], [], []
        forged = situation_3(hwio_tick, plc_class, seed, started=forged_start)
        control = situation_3(hwio_tick, plc_class, seed, forged=None, started=control_start)
        sixty = situation_3(hwio_tick, plc_class, seed, forged=60, started=sixty_start)
        assert forged_start == [1]
        assert 3 <= control_start[0] <= 14, control_start
        assert control[0] in (check.SPOOF_TICKS + 3, check.SPOOF_TICKS + 4), control
        assert forged[1]["hpt"] == control[1]["hpt"] == 90
        assert (sixty, sixty_start) == (control, control_start)


def test_situation_3_needs_the_forged_scan_and_a_value_below_60(plc_class):
    """At the real HPT of 62 the compressor stays off; a forged 60 does not
    start it either, 59 does, and the latch then holds it on the real 62."""
    for forged, on in ((62, 0), (60, 0), (59, 1), (40, 1)):
        plc = plc_class()
        assert plc.scan(200, forged, 0)["compressor"] == on, forged
        assert plc.scan(200, 62, 0)["compressor"] == on, forged


def test_manual_register_freezes_the_outputs():
    with open(PLC_PROGRAM, encoding="utf-8") as f:
        st = f.read()
    assert re.search(r"\bmanual\s+AT\s+%MW106\b", st)
    assert re.search(r"\bstop\s+AT\s+%MW104\b", st)
    # %MWn is holding register 1024 + n in OpenPLC.
    assert 1024 + 106 == check.MANUAL_REGISTER
    # The manual branch writes no output: the IF manual < 1 block is followed
    # directly by its END_IF, with only a comment for the ELSE.
    auto = st.split("IF manual < 1 THEN", 1)[1]
    tail = auto.split("(* ELSE System running in manual mode *)", 1)[1]
    assert tail.lstrip().startswith("END_IF;")


def test_no_answer_in_the_challenge_text_lesson_or_config():
    with open(CTF_CONFIG, encoding="utf-8") as f:
        config = json.load(f)
    entry = next(c for cat in config["categories"].values() for c in cat["challenges"]
                 if c["id"] == "plant_physics_sandbox")
    texts = {CTF_CONFIG: json.dumps(entry)}
    for path in (README, LESSON + ".md", LESSON + ".json"):
        with open(path, encoding="utf-8") as f:
            texts[path] = f.read()
    for path, text in texts.items():
        for value in (check.SETTLE_HPT, check.BLOWOUT_TICK, check.SPOOF_TICKS, check.MANUAL_REGISTER):
            assert not re.search(rf"(?<![\d.]){value}(?![\d.])", text), (path, value)
        assert "%MW106" not in text and "MW106" not in text, path
        if path != CTF_CONFIG:
            assert "CybICS(" not in text, path


RIGHT = {"settle_hpt": "111", "blowout_tick": "131", "spoof_ticks": "28", "freeze_register": "1130"}


@pytest.mark.parametrize("answers,ok", [
    (RIGHT, True),
    ({**RIGHT, "freeze_register": "%MW106"}, True),
    ({**RIGHT, "freeze_register": "manual (HR 1130)"}, True),
    ({**RIGHT, "freeze_register": "0x46A"}, True),
    ({**RIGHT, "settle_hpt": "111 "}, True),
    # the PLC's guard instead of the plant's
    ({**RIGHT, "settle_hpt": "110"}, False),
    # GST used up to zero, or the HPT that the GST would allow at 1:1
    ({**RIGHT, "settle_hpt": "135"}, False),
    ({**RIGHT, "blowout_tick": "130"}, False),
    ({**RIGHT, "blowout_tick": "132"}, False),
    # "the spoof lasts one scan, so one tick"
    ({**RIGHT, "spoof_ticks": "1"}, False),
    ({**RIGHT, "spoof_ticks": "29"}, False),
    # the counter read after the next, normal cycle (the control run's length)
    ({**RIGHT, "spoof_ticks": "31"}, False),
    ({**RIGHT, "spoof_ticks": "32"}, False),
    ({**RIGHT, "freeze_register": "1128"}, False),
    ({**RIGHT, "freeze_register": "stop"}, False),
    ({**RIGHT, "freeze_register": "manual"}, False),
    ({**RIGHT, "freeze_register": "1128 1130"}, False),
    ({**RIGHT, "freeze_register": ""}, False),
    ({}, False),
])
def test_grading(answers, ok):
    result = check.verify(answers)
    assert result["success"] is ok
    assert len(result["checks"]) == 1, "all or nothing"
    blob = json.dumps(result)
    for value in ("111", "131", "1130"):
        assert value not in blob


def test_right_answers_match_the_constants():
    assert RIGHT == {"settle_hpt": str(check.SETTLE_HPT), "blowout_tick": str(check.BLOWOUT_TICK),
                     "spoof_ticks": str(check.SPOOF_TICKS),
                     "freeze_register": str(check.MANUAL_REGISTER)}


def test_config_entry():
    with open(CTF_CONFIG, encoding="utf-8") as f:
        config = json.load(f)
    entry = next(c for cat in config["categories"].values() for c in cat["challenges"]
                 if c["id"] == "plant_physics_sandbox")
    assert entry["type"] == "verify" and entry["verify_module"] == "check_plant_physics_sandbox"
    assert [a["name"] for a in entry["answers"]] == list(check.LABELS)
    assert re.fullmatch(r"CybICS\([A-Za-z0-9_]+\)", entry["flag"])
    assert "O" not in entry["flag"][6:] and "0" not in entry["flag"], "no 0/O ambiguity"
    assert entry["training_content"] == "training/plant_physics_sandbox/README.md"
    ids = [c["id"] for cat in config["categories"].values() for c in cat["challenges"]]
    assert ids.count("plant_physics_sandbox") == 1
