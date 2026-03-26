"""
Defense check: Verify firewall rules restrict Modbus (port 502) access on OpenPLC.
"""
import subprocess
import socket
from utils.logger import logger

OPENPLC_IP = "172.18.0.3"
MODBUS_PORT = 502


def _get_openplc_container():
    """Find the OpenPLC container name dynamically."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=5
        )
        for name in result.stdout.strip().split('\n'):
            if 'openplc' in name.lower():
                return name
    except Exception as e:
        logger.error(f"Error finding OpenPLC container: {e}")
    return None


def verify():
    """Check that iptables rules restrict Modbus access on the OpenPLC container."""
    checks = []

    # Check 1: Verify iptables rules exist on the OpenPLC container
    container = _get_openplc_container()
    if not container:
        checks.append({
            "name": "OpenPLC container found",
            "passed": False,
            "detail": "Cannot find a running OpenPLC container"
        })
        return {"success": False, "message": "OpenPLC container not found", "checks": checks}

    try:
        result = subprocess.run(
            ["docker", "exec", container, "iptables", "-L", "INPUT", "-n"],
            capture_output=True, text=True, timeout=10
        )
        has_rules = ("DROP" in result.stdout or "REJECT" in result.stdout)
        checks.append({
            "name": "Firewall rules configured",
            "passed": has_rules,
            "detail": "iptables rules with DROP/REJECT found on OpenPLC"
            if has_rules
            else "No restrictive iptables rules found on OpenPLC container"
        })
    except Exception as e:
        checks.append({
            "name": "Firewall rules configured",
            "passed": False,
            "detail": f"Could not check iptables: {e}"
        })

    # Check 2: Verify Modbus port is NOT accessible from this host (unauthorized source)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result_code = sock.connect_ex((OPENPLC_IP, MODBUS_PORT))
        sock.close()

        blocked = result_code != 0
        checks.append({
            "name": "Modbus blocked from unauthorized hosts",
            "passed": blocked,
            "detail": "Port 502 is blocked from this host"
            if blocked
            else "Port 502 is still accessible from unauthorized hosts"
        })
    except Exception as e:
        # Connection failed = good, it's blocked
        checks.append({
            "name": "Modbus blocked from unauthorized hosts",
            "passed": True,
            "detail": f"Connection attempt failed (blocked): {e}"
        })

    success = all(c["passed"] for c in checks)
    message = ("Modbus firewall rules correctly applied!"
               if success
               else "Firewall configuration incomplete. "
                    "Add iptables rules on the OpenPLC container to restrict port 502 access.")

    return {"success": success, "message": message, "checks": checks}
