"""
Industrial protocol parsers for network packet analysis
"""
from utils.logger import logger

def parse_modbus_tcp(payload):
    """Parse Modbus TCP protocol"""
    try:
        if len(payload) < 8:
            return None

        transaction_id = int.from_bytes(payload[0:2], 'big')
        protocol_id = int.from_bytes(payload[2:4], 'big')
        length = int.from_bytes(payload[4:6], 'big')
        unit_id = payload[6]
        function_code = payload[7]

        function_names = {
            1: "Read Coils",
            2: "Read Discrete Inputs",
            3: "Read Holding Registers",
            4: "Read Input Registers",
            5: "Write Single Coil",
            6: "Write Single Register",
            15: "Write Multiple Coils",
            16: "Write Multiple Registers",
            23: "Read/Write Multiple Registers"
        }

        return {
            'transaction_id': transaction_id,
            'protocol_id': protocol_id,
            'length': length,
            'unit_id': unit_id,
            'function_code': function_code,
            'function_name': function_names.get(function_code, f"Unknown (0x{function_code:02x})")
        }
    except Exception as e:
        logger.debug(f"Error parsing Modbus: {e}")
        return None

def parse_s7comm(payload):
    """Parse S7comm protocol"""
    try:
        if len(payload) < 10:
            return None

        # TPKT header
        tpkt_version = payload[0]
        tpkt_reserved = payload[1]
        tpkt_length = int.from_bytes(payload[2:4], 'big')

        # COTP header
        cotp_length = payload[4]
        cotp_pdu_type = payload[5]

        if len(payload) < 12:
            return {'protocol': 'S7comm', 'type': 'COTP'}

        # S7comm header
        protocol_id = payload[7]
        message_type = payload[8]

        message_types = {
            1: "Job Request",
            2: "Ack",
            3: "Ack-Data",
            7: "Userdata"
        }

        return {
            'tpkt_length': tpkt_length,
            'protocol_id': protocol_id,
            'message_type': message_type,
            'message_type_name': message_types.get(message_type, f"Unknown (0x{message_type:02x})")
        }
    except Exception as e:
        logger.debug(f"Error parsing S7comm: {e}")
        return None

def parse_opcua(payload):
    """Parse OPC-UA protocol"""
    try:
        if len(payload) < 8:
            return None

        # OPC-UA header
        message_type = payload[0:3].decode('ascii', errors='ignore')
        chunk_type = chr(payload[3]) if payload[3] < 128 else '?'
        message_size = int.from_bytes(payload[4:8], 'little')

        message_types_map = {
            'HEL': 'Hello',
            'ACK': 'Acknowledge',
            'ERR': 'Error',
            'RHE': 'Reverse Hello',
            'OPN': 'Open Secure Channel',
            'CLO': 'Close Secure Channel',
            'MSG': 'Message'
        }

        chunk_types = {
            'F': 'Final',
            'C': 'Continue',
            'A': 'Abort'
        }

        return {
            'message_type': message_type,
            'message_type_name': message_types_map.get(message_type, message_type),
            'chunk_type': chunk_type,
            'chunk_type_name': chunk_types.get(chunk_type, 'Unknown'),
            'message_size': message_size
        }
    except Exception as e:
        logger.debug(f"Error parsing OPC-UA: {e}")
        return None

def parse_enip(payload):
    """Parse EtherNet/IP protocol"""
    try:
        if len(payload) < 24:
            return None

        command = int.from_bytes(payload[0:2], 'little')
        length = int.from_bytes(payload[2:4], 'little')
        session_handle = int.from_bytes(payload[4:8], 'little')
        status = int.from_bytes(payload[8:12], 'little')

        commands = {
            0x0001: "NOP",
            0x0004: "ListServices",
            0x0063: "ListIdentity",
            0x0064: "ListInterfaces",
            0x0065: "RegisterSession",
            0x0066: "UnregisterSession",
            0x006F: "SendRRData",
            0x0070: "SendUnitData"
        }

        return {
            'command': command,
            'command_name': commands.get(command, f"Unknown (0x{command:04x})"),
            'length': length,
            'session_handle': session_handle,
            'status': status
        }
    except Exception as e:
        logger.debug(f"Error parsing EtherNet/IP: {e}")
        return None
