#!/usr/bin/env python3
"""
Custom S7 Protocol Server
Implements basic S7 communication protocol to respond to nmap's s7-info script
with a CTF flag embedded in the system identification fields.
"""

import socket
import struct
import threading
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S"
)

# CTF Flag
FLAG = b"CybICS(s7comm_analysis_complete)"

class S7Server:
    def __init__(self, host='0.0.0.0', port=102):
        self.host = host
        self.port = port
        self.server_socket = None

    def handle_client(self, client_socket, addr):
        """Handle individual S7 client connections"""
        try:
            logging.info(f"Connection from {addr}")

            # S7 communication sequence:
            # 1. COTP Connection Request
            # 2. S7 Communication Setup
            # 3. SZL Read Requests

            while True:
                data = client_socket.recv(4096)
                if not data:
                    break

                logging.debug(f"Received {len(data)} bytes: {data.hex()}")

                # Parse TPKT header
                if len(data) < 4:
                    break

                version = data[0]
                reserved = data[1]
                length = struct.unpack('>H', data[2:4])[0]

                # Check if it's a COTP packet
                if len(data) >= 7:
                    cotp_length = data[4]
                    pdu_type = data[5]

                    # COTP Connection Request (0xe0)
                    if pdu_type == 0xe0:
                        response = self.build_cotp_connection_response()
                        client_socket.send(response)
                        logging.debug("Sent COTP connection response")
                        continue

                    # S7 Communication (0xf0 = Data Transfer)
                    if pdu_type == 0xf0 and len(data) > 7:
                        # Extract S7 header
                        s7_start = 7  # After TPKT(4) + COTP(3)
                        if len(data) > s7_start + 10:
                            protocol_id = data[s7_start]
                            msg_type = data[s7_start + 1]

                            # Job Request (0x01) or Userdata (0x07)
                            if msg_type == 0x01:  # Job request
                                response = self.build_s7_setup_response()
                                client_socket.send(response)
                                logging.debug("Sent S7 setup response")
                            elif msg_type == 0x07:  # Userdata (SZL read)
                                response = self.build_szl_response(data)
                                client_socket.send(response)
                                logging.debug("Sent SZL response")

        except Exception as e:
            logging.error(f"Error handling client {addr}: {e}")
        finally:
            client_socket.close()
            logging.info(f"Connection closed: {addr}")

    def build_cotp_connection_response(self):
        """Build COTP Connection Confirm response"""
        # TPKT Header
        tpkt = struct.pack('>BBH', 3, 0, 22)  # Version 3, Reserved 0, Length 22

        # COTP Connection Confirm
        cotp = bytes([
            0x11,  # Length
            0xd0,  # PDU Type: Connection Confirm
            0x00, 0x01,  # Destination reference
            0x00, 0x01,  # Source reference
            0x00,  # Class/Option
            # Parameters
            0xc0, 0x01, 0x0a,  # TPDU Size: 1024
            0xc1, 0x02, 0x01, 0x00,  # Source TSAP
            0xc2, 0x02, 0x01, 0x02,  # Destination TSAP
        ])

        return tpkt + cotp

    def build_s7_setup_response(self):
        """Build S7 Communication Setup response"""
        # TPKT Header
        tpkt = struct.pack('>BBH', 3, 0, 27)

        # COTP Data
        cotp = bytes([0x02, 0xf0, 0x80])  # Length 2, Data, EOT

        # S7 Header
        s7_header = bytes([
            0x32,  # Protocol ID
            0x03,  # ROPTYPE: Ack Data
            0x00, 0x00,  # Reserved
            0x00, 0x01,  # PDU Reference
            0x00, 0x08,  # Parameter length
            0x00, 0x00,  # Data length
        ])

        # S7 Parameters
        s7_params = bytes([
            0xf0,  # Function: Setup communication
            0x00,  # Reserved
            0x00, 0x01,  # Max AMQ Calling
            0x00, 0x01,  # Max AMQ Called
            0x03, 0xc0,  # PDU length (960)
        ])

        return tpkt + cotp + s7_header + s7_params

    def build_szl_response(self, request):
        """Build SZL (System Status List) response with CTF flag"""
        # Parse the request to extract PDU reference and SZL ID
        pdu_ref = 0x0001
        szl_id = 0x0011
        szl_index = 0x0001

        if len(request) > 13:
            pdu_ref = struct.unpack('>H', request[11:13])[0]

        # Check if this is requesting SZL 0x001c (second request)
        if len(request) > 30:
            szl_id = struct.unpack('>H', request[29:31])[0]
            if len(request) > 32:
                szl_index = struct.unpack('>H', request[31:33])[0]

        # Build response based on requested SZL ID
        if szl_id == 0x0011:
            # First SZL request - Module identification
            # Nmap expects response >= 125 bytes total
            # Position 44: Module (20 bytes, null-terminated)
            # Position 72: Basic Hardware (28 bytes, null-terminated)
            # Position 123-125: Version (3 bytes)

            # Build the complete response to match nmap's expectations
            # TPKT (4) + COTP (3) + S7 Header (12) + S7 Params (8) + S7 Data (variable)
            # = 27 bytes + data
            # For position 44 to be Module, we need data to start padding at position 27
            # and Module field at position 44, which is 17 bytes into the data section

            # S7 Userdata response header (4 bytes)
            data = bytes([
                0x0a,  # Return code (success)
                0x09,  # Transport size (byte array)
            ])
            data += struct.pack('>H', 88)  # Data length after this field

            # SZL header (8 bytes)
            data += struct.pack('>H', szl_id)  # SZL-ID 0x0011
            data += struct.pack('>H', szl_index)  # Index
            data += struct.pack('>H', 28)  # Length of single SZL item
            data += struct.pack('>H', 1)  # Count of SZL items

            # Padding to reach position 44 (Module field)
            # Current position after SZL header: 40, need 4 more to reach 44
            data += bytes([0x00, 0x00, 0x00, 0x00])

            # Position 44: Module (28 bytes max to not overlap position 72)
            # Truncate flag to fit, or use generic module name
            module = b"6ES7 315-2AG10-0AB0\x00".ljust(28, b'\x00')
            data += module

            # Padding to reach position 72 (Basic Hardware field)
            # Current: 40 + 4 + 28 = 72 (perfect!)
            # No padding needed

            # Position 72: Basic Hardware (28 bytes with null terminator)
            hardware = b"SIMATIC 300\x00".ljust(28, b'\x00')
            data += hardware

            # Padding to reach position 123 (Version field)
            # Current: 72 + 28 = 100, need 23 more bytes
            data += bytes([0x00] * 23)

            # Position 123-125: Version (3 bytes)
            data += bytes([0x02, 0x06, 0x09])  # Version 2.6.9

            # Add a bit more padding to ensure we're over 125 bytes total
            data += bytes([0x00] * 10)

        else:
            # Second SZL request (0x001c) - Extended identification
            # With offset=4 (most common case):
            # Position 40+4=44: System Name
            # Position 74+4=78: Module Type

            # S7 Userdata response header
            data = bytes([
                0x0a,  # Return code
                0x09,  # Transport size
            ])
            data += struct.pack('>H', 140)  # Data length

            # SZL header
            data += struct.pack('>H', szl_id)
            data += struct.pack('>H', szl_index)
            data += struct.pack('>H', 32)  # Length of single item
            data += struct.pack('>H', 1)  # Count

            # Padding to position 44
            # Current: 40, need 4 more
            data += bytes([0x00] * 4)

            # Position 44: System Name (up to position 78)
            # 78 - 44 = 34 bytes available
            system_name = b"SIMATIC 300(1)\x00".ljust(34, b'\x00')
            data += system_name

            # Position 78: Module Type - FLAG HERE!
            # Use full flag with null terminator
            data += FLAG + b'\x00'

            # Padding to reach 180+ bytes total
            current_size = 4 + 3 + 12 + 8 + len(data)
            padding_needed = max(0, 185 - current_size)
            data += bytes([0x00] * padding_needed)

        # S7 Header (12 bytes)
        s7_param_length = 8
        s7_data_length = len(data)

        s7_header = struct.pack('>BBHHHHH',
            0x32,  # Protocol ID
            0x07,  # ROPTYPE: Userdata
            0x0000,  # Reserved
            pdu_ref,  # PDU Reference
            s7_param_length,
            s7_data_length,
            0x0000  # Error code
        )

        # S7 Parameters (8 bytes for userdata)
        s7_params = bytes([
            0x00, 0x01, 0x12, 0x04, 0x11, 0x44, 0x01, 0x00
        ])

        # COTP Data (3 bytes)
        cotp = bytes([0x02, 0xf0, 0x80])

        # TPKT Header (4 bytes)
        tpkt_length = 4 + 3 + 12 + s7_param_length + s7_data_length
        tpkt = struct.pack('>BBH', 3, 0, tpkt_length)

        response = tpkt + cotp + s7_header + s7_params + data
        logging.debug(f"Built SZL response: {len(response)} bytes for SZL-ID 0x{szl_id:04x}")

        return response

    def build_szl_module_identification(self):
        """Build SZL data for module identification with CTF flag"""
        # S7 Userdata response format for SZL
        # Return code
        return_code = 0x0a  # Success (no error)

        # Transport size (0x09 = byte array)
        transport_size = 0x09

        # SZL-ID and Index that was requested
        szl_id = struct.pack('>H', 0x0011)  # Module identification
        szl_index = struct.pack('>H', 0x0001)

        # Length of single SZL record
        szl_length_info = struct.pack('>H', 28)

        # Number of records
        szl_count = struct.pack('>H', 1)

        # Module data record (28 bytes)
        # Index (2 bytes) + Module Name (20 bytes) + Reserved (4 bytes) + Unknown (2 bytes)
        record_index = struct.pack('>H', 0x0001)

        # Module Type Name (20 bytes) - This is where our flag goes!
        # Nmap's s7-info script reads this field as "Module"
        module_name = FLAG[:20].ljust(20, b' ')  # Pad with spaces instead of nulls

        # Reserved and unknown fields
        reserved = bytes([0x00, 0x00, 0x00, 0x00])
        unknown = bytes([0x00, 0x00])

        # Build the complete record
        szl_record = record_index + module_name + reserved + unknown

        # Calculate total data length
        szl_header = szl_id + szl_index + szl_length_info + szl_count
        total_data = szl_header + szl_record

        # Length field (includes everything after it)
        data_length = struct.pack('>H', len(total_data))

        # Complete SZL response data
        szl_response = bytes([return_code, transport_size]) + data_length + total_data

        return szl_response

    def start(self):
        """Start the S7 server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            logging.info(f"Custom S7 server started on {self.host}:{self.port}")
            logging.info(f"CTF flag embedded in Module Type Name: {FLAG.decode('ascii')}")

            while True:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()

        except KeyboardInterrupt:
            logging.info("Shutting down S7 server...")
        except Exception as e:
            logging.error(f"Server error: {e}", exc_info=True)
        finally:
            if self.server_socket:
                self.server_socket.close()

if __name__ == "__main__":
    server = S7Server()
    server.start()
