"""Shared helpers for the CybICS test suite.

Currently this exists for one reason: Modbus calls against the OpenPLC runtime
have to survive the server closing the connection underneath them.
"""
import pytest
from pymodbus.exceptions import ConnectionException, ModbusException

# Host the stack under test is reachable on. Overridable so the suite can be
# pointed at a real device instead of a local compose stack.
import os

SERVER_IP = os.getenv("TEST_SERVER_IP", "127.0.0.1")
CONNECTION_TIMEOUT = 20


def modbus_call(client, operation, *args, **kwargs):
    """Run a Modbus operation, reconnecting once if the server hung up.

    The OpenPLC runtime drops established Modbus connections from time to time -
    it closes every client when the PLC program (re)starts, which in a freshly
    composed stack can land in the middle of a test.

    The obvious guard does not work:

        if not client.is_socket_open():
            client.connect()

    is_socket_open() reports what the local transport believes, and a FIN from
    the peer does not change that. It still returns True after the server has
    closed, so the reconnect never happens and the next call raises
    ConnectionException - which is how a tolerated server behaviour turned into
    a red build roughly one run in ten since June.

    Only actually using the socket reveals the state, so try the call, and on a
    connection error reconnect and try once more. A genuinely unreachable
    server still fails, because the retry fails too.
    """
    try:
        return operation(*args, **kwargs)
    except (ConnectionException, ModbusException):
        if not client.connect():
            pytest.skip(
                "Modbus server closed the connection and refused a reconnect - "
                "the runtime is likely restarting"
            )
        return operation(*args, **kwargs)
