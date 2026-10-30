"""
Challenge check: the student mapped the plant from FUXA's project (hmi_project_recon).

FUXA, the HMI on 172.18.0.4:1881, sends its whole project to every browser
that opens it: GET /api/project answers without a login, because the HMI
page needs it to draw the views. The project names the PLC connection, every
tag with its Modbus address, and which button writes which tag. FUXA 1.2.6
never removes devices, tags or view items from it: for a user without
permission it only marks items hidden or disables their buttons.

The student answers four questions that come straight out of that file:
the PLC endpoint the HMI polls, the holding register the STOP / SHUTDOWN
button writes and the coil the SystemView "Comp." button toggles (both as
sent on the wire, i.e. FUXA's 1-based address minus one), and the FUXA tag
ID of HPT, which is what FUXA's own /api/getTagValue needs to read a live
value. The tag ID is in no document; it is the part that proves the project
was read rather than the register map recalled.

Grading is all or nothing (grade()'s default): a single field with few
possible values cannot be found one at a time. The module does not touch
the stack. The expected values mirror software/FUXA/fuxa-project.json, which
the landing container does not carry; tests/test_hmi_project_recon_check.py
derives them from that file again and fails if a re-export changes them.
"""
from modules.defense_checks._answers import grade, number, one_of

# What software/FUXA/fuxa-project.json says (see the module docstring).
PLC_ENDPOINTS = ("openplc:502", "172.18.0.3:502")
STOP_REGISTER = 1128      # FUXA tag "stop", address 1129, holding registers (400000)
COMPRESSOR_COIL = 1       # FUXA tag "compressor", address 2, coils (000000)
HPT_TAG_ID = "t_e76df10e-a85c4674"

LABELS = {
    "plc": "PLC endpoint the HMI polls",
    "stop_register": "Holding register the STOP / SHUTDOWN button writes",
    "compressor_coil": "Coil the Comp. button toggles",
    "hpt_tag_id": "FUXA tag ID of HPT",
}


def verify(answers=None):
    return grade(answers, {
        "plc": one_of(*PLC_ENDPOINTS),
        "stop_register": number(STOP_REGISTER),
        "compressor_coil": number(COMPRESSOR_COIL),
        "hpt_tag_id": one_of(HPT_TAG_ID),
    }, labels=LABELS,
        success_message="Your map of the plant matches the HMI's. Everything you needed "
                        "to stop the plant or switch the compressor came from a file "
                        "the HMI hands to anyone who opens it.",
        failure_message="At least one answer does not match the HMI project yet.")
