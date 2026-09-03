"""The framing of the i2c messages between the STM32 and the Pi.

This is the contract two implementations have to agree on: nanopb on the STM32
writes a length byte followed by a serialised message, and hardwareIO reads that
back. #133 failed precisely here — it sent a zero-padded buffer with no length,
which can never be decoded, and the failure was swallowed into a warning while
the plant reported zero pressure. Nothing tested it, so nothing said so.

Runs without hardware: the bindings are generated from the .proto in conftest,
and the STM32 side is modelled by the same operations nanopb performs.
"""
import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

from conftest import protobuf_available

HWIO = Path(__file__).resolve().parent.parent / "software" / "hwio-raspberry" / "hardwareIO.py"

# Sizes nanopb derives from cybics.options: uid is capped at 6 bytes and
# ip_addr at 15, giving a 12-byte PressureData and a 14-byte DeviceInfo, each
# with a length byte in front. The Pi's reads have to match, or it either
# truncates a message or reads past the buffer.
PRESSURE_BUFFER = 13
DEVICE_INFO_BUFFER = 15
RX_DATA = 20

# nanopb caps ip_addr at max_size:16 in cybics.options, and that count includes
# the null terminator, so fifteen characters are usable and the encoded message
# reaches seventeen bytes. The STM32 compares the length prefix against this, so
# anything longer is dropped without a word.
IP_ADDRESS_MAX_ENCODED = 17


@pytest.fixture(scope="module")
def pb():
    # A failure here is a broken environment, not a reason to pass quietly.
    # grpcio-tools is in tests/requirements.txt precisely so this works, and a
    # skip would let the framing go untested behind a green tick.
    if not protobuf_available():
        pytest.fail(
            "The protobuf bindings could not be generated from "
            "software/stm32/proto/cybics.proto. Install tests/requirements.txt, "
            "which pins grpcio-tools for exactly this.")
    import cybics_pb2
    return cybics_pb2


@pytest.fixture(scope="module")
def hwio():
    """hardwareIO with the Pi-only modules stubbed; cybics_pb2 is the real one."""
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


def frame(message, buffer_size):
    """What the STM32 does: zeroed buffer, encode from [1], length into [0]."""
    payload = message.SerializeToString()
    assert len(payload) <= buffer_size - 1, (
        f"{len(payload)} bytes do not fit the {buffer_size - 1} the STM32 has")
    buf = bytearray(buffer_size)
    buf[0] = len(payload)
    buf[1:1 + len(payload)] = payload
    return list(buf)


@pytest.mark.parametrize("gst, hpt", [(0, 0), (1, 0), (42, 99), (255, 255), (0, 255)])
def test_pressure_survives_the_round_trip(hwio, pb, gst, hpt):
    wire = frame(pb.PressureData(gst_pressure=gst, hpt_pressure=hpt), PRESSURE_BUFFER)
    out = pb.PressureData()
    hwio.unframe(wire, out, ("gst_pressure", "hpt_pressure"))
    assert (out.gst_pressure, out.hpt_pressure) == (gst, hpt)


@pytest.mark.parametrize("mode", [0, 1])
def test_device_info_yields_the_dataID_the_wifi_code_expects(hwio, pb, mode):
    """thread_network indexes dataID[12] for the mode, so the shape matters as
    much as the content."""
    uid = bytes.fromhex("0102030405ff")
    wire = frame(pb.DeviceInfo(uid=uid, wifi_mode=mode), DEVICE_INFO_BUFFER)
    out = pb.DeviceInfo()
    hwio.unframe(wire, out, ("wifi_mode",))

    dataID = "".join(f"{b:02x}" for b in out.uid) + str(out.wifi_mode)
    assert len(dataID) == 13
    assert dataID[12] == str(mode)


def test_zero_pressure_is_not_an_empty_message(pb):
    """The reason the scalars carry explicit presence. Without it a reading of
    zero encodes to nothing, and an unwritten buffer looks exactly the same."""
    wire = pb.PressureData(gst_pressure=0, hpt_pressure=0).SerializeToString()
    assert wire, "a genuine zero reading must still put something on the wire"

    nothing_sent = pb.PressureData()
    nothing_sent.ParseFromString(b"")
    assert not nothing_sent.HasField("gst_pressure")


def test_an_unwritten_buffer_is_rejected(hwio, pb):
    """A buffer the STM32 has not filled in yet reads as length 0. That must be
    an error, not a reading of zero bar."""
    with pytest.raises(ValueError, match="missing"):
        hwio.unframe([0] * PRESSURE_BUFFER, pb.PressureData(),
                     ("gst_pressure", "hpt_pressure"))


def test_a_truncated_message_is_rejected(hwio, pb):
    """A torn read can cut a message short. Presence makes the missing tail
    visible instead of it reading back as zero."""
    wire = frame(pb.PressureData(gst_pressure=42, hpt_pressure=99), PRESSURE_BUFFER)
    wire[0] = 2  # claim only the first field is there

    with pytest.raises(ValueError, match="missing hpt_pressure"):
        hwio.unframe(wire, pb.PressureData(), ("gst_pressure", "hpt_pressure"))


def test_a_length_beyond_the_buffer_is_rejected(hwio, pb):
    """Python truncates an over-long slice instead of raising, so the length has
    to be checked rather than trusted."""
    wire = frame(pb.PressureData(gst_pressure=42, hpt_pressure=99), PRESSURE_BUFFER)
    wire[0] = 200

    with pytest.raises(ValueError, match="exceeds"):
        hwio.unframe(wire, pb.PressureData(), ("gst_pressure", "hpt_pressure"))


@pytest.mark.parametrize("ip", ["10.0.0.1", "192.168.1.100", "192.168.100.100", "255.255.255.255"])
def test_the_longest_ip_survives_both_limits(pb, ip):
    """Two separate ceilings, and the fifteen-character addresses used to fail
    the first one: max_size was 15, which leaves fourteen characters once the
    null terminator is counted, so the STM32 rejected 192.168.100.100 silently.
    """
    payload = pb.IPAddress(ip_addr=ip).SerializeToString()

    assert len(payload) <= IP_ADDRESS_MAX_ENCODED, (
        f"{ip} encodes to {len(payload)} bytes, past what the STM32 accepts")
    # Plus the register byte and the length prefix, into RxData.
    assert 2 + len(payload) <= RX_DATA


def test_messages_fit_the_buffers_the_stm32_declares(pb):
    """Worst-case encodings, which is what nanopb sizes the buffers for."""
    biggest_pressure = pb.PressureData(gst_pressure=0xFFFFFFFF, hpt_pressure=0xFFFFFFFF)
    assert len(biggest_pressure.SerializeToString()) <= PRESSURE_BUFFER - 1

    biggest_info = pb.DeviceInfo(uid=b"\xff" * 6, wifi_mode=0xFFFFFFFF)
    assert len(biggest_info.SerializeToString()) <= DEVICE_INFO_BUFFER - 1
