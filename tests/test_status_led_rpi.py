"""Unit tests for the Raspberry Pi's heartbeat LED drive.

software/hwio-raspberry/status_led.py takes the GPIO module as an argument
rather than importing it, so these run anywhere -- no Pi, no RPi.GPIO, no
running stack.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HWIO_DIR = os.path.join(ROOT, "software", "hwio-raspberry")

if not os.path.exists(os.path.join(HWIO_DIR, "status_led.py")):
    pytest.skip("hwio-raspberry/status_led.py not present", allow_module_level=True)

sys.path.insert(0, HWIO_DIR)
import status_led  # noqa: E402


class FakeGPIO:
    """Enough of RPi.GPIO for one pin, recording every call in order."""

    OUT = "out"
    IN = "in"
    HIGH = 1
    PUD_DOWN = "pud_down"

    def __init__(self):
        self.calls = []

    def output(self, pin, level):
        self.calls.append(("output", pin, level))

    def setup(self, pin, direction, initial=None, pull_up_down=None):
        self.calls.append(("setup", pin, direction, initial, pull_up_down))


def test_v1_0_drives_the_pin_directly():
    gpio = FakeGPIO()
    led = status_led.HeartbeatLed(gpio, 4, status_led.dims("v1.0"))
    led.set(1)
    led.set(0)
    assert gpio.calls == [("output", 4, True), ("output", 4, False)]


def test_v1_1_lights_through_the_pull_down():
    """On is an input with the pull-down, never the pin driven low."""
    gpio = FakeGPIO()
    led = status_led.HeartbeatLed(gpio, 4, status_led.dims("v1.1"))
    led.set(0)
    led.set(1)
    assert gpio.calls == [
        ("setup", 4, "in", None, "pud_down"),
        ("setup", 4, "out", 1, None),
    ]


def test_repeated_level_does_not_touch_the_pin():
    """hardwareIO.py writes the coil every 20 ms; only a change may reach the pin."""
    gpio = FakeGPIO()
    led = status_led.HeartbeatLed(gpio, 4, True)
    for _ in range(10):
        led.set(0)
    assert len(gpio.calls) == 1


@pytest.mark.parametrize("revision,dim", [
    ("v1.0", False),
    ("v1.1", True),
    # The straps could not be read: keep what the pin always did.
    (None, False),
])
def test_which_revisions_dim(revision, dim):
    assert status_led.dims(revision) is dim
