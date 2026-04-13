"""
Defense check: Verify FUXA default admin password has been changed.
"""
import requests
from utils.logger import logger

FUXA_URL = "http://172.18.0.4:1881"
DEFAULT_USER = "admin"
DEFAULT_PASS = "123456"


def verify():
    """Check that the default FUXA admin credentials no longer work."""
    checks = []

    try:
        resp = requests.post(
            f"{FUXA_URL}/api/signin",
            json={"username": DEFAULT_USER, "password": DEFAULT_PASS},
            timeout=10
        )

        # FUXA returns 200 with user data on success,
        # or 200 with error message on failure
        default_works = (resp.status_code == 200
                         and "error" not in resp.text.lower()
                         and resp.text.strip() != "")

        checks.append({
            "name": "Default password disabled",
            "passed": not default_works,
            "detail": "Default admin/123456 credentials rejected"
            if not default_works
            else "Default credentials still work - change the password!"
        })

        success = not default_works
        message = ("FUXA admin password has been changed!"
                   if success
                   else "FUXA still uses the default admin password (123456). "
                        "Change it in the FUXA settings.")

        return {"success": success, "message": message, "checks": checks}

    except requests.exceptions.ConnectionError:
        checks.append({
            "name": "FUXA reachable",
            "passed": False,
            "detail": "Cannot connect to FUXA at port 1881"
        })
        return {"success": False, "message": "Cannot reach FUXA service", "checks": checks}
    except Exception as e:
        logger.error(f"FUXA password check error: {e}")
        return {"success": False, "message": f"Verification error: {e}", "checks": checks}
