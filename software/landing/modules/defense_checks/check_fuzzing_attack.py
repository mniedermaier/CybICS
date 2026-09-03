"""CTF check: the Modbus fuzzer exercised non-standard function codes."""
from modules.defense_checks._ids_rule import rule_fired


def verify():
    fired, err, err_checks = rule_fired("modbus_diagnostic")
    if err:
        return {"success": False, "message": err, "checks": err_checks}
    checks = [{
        "name": "Malformed / non-standard Modbus traffic observed",
        "passed": fired,
        "detail": "The plant received diagnostic or non-standard Modbus function codes."
        if fired else
        "No fuzzing traffic detected yet. Run the Modbus fuzzer against the plant and try again.",
    }]
    return {
        "success": fired,
        "message": "Fuzzing confirmed." if fired
        else "Run the Modbus fuzzer, then verify again.",
        "checks": checks,
    }
