"""
Tests for the attack shell, the attacker host at 172.18.0.100.

The attack shell is a ttyd terminal in its own container on the plant network.
These tests drive it the way the browser does, over ttyd's WebSocket, and check
the three things the challenges rely on: it answers on its port and through the
TLS proxy, it is really 172.18.0.100 (the address the IDS and the defense checks
treat as the attacker), and the tools and libraries the training modules call
are installed.

Every browser tab shares one tmux session, so each test opens a tmux window of
its own and closes it again, leaving the window the user works in alone.
"""

import json
import re
import ssl
import time
import uuid

import pytest
import requests
import websocket
from conftest import SERVER_IP, ATTACK_SHELL_PORT, CONNECTION_TIMEOUT

pytestmark = pytest.mark.usefixtures("stack_ready")

ATTACK_SHELL_URL = f"http://{SERVER_IP}:{ATTACK_SHELL_PORT}"
# The proxy's TLS listener for the attack shell: service port + 10000.
ATTACK_SHELL_TLS_URL = f"https://{SERVER_IP}:{ATTACK_SHELL_PORT + 10000}"

# ttyd's message types, the first byte of every WebSocket message.
TTYD_INPUT = b"0"
TTYD_OUTPUT = ord("0")

# Escape sequences: tmux redraws the screen, the commands' output is in between.
ANSI = re.compile(rb"\x1b(\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07|[()][0-9A-B]|[=>78M])")


class TtydShell:
    """A minimal ttyd client: type a command, collect the output until a marker."""

    def __init__(self, url):
        ws_url = url.replace("http", "ws", 1) + "/ws"
        self.ws = websocket.create_connection(
            ws_url, subprotocols=["tty"], timeout=CONNECTION_TIMEOUT,
            sslopt={"cert_reqs": ssl.CERT_NONE})
        # The first message opens the terminal; without -c ttyd wants no token.
        self.ws.send(json.dumps({"AuthToken": "", "columns": 200, "rows": 50}))
        # A window of its own, opened with tmux's key binding (Ctrl-b c)
        # rather than a command, so nothing is typed into the user's window.
        self.ws.send_binary(TTYD_INPUT + b"\x02c")
        time.sleep(1)

    def type(self, text):
        self.ws.send_binary(TTYD_INPUT + text.encode() + b"\r")

    def run(self, command, timeout=30):
        """Run a command and return what it printed between two markers."""
        tag = uuid.uuid4().hex[:8]
        # The markers are assembled by the shell, so the echo of the typed
        # line itself never matches.
        self.type(f"echo B{tag}''B; {command}; echo E{tag}''E")
        start, end = f"B{tag}B".encode(), f"E{tag}E".encode()
        buf = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                msg = self.ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            if isinstance(msg, bytes) and msg and msg[0] == TTYD_OUTPUT:
                buf += ANSI.sub(b"", msg[1:])
                if start in buf and end in buf.split(start, 1)[1]:
                    out = buf.split(start, 1)[1].split(end, 1)[0]
                    return out.decode(errors="replace").replace("\r", "")
        pytest.fail(f"no output from the attack shell for: {command}\n{buf[-2000:]!r}")

    def close(self):
        try:
            self.type("exit")
            time.sleep(0.5)
        finally:
            self.ws.close()


@pytest.fixture
def shell():
    sh = TtydShell(ATTACK_SHELL_URL)
    try:
        yield sh
    finally:
        sh.close()


class TestReachability:
    def test_terminal_page_is_served(self):
        response = requests.get(ATTACK_SHELL_URL, timeout=CONNECTION_TIMEOUT)
        assert response.status_code == 200
        assert "ttyd" in response.text

    @pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
    def test_terminal_page_is_served_through_the_tls_proxy(self):
        """Over HTTPS the dashboard embeds the terminal from the proxy's 17681."""
        response = requests.get(ATTACK_SHELL_TLS_URL, timeout=CONNECTION_TIMEOUT, verify=False)
        assert response.status_code == 200
        assert "ttyd" in response.text

    def test_terminal_works_through_the_tls_proxy(self):
        """The proxy has to upgrade the WebSocket, not only serve the page."""
        sh = TtydShell(ATTACK_SHELL_TLS_URL)
        try:
            assert "hello-tls" in sh.run("echo hello-tls")
        finally:
            sh.close()


class TestNetworkPosition:
    def test_shell_is_the_attacker_address(self, shell):
        """The IDS and the segmentation check expect the attacker at .100."""
        out = shell.run("ip -4 -o addr show eth0")
        assert "172.18.0.100/24" in out

    def test_forwarding_is_on_for_a_man_in_the_middle(self, shell):
        """/proc/sys is read-only in the container, so compose has to set it."""
        out = shell.run("echo FWD $(cat /proc/sys/net/ipv4/ip_forward) $(cat /proc/sys/net/ipv4/conf/all/send_redirects)")
        assert "FWD 1 0" in out

    def test_plc_answers_modbus_from_the_shell(self, shell):
        out = shell.run(
            "python3 -c \"from pymodbus.client import ModbusTcpClient as C; "
            "c=C('172.18.0.3'); c.connect(); "
            "r=c.read_holding_registers(1124, count=1); print('REGS', not r.isError())\"")
        assert "REGS True" in out


class TestTools:
    @pytest.mark.parametrize("tool", [
        "nmap", "hydra", "ffuf", "curl", "nc", "socat", "tcpdump", "git",
        "picocom", "iptables", "flooding_hpt.py",
    ])
    def test_tool_is_installed(self, shell, tool):
        assert f"FOUND {tool}" in shell.run(f"command -v {tool} >/dev/null && echo FOUND {tool}")

    def test_python_libraries_import(self, shell):
        out = shell.run(
            "python3 -c 'import pymodbus, asyncua, nmap, colorama, serial, requests, dotenv, snap7; "
            "from scapy.layers.l2 import ARP; print(\"IMPORTS\", pymodbus.__version__)'",
            timeout=60)
        assert "IMPORTS 3.11.3" in out

    def test_training_material_and_wordlist_are_present(self, shell):
        out = shell.run("ls /CybICS/training/README.md && echo WORDS $(wc -l < /usr/share/wordlists/passwords.txt)")
        assert "/CybICS/training/README.md" in out
        # Matched rather than split: tmux may redraw its status line in between.
        assert int(re.search(r"WORDS (\d+)", out).group(1)) > 1000

    def test_s7_info_script_is_available(self, shell):
        """scanning2 patches a copy of nmap's s7-info script."""
        assert "s7-info.nse" in shell.run("ls /usr/share/nmap/scripts/s7-info.nse")
