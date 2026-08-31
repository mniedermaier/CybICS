"""
Defense check: Verify IDS is running and actively detecting threats.
"""
import requests
from utils.logger import logger

IDS_URL = "http://localhost:8443"


def verify():
    """Check that the IDS is running, capturing, and has detected multiple attack types."""
    checks = []

    try:
        # Check 1: IDS is running
        try:
            resp = requests.get(f"{IDS_URL}/health", timeout=5)
            ids_running = resp.status_code == 200
        except requests.exceptions.ConnectionError:
            ids_running = False

        checks.append({
            "name": "IDS is running",
            "passed": ids_running,
            "detail": "IDS service is operational"
            if ids_running
            else "IDS service is not responding at port 8443"
        })

        if not ids_running:
            return {
                "success": False,
                "message": "IDS is not running. Start it from the IDS dashboard.",
                "checks": checks
            }

        # Check 2: IDS is actively capturing packets
        resp = requests.get(f"{IDS_URL}/api/status", timeout=5)
        status = resp.json()
        is_capturing = status.get("active", False)
        checks.append({
            "name": "IDS detection active",
            "passed": is_capturing,
            "detail": "IDS is actively monitoring network traffic"
            if is_capturing
            else "IDS packet capture is not started"
        })

        # Check 3: Multiple detection rules have been triggered
        resp = requests.get(f"{IDS_URL}/api/rules/stats", timeout=5)
        rules_data = resp.json()

        # Count rules that have triggered at least once
        if isinstance(rules_data, dict):
            active_rules = sum(
                1 for r in rules_data.values()
                if isinstance(r, dict) and r.get("count", 0) > 0
            )
        else:
            active_rules = 0

        checks.append({
            "name": "Multiple detection rules triggered",
            "passed": active_rules >= 3,
            "detail": f"{active_rules} rule(s) have triggered alerts (need at least 3)"
        })

        success = all(c["passed"] for c in checks)
        message = ("IDS is properly configured and detecting threats!"
                   if success
                   else "IDS needs further tuning. Ensure it is running, "
                        "capturing packets, and has detected at least 3 different attack types.")

        return {"success": success, "message": message, "checks": checks}

    except Exception as e:
        logger.error(f"IDS tuning check error: {e}")
        return {"success": False, "message": f"Verification error: {e}", "checks": checks}
