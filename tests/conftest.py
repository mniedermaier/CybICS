"""Shared configuration and helpers for the CybICS test suite.

Two things live here that the suite previously lacked:

* one definition of where the stack is and how long to wait for it, instead of
  three copies that had drifted to different timeouts;
* a readiness gate, so "the service was not up yet" fails once, loudly, instead
  of being absorbed by every individual test as a skip.
"""
import os
import socket
import time

import pytest
from pymodbus.exceptions import ConnectionException, ModbusException

# --------------------------------------------------------------------------
# Where the stack under test lives
# --------------------------------------------------------------------------

SERVER_IP = os.getenv("TEST_SERVER_IP", "127.0.0.1")

# Connection timeout for protocol clients.  This used to be 20 in two files and
# 10 in a third, for no stated reason.
CONNECTION_TIMEOUT = 20
READ_TIMEOUT = 10

MODBUS_SERVER_PORT = 502
OPCUA_SERVER_PORT = 4840
# Port 102 is OpenPLC's own S7/ISO-TSAP surface, 1102 is the separate s7com
# service. test_connections scans 102, so keep that name pointing there.
S7_SERVER_PORT = 102
S7COM_PORT = 1102
OPENPLC_PORT = 8080
FUXA_PORT = 1881
HWIO_PORT = 8090

OPCUA_SERVER_URL = f"opc.tcp://{SERVER_IP}:{OPCUA_SERVER_PORT}"

# Services the suite needs, and how long to wait for each on start-up.  The
# workflow starts the stack immediately before running the suite, so the first
# test can otherwise race the containers.
REQUIRED_SERVICES = {
    "modbus (openplc)": MODBUS_SERVER_PORT,
    "opcua": OPCUA_SERVER_PORT,
    "s7 (openplc)": S7_SERVER_PORT,
    "s7com": S7COM_PORT,
    "openplc web": OPENPLC_PORT,
    "fuxa": FUXA_PORT,
    "hwio": HWIO_PORT,
}

STACK_READY_TIMEOUT = int(os.getenv("TEST_STACK_TIMEOUT", "180"))


# --------------------------------------------------------------------------
# Readiness
# --------------------------------------------------------------------------

def wait_for_port(host, port, timeout, interval=1.0):
    """Poll a TCP port until it accepts a connection. Returns True if it did.

    Polling beats sleeping: it returns as soon as the service is actually up
    rather than after a fixed guess, and it reports honestly when the service
    never arrives.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(interval)
    return False


@pytest.fixture(scope="session")
def stack_ready():
    """Wait for the whole stack once, and say plainly which parts never came up.

    Requested per module via `pytestmark = pytest.mark.usefixtures("stack_ready")`
    rather than autouse, so the tests that need no stack at all -- the IDS rule
    engine and the plant model parity checks -- still run when nothing is up.

    Without this, a service that is slow or dead surfaces as a scatter of
    skipped tests, which reads as success on a green tick.  Here it is a single
    failure naming exactly what is missing.
    """
    missing = []
    deadline = time.monotonic() + STACK_READY_TIMEOUT
    for name, port in REQUIRED_SERVICES.items():
        remaining = max(1, deadline - time.monotonic())
        if not wait_for_port(SERVER_IP, port, remaining):
            missing.append(f"{name} ({SERVER_IP}:{port})")
    if missing:
        pytest.fail(
            "Stack did not become ready within "
            f"{STACK_READY_TIMEOUT}s. Not reachable: " + ", ".join(missing) +
            ". These tests describe a running CybICS stack; a service that is "
            "down is a failure, not a reason to skip."
        )


# --------------------------------------------------------------------------
# Modbus
# --------------------------------------------------------------------------

def modbus_call(client, operation, *args, **kwargs):
    """Run a Modbus operation, reconnecting once if the server hung up.

    The OpenPLC runtime drops established Modbus connections from time to time -
    it closes every client when the PLC program (re)starts, which in a freshly
    composed stack can land in the middle of a test.

    The obvious guard does not work:

        if not client.is_socket_open():
            client.connect()

    is_socket_open() reports what the local transport believes, and a FIN from
    the peer does not change that.  It still returns True after the server has
    closed, so the reconnect never happens and the next call raises
    ConnectionException - which is how a tolerated server behaviour turned into
    a red build roughly one run in ten since June.

    Only actually using the socket reveals the state, so try the call, and on a
    connection error reconnect and try once more.  A genuinely unreachable
    server still fails, because the retry fails too.
    """
    try:
        return operation(*args, **kwargs)
    except (ConnectionException, ModbusException):
        if not client.connect():
            raise AssertionError(
                "Modbus server closed the connection and refused a reconnect"
            )
        return operation(*args, **kwargs)
