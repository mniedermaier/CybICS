"""
Defense check: Verify that target containers have iptables rules blocking the attack machine.
"""
import subprocess
from utils.logger import logger

ATTACK_IP = "172.18.0.100"

# (container keyword, ip, port, service name)
TARGETS = [
    ("openplc", "172.18.0.3", 8080, "OpenPLC Web UI"),
    ("openplc", "172.18.0.3", 502, "Modbus TCP"),
    ("opcua", "172.18.0.5", 4840, "OPC-UA Server"),
]


def _find_container(keyword):
    """Find a container name containing the keyword."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=5
        )
        for name in result.stdout.strip().split('\n'):
            if keyword in name.lower():
                return name
    except Exception as e:
        logger.error(f"Error finding container '{keyword}': {e}")
    return None


def _check_iptables_rule(container, source_ip):
    """Check if the container has an iptables DROP/REJECT rule for the given source IP."""
    try:
        result = subprocess.run(
            ["docker", "exec", container, "iptables", "-L", "INPUT", "-n"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split('\n'):
            if source_ip in line and ('DROP' in line or 'REJECT' in line):
                return True
    except Exception as e:
        logger.error(f"Error checking iptables on {container}: {e}")
    return False


def verify():
    """Check that target containers have firewall rules blocking the attack machine."""
    checks = []

    # Group targets by container keyword to avoid repeated lookups
    containers = {}
    for keyword, ip, port, service_name in TARGETS:
        if keyword not in containers:
            containers[keyword] = _find_container(keyword)

    for keyword, ip, port, service_name in TARGETS:
        container = containers.get(keyword)
        if not container:
            checks.append({
                "name": f"Block {service_name} ({ip}:{port})",
                "passed": False,
                "detail": f"Container '{keyword}' not found or not running"
            })
            continue

        has_rule = _check_iptables_rule(container, ATTACK_IP)
        checks.append({
            "name": f"Block {service_name} ({ip}:{port})",
            "passed": has_rule,
            "detail": f"iptables DROP rule for {ATTACK_IP} found on {container}"
            if has_rule
            else f"No iptables rule blocking {ATTACK_IP} on {container}"
        })

    success = all(c["passed"] for c in checks)
    message = ("Network segmentation correctly applied! "
               "The target containers block traffic from the attack machine."
               if success
               else "Network segmentation incomplete. "
                    "Add iptables rules on the target containers to block the attack machine.")

    return {"success": success, "message": message, "checks": checks}
