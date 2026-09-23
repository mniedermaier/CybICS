"""Read the CybICS board revision from the version straps on the Pi header.

From board v1.1 the PCB encodes its revision as a 5-bit code, once for each
controller.  The Raspberry Pi's copy is R46-R50 on GPIO17, 27, 22, 23 and 10
(BCM), header pins 11, 13, 15, 16 and 19.  Each bit is one 10k resistor to GND
read against the internal pull-up: **fitted = 0, omitted = 1**.

This mirrors software/stm32/src/hw_version.c, which does the same job for the
STM32's copy on PC11-PC15.  The two must agree on the encoding; the
authoritative table is in hardware/README.md#version-coding.

A pre-v1.1 board has no strap footprints at all, so every pin floats high and
the code reads 0b11111.  That is why 31 means "v1.0, or a board whose straps
were never populated" and is never assigned to a real revision.
"""
import logging

logger = logging.getLogger(__name__)

# Bit 0 first, so STRAP_PINS[i] is bit i of the code.  BCM numbering.
STRAP_PINS = (17, 27, 22, 23, 10)

CODE_NO_STRAPS = 0b11111
CODE_V1_1 = 0b00001

_REVISIONS = {
    CODE_NO_STRAPS: "v1.0",
    CODE_V1_1: "v1.1",
}

# The newest revision this code knows about.  Codes are only ever assigned
# going forward, so an unrecognised one is newer hardware, not older.
NEWEST_KNOWN = "v1.1"


def decode(code):
    """Map a 5-bit strap code to a revision name."""
    return _REVISIONS.get(code)


def read(gpio):
    """Read the straps and return (code, name, straps_present).

    `gpio` is the RPi.GPIO module, already in BCM mode.  Pass it in rather than
    importing it here so this stays testable off a Pi.

    `straps_present` is False when every strap reads high, which is either a
    pre-v1.1 board or a v1.1 board assembled without them -- the two are
    indistinguishable by design, and the caller should not claim more than that.
    """
    code = 0
    for bit, pin in enumerate(STRAP_PINS):
        gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)
        if gpio.input(pin):
            code |= 1 << bit

    straps_present = code != CODE_NO_STRAPS
    name = decode(code)
    if name is None:
        # Python's %-formatting has no binary conversion, so the bit pattern
        # is rendered with format() before it reaches the log call.
        logger.warning(
            "strap code %d (0b%s) is not a revision this build knows; "
            "treating the board as %s or newer",
            code, format(code, "05b"), NEWEST_KNOWN
        )
        name = NEWEST_KNOWN
    return code, name, straps_present


def describe(code, name, straps_present):
    """A one-line summary for the log and for the status file."""
    if not straps_present:
        return "%s (no straps fitted: pre-v1.1, or v1.1 with the straps left off)" % name
    return "%s (strap code %d, 0b%s)" % (name, code, format(code, "05b"))


def status_payload(code, name, straps_present):
    """The status file the landing page reads.

    Built here rather than in hardwareIO.py so the contract between the writer
    and software/landing/utils/hardware.py can be tested without importing
    RPi.GPIO, smbus or pymodbus.
    """
    return {
        "revision": name,
        "strap_code": code,
        "straps_present": straps_present,
        "description": describe(code, name, straps_present),
        "source": "raspberry-pi-straps",
    }
