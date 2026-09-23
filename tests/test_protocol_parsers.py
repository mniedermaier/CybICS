"""Unit tests for the ICS protocol parsers behind the landing page's traffic view.

software/landing/modules/protocol_parsers.py turns raw payloads into the
fields the network view and the IDS dashboard display. It needs no Flask and no
running stack, so these are ordinary unit tests over real frames.

Byte order is the thing most worth pinning: Modbus/TCP and S7comm are
big-endian, OPC-UA and EtherNet/IP are little-endian, and every parser here
reads several multi-byte fields. A swapped width turns 6 into 1536 and still
returns a plausible-looking dict.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")

if not os.path.exists(os.path.join(LANDING, "modules", "protocol_parsers.py")):
    pytest.skip("landing protocol parsers not present", allow_module_level=True)

sys.path.insert(0, LANDING)
from modules import protocol_parsers as pp  # noqa: E402


# --- Modbus/TCP --------------------------------------------------------------

# Read Holding Registers, transaction 1, unit 1, 10 registers from 0.
MODBUS_READ = bytes.fromhex("000100000006010300000 00a".replace(" ", ""))


def test_modbus_fields_are_big_endian():
    got = pp.parse_modbus_tcp(MODBUS_READ)
    assert got is not None
    assert got["transaction_id"] == 1
    assert got["protocol_id"] == 0
    assert got["length"] == 6, "length read little-endian would be 1536"
    assert got["unit_id"] == 1
    assert got["function_code"] == 3
    assert got["function_name"] == "Read Holding Registers"


@pytest.mark.parametrize(
    "code,name",
    [(1, "Read Coils"), (5, "Write Single Coil"), (6, "Write Single Register"),
     (16, "Write Multiple Registers")],
)
def test_modbus_names_the_function_codes_the_rules_care_about(code, name):
    """The IDS rules act on write codes, so the UI must label them correctly."""
    frame = bytearray(MODBUS_READ)
    frame[7] = code
    assert pp.parse_modbus_tcp(bytes(frame))["function_name"] == name


def test_modbus_labels_an_unknown_function_instead_of_raising():
    frame = bytearray(MODBUS_READ)
    frame[7] = 0x5A
    got = pp.parse_modbus_tcp(bytes(frame))
    assert got["function_code"] == 0x5A
    assert got["function_name"] == "Unknown (0x5a)"


@pytest.mark.parametrize("size", [0, 1, 7])
def test_modbus_rejects_a_frame_too_short_to_hold_a_header(size):
    assert pp.parse_modbus_tcp(MODBUS_READ[:size]) is None


# --- S7comm ------------------------------------------------------------------

# TPKT 03 00 00 1f | COTP 02 f0 80 | S7 32 01 (Job Request)
S7_JOB = bytes.fromhex("0300001f02f08032010000000000080000")


def test_s7comm_reads_the_tpkt_length_big_endian():
    got = pp.parse_s7comm(S7_JOB)
    assert got is not None
    assert got["tpkt_length"] == 0x001F
    assert got["protocol_id"] == 0x32, "0x32 is the S7comm protocol identifier"
    assert got["message_type"] == 1
    assert got["message_type_name"] == "Job Request"


def test_s7comm_reports_cotp_only_when_the_s7_header_is_absent():
    """A COTP connection request carries no S7 header; saying so beats guessing."""
    got = pp.parse_s7comm(S7_JOB[:11])
    assert got == {"protocol": "S7comm", "type": "COTP"}


@pytest.mark.parametrize("size", [0, 9])
def test_s7comm_rejects_a_frame_too_short_for_tpkt_and_cotp(size):
    assert pp.parse_s7comm(S7_JOB[:size]) is None


# --- OPC-UA ------------------------------------------------------------------

# "HELF" plus a little-endian message size of 56.
OPCUA_HELLO = b"HELF" + (56).to_bytes(4, "little") + b"\x00" * 8


def test_opcua_size_is_little_endian_unlike_the_others():
    got = pp.parse_opcua(OPCUA_HELLO)
    assert got is not None
    assert got["message_type"] == "HEL"
    assert got["message_type_name"] == "Hello"
    assert got["chunk_type"] == "F"
    assert got["chunk_type_name"] == "Final"
    assert got["message_size"] == 56, "read big-endian this would be 939524096"


@pytest.mark.parametrize(
    "tag,name", [(b"ACK", "Acknowledge"), (b"ERR", "Error"), (b"MSG", "Message"),
                 (b"OPN", "Open Secure Channel"), (b"CLO", "Close Secure Channel")],
)
def test_opcua_names_every_message_type_it_claims_to_know(tag, name):
    got = pp.parse_opcua(tag + b"F" + (0).to_bytes(4, "little"))
    assert got["message_type_name"] == name


def test_opcua_passes_an_unknown_tag_through_rather_than_inventing_one():
    got = pp.parse_opcua(b"XYZF" + (0).to_bytes(4, "little"))
    assert got["message_type"] == "XYZ"
    assert got["message_type_name"] == "XYZ"
    assert got["chunk_type_name"] == "Unknown" or got["chunk_type"] == "F"


def test_opcua_survives_a_non_ascii_chunk_byte():
    """Arbitrary traffic lands here too; a high byte must not raise."""
    got = pp.parse_opcua(b"MSG\xff" + (0).to_bytes(4, "little"))
    assert got["chunk_type"] == "?"


# --- EtherNet/IP -------------------------------------------------------------

def _enip(command, length=0, session=0, status=0):
    return (command.to_bytes(2, "little") + length.to_bytes(2, "little")
            + session.to_bytes(4, "little") + status.to_bytes(4, "little")
            + b"\x00" * 12)


def test_enip_fields_are_little_endian():
    got = pp.parse_enip(_enip(0x0065, length=4, session=0x12345678, status=0))
    assert got is not None
    assert got["command"] == 0x0065
    assert got["command_name"] == "RegisterSession"
    assert got["length"] == 4
    assert got["session_handle"] == 0x12345678, "big-endian would give 0x78563412"


@pytest.mark.parametrize(
    "cmd,name", [(0x0063, "ListIdentity"), (0x006F, "SendRRData"), (0x0001, "NOP")],
)
def test_enip_names_the_commands_a_scan_would_use(cmd, name):
    assert pp.parse_enip(_enip(cmd))["command_name"] == name


def test_enip_labels_an_unknown_command_with_its_hex_value():
    assert pp.parse_enip(_enip(0xABCD))["command_name"] == "Unknown (0xabcd)"


@pytest.mark.parametrize("size", [0, 23])
def test_enip_rejects_anything_shorter_than_its_24_byte_header(size):
    assert pp.parse_enip(_enip(0x0063)[:size]) is None


# --- shared behaviour --------------------------------------------------------

@pytest.mark.parametrize(
    "parser", [pp.parse_modbus_tcp, pp.parse_s7comm, pp.parse_opcua, pp.parse_enip]
)
def test_no_parser_raises_on_hostile_input(parser):
    """These run over whatever is on the wire, including a port scan's noise."""
    for payload in (b"", b"\x00", b"\xff" * 64, bytes(range(256))):
        parser(payload)  # must not raise
