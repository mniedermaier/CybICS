"""
Challenge check: the student rebuilt the PLC's register map by observation (register_map_recon).

No document hands a student the PLC's internal memory. OpenPLC still answers
every Modbus read of its %MW area, holding registers 1024 + n, and the IEC
program keeps two words there that no HMI tag, OPC-UA node or lesson table
shows: the hysteresis latches compressorState (%MW200) and gstState (%MW202)
that software/OpenPLC/cybICS.st uses to remember whether the compressor and
the gas-storage refill are running. A read-only sweep with a time series
finds them as the only words in the %MW area that hold nothing but 0 and 1
and switch together with the plant.

The student answers four questions:
  - the wire address of the compressor latch (1224),
  - the wire address of the refill latch (1226),
  - the HPT value at which the compressor latch releases (90, observed as
    the HPT reading when the word falls back to 0; one unit either side is
    accepted because the PLC scans every 50 ms while a read takes longer),
  - where the compressor latch lives in OpenPLC's S7comm view of the same
    memory: data block DB1002, byte offset 2 * 200 = 400.

Grading is all or nothing (grade()'s default), so the two latch addresses,
which differ only in which one tracks which tank, cannot be swapped and
tried one field at a time. Nothing here touches the stack.
tests/test_register_map_recon_check.py derives every value from cybICS.st
again and fails if the program's map changes.
"""
import re

from modules.defense_checks._answers import grade, normalize, number

OPENPLC_MW_BASE = 1024            # OpenPLC: %MWn is holding register 1024 + n
COMPRESSOR_LATCH_MW = 200         # compressorState AT %MW200
REFILL_LATCH_MW = 202             # gstState AT %MW202
COMPRESSOR_LATCH = OPENPLC_MW_BASE + COMPRESSOR_LATCH_MW   # 1224
REFILL_LATCH = OPENPLC_MW_BASE + REFILL_LATCH_MW           # 1226
RELEASE_HPT = 90                  # "ELSIF hpt < 90 AND compressorState = 1"
S7_DB = 1002                      # OpenPLC's Snap7 server: %MW area is DB1002
S7_OFFSET = 2 * COMPRESSOR_LATCH_MW                        # 400, two bytes per word

LABELS = {
    "compressor_latch": "Holding register of the compressor latch (wire address)",
    "refill_latch": "Holding register of the refill latch (wire address)",
    "release_hpt": "HPT value at which the compressor latch releases",
    "s7_offset": "Byte offset of the compressor latch in DB1002",
}

# 400, DBW400, DBB400, DB1002.DBW400, "DB1002 DBW 400": all the same place.
_S7_RE = re.compile(r"^(?:db0*%d[.,:]?)?(?:db[bw])?0*(\d{1,6})$" % S7_DB)


def s7_offset(value):
    text = normalize(value).replace(" ", "")
    match = _S7_RE.match(text)
    return bool(match) and int(match.group(1)) == S7_OFFSET


def verify(answers=None):
    return grade(answers, {
        "compressor_latch": number(COMPRESSOR_LATCH),
        "refill_latch": number(REFILL_LATCH),
        "release_hpt": number(RELEASE_HPT, tolerance=1),
        "s7_offset": s7_offset,
    }, labels=LABELS,
        success_message="Your map matches the PLC's memory. You found two words no HMI "
                        "screen shows, worked out what they mean from the plant's "
                        "behaviour and located them in a second protocol.",
        failure_message="At least one answer does not match the PLC's memory yet.")
