"""
Defense check: Verify the attack machine cannot reach critical services.
"""
import subprocess
from utils.logger import logger

TARGETS = [
    ("172.18.0.3", 8080, "OpenPLC Web UI"),
    ("172.18.0.3", 502, "Modbus TCP"),
    ("172.18.0.5", 4840, "OPC-UA Server"),
]


def _get_attack_container():
    """Find the attack machine container name dynamically."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=5
        )
        for name in result.stdout.strip().split('\n'):
            if 'attack' in name.lower():
                return name
    except Exception as e:
        logger.error(f"Error finding attack container: {e}")
    return None


def verify():
    """Check that the attack machine is blocked from reaching critical services."""
    checks = []

    container = _get_attack_container()
    if not container:
        checks.append({
            "name": "Attack machine container found",
            "passed": False,
            "detail": "Attack machine container not found or not running. "
                      "This challenge requires the virtual environment with the attack machine."
        })
        return {
            "success": False,
            "message": "Attack machine container not found. "
                       "Ensure the virtual environment is running.",
            "checks": checks
        }

    for ip, port, service_name in TARGETS:
        try:
            result = subprocess.run(
                ["docker", "exec", container, "nc", "-z", "-w", "3", ip, str(port)],
                capture_output=True, text=True, timeout=10
            )

            blocked = result.returncode != 0
            checks.append({
                "name": f"Block {service_name} ({ip}:{port})",
                "passed": blocked,
                "detail": f"Attack machine cannot reach {service_name}"
                if blocked
                else f"Attack machine can still reach {service_name} at {ip}:{port}"
            })
        except subprocess.TimeoutExpired:
            checks.append({
                "name": f"Block {service_name} ({ip}:{port})",
                "passed": True,
                "detail": f"Connection to {ip}:{port} timed out (blocked)"
            })
        except Exception as e:
            checks.append({
                "name": f"Block {service_name} ({ip}:{port})",
                "passed": False,
                "detail": f"Check error: {e}"
            })

    success = all(c["passed"] for c in checks)
    message = ("Network segmentation correctly applied! "
               "The attack machine is blocked from all critical services."
               if success
               else "Network segmentation incomplete. "
                    "Block the attack machine from reaching critical services.")

    return {"success": success, "message": message, "checks": checks}
