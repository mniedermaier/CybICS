import pytest
import requests
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

# Define the IP and Ports
SERVER_IP = '127.0.0.1'   # Replace with your server IP
MODBUS_SERVER_PORT = 502  # Replace with your Modbus server Port (default is 502)

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
    result = modbus_client.read_holding_registers(register_address, 1)
    
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
    read_result = modbus_client.read_holding_registers(register_address, 1)
    assert read_result.registers[0] == value_to_write, f"Expected {value_to_write}, got {read_result.registers[0]}"
