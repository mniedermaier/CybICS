"""
Guard against the two plant models drifting apart again.

CybICS simulates the same process twice: as Zephyr firmware on the STM32 in the
physical deployment (software/stm32/src/main.c, thread_physical), and as a
Python service in the virtual one (software/hwio-virtual/hardwareAbstraction.py,
physical_process_thread). The firmware is the reference -- it is what runs on
the board.

They had diverged in four places, and the effect was not cosmetic: an attack
that forces the compressor ended in unrecoverable overpressure on hardware and
in a successful safety intervention in containers, so an instructor who
prepared an exercise on one deployment saw something else on the other.

These tests read both sources and assert the rates and guards still agree.
They are deliberately source-level: the two implementations are in different
languages and cannot be executed against each other in a unit test.
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMWARE = os.path.join(ROOT, "software", "stm32", "src", "main.c")
VIRTUAL = os.path.join(ROOT, "software", "hwio-virtual", "hardwareAbstraction.py")


def _read(path):
    if not os.path.exists(path):
        pytest.skip(f"{os.path.relpath(path, ROOT)} not present in this checkout")
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def firmware():
    src = _read(FIRMWARE)
    start = src.index("void thread_physical")
    return src[start:src.index("void thread_i2c", start)]


@pytest.fixture(scope="module")
def virtual():
    src = _read(VIRTUAL)
    start = src.index("def physical_process_thread")
    return src[start:src.index("def button_reset", start)]


def test_gst_refill_rate(firmware, virtual):
    """External supply adds 0..3 bar per tick, and stops at the tank ceiling."""
    assert "rand() % 4" in firmware
    assert re.search(r"random\.randint\(0,\s*3\)", virtual)
    assert "GSTpressure < 251" in firmware
    assert "gst < 251" in virtual


def test_compressor_transfer_and_interlock(firmware, virtual):
    """Compressor moves 2 bar out of the GST for every 1 bar into the HPT,
    only while the GST holds at least 50 bar and the HPT is below range."""
    assert "GSTpressure = GSTpressure - 2" in firmware
    assert "HPTpressure++" in firmware
    assert "GSTpressure >= 50" in firmware
    assert "HPTpressure < 255" in firmware

    assert re.search(r"gst\s*=\s*gst\s*-\s*2", virtual)
    assert re.search(r"hpt\s*=\s*hpt\s*\+\s*1", virtual)
    assert re.search(r"gst\s*>=\s*50", virtual)
    assert re.search(r"hpt\s*<\s*255", virtual)


def test_downstream_consumption(firmware, virtual):
    """Consumption draws 0..2 bar per tick, only while the system valve is
    open, and only when the compressor is idle."""
    assert "rand() % 3" in firmware
    assert re.search(r"random\.randint\(0,\s*2\)", virtual)
    # In both, consumption is the else-branch of the compressor test.
    assert re.search(r"if\s*\(cState\).*?\}\s*else\s*\{.*?rand\(\)\s*%\s*3",
                     firmware, re.S)
    assert re.search(r"if compressor > 0:.*?else:.*?random\.randint\(0,\s*2\)",
                     virtual, re.S)


def test_blowout_vent_rate(firmware, virtual):
    """The relief valve vents 0..1 bar per tick -- slower than the compressor
    fills. A compressor stuck on therefore cannot be recovered by the valve,
    which several training modules depend on."""
    assert "rand() % 2" in firmware
    assert re.search(r"random\.randint\(0,\s*1\)", virtual)


def test_blowout_hysteresis(firmware, virtual):
    """Opens above 220 bar, stays open until the tank falls below 200."""
    assert "HPTpressure > 220" in firmware and "HPTpressure > 200" in firmware
    assert re.search(r"hpt\s*>\s*220", virtual) and re.search(r"hpt\s*>\s*200", virtual)


def test_vent_rate_is_below_compressor_rate(firmware, virtual):
    """The property the exercises rely on, stated as a test rather than left
    implicit: mean vent (0.5 bar/tick) < compressor delivery (1 bar/tick)."""
    for src, hi in ((firmware, "rand() % 2"), (virtual, "random.randint(0, 1)")):
        assert hi in src, "vent rate changed; check it still trails the compressor"
