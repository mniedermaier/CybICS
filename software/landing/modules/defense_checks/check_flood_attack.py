"""CTF check: the Modbus write flood against the plant actually happened."""
from modules.defense_checks._ids_rule import rule_fired


def verify():
    fired, err, err_checks = rule_fired("modbus_flood")
    if err:
        return {"success": False, "message": err, "checks": err_checks}
    checks = [{
        "name": "Modbus write flood observed",
        "passed": fired,
        "detail": "A high-rate burst of Modbus writes to the plant was seen on the wire."
        if fired else
        "No write flood detected yet. Run the flood against the HPT register and try again.",
    }]
    return {
        "success": fired,
        "message": "Flood attack confirmed." if fired
        else "Perform the write flood, then verify again.",
        "checks": checks,
    }
