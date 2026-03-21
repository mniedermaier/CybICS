"""
Defense check: Verify OpenPLC default password has been changed.
"""
import requests
from utils.logger import logger

OPENPLC_URL = "http://172.18.0.3:8080"
DEFAULT_USER = "openplc"
DEFAULT_PASS = "openplc"


def verify():
    """Check that the default OpenPLC credentials no longer work."""
    checks = []

    try:
        # Try login with default credentials
        session = requests.Session()
        resp = session.post(
            f"{OPENPLC_URL}/login",
            data={"username": DEFAULT_USER, "password": DEFAULT_PASS},
            allow_redirects=False,
            timeout=10
        )

        # OpenPLC redirects to dashboard (302) on success,
        # returns login page HTML (200) on failure
        default_works = resp.status_code == 302

        checks.append({
            "name": "Default password disabled",
            "passed": not default_works,
            "detail": "Default openplc/openplc credentials rejected"
            if not default_works
            else "Default credentials still work - change the password!"
        })

        success = not default_works
        message = ("OpenPLC password has been changed!"
                   if success
                   else "OpenPLC still uses default credentials. "
                        "Change the password via the OpenPLC web UI at port 8080 under Settings > Users.")

        return {"success": success, "message": message, "checks": checks}

    except requests.exceptions.ConnectionError:
        checks.append({
            "name": "OpenPLC reachable",
            "passed": False,
            "detail": "Cannot connect to OpenPLC at port 8080"
        })
        return {"success": False, "message": "Cannot reach OpenPLC service", "checks": checks}
    except Exception as e:
        logger.error(f"OpenPLC password check error: {e}")
        return {"success": False, "message": f"Verification error: {e}", "checks": checks}
