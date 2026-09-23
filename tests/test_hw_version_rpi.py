"""Unit tests for the Raspberry Pi's board-revision detection.

software/hwio-raspberry/hw_version.py takes the GPIO module as an argument
rather than importing it, so these run anywhere -- no Pi, no RPi.GPIO, no
running stack.

The encoding these check against is the table in
hardware/README.md#version-coding, which software/stm32/src/hw_version.c
implements for the STM32's copy of the same straps.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HWIO_DIR = os.path.join(ROOT, "software", "hwio-raspberry")

if not os.path.exists(os.path.join(HWIO_DIR, "hw_version.py")):
    pytest.skip("hwio-raspberry/hw_version.py not present", allow_module_level=True)

sys.path.insert(0, HWIO_DIR)
import hw_version  # noqa: E402


class FakeGPIO:
    """Enough of RPi.GPIO to read straps, recording how it was asked."""

    IN = "in"
    PUD_UP = "pud_up"

    def __init__(self, levels):
        self.levels = levels
        self.configured = {}

    def setup(self, pin, direction, pull_up_down=None):
        self.configured[pin] = (direction, pull_up_down)

    def input(self, pin):
        return self.levels[pin]


def _read(bits):
    """bits[i] is the level of strap bit i (1 = omitted, 0 = fitted)."""
    levels = {pin: bits[i] for i, pin in enumerate(hw_version.STRAP_PINS)}
    gpio = FakeGPIO(levels)
    return gpio, hw_version.read(gpio)


def test_straps_are_read_with_the_internal_pull_up():
    """Without the pull-up a fitted resistor and an open pin read the same."""
    gpio, _ = _read([1, 1, 1, 1, 1])
    assert set(gpio.configured) == set(hw_version.STRAP_PINS)
    for pin, (direction, pull) in gpio.configured.items():
        assert direction == FakeGPIO.IN, f"pin {pin} was not configured as an input"
        assert pull == FakeGPIO.PUD_UP, f"pin {pin} was read without the pull-up"


def test_bit_order_is_least_significant_first():
    """STRAP_PINS[i] is bit i; getting this backwards inverts the code."""
    _, (code, _, _) = _read([1, 0, 0, 0, 0])
    assert code == 1, "the first pin must contribute bit 0"
    _, (code, _, _) = _read([0, 0, 0, 0, 1])
    assert code == 16, "the last pin must contribute bit 4"


def test_all_straps_fitted_is_not_a_revision_yet():
    """Code 0 is unassigned, so it is treated as newer than anything known."""
    _, (code, name, present) = _read([0, 0, 0, 0, 0])
    assert code == 0
    assert present is True
    assert name == hw_version.NEWEST_KNOWN


def test_v1_1_is_one_omitted_resistor():
    _, (code, name, present) = _read([1, 0, 0, 0, 0])
    assert code == hw_version.CODE_V1_1
    assert name == "v1.1"
    assert present is True


def test_no_straps_reads_as_v1_0():
    """A pre-v1.1 board has no strap footprints, so every pin floats high."""
    _, (code, name, present) = _read([1, 1, 1, 1, 1])
    assert code == hw_version.CODE_NO_STRAPS == 31
    assert name == "v1.0"
    assert present is False


def test_an_unknown_code_is_treated_as_the_newest_known_revision():
    """Codes are assigned going forward, so an unknown one is newer hardware.

    Falling back to v1.0 instead would be the damaging guess: v1.0 is the one
    revision whose front panel wiring differs.
    """
    _, (code, name, present) = _read([0, 1, 0, 1, 0])
    assert code == 10
    assert hw_version.decode(code) is None
    assert name == hw_version.NEWEST_KNOWN
    assert present is True


def test_no_straps_is_described_honestly():
    """31 cannot distinguish a v1.0 board from a v1.1 with the straps left off."""
    text = hw_version.describe(31, "v1.0", False)
    assert "no straps fitted" in text
    assert "v1.1" in text, "the description must admit the ambiguity"


def test_the_pins_match_the_hardware_documentation():
    """hardware/README.md is the authoritative table; drift there is a wiring bug."""
    readme = os.path.join(ROOT, "hardware", "README.md")
    if not os.path.exists(readme):
        pytest.skip("hardware/README.md not present")
    with open(readme, encoding="utf-8") as fh:
        text = fh.read()
    for bit, pin in enumerate(hw_version.STRAP_PINS):
        assert f"GPIO{pin}" in text, (
            f"bit {bit} is read from GPIO{pin}, which hardware/README.md does not mention"
        )


# --- the contract between the Pi and the landing page ------------------------
#
# hwio-raspberry writes a status file; the landing page reads it. The two live
# in different containers, so nothing but a test keeps their idea of the file
# in step. These exercise the real writer payload against the real reader.

LANDING_UTILS = os.path.join(ROOT, "software", "landing", "utils")

if os.path.exists(os.path.join(LANDING_UTILS, "hardware.py")):
    sys.path.insert(0, LANDING_UTILS)
    import hardware as landing_hardware  # noqa: E402
else:  # pragma: no cover
    landing_hardware = None


needs_landing = pytest.mark.skipif(
    landing_hardware is None, reason="software/landing/utils/hardware.py not present"
)


@needs_landing
def test_the_landing_page_reads_what_the_pi_writes(tmp_path):
    """The writer's payload must survive the round trip through the file."""
    _, (code, name, present) = _read([1, 0, 0, 0, 0])
    state = tmp_path / "hardware.json"
    state.write_text(json.dumps(hw_version.status_payload(code, name, present)))

    reported = landing_hardware.read_hardware_version(str(state))
    assert reported["detected"] is True
    assert reported["revision"] == "v1.1"
    assert reported["strap_code"] == hw_version.CODE_V1_1
    assert reported["straps_present"] is True
    assert "v1.1" in reported["description"]


@needs_landing
def test_a_board_without_straps_round_trips_honestly(tmp_path):
    """31 must not be dressed up as a confirmed v1.0 in the UI."""
    _, (code, name, present) = _read([1, 1, 1, 1, 1])
    state = tmp_path / "hardware.json"
    state.write_text(json.dumps(hw_version.status_payload(code, name, present)))

    reported = landing_hardware.read_hardware_version(str(state))
    assert reported["straps_present"] is False
    assert "no straps fitted" in reported["description"]


@needs_landing
def test_no_file_means_the_virtual_stack_not_an_error(tmp_path):
    """The Docker-only stack has no board; that is normal, not a failure."""
    reported = landing_hardware.read_hardware_version(str(tmp_path / "absent.json"))
    assert reported["detected"] is False
    assert reported["revision"] is None
    assert "virtual" in reported["description"]


@needs_landing
@pytest.mark.parametrize("content", ["", "{", "null", "[]", '{"source": "x"}'])
def test_a_damaged_status_file_does_not_take_the_settings_panel_down(tmp_path, content):
    """A half-written or truncated file must degrade, not raise."""
    state = tmp_path / "hardware.json"
    state.write_text(content)
    reported = landing_hardware.read_hardware_version(str(state))
    assert reported["detected"] is False
    assert reported["revision"] is None
