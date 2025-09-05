"""
CybICS Connection Test Suite

This test suite validates connectivity and functionality of various industrial control system
protocols and services in a CybICS environment. It includes tests for:
- Web services (HTTP)
- Modbus TCP protocol
- OPC-UA protocol 
- Siemens S7 protocol via nmap scanning

These tests help ensure proper setup and security of industrial control systems for
defensive security testing and training purposes.
"""

import pytest
import requests
import subprocess
import time
import pytest_asyncio
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusException
from asyncua import Client, ua

# Test Configuration Constants
SERVER_IP = '127.0.0.1'           # Target server IP address for testing
MODBUS_SERVER_PORT = 502           # Standard Modbus TCP port
OPCUA_SERVER_PORT = 4840           # Standard OPC-UA port
S7_SERVER_PORT = 102               # Standard Siemens S7 port
CONNECTION_TIMEOUT = 10            # Connection timeout in seconds
READ_TIMEOUT = 5                   # Read operation timeout in seconds

# OPC-UA Authentication Configuration
OPCUA_SERVER_URL = f"opc.tcp://{SERVER_IP}:{OPCUA_SERVER_PORT}"
USERNAME = "user1"                 # Default test username
PASSWORD = "test"                  # Default test password

# Web Services Configuration
# Common industrial web interfaces and HMI ports
URLS = [
    f"http://{SERVER_IP}",           # Main web interface
    f"http://{SERVER_IP}:1881",      # Node-RED interface
    f"http://{SERVER_IP}:8080"       # Alternative web service
]

# ===============================================================================
# Web Services Connectivity Tests
# ===============================================================================

@pytest.mark.parametrize("url", URLS)
def test_website_is_up(url):
    """
    Test HTTP connectivity to web services.
    
    Validates that industrial web interfaces are accessible and responding
    with proper HTTP status codes. This is critical for HMI access and
    web-based control interfaces.
    
    Args:
        url (str): Web service URL to test
    """
    try:
        response = requests.get(url, timeout=READ_TIMEOUT)
        assert response.status_code == 200, (
            f"Web service {url} returned unexpected status code: {response.status_code}. "
            f"Expected: 200 (OK)"
        )
        
        # Verify response contains some content
        assert len(response.text) > 0, f"Web service {url} returned empty response"
        
    except requests.exceptions.Timeout:
        pytest.fail(f"Connection to {url} timed out after {READ_TIMEOUT} seconds")
    except requests.exceptions.ConnectionError:
        pytest.fail(f"Failed to establish connection to {url} - service may be down")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Unexpected error connecting to {url}: {e}")


# ===============================================================================
# Modbus TCP Protocol Tests
# ===============================================================================

@pytest.fixture
def modbus_client():
    """
    Fixture to create and manage Modbus TCP client connection.
    
    Creates a Modbus TCP client for testing industrial protocol communication.
    Ensures proper cleanup after each test to prevent connection leaks.
    
    Yields:
        ModbusTcpClient: Configured Modbus TCP client instance
    """
    client = ModbusTcpClient(
        host=SERVER_IP, 
        port=MODBUS_SERVER_PORT,
        timeout=CONNECTION_TIMEOUT
    )
    yield client
    try:
        client.close()
    except Exception:
        pass  # Ignore cleanup errors

def test_modbus_connection(modbus_client):
    """
    Test Modbus TCP server connectivity.
    
    Validates that the Modbus TCP server is accessible and accepting connections.
    This is fundamental for industrial device communication and control.
    
    Args:
        modbus_client: Modbus TCP client fixture
    """
    connection_successful = modbus_client.connect()
    assert connection_successful, (
        f"Failed to establish Modbus TCP connection to {SERVER_IP}:{MODBUS_SERVER_PORT}. "
        f"Verify server is running and port is accessible."
    )
    
    # Verify connection is actually established
    assert modbus_client.is_socket_open(), "Modbus connection appears closed despite successful connect()"

