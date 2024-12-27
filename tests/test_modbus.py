import pytest
import requests
import pytest_asyncio
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
from asyncua import Client, ua

# Define the IP and Ports
SERVER_IP = '127.0.0.1'   # Replace with your server IP
MODBUS_SERVER_PORT = 502  # Replace with your Modbus server Port (default is 502)

# OPC UA server URL (with the correct address)
OPCUA_SERVER_URL = "opc.tcp://"+SERVER_IP+":4840"
USERNAME = "user1"
PASSWORD = "test"

# List of URLs to check
URLS = [
    "http://"+SERVER_IP+"",
    "http://"+SERVER_IP+":1881",
    "http://"+SERVER_IP+":8080"
]

@pytest.mark.parametrize("url", URLS)
def test_website_is_up(url):
    try:
        response = requests.get(url, timeout=5)  # Set a timeout of 5 seconds
        assert response.status_code == 200, f"Website {url} is not up. Status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to reach {url}: {e}")

@pytest.fixture
def modbus_client():
    """
    Fixture to create and clean up the Modbus TCP client.
    """
    client = ModbusTcpClient(SERVER_IP, port=MODBUS_SERVER_PORT)
    yield client
    client.close()

def test_modbus_connection(modbus_client):
    """
    Test to check if the Modbus client can successfully connect to the server.
    """
    assert modbus_client.connect(), "Failed to connect to the Modbus server"

def test_read_holding_register(modbus_client):
    """
    Test to read a specific holding register.
    Assuming register 1 exists and has a valid value.
    """
    # Address of the register (Modbus address is often 0-based)
    register_address = 1
    result = modbus_client.read_holding_registers(register_address, count=1)
    
    # Check if we received a valid response
    assert result is not None, "No response from the Modbus server"
    assert not result.isError(), f"Modbus error: {result}"
    assert result.registers[0] is not None, "Invalid register value"

def test_write_single_register(modbus_client):
    """
    Test to write a value to a single holding register.
    """
    register_address = 1  # Example register address
    value_to_write = 123  # Example value to write

    # Write the value to the register
    result = modbus_client.write_register(register_address, value_to_write)

    # Check if write was successful
    assert result is not None, "No response from the Modbus server"
    assert not result.isError(), f"Modbus error: {result}"

    # Verify that the value was written correctly by reading it back
    read_result = modbus_client.read_holding_registers(register_address, count=1)
    assert read_result.registers[0] == value_to_write, f"Expected {value_to_write}, got {read_result.registers[0]}"

@pytest.mark.asyncio
async def test_opcua_server_running():
    """
    Test to check if the OPC UA server is running and accessible.
    """
    client = Client(OPCUA_SERVER_URL)
    
    # Set username and password for the asyncua client
    client.set_user(USERNAME)
    client.set_password(PASSWORD)
    
    try:
        # Increase the timeout for connection attempts
        client.timeout = 10
        
        # Try to connect to the server
        await client.connect()
        print("Successfully connected to the OPC UA server.")
        
        # Optionally, check server status
        server_status_node = client.get_node(ua.ObjectIds.Server_ServerStatus)
        server_status = await server_status_node.read_value()
        assert server_status is not None, "Server status is None."
        
        print(f"Server Status: {server_status}")

    except Exception as e:
        pytest.fail(f"Failed to connect to the OPC UA server: {e}")
    finally:
        await client.disconnect()  # Ensure proper cleanup