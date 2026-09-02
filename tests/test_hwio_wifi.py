"""Which WiFi profile hwio-raspberry picks for station mode.

The device ships with two NetworkManager profiles: the 'cybics' access point,
and 'cybics-station' as a starting point for the network the user wants to join.
Choosing between those and anything the user adds is what decides whether the
WiFi button works, so it is worth pinning down.

hardwareIO imports Raspberry Pi hardware modules and touches GPIO and i2c at
import time, none of which exists on a CI runner, so those are stubbed before
the import.
"""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

HWIO = Path(__file__).resolve().parent.parent / "software" / "hwio-raspberry" / "hardwareIO.py"


@pytest.fixture(scope="module")
def hwio():
    """Import hardwareIO with the hardware-facing modules stubbed out."""
    stubs = {
        name: mock.MagicMock()
        for name in ("RPi", "RPi.GPIO", "smbus", "smbus2", "nmcli",
                     "pymodbus", "pymodbus.client")
    }
    with mock.patch.dict(sys.modules, stubs):
        spec = importlib.util.spec_from_file_location("hardwareIO", HWIO)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def connections(*specs):
    """Build what nmcli.connection() returns: (name, conn_type) pairs."""
    return [SimpleNamespace(name=n, conn_type=t, device="wlan0") for n, t in specs]


AP = ("cybics", "wifi")
SHIPPED = ("cybics-station", "wifi")
USER = ("MyHomeNetwork", "wifi")
ETHERNET = ("Wired connection 1", "ethernet")


@pytest.mark.parametrize("listed, expected", [
    # Nothing but the access point: station mode is impossible, and saying so
    # beats silently picking the AP and fighting over the radio.
    ([AP], None),
    ([AP, ETHERNET], None),
    # Only the shipped placeholder: use it.
    ([AP, SHIPPED], "cybics-station"),
    # A profile the user added beats the placeholder, whichever order nmcli
    # happens to list them in. This is the case the old code got wrong: it took
    # the first non-AP profile and stopped.
    ([AP, SHIPPED, USER], "MyHomeNetwork"),
    ([AP, USER, SHIPPED], "MyHomeNetwork"),
    # Ethernet is not a candidate.
    ([AP, ETHERNET, SHIPPED], "cybics-station"),
])
def test_picks_the_right_profile(hwio, listed, expected):
    with mock.patch.object(hwio.nmcli, "connection", return_value=connections(*listed)):
        assert hwio.detect_station_connection() == expected


def test_a_profile_added_later_is_picked_up(hwio):
    """The documented way to configure station WiFi is to add a profile on a
    running device, so the lookup has to happen again rather than once."""
    before = connections(AP, SHIPPED)
    after = connections(AP, SHIPPED, USER)

    with mock.patch.object(hwio.nmcli, "connection", return_value=before):
        assert hwio.detect_station_connection() == "cybics-station"
    with mock.patch.object(hwio.nmcli, "connection", return_value=after):
        assert hwio.detect_station_connection() == "MyHomeNetwork"


def test_a_broken_nmcli_yields_no_profile(hwio):
    """nmcli failing must not take the network thread down with it."""
    with mock.patch.object(hwio.nmcli, "connection", side_effect=RuntimeError("nmcli is unhappy")):
        assert hwio.detect_station_connection() is None