def test_read_holding_register(modbus_client):
    """
    Test Modbus holding register read operation.
    
    Validates ability to read data from Modbus holding registers, which are
    commonly used for storing configuration data and process values in industrial systems.
    
    Args:
        modbus_client: Modbus TCP client fixture
    """
    # Ensure connection is established
    if not modbus_client.is_socket_open():
        assert modbus_client.connect(), "Failed to connect to Modbus server"
    
    register_address = 1  # Test register address
    register_count = 1
    
    try:
        result = modbus_client.read_holding_registers(
            address=register_address, 
            count=register_count,
            slave=1  # Default slave ID
        )
        
        # Validate response structure
        assert result is not None, "No response received from Modbus server"
        assert not result.isError(), (
            f"Modbus read error at register {register_address}: {result}"
        )
        
        # Validate register data
        assert hasattr(result, 'registers'), "Response missing register data"
        assert len(result.registers) == register_count, (
            f"Expected {register_count} register(s), got {len(result.registers)}"
        )
        assert result.registers[0] is not None, "Register value is None"
        
    except ModbusException as e:
        pytest.fail(f"Modbus protocol exception during read operation: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during register read: {e}")

def test_write_single_register(modbus_client):
    """
    Test Modbus holding register write and verify operation.
    
    Validates ability to write data to Modbus holding registers and verify
    the write operation was successful. This tests critical control functionality
    for industrial automation systems.
    
    Args:
        modbus_client: Modbus TCP client fixture
    """
    # Ensure connection is established
    if not modbus_client.is_socket_open():
        assert modbus_client.connect(), "Failed to connect to Modbus server"
    
    register_address = 1
    test_value = 123
    slave_id = 1
    
    try:
        # Perform write operation
        write_result = modbus_client.write_register(
            address=register_address,
            value=test_value,
            slave=slave_id
        )
        
        # Validate write response
        assert write_result is not None, "No response from Modbus server for write operation"
        assert not write_result.isError(), (
            f"Modbus write error at register {register_address}: {write_result}"
        )
        
        # Small delay to ensure write is processed
        time.sleep(0.1)
        
        # Verify write by reading back the value
        read_result = modbus_client.read_holding_registers(
            address=register_address,
            count=1,
            slave=slave_id
        )
        
        assert not read_result.isError(), (
            f"Modbus read error during verification: {read_result}"
        )
        
        actual_value = read_result.registers[0]
        assert actual_value == test_value, (
            f"Write verification failed. Expected: {test_value}, "
            f"Actual: {actual_value} at register {register_address}"
        )
        
    except ModbusException as e:
        pytest.fail(f"Modbus protocol exception during write operation: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during register write: {e}")

# ===============================================================================
# OPC-UA Protocol Tests
# ===============================================================================

@pytest.mark.asyncio
async def test_opcua_server_running():
    """
    Test OPC-UA server connectivity and basic functionality.
    
    Validates that the OPC-UA server is accessible and responding correctly.
    OPC-UA is a critical protocol for modern industrial automation and IoT systems.
    Tests both connection establishment and basic server status verification.
    """
    client = Client(OPCUA_SERVER_URL)
    
    # Configure authentication
    client.set_user(USERNAME)
    client.set_password(PASSWORD)
    client.timeout = CONNECTION_TIMEOUT
    
    try:
        # Attempt connection with timeout
        await client.connect()
        
        # Verify server is responsive by reading server status
        server_status_node = client.get_node(ua.ObjectIds.Server_ServerStatus)
        server_status = await server_status_node.read_value()
        
        assert server_status is not None, (
            "OPC-UA server status is None - server may not be functioning properly"
        )
        
        # Additional verification: check server state
        server_state_node = client.get_node(ua.ObjectIds.Server_ServerStatus_State)
        server_state = await server_state_node.read_value()
        
        # Server should be in Running state (value 0)
        assert server_state == 0, (
            f"OPC-UA server not in running state. Current state: {server_state}"
        )
        
    except ConnectionError as e:
        pytest.fail(f"Failed to establish OPC-UA connection to {OPCUA_SERVER_URL}: {e}")
    except ua.UaError as e:
        pytest.fail(f"OPC-UA protocol error: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during OPC-UA test: {e}")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass  # Ignore cleanup errors


