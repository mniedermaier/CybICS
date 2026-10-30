"""
Defense check: the attack machine is cut off from the PLC and the OPC-UA server.

The check does not read the rule text, it tries the connections: from inside
the attack shell (172.18.0.100, the attack machine's network namespace) the
OpenPLC web interface (172.18.0.3:8080), Modbus (172.18.0.3:502) and the
OPC-UA server (172.18.0.5:4840) must all refuse or drop a TCP connection. A
DROP rule for 172.18.0.100 on an unrelated port, or after an ACCEPT that
matches first, therefore does not pass.

Segmentation must not cut the plant's own paths either: the web interface
and the OPC-UA server still answer from this board (172.18.0.1), and hwio,
FUXA and the OPC-UA gateway still reach Modbus.

Everything it does is a TCP connect; it changes nothing.
"""
from modules.defense_checks._reach import container, tcp_open_from, tcp_open_here
from modules.defense_checks.check_firewall import _clients_check
from utils.logger import logger

ATTACK_IP = "172.18.0.100"

# (ip, port, service name)
TARGETS = (
    ("172.18.0.3", 8080, "OpenPLC Web UI"),
    ("172.18.0.3", 502, "Modbus TCP"),
    ("172.18.0.5", 4840, "OPC-UA Server"),
)
# Paths from this board that must stay open (the board is not the attacker).
KEEP_OPEN = (
    ("172.18.0.3", 8080, "OpenPLC Web UI"),
    ("172.18.0.5", 4840, "OPC-UA Server"),
)


def verify():
    """Check that the attack shell reaches none of the targets and the plant still runs."""
    attacker = container("attack-shell")
    if not attacker:
        return {"success": False,
                "message": "The attack shell is not running, so there is nothing to test the "
                           "segmentation from. Start it again and verify.",
                "checks": [{"name": "Attack shell running", "passed": False,
                            "detail": f"No running container for the attack machine ({ATTACK_IP})"}]}

    checks = []
    for ip, port, service in TARGETS:
        name = f"Block {service} ({ip}:{port})"
        try:
            reachable = tcp_open_from(attacker, ip, port)
            checks.append({"name": name, "passed": not reachable,
                           "detail": f"{ATTACK_IP} can no longer connect to {ip}:{port}"
                           if not reachable
                           else f"{ATTACK_IP} still connects to {ip}:{port}"})
        except Exception as e:
            logger.error(f"segmentation: probe of {ip}:{port} failed: {e}")
            checks.append({"name": name, "passed": False,
                           "detail": "Could not probe from the attack shell, see the landing log"})

    cut = [f"{service} ({ip}:{port})" for ip, port, service in KEEP_OPEN
           if not tcp_open_here(ip, port)]
    checks.append({"name": "Services still reachable from the board", "passed": not cut,
                   "detail": "The web interface and the OPC-UA server still answer this board "
                             "(172.18.0.1)" if not cut
                   else "Blocked for this board (172.18.0.1) too: " + ", ".join(cut)
                        + ". Block the attack machine's address, not everyone"})
    checks.append(_clients_check())

    success = all(c["passed"] for c in checks)
    message = ("Network segmentation correctly applied! "
               "The attack machine reaches none of the targets and the plant runs on."
               if success
               else "Network segmentation incomplete. Block the attack machine (172.18.0.100) "
                    "on the OpenPLC and OPC-UA containers, and nothing else.")
    return {"success": success, "message": message, "checks": checks}
