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


# ---------------------------------------------------------------------------
# The third copy: the plant sandbox in the Theory Path
# ---------------------------------------------------------------------------
# software/landing/static/js/theory-widgets.js carries the model as
# PLANT_MODEL (the numbers) and plantTick() (the order and the guards) for
# the plant-sandbox widget. The numbers are compared with the ones read out
# of the firmware, the reference, so a rate changed there without the
# sandbox fails here.
WIDGETS_JS = os.path.join(ROOT, "software", "landing", "static", "js", "theory-widgets.js")
PLC_PROGRAM = os.path.join(ROOT, "software", "OpenPLC", "cybICS.st")


@pytest.fixture(scope="module")
def sandbox():
    src = _read(WIDGETS_JS)
    start = src.index("const PLANT_MODEL = {")
    return src[start:src.index("register('plant-sandbox'", start)]


def _one(pattern, text):
    m = re.search(pattern, text)
    assert m, f"pattern {pattern!r} no longer matches; update this test with the model"
    return int(m.group(1))


def test_sandbox_constants_match_the_firmware(firmware, virtual, sandbox):
    obj = sandbox[:sandbox.index("};")]
    js = {k: int(v) for k, v in re.findall(r"^\s*(\w+):\s*(\d+),", obj, re.M)}
    # rand() % n draws 0..n-1: consumption, refill and vent, in that order.
    draws = [int(n) for n in re.findall(r"rand\(\)\s*%\s*(\d+)", firmware)]
    assert len(draws) == 3, draws
    expected = {
        "compressorGstDraw": _one(r"GSTpressure = GSTpressure - (\d+)", firmware),
        "compressorHptGain": 1 if "HPTpressure++" in firmware
        else _one(r"HPTpressure = HPTpressure \+ (\d+)", firmware),
        "compressorMinGst": _one(r"GSTpressure >= (\d+)", firmware),
        "hptMax": _one(r"HPTpressure < (\d+)", firmware),
        "consumptionMax": draws[0] - 1,
        "refillMax": draws[1] - 1,
        "ventMax": draws[2] - 1,
        "refillBelow": _one(r"GSTpressure < (\d+)", firmware),
        "blowoutOpenAbove": _one(r"HPTpressure > (\d+)\)\s*\|\|", firmware),
        "blowoutCloseAt": _one(r"\(HPTpressure > (\d+)\)\s*&\s*\(BO_sen", firmware),
        # hwio clamps both pressures to the sensor range.
        "sensorMax": _one(r"if hpt\s*>\s*(\d+):", virtual),
    }
    # The PLC scans every T#50ms; hwio ticks every 51 loops of 20 ms.
    with open(PLC_PROGRAM, encoding="utf-8") as f:
        scan_ms = _one(r"INTERVAL\s*:=\s*T#(\d+)ms", f.read())
    loops = _one(r"if delay > (\d+):", virtual) + 1
    # The loop's own pause is the last sleep in the thread (the others wait for a reconnect).
    loop_ms = round(float(re.findall(r"time\.sleep\((0\.\d+)\)", virtual)[-1]) * 1000)
    expected["scansPerTick"] = round(loops * loop_ms / scan_ms)
    assert js == expected


def test_sandbox_tick_order_and_guards(sandbox):
    """Same structure as the firmware and hwio: consumption is the else-branch
    of the compressor, then the refill, then the blow-out valve, which is
    evaluated right before it vents."""
    tick = sandbox[sandbox.index("function plantTick("):]
    assert re.search(r"if \(coils\.compressor\) \{.*?\} else \{.*?rnd\(M\.consumptionMax\)", tick, re.S)
    assert "s.hpt < M.hptMax && s.gst >= M.compressorMinGst" in tick
    assert "coils.systemValve && s.hpt - use >= 0" in tick
    assert "coils.gstSig && s.gst < M.refillBelow" in tick
    assert "s.hpt > M.blowoutOpenAbove || (s.boSen && s.hpt > M.blowoutCloseAt)" in tick
    assert "s.hpt - vent >= 0" in tick
    order = [tick.index(f"rnd(M.{k})") for k in ("consumptionMax", "refillMax", "ventMax")]
    assert order == sorted(order)
    assert tick.index("M.compressorGstDraw") < tick.index("rnd(M.refillMax)")


def test_sandbox_drives_the_plc_rules_of_the_scan_cycle_widget():
    """The sandbox's automatic mode is plcScan(), which test_theory_content.py
    compares with cybICS.st; it must not grow rules of its own."""
    src = _read(WIDGETS_JS)
    widget = src[src.index("register('plant-sandbox'"):]
    assert "plcScan({ hpt: seen, gst: s.gst, stop: false }, plc)" in widget
    assert "plcScan({ stop: true }, plc)" in widget
    assert not re.search(r"\b(60|90|240)\b", widget.split("function control()", 1)[1].split("function advance()", 1)[0])
