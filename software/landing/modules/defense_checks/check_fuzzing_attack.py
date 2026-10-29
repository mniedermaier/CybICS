"""CTF check: the Modbus fuzzer exercised non-standard function codes in the last 10 minutes."""
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
        "No fuzzing traffic detected in the last 10 minutes. Run the Modbus fuzzer against the "
        "plant and verify right after.",
    }]
    return {
        "success": fired,
        "message": "Fuzzing confirmed." if fired
        else "Run the Modbus fuzzer, then verify again.",
        "checks": checks,
    }
