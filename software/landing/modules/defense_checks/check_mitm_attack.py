"""CTF check: a man-in-the-middle between FUXA and the PLC actually happened.

The challenge asks for ARP poisoning (arpspoof or arp_spoof.py), which the IDS
raises as arp_spoof: an address announced by a second MAC that also answers
for another address. A container recreated with a new MAC does not raise it.
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
