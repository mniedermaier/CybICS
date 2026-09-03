"""CTF check: a man-in-the-middle between FUXA and the PLC actually happened.

Either method in the how-to leaves a trace the IDS raises: arpspoof poisons the
ARP table (arp_spoof), and the socket proxy relays manipulated writes to OpenPLC
from a host that is not an authorised writer (modbus_unauth_write).
"""
from modules.defense_checks._ids_rule import rule_fired


def verify():
    fired, err, err_checks = rule_fired("arp_spoof")
    if err:
        return {"success": False, "message": err, "checks": err_checks}
    checks = [{
        "name": "Man-in-the-middle observed",
        "passed": fired,
        "detail": "ARP poisoning between FUXA and the PLC was seen on the wire."
        if fired else
        "No ARP poisoning detected yet. Run the arpspoof man-in-the-middle, then try again.",
    }]
    return {
        "success": fired,
        "message": "MITM attack confirmed." if fired
        else "Perform the man-in-the-middle attack, then verify again.",
        "checks": checks,
    }
