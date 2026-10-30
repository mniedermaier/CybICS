"""The Packet Anatomy challenge's verify module and solution script, without a stack.

software/landing/modules/defense_checks/check_packet_anatomy.py takes four
Modbus/TCP frames typed as hex apart and checks every field: a read of GST
and HPT in one request, the PLC's response to exactly that request, one write
that sets STOP and MANUAL to 0, and the PLC's exception to a read of a
register it does not have. These tests check the addresses against the PLC
program, that the solution script's frames pass, that every single defect a
student is likely to make fails, and that neither the page nor the lessons
carry an answer.

tests/test_training.py::TestPacketAnatomy runs the challenge on a live stack.
"""
import importlib.util
import json
import os
import re
import struct
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))
CTF_CONFIG = os.path.join(ROOT, "software", "landing", "ctf_config.json")
PLC_PROGRAM = os.path.join(ROOT, "software", "OpenPLC", "cybICS.st")
SCRIPT = os.path.join(ROOT, "training", "packet_anatomy", "frames.py")
README = os.path.join(ROOT, "training", "packet_anatomy", "README.md")
LESSON = os.path.join(ROOT, "training", "theory", "modules", "packet_anatomy.md")
SIDECAR = os.path.join(ROOT, "training", "theory", "modules", "packet_anatomy.json")

from modules.defense_checks import check_packet_anatomy as check  # noqa: E402