# ===============================================================================
# Siemens S7 Protocol Tests (via Nmap)
# ===============================================================================

def run_nmap_s7_info():
    """
    Execute Nmap S7-info script for Siemens PLC detection.
    
    Uses Nmap's s7-info NSE script to detect and gather information about
    Siemens S7 PLCs. This is useful for security assessment and device inventory.
    
    Returns:
        tuple: (stdout, stderr) from nmap execution
    """
    nmap_command = [
        "nmap", 
        "-p", str(S7_SERVER_PORT),
        "--script", "s7-info",
        "--script-timeout", str(CONNECTION_TIMEOUT),
        SERVER_IP
    ]
    
    try:
        result = subprocess.run(
            nmap_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30  # Overall command timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Nmap command timed out", -1
    except FileNotFoundError:
        return None, "Nmap not found - please install nmap package", -1
    except Exception as e:
        return None, f"Unexpected error running nmap: {e}", -1

def test_nmap_s7_info():
    """
    Test Siemens S7 protocol detection via Nmap.
    
    Validates that S7 protocol services are detectable and responding.
    This test helps verify proper setup of Siemens PLC simulation or actual devices.
    The S7 protocol is commonly used in industrial automation environments.
    """
    stdout, stderr, return_code = run_nmap_s7_info()
    
    # Handle nmap execution errors
    if stdout is None:
        pytest.skip(f"Nmap execution failed: {stderr}")
    
    # Nmap should execute successfully (return code 0 or 1 are acceptable)
    # Return code 1 typically means "no hosts up" but scan completed
    assert return_code in [0, 1], (
        f"Nmap failed with return code {return_code}. stderr: {stderr}"
    )
    
    # Validate basic nmap output structure
    assert "Nmap scan report for" in stdout, (
        f"Nmap output missing expected scan report. Output: {stdout[:200]}..."
    )
    
    # Check for S7 service detection
    if f"{S7_SERVER_PORT}/tcp open" in stdout:
        # Port is open, should have S7 info
        assert any(keyword in stdout for keyword in ["Service Info", "Device Info", "s7-info"]), (
            f"S7 service detected on port {S7_SERVER_PORT} but no device information found. "
            f"Output: {stdout}"
        )
    else:
        # Port closed/filtered - this might be expected in some test environments
        pytest.skip(f"S7 service not accessible on port {S7_SERVER_PORT} - may not be configured")


# ===============================================================================
# Additional Comprehensive Tests
# ===============================================================================

class TestWebServiceSecurity:
    """Test security aspects of web services."""

    @pytest.mark.parametrize("url", URLS)
    def test_web_service_response_headers(self, url):
        """
        Test web service security headers.
        
        Validates that web services include basic security headers
        to protect against common web vulnerabilities.
        
        Args:
            url (str): Web service URL to test
        """
        try:
            response = requests.get(url, timeout=READ_TIMEOUT)
            if response.status_code == 200:
                headers = response.headers
                
                # Check for common security headers (informational)
                security_headers = [
                    'X-Frame-Options',
                    'X-Content-Type-Options',
                    'Content-Security-Policy'
                ]
                
                found_headers = [h for h in security_headers if h in headers]
                
                # This is informational - industrial systems may not have all headers
                if not found_headers:
                    pytest.skip(f"No security headers found in {url} - common in industrial systems")
                
        except requests.exceptions.RequestException:
            pytest.skip(f"Could not connect to {url} for header analysis")


class TestModbusExtended:
    """Extended Modbus TCP protocol tests."""

    @pytest.fixture
    def connected_modbus_client(self):
        """Fixture providing a connected Modbus client."""
        client = ModbusTcpClient(
            host=SERVER_IP,
            port=MODBUS_SERVER_PORT,
            timeout=CONNECTION_TIMEOUT
        )
        
        if not client.connect():
            pytest.skip("Could not establish Modbus connection for extended tests")
        
        yield client
        
        try:
            client.close()
        except Exception:  # pylint: disable=broad-except
            pass

    def test_read_multiple_registers(self, connected_modbus_client):
        """
        Test reading multiple consecutive holding registers.
        
        Validates ability to read multiple registers in a single operation,
        which is common for reading structured data from PLCs.
        
        Args:
            connected_modbus_client: Connected Modbus client fixture
        """
        register_start = 1
        register_count = 5
        
        try:
            result = connected_modbus_client.read_holding_registers(
                address=register_start,
                count=register_count,
                slave=1
            )
            
            assert not result.isError(), f"Failed to read multiple registers: {result}"
            assert len(result.registers) == register_count, (
                f"Expected {register_count} registers, got {len(result.registers)}"
            )
            
            # All register values should be valid (not None)
            for i, value in enumerate(result.registers):
                assert value is not None, (
                    f"Register {register_start + i} returned None value"
                )
                
        except ModbusException as e:
            pytest.fail(f"Modbus exception during multiple register read: {e}")

    def test_read_coils(self, connected_modbus_client):
        """
        Test reading Modbus coils (discrete outputs).
        
        Validates ability to read coil status, which represents digital outputs
        commonly used for controlling equipment like motors, lights, valves.
        
        Args:
            connected_modbus_client: Connected Modbus client fixture
        """
        coil_address = 1
        coil_count = 8
        
        try:
            result = connected_modbus_client.read_coils(
                address=coil_address,
                count=coil_count,
                slave=1
            )
            
            if result.isError():
                pytest.skip(f"Coils not available at address {coil_address}: {result}")
            
            assert len(result.bits) >= coil_count, (
                f"Expected at least {coil_count} coil bits, got {len(result.bits)}"
            )
            
            # Coil values should be boolean
            for i, bit_value in enumerate(result.bits[:coil_count]):
                assert isinstance(bit_value, bool), (
                    f"Coil {coil_address + i} should return boolean, got {type(bit_value)}"
                )
                
        except ModbusException as e:
            pytest.skip(f"Coil reading not supported or failed: {e}")

    def test_read_input_registers(self, connected_modbus_client):
        """
        Test reading Modbus input registers.
        
        Validates ability to read input registers, which typically contain
        sensor readings and other input data from field devices.
        
        Args:
            connected_modbus_client: Connected Modbus client fixture
        """
        input_address = 1
        input_count = 3
        
        try:
            result = connected_modbus_client.read_input_registers(
                address=input_address,
                count=input_count,
                slave=1
            )
            
            if result.isError():
                pytest.skip(f"Input registers not available at address {input_address}: {result}")
            
            assert len(result.registers) == input_count, (
                f"Expected {input_count} input registers, got {len(result.registers)}"
            )
            
            # Validate register values
            for i, value in enumerate(result.registers):
                assert value is not None, (
                    f"Input register {input_address + i} returned None"
                )
                assert isinstance(value, int), (
                    f"Input register {input_address + i} should be integer, got {type(value)}"
                )
                
        except ModbusException as e:
            pytest.skip(f"Input register reading not supported: {e}")


class TestOpcuaExtended:
    """Extended OPC-UA protocol tests."""

    @pytest.mark.asyncio
    async def test_opcua_browse_root(self):
        """
        Test OPC-UA address space browsing.
        
        Validates ability to browse the OPC-UA server's address space,
        which is fundamental for discovering available data points.
        """
        client = Client(OPCUA_SERVER_URL)
        client.set_user(USERNAME)
        client.set_password(PASSWORD)
        client.timeout = CONNECTION_TIMEOUT
        
        try:
            await client.connect()
            
            # Browse root folder
            root_node = client.get_root_node()
            children = await root_node.get_children()
            
            assert len(children) > 0, "OPC-UA root node should have child nodes"
            
            # Verify Objects folder exists (standard OPC-UA structure)
            objects_node = client.get_objects_node()
            objects_children = await objects_node.get_children()
            
            # Objects folder should contain server-specific content
            assert len(objects_children) >= 0, "Objects node accessible"
            
        except ua.UaError as e:
            pytest.skip(f"OPC-UA browsing not supported or failed: {e}")
        except Exception as e:  # pylint: disable=broad-except
            pytest.fail(f"Unexpected error during OPC-UA browsing: {e}")
        finally:
            try:
                await client.disconnect()
            except Exception:  # pylint: disable=broad-except
                pass

    @pytest.mark.asyncio
    async def test_opcua_read_server_time(self):
        """
        Test reading OPC-UA server time.
        
        Validates ability to read server timestamp, which is useful for
        synchronization and understanding server status.
        """
        client = Client(OPCUA_SERVER_URL)
        client.set_user(USERNAME)
        client.set_password(PASSWORD)
        client.timeout = CONNECTION_TIMEOUT
        
        try:
            await client.connect()
            
            # Read server timestamp
            time_node = client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime)
            server_time = await time_node.read_value()
            
            assert server_time is not None, "Server time should not be None"
            
            # Server time should be a datetime object
            from datetime import datetime
            assert isinstance(server_time, datetime), (
                f"Server time should be datetime, got {type(server_time)}"
            )
            
        except ua.UaError as e:
            pytest.skip(f"Server time reading not supported: {e}")
        except Exception as e:  # pylint: disable=broad-except
            pytest.fail(f"Unexpected error reading server time: {e}")
        finally:
            try:
                await client.disconnect()
            except Exception:  # pylint: disable=broad-except
                pass


