"""The Close the Side Doors verify module, without a stack.

software/landing/modules/defense_checks/check_unused_protocols.py passes only
when OpenPLC's Settings table switches S7, DNP3 and EtherNet/IP off AND the
PLC no longer listens on 102, 20000 and 44818, port 8443 refuses a TCP
connect from the board and from the attack shell, 502 and 8080 still listen,
and the PLC's heartbeat still toggles. These tests pin that it fails closed:
a firewall rule in front of a running service, a setting saved but not
applied, a service stopped but still enabled in the database, 8443 blocked
for only one source, Modbus switched off with the rest, a frozen plant, and
an unreadable PLC must not pass.

docker, the TCP probes and the heartbeat are replaced by fakes; the
/proc/net/tcp lines are captured from the virtual stack's OpenPLC container.

tests/test_training.py::TestDefenseUnusedProtocols runs the real thing.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software", "landing"))

try:
    from modules.defense_checks import check_unused_protocols as check
except ImportError as error:  # requests missing on this host
    pytest.skip(f"check_unused_protocols not importable here ({error})", allow_module_level=True)

HEADER = ("  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt"
          "   uid  timeout inode\n")
# port (hex) of a LISTEN line on 0.0.0.0, as /proc/net/tcp writes it
LISTEN_LINE = "   {n}: 00000000:{port:04X} 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 4047884 1 0000000000000000 100 0 0 10 0\n"
# Captured: the runtime's control port on 127.0.0.1, and Modbus clients.
LOCAL_AND_CLIENTS = (
    "   7: 0100007F:AA6C 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 4038210 1 0000000000000000 100 0 0 10 0\n"
    "   8: 030012AC:01F6 040012AC:88A0 01 00000000:00000000 00:00000000 00000000     0        0 4041392 2 0000000000000000 20 4 30 10 -1\n"
    "   9: 030012AC:01F6 050012AC:B2FA 01 00000000:00000000 00:00000000 00000000     0        0 4041233 1 0000000000000000 20 4 30 10 -1\n")

SHIPPED = {"Modbus_port": "502", "Dnp3_port": "20000", "Start_run_mode": "true",
           "Slave_polling": "100", "Slave_timeout": "1000", "Enip_port": "44818",
           "Pstorage_polling": "disabled", "snap7": "true"}
HARDENED = dict(SHIPPED, Dnp3_port="disabled", Enip_port="disabled", snap7="false")
ALL_PORTS = {102, 502, 8080, 8443, 20000, 44818}


def proc_net_tcp(ports):
    return HEADER + "".join(LISTEN_LINE.format(n=i, port=p) for i, p in enumerate(sorted(ports))) \
        + LOCAL_AND_CLIENTS


class Plc:
    """The PLC container, the attack shell and the plant as the check sees them."""

    def __init__(self):
        self.settings = dict(HARDENED)
        self.listening = {502, 8080, 8443}
        self.open_from_board = set()          # ports a connect from 172.18.0.1 reaches
        self.open_from_attacker = set()       # ... from 172.18.0.100
        self.containers = ["virtual-openplc-1", "virtual-attack-shell-1", "virtual-hwio-1"]
        self.exec_fails = False
        self.hwio = True
        self.heartbeat = True
        self.commands = []

    def run(self, argv, capture_output=True, text=True, timeout=None):
        assert timeout, "every docker call needs a timeout"
        self.commands.append(argv)
        if argv[:2] == ["docker", "ps"]:
            return subprocess.CompletedProcess(argv, 0, "\n".join(self.containers) + "\n", "")
        assert argv[:2] == ["docker", "exec"], argv
        container, command = argv[2], argv[3:]
        if self.exec_fails:
            return subprocess.CompletedProcess(argv, 1, "", "Error: No such container")
        if container == "virtual-openplc-1" and command[:1] == ["cat"]:
            assert command[1:] == ["/proc/net/tcp", "/proc/net/tcp6"]
            return subprocess.CompletedProcess(argv, 0, proc_net_tcp(self.listening), "")
        if container == "virtual-openplc-1" and command[:1] == ["sqlite3"]:
            assert "mode=ro" in command[1], "the settings must be read read-only"
            assert command[2].lstrip().upper().startswith("SELECT")
            out = "".join(f"{k}|{v}\n" for k, v in self.settings.items())
            return subprocess.CompletedProcess(argv, 0, out, "")
        if container == "virtual-attack-shell-1" and command[:2] == ["python3", "-c"]:
            assert "connect_ex(('172.18.0.3',8443))" in command[2], command[2]
            code = 0 if 8443 in self.open_from_attacker else 1
            return subprocess.CompletedProcess(argv, code, "", "")
        raise AssertionError(f"the check must not run {argv}")


@pytest.fixture
def plc(monkeypatch):
    fake = Plc()
    monkeypatch.setattr(check.subprocess, "run", fake.run)
    monkeypatch.setattr(check, "_tcp_open_here", lambda port: port in fake.open_from_board)

    def plant_running():
        if fake.hwio:
            return fake.heartbeat, "by the plant simulation (hwio)"
        return fake.heartbeat, "over Modbus from this board"
    monkeypatch.setattr(check, "plant_running", plant_running)
    return fake


def checks(result):
    return {c["name"]: c for c in result["checks"]}


def failed(result):
    return {c["name"] for c in result["checks"] if not c["passed"]}


def test_hardened_plc_passes(plc):
    result = check.verify()
    assert result["success"], result
    assert set(checks(result)) == {
        "S7comm (port 102) switched off", "DNP3 (port 20000) switched off",
        "EtherNet/IP (port 44818) switched off", "REST API (port 8443) unreachable",
        "Modbus and the web interface still on", "Plant still running"}
    assert "firewall rule is what keeps it closed" in checks(result)["REST API (port 8443) unreachable"]["detail"]


def test_shipped_plc_fails_every_side_door(plc):
    plc.settings = dict(SHIPPED)
    plc.listening = set(ALL_PORTS)
    plc.open_from_board = {8443}
    plc.open_from_attacker = {8443}
    result = check.verify()
    assert not result["success"]
    assert failed(result) == {"S7comm (port 102) switched off", "DNP3 (port 20000) switched off",
                              "EtherNet/IP (port 44818) switched off",
                              "REST API (port 8443) unreachable"}


@pytest.mark.parametrize("port,key", [(102, "snap7"), (20000, "Dnp3_port"), (44818, "Enip_port")])
def test_a_firewall_rule_in_front_of_a_running_service_does_not_count(plc, port, key):
    plc.settings[key] = SHIPPED[key]
    plc.listening.add(port)          # still listening, only a rule hides it
    result = check.verify()
    assert not result["success"]
    name = next(n for n in failed(result))
    assert f"port {port}" in name and "would only hide it" in checks(result)[name]["detail"]


def test_saved_in_the_database_but_still_listening_fails(plc):
    plc.listening.add(20000)
    result = check.verify()
    assert failed(result) == {"DNP3 (port 20000) switched off"}
    assert "Save the Settings page" in checks(result)["DNP3 (port 20000) switched off"]["detail"]


def test_stopped_but_still_enabled_in_the_database_fails(plc):
    plc.settings["snap7"] = "true"
    result = check.verify()
    assert failed(result) == {"S7comm (port 102) switched off"}
    assert "next PLC restart" in checks(result)["S7comm (port 102) switched off"]["detail"]


@pytest.mark.parametrize("board,attacker", [(True, False), (False, True), (True, True)])
def test_rest_api_must_be_closed_for_everyone(plc, board, attacker):
    plc.open_from_board = {8443} if board else set()
    plc.open_from_attacker = {8443} if attacker else set()
    result = check.verify()
    assert failed(result) == {"REST API (port 8443) unreachable"}
    detail = checks(result)["REST API (port 8443) unreachable"]["detail"]
    assert ("(172.18.0.1)" in detail) == board and ("(172.18.0.100)" in detail) == attacker


def test_without_an_attack_shell_only_the_board_probe_runs(plc):
    plc.containers.remove("virtual-attack-shell-1")
    result = check.verify()
    assert result["success"], result
    assert not any(c[2] == "virtual-attack-shell-1" for c in plc.commands if c[1] == "exec")


@pytest.mark.parametrize("port", [502, 8080])
def test_switching_off_what_the_plant_needs_fails(plc, port):
    plc.listening.discard(port)
    result = check.verify()
    assert failed(result) == {"Modbus and the web interface still on"}


def test_a_frozen_plant_fails(plc):
    plc.heartbeat = False
    result = check.verify()
    assert failed(result) == {"Plant still running"}


def test_board_without_hwio_reads_the_heartbeat_over_modbus(plc):
    plc.hwio = False
    result = check.verify()
    assert result["success"]
    assert "over Modbus" in checks(result)["Plant still running"]["detail"]


def test_missing_plc_container_fails(plc):
    plc.containers = ["virtual-attack-shell-1"]
    result = check.verify()
    assert not result["success"] and failed(result) == {"OpenPLC container found"}


def test_unreadable_plc_fails_closed(plc):
    plc.exec_fails = True
    result = check.verify()
    assert not result["success"] and failed(result) == {"PLC state readable"}


def test_the_check_writes_nothing(plc):
    check.verify()
    for argv in plc.commands:
        joined = " ".join(argv).lower()
        for verb in ("update ", "insert ", "delete ", "iptables", "restart", "-i "):
            assert verb not in joined, argv


def test_listening_ports_parses_captured_proc_lines():
    text = proc_net_tcp({102, 502}) + LOCAL_AND_CLIENTS
    # 127.0.0.1:43628 listens too; established Modbus clients are not listeners.
    assert check.listening_ports(text) == {102, 502, 43628}
    assert check.listening_ports("garbage\n  1: zz 00 0A\n") == set()


def test_parse_settings_reads_sqlite_output():
    assert check.parse_settings("snap7|false\nDnp3_port|disabled\n\n") == {
        "snap7": "false", "Dnp3_port": "disabled"}


def test_heartbeat_sampler_needs_a_change():
    values = iter([True, True, False])
    assert check._sample(lambda: next(values))


def test_inventory_script_decodes_the_same_ports():
    """plc_ports.py, which the student runs in the PLC, sees what the check sees."""
    import importlib.util
    path = os.path.join(ROOT, "training", "defense_unused_protocols", "plc_ports.py")
    spec = importlib.util.spec_from_file_location("plc_ports", path)
    plc_ports = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plc_ports)
    assert plc_ports._address("030012AC:01F6") == ("172.18.0.3", 502)
    assert plc_ports._address("0100007F:AA6C") == ("127.0.0.1", 43628)
    assert plc_ports._address("0000000000000000FFFF0000030012AC:20FB") == ("172.18.0.3", 8443)
    for port in check.SIDE_DOORS:
        assert port in plc_ports.SERVICES
    assert check.REST_PORT in plc_ports.SERVICES