def load_script():
    spec = importlib.util.spec_from_file_location("packet_anatomy_frames", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


frames = load_script()


def hexs(data):
    return data.hex(" ")


def response_to(request, gst=118, middle=0, hpt=66):
    """What OpenPLC answers to a 3-register FC 03 read: same tid and unit, length 9."""
    tid, unit = struct.unpack(">H", request[:2])[0], request[6]
    return struct.pack(">HHHBBB3H", tid, 0, 9, unit, 0x03, 6, gst, middle, hpt)


def right(tid=0x2A2A, unit=1):
    read = frames.read_holding(tid, unit, 1124, 3)
    return {
        "read_request": hexs(read),
        "read_response": hexs(response_to(read)),
        "write_request": hexs(frames.write_multiple(tid + 1, unit, 1128, [0, 0, 0])),
        "exception": "00 03 00 00 00 03 01 83 02",
    }


def passes(answers):
    result = check.verify(answers)
    assert len(result["checks"]) == 1, "the grade must stay all or nothing"
    return result["success"]


# ---------------------------------------------------------------------------
# The answer key matches the PLC program
# ---------------------------------------------------------------------------

def memory_word(name):
    with open(PLC_PROGRAM, encoding="utf-8") as f:
        match = re.search(rf"^\s*{name}\s+AT\s+%MW(\d+)\s*:", f.read(), re.M)
    assert match, f"{name} is no longer a %MW variable in cybICS.st"
    return 1024 + int(match.group(1))     # OpenPLC: %MWn is holding register 1024 + n


def test_addresses_follow_the_plc_program():
    gst, hpt, stop, manual = (memory_word(n) for n in ("gst", "hpt", "stop", "manual"))
    assert check.GST_REGISTER == gst
    assert check.READ_QUANTITY == hpt - gst + 1
    assert check.STOP_REGISTER == stop
    assert check.WRITE_QUANTITY == manual - stop + 1


def test_words_inside_the_blocks_are_declared_nowhere():
    """The read and write cover one word each that the program does not use;
    the README promises it reads 0 and writing 0 to it changes nothing."""
    with open(PLC_PROGRAM, encoding="utf-8") as f:
        program = f.read()
    for register in (check.GST_REGISTER + 1, check.STOP_REGISTER + 1):
        assert f"%MW{register - 1024} " not in program and f"%MW{register - 1024}:" not in program


# ---------------------------------------------------------------------------
# Right answers pass, in every reasonable spelling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tid,unit", [(0x2A2A, 1), (0, 0), (0xFFFF, 255), (7, 0x11)])
def test_solution_frames_pass_with_any_transaction_and_unit(tid, unit):
    assert passes(right(tid, unit))


@pytest.mark.parametrize("spell", [
    lambda h: h.replace(" ", ""),
    lambda h: h.upper(),
    lambda h: h.replace(" ", ":"),
    lambda h: " ".join("0x" + b for b in h.split()),
    lambda h: "  " + h.replace(" ", "  ") + " ",
])
def test_hex_spellings_are_accepted(spell):
    assert passes({k: spell(v) for k, v in right().items()})


def test_live_like_values_are_accepted():
    answers = right()
    read = bytes.fromhex(answers["read_request"].replace(" ", ""))
    answers["read_response"] = hexs(response_to(read, gst=255, hpt=0))
    assert passes(answers)


# ---------------------------------------------------------------------------
# Every single mistake fails
# ---------------------------------------------------------------------------

def mutate(field, transform):
    answers = right()
    raw = bytearray(bytes.fromhex(answers[field].replace(" ", "")))
    answers[field] = hexs(bytes(transform(raw)))
    return answers


def set_bytes(offset, *values):
    def apply(raw):
        raw[offset:offset + len(values)] = bytes(values)
        return raw
    return apply


WRONG = {
    # read request
    "read: start counted from 1": mutate("read_request", set_bytes(8, 0x04, 0x65)),
    "read: quantity 2 misses HPT": mutate("read_request", set_bytes(10, 0x00, 0x02)),
    "read: quantity 4 reads more than needed": mutate("read_request", set_bytes(10, 0x00, 0x04)),
    "read: input registers (FC 04)": mutate("read_request", set_bytes(7, 0x04)),
    "read: length counts the whole frame": mutate("read_request", set_bytes(4, 0x00, 0x0C)),
    "read: length counts only the PDU": mutate("read_request", set_bytes(4, 0x00, 0x05)),
    "read: protocol ID not zero": mutate("read_request", set_bytes(2, 0x00, 0x01)),
    "read: trailing byte": mutate("read_request", lambda r: r + b"\x00"),
    # response
    "response: other transaction": mutate("read_response", set_bytes(0, 0x00, 0x01)),
    "response: other unit": mutate("read_response", set_bytes(6, 0x02)),
    "response: byte count is a register count": mutate("read_response", set_bytes(8, 0x03)),
    "response: one register missing": mutate("read_response", lambda r: set_bytes(4, 0, 7)(r[:-2])),
    "response: an exception, not data": {**right(), "read_response": "2a 2a 00 00 00 03 01 83 02"},
    # write request
    "write: STOP and MANUAL as if adjacent": {**right(), "write_request": hexs(
        frames.write_multiple(1, 1, 1128, [0, 0]))},
    "write: start counted from 1": {**right(), "write_request": hexs(
        frames.write_multiple(1, 1, 1129, [0, 0, 0]))},
    "write: stops the plant": {**right(), "write_request": hexs(
        frames.write_multiple(1, 1, 1128, [1, 0, 0]))},
    "write: byte count is a register count": mutate("write_request", set_bytes(12, 0x03)),
    "write: single-register function": {**right(), "write_request": "00 01 00 00 00 06 01 06 04 68 00 00"},
    "write: length off by one": mutate("write_request", set_bytes(4, 0x00, 0x0E)),
    # exception
    "exception: cut-off request (code 03)": {**right(), "exception": "00 03 00 00 00 03 01 83 03"},
    "exception: illegal function (code 01)": {**right(), "exception": "00 03 00 00 00 03 01 87 01"},
    "exception: top bit not set": {**right(), "exception": "00 03 00 00 00 03 01 03 02"},
    "exception: length 2": {**right(), "exception": "00 03 00 00 00 02 01 83 02"},
    # malformed input
    "odd number of hex digits": {**right(), "exception": "00 03 00 00 00 03 01 83 0"},
    "not hex": {**right(), "exception": "zz 03 00 00 00 03 01 83 02"},
}


@pytest.mark.parametrize("name", sorted(WRONG))
def test_single_mistake_fails(name):
    assert not passes(WRONG[name]), name


def test_missing_or_odd_input_fails_without_error():
    assert not passes({})
    assert not passes(None)
    assert not passes({**right(), "read_request": ""})


def test_nothing_typed_or_expected_is_echoed():
    answers = WRONG["read: quantity 2 misses HPT"]
    text = json.dumps(check.verify(answers)).lower()
    for value in answers.values():
        assert value.lower() not in text
    assert "1124" not in text and "1128" not in text and "04 64" not in text


# ---------------------------------------------------------------------------
# Configuration and content
# ---------------------------------------------------------------------------

def challenge():
    with open(CTF_CONFIG, encoding="utf-8") as f:
        config = json.load(f)
    return next(c for cat in config["categories"].values() for c in cat["challenges"]
                if c["id"] == "packet_anatomy")


def test_challenge_declares_the_graded_fields():
    entry = challenge()
    assert entry["type"] == "verify" and entry["verify_module"] == "check_packet_anatomy"
    assert [a["name"] for a in entry["answers"]] == list(check.LABELS)
    longest = max(len(" ".join("0x" + b for b in v.split())) for v in right().values())
    assert all(a["max_length"] >= longest for a in entry["answers"])
    assert re.fullmatch(r"CybICS\([^)]+\)", entry["flag"])


def answer_patterns():
    """The graded parts of the three requests, as hex without the free fields."""
    return [
        "03 04 64 00 03",                 # FC 03, start 1124, quantity 3
        "10 04 68 00 03 06",              # FC 16, start 1128, quantity 3, byte count 6
        "00 03 01 83 02",                 # exception response, length 3
    ]


@pytest.mark.parametrize("path", [README, LESSON, SIDECAR, CTF_CONFIG])
def test_no_answer_frame_is_published(path):
    with open(path, encoding="utf-8") as f:
        text = re.sub(r"\\x", " ", f.read().lower())
    compact = re.sub(r"[^0-9a-f]", "", text)
    for pattern in answer_patterns():
        assert pattern.replace(" ", "") not in compact, f"{os.path.basename(path)} gives away {pattern}"


def test_solution_script_never_sends_the_write():
    with open(SCRIPT, encoding="utf-8") as f:
        source = f.read()
    sent = re.findall(r"ask\([^)]*\)", source)
    assert sent and all("write" not in call for call in sent), sent