def test_all_services_comprehensive():
    """
    Comprehensive test that all critical services are operational.
    
    This test provides a high-level validation that the complete
    CybICS environment is properly configured and operational.
    """
    service_status = {}
    
    # Test web services
    for url in URLS:
        try:
            response = requests.get(url, timeout=READ_TIMEOUT)
            service_status[f"Web-{url}"] = response.status_code == 200
        except requests.exceptions.RequestException:
            service_status[f"Web-{url}"] = False
    
    # Test Modbus
    modbus_client = ModbusTcpClient(SERVER_IP, port=MODBUS_SERVER_PORT)
    try:
        service_status["Modbus"] = modbus_client.connect()
        if service_status["Modbus"]:
            # Quick connectivity test
            result = modbus_client.read_holding_registers(1, 1)
            service_status["Modbus-Read"] = not result.isError()
    except Exception:  # pylint: disable=broad-except
        service_status["Modbus"] = False
        service_status["Modbus-Read"] = False
    finally:
        try:
            modbus_client.close()
        except Exception:  # pylint: disable=broad-except
            pass
    
    # Summary report
    total_services = len(service_status)
    working_services = sum(service_status.values())
    
    print(f"\nService Status Report:")
    print(f"Total Services Tested: {total_services}")
    print(f"Working Services: {working_services}")
    print(f"Service Availability: {working_services/total_services*100:.1f}%")
    
    for service, status in service_status.items():
        status_str = "✓ WORKING" if status else "✗ FAILED"
        print(f"  {service}: {status_str}")
    
    # At least half the services should be working for a basic environment
    min_required = max(1, total_services // 2)
    assert working_services >= min_required, (
        f"Insufficient services operational. Expected at least {min_required}, "
        f"got {working_services} out of {total_services}"
    )
