"""
Challenge check: the student built and read Modbus/TCP frames byte by byte (packet_anatomy).

The student types four frames as hex. Nothing is sent to the PLC from here;
every frame is taken apart field by field and compared with what the
protocol and the CybICS register map require:

  read_request   a Read Holding Registers (FC 03) request for GST and HPT
                 in one go: start 1124 (%MW100), quantity 3 (1124..1126).
  read_response  the PLC's answer to *that* request: same transaction ID
                 and unit ID, length 9, FC 03, byte count 6, three words.
                 The values are live and change, so any value is accepted;
                 what is checked is that the response belongs to the request.
  write_request  one Write Multiple Registers (FC 16) request that sets
                 STOP (%MW104, 1128) and MANUAL (%MW106, 1130) to 0: start
                 1128, quantity 3, byte count 6, three zero words.
  exception      the PLC's exception response to a read of a holding
                 register it does not have: FC 0x83, exception code 02,
                 length 3.

Transaction and unit IDs are free (only the response has to match the
request), so there is no single right string to copy. Grading is all or
nothing (grade()'s default); a field is never echoed back.
"""
import re

from modules.defense_checks._answers import grade

GST_REGISTER = 1124       # %MW100
READ_QUANTITY = 3         # 1124 GST, 1125 (unused), 1126 HPT
STOP_REGISTER = 1128      # %MW104
# FC 16 writes a contiguous block. STOP is 1128 and MANUAL is 1130 (%MW106),
# so one frame that sets both covers 1128, 1129 and 1130: quantity 3, byte
# count 6, three zero words. 1129 is %MW105, declared nowhere in cybICS.st.
WRITE_QUANTITY = 3

_SEPARATORS = re.compile(r"[\s:,\-]+")


def parse_hex(text):
    """Bytes from hex typed in the usual ways ("00 07", "00:07", "0x00 0x07"), or None."""
    if not isinstance(text, str):
        return None
    cleaned = re.sub(r"0x", "", text.strip(), flags=re.IGNORECASE)
    cleaned = _SEPARATORS.sub("", cleaned)
    if not cleaned or len(cleaned) % 2 or not re.fullmatch(r"[0-9a-fA-F]+", cleaned):
        return None
    return bytes.fromhex(cleaned)


def _mbap(frame):
    """(transaction, unit, pdu) if frame is exactly one well-formed Modbus/TCP ADU."""
    if frame is None or len(frame) < 8:
        return None
    tid = int.from_bytes(frame[0:2], "big")
    proto = int.from_bytes(frame[2:4], "big")
    length = int.from_bytes(frame[4:6], "big")
    if proto != 0 or length != len(frame) - 6:
        return None
    return tid, frame[6], frame[7:]


def _word(pdu, offset):
    return int.from_bytes(pdu[offset:offset + 2], "big")


def read_request_ok(text):
    adu = _mbap(parse_hex(text))
    if not adu:
        return False
    _, _, pdu = adu
    return (len(pdu) == 5 and pdu[0] == 0x03
            and _word(pdu, 1) == GST_REGISTER and _word(pdu, 3) == READ_QUANTITY)


def read_response_ok(request_text, response_text):
    request, response = _mbap(parse_hex(request_text)), _mbap(parse_hex(response_text))
    if not request or not response or not read_request_ok(request_text):
        return False
    (req_tid, req_unit, _), (tid, unit, pdu) = request, response
    return (tid == req_tid and unit == req_unit
            and len(pdu) == 2 + 2 * READ_QUANTITY
            and pdu[0] == 0x03 and pdu[1] == 2 * READ_QUANTITY)


def write_request_ok(text):
    adu = _mbap(parse_hex(text))
    if not adu:
        return False
    _, _, pdu = adu
    return (len(pdu) == 6 + 2 * WRITE_QUANTITY and pdu[0] == 0x10
            and _word(pdu, 1) == STOP_REGISTER and _word(pdu, 3) == WRITE_QUANTITY
            and pdu[5] == 2 * WRITE_QUANTITY
            and all(b == 0 for b in pdu[6:]))


def exception_ok(text):
    adu = _mbap(parse_hex(text))
    if not adu:
        return False
    _, _, pdu = adu
    return len(pdu) == 2 and pdu[0] == 0x83 and pdu[1] == 0x02


LABELS = {
    "read_request": "Request that reads GST and HPT in one frame",
    "read_response": "The PLC's response to that request",
    "write_request": "One frame that sets STOP and MANUAL to 0",
    "exception": "The PLC's answer to a read of a register it does not have",
}


def verify(answers=None):
    answers = answers if isinstance(answers, dict) else {}
    request = answers.get("read_request", "")
    return grade(answers, {
        "read_request": read_request_ok,
        "read_response": lambda value: read_response_ok(request, value),
        "write_request": write_request_ok,
        "exception": exception_ok,
    }, labels=LABELS,
        success_message="Every byte is where it belongs. You can now read any Modbus frame "
                        "in a capture, and you know that nothing in one proves who sent it.",
        failure_message="At least one frame is not right yet. Check the MBAP length, the "
                        "function code, the start address and the quantity of each one.")
