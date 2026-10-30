"""
Defense check: firewall rules restrict Modbus (port 502) access on OpenPLC.

The check passes when

* the OpenPLC container's INPUT chain has a DROP or REJECT rule;
* port 502 refuses or drops a TCP connection from this board (172.18.0.1,
  the landing page's host network) and from the attack shell (172.18.0.100);
* the plant's own Modbus clients still get through: hwio (172.18.0.2), the
  FUXA HMI (172.18.0.4) and the OPC-UA gateway (172.18.0.5) each connect to
  502 from inside their container. A rule set that drops everything on 502
  stops the plant and is an outage, not a defence.

Everything it does is an iptables listing or a TCP connect; it changes
nothing. A container that is not running is left out of the client probes.
"""
import subprocess

from modules.defense_checks._reach import (DOCKER_TIMEOUT, container, tcp_open_from,
                                           tcp_open_here)
from utils.config import PLC_HOST, PLC_MODBUS_PORT
from utils.logger import logger

# (container name fragment, who, address, probe runtime)
PLANT_CLIENTS = (
    ("hwio", "hwio", "172.18.0.2", "python3"),
    ("fuxa", "FUXA HMI", "172.18.0.4", "node"),
    ("opcua", "OPC-UA gateway", "172.18.0.5", "python3"),
)


def _rules_check(plc):
    try:
        result = subprocess.run(["docker", "exec", plc, "iptables", "-L", "INPUT", "-n"],
                                capture_output=True, text=True, timeout=DOCKER_TIMEOUT)
        has_rules = "DROP" in result.stdout or "REJECT" in result.stdout
        return {"name": "Firewall rules configured", "passed": has_rules,
                "detail": "iptables rules with DROP/REJECT found on OpenPLC" if has_rules
                else "No restrictive iptables rules found on OpenPLC container"}
    except Exception as e:
        logger.error(f"firewall: cannot list iptables: {e}")
        return {"name": "Firewall rules configured", "passed": False,
                "detail": "Could not list the OpenPLC container's iptables rules"}


def _blocked_checks():
    checks = []
    open_here = tcp_open_here(PLC_HOST, PLC_MODBUS_PORT)
    checks.append({"name": "Modbus blocked from this board", "passed": not open_here,
                   "detail": "Port 502 is blocked from this board (172.18.0.1)" if not open_here
                   else "Port 502 still accepts connections from this board (172.18.0.1), "
                        "which is not on the allow list"})
    attacker = container("attack-shell")
    if attacker:
        try:
            open_there = tcp_open_from(attacker, PLC_HOST, PLC_MODBUS_PORT)
            checks.append({"name": "Modbus blocked from the attack shell", "passed": not open_there,
                           "detail": "Port 502 is blocked from the attack shell (172.18.0.100)"
                           if not open_there
                           else "The attack shell (172.18.0.100) still reaches port 502"})
        except Exception as e:
            logger.error(f"firewall: attack shell probe failed: {e}")
            checks.append({"name": "Modbus blocked from the attack shell", "passed": False,
                           "detail": "Could not probe port 502 from the attack shell"})
    return checks


def _clients_check():
    cut_off, probed = [], []
    for fragment, who, address, runtime in PLANT_CLIENTS:
        name = container(fragment)
        if not name:
            continue
        probed.append(who)
        try:
            if not tcp_open_from(name, PLC_HOST, PLC_MODBUS_PORT, runtime):
                cut_off.append(f"{who} ({address})")
        except Exception as e:
            logger.error(f"firewall: probe from {who} failed: {e}")
            cut_off.append(f"{who} ({address}, probe failed)")
    if cut_off:
        detail = ("Port 502 is blocked for " + ", ".join(cut_off) + " too. The plant needs "
                  "them: ACCEPT their addresses before the rule that drops the rest")
    else:
        detail = "Port 502 still answers " + ", ".join(probed)
    return {"name": "Plant's Modbus clients still allowed", "passed": not cut_off,
            "detail": detail}


def verify():
    """Check that only the plant's own Modbus clients reach port 502 on OpenPLC."""
    plc = container("openplc")
    if not plc:
        return {"success": False, "message": "OpenPLC container not found",
                "checks": [{"name": "OpenPLC container found", "passed": False,
                            "detail": "Cannot find a running OpenPLC container"}]}

    checks = [_rules_check(plc)]
    checks.extend(_blocked_checks())
    checks.append(_clients_check())

    success = all(c["passed"] for c in checks)
    message = ("Modbus firewall rules correctly applied: only hwio, FUXA and the OPC-UA "
               "gateway reach port 502."
               if success
               else "Firewall configuration incomplete. Port 502 must be closed to everyone "
                    "except hwio (172.18.0.2), FUXA (172.18.0.4) and the OPC-UA gateway "
                    "(172.18.0.5).")
    return {"success": success, "message": message, "checks": checks}
