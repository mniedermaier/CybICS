"""The LCD shows the same thing on the board and in the browser.

CybICS exists twice: as firmware on an STM32 driving a 16x2 HD44780, and as a
virtual plant in a browser.  A student is meant to be able to work through the
training on either one, so the panel has to read the same in both -- the same
screens, in the same order, laid out the same way.

Nothing enforces that on its own.  The firmware is C and the virtual plant is
Python, and the two have already drifted once: the browser rendered the first
screen only, with a hand-written copy of its first line, and ignored the other
four entirely.

So both sides declare their screen text as named constants inside a marked
block, and this test parses the two blocks and compares them.  It needs no
stack and no hardware, like test_plant_model_parity.py, which guards the
physical model the same way.
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMWARE = os.path.join(ROOT, "software", "stm32", "src", "main.c")
VIRTUAL = os.path.join(ROOT, "software", "hwio-virtual", "hardwareAbstraction.py")

BEGIN = "LCD_SCREENS_BEGIN"
END = "LCD_SCREENS_END"


def _block(path):
    """The text between the two markers, or fail loudly saying where to look."""
    with open(path, encoding="utf-8") as handle:
        src = handle.read()

    if BEGIN not in src or END not in src:
        pytest.fail(
            f"{os.path.relpath(path, ROOT)} has no {BEGIN}/{END} block. "
            "Both the firmware and the virtual plant must declare their LCD "
            "strings inside one, so this test can compare them."
        )

    return src[src.index(BEGIN) + len(BEGIN):src.index(END)]


def _c_constants():
    """#define NAME "value" or #define NAME 5, from the firmware block."""
    out = {}
    for name, value in re.findall(
        r'#define\s+(LCD_\w+)\s+"((?:[^"\\]|\\.)*)"', _block(FIRMWARE)
    ):
        out[name] = value
    for name, value in re.findall(r"#define\s+(LCD_\w+)\s+(\d+)\s*$", _block(FIRMWARE), re.M):
        out[name] = value
    return out


def _py_constants():
    """NAME = "value" or NAME = 5, from the virtual plant block."""
    out = {}
    block = _block(VIRTUAL)
    for name, value in re.findall(r'(LCD_\w+)\s*=\s*"((?:[^"\\]|\\.)*)"', block):
        out[name] = value
    for name, value in re.findall(r"(LCD_\w+)\s*=\s*(\d+)\s*$", block, re.M):
        out[name] = value
    return out


def test_both_sides_declare_screens():
    """Neither block is empty, which would make every other check pass vacuously."""
    assert _c_constants(), "no LCD constants found in the firmware block"
    assert _py_constants(), "no LCD constants found in the virtual plant block"


def test_same_constants_exist():
    firmware = set(_c_constants())
    virtual = set(_py_constants())

    only_firmware = sorted(firmware - virtual)
    only_virtual = sorted(virtual - firmware)

    assert not only_firmware, (
        f"the firmware declares {only_firmware} and the virtual plant does not. "
        f"Add them to the {BEGIN} block in {os.path.relpath(VIRTUAL, ROOT)} "
        "and render them, or the browser will show a screen the board does not."
    )
    assert not only_virtual, (
        f"the virtual plant declares {only_virtual} and the firmware does not. "
        f"Add them to the {BEGIN} block in {os.path.relpath(FIRMWARE, ROOT)}."
    )


def test_same_text():
    firmware = _c_constants()
    virtual = _py_constants()

    drifted = {
        name: (firmware[name], virtual[name])
        for name in sorted(set(firmware) & set(virtual))
        if firmware[name] != virtual[name]
    }

    assert not drifted, (
        "the two panels would show different text: "
        + "; ".join(f"{n}: firmware {c!r} vs virtual {p!r}" for n, (c, p) in drifted.items())
    )


def test_screen_count_matches_the_firmware_switch():
    """The declared count is the one the firmware actually cycles through.

    LCD_SCREEN_COUNT drives the wrap-around in both implementations, so a fifth
    screen added to the switch without bumping the constant would be
    unreachable, and a count raised without adding the screen would show the
    default branch twice.
    """
    count = int(_c_constants()["LCD_SCREEN_COUNT"])

    with open(FIRMWARE, encoding="utf-8") as handle:
        src = handle.read()

    start = src.index("void thread_display")
    body = src[start:src.index("\n}", start)]

    cases = len(re.findall(r"^\t\tcase \d+:", body, re.M))
    defaults = len(re.findall(r"^\t\tdefault:", body, re.M))

    assert defaults == 1, "the display switch should have exactly one default branch"
    assert cases + defaults == count, (
        f"LCD_SCREEN_COUNT is {count} but thread_display handles {cases + defaults} "
        "screens; one of them is unreachable or duplicated"
    )
