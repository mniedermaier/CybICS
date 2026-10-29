"""The Modbus Firewall verify module, without a stack.

software/landing/modules/defense_checks/check_firewall.py passes only when
the PLC has a DROP/REJECT rule, port 502 is closed to the board (172.18.0.1)
and the attack shell (172.18.0.100), and hwio, FUXA and the OPC-UA gateway
still connect to it. check_network_segmentation.py passes only when the
attack shell reaches none of 8080 and 502 on the PLC and 4840 on the OPC-UA
server, the board still reaches 8080 and 4840, and the plant's Modbus
clients still get through.

Both used to accept rule text: the README's firewall rules cut the OPC-UA
gateway off from the PLC and still passed, and a DROP rule for the attacker
on an unrelated port passed segmentation while the attacker still reached
Modbus. These tests pin that both fail closed.

docker and the TCP probes are replaced by a fake network that decides each
connect from a set of blocked (source, destination, port) triples.
"""
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

try:
    from modules.defense_checks import _reach
    from modules.defense_checks import check_firewall as firewall
except ImportError as error:  # requests missing on this host
    pytest.skip(f"defense checks not importable here ({error})", allow_module_level=True)

PLC, OPCUA, BOARD, ATTACKER = "172.18.0.3", "172.18.0.5", "172.18.0.1", "172.18.0.100"
CONTAINER_IP = {"virtual-hwio-1": "172.18.0.2", "virtual-fuxa-1": "172.18.0.4",
                "virtual-opcua-1": OPCUA, "virtual-attack-shell-1": ATTACKER,
                "virtual-openplc-1": PLC}
LISTENING = {(PLC, 502), (PLC, 8080), (OPCUA, 4840)}


class Network:
    def __init__(self):
        self.blocked = set()            # (source, destination, port)
        self.rules_text = ""            # what iptables -L INPUT -n prints on the PLC
        self.containers = list(CONTAINER_IP)
        self.commands = []

    def block(self, sources, destination, port):
        for source in sources:
            self.blocked.add((source, destination, port))
        self.rules_text += f"DROP       6    --  0.0.0.0/0  0.0.0.0/0  tcp dpt:{port}\n"

    def connects(self, source, host, port):
        return (host, port) in LISTENING and (source, host, port) not in self.blocked

    def run(self, argv, capture_output=True, text=True, timeout=None):
        assert timeout, "every docker call needs a timeout"
        self.commands.append(argv)
        if argv[:2] == ["docker", "ps"]:
            return subprocess.CompletedProcess(argv, 0, "\n".join(self.containers) + "\n", "")
        assert argv[:2] == ["docker", "exec"], argv
        name, command = argv[2], argv[3:]
        if command[:1] == ["iptables"]:
            assert name == "virtual-openplc-1" and command[1:] == ["-L", "INPUT", "-n"]
            return subprocess.CompletedProcess(argv, 0, "Chain INPUT (policy ACCEPT)\n"
                                               + self.rules_text, "")
        runtime = "node" if name == "virtual-fuxa-1" else "python3"
        assert command[0] == runtime, f"{name} must be probed with {runtime}: {command}"
        match = re.search(r"'(\d+\.\d+\.\d+\.\d+)',?\s*(?:port:)?(\d+)", command[2])
        assert match, command[2]
        host, port = match.group(1), int(match.group(2))
        return subprocess.CompletedProcess(
            argv, 0 if self.connects(CONTAINER_IP[name], host, port) else 1, "", "")


@pytest.fixture
def net(monkeypatch):
    fake = Network()
    monkeypatch.setattr(subprocess, "run", fake.run)
    here = lambda host, port: fake.connects(BOARD, host, port)  # noqa: E731
    monkeypatch.setattr(firewall, "tcp_open_here", here)
    return fake


def failed(result):
    return {c["name"] for c in result["checks"] if not c["passed"]}


ALLOWED = {"172.18.0.2", "172.18.0.4", OPCUA}
EVERYONE = ALLOWED | {BOARD, ATTACKER}


def test_node_probe_parses_for_the_fake():
    # The fake reads host and port out of both probe programs.
    for template in (_reach._PYTHON, _reach._NODE):
        code = template.format(t=3, h=PLC, p=502)
        assert re.search(r"'172\.18\.0\.3',?\s*(?:port:)?502", code), code


# -- Modbus Firewall ---------------------------------------------------------

def test_firewall_unhardened_fails(net):
    result = firewall.verify()
    assert failed(result) == {"Firewall rules configured", "Modbus blocked from this board",
                              "Modbus blocked from the attack shell"}


def test_firewall_allow_list_with_all_three_clients_passes(net):
    net.block(EVERYONE - ALLOWED, PLC, 502)
    result = firewall.verify()
    assert result["success"], result


def test_firewall_that_forgets_the_opcua_gateway_fails(net):
    # The README used to allow only hwio and FUXA.
    net.block(EVERYONE - {"172.18.0.2", "172.18.0.4"}, PLC, 502)
    result = firewall.verify()
    assert failed(result) == {"Plant's Modbus clients still allowed"}
    detail = next(c["detail"] for c in result["checks"] if not c["passed"])
    assert "OPC-UA gateway (172.18.0.5)" in detail


def test_firewall_that_drops_everyone_fails(net):
    net.block(EVERYONE, PLC, 502)
    assert failed(firewall.verify()) == {"Plant's Modbus clients still allowed"}


def test_firewall_open_to_the_attacker_fails(net):
    net.block(EVERYONE - ALLOWED - {ATTACKER}, PLC, 502)
    assert failed(firewall.verify()) == {"Modbus blocked from the attack shell"}


def test_firewall_without_plc_container_fails(net):
    net.containers.remove("virtual-openplc-1")
    assert failed(firewall.verify()) == {"OpenPLC container found"}


def test_firewall_skips_a_client_that_is_not_running(net):
    net.block(EVERYONE - ALLOWED, PLC, 502)
    net.containers.remove("virtual-fuxa-1")
    assert firewall.verify()["success"]
    assert not any(c[2] == "virtual-fuxa-1" for c in net.commands if c[1] == "exec")
