"""
Industrial protocol parsers for network packet analysis
"""
from utils.logger import logger

MODBUS_FUNCTIONS = {
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

MODBUS_EXCEPTIONS = {
    1: "Illegal Function",
    2: "Illegal Data Address",
    3: "Illegal Data Value",
    4: "Server Device Failure",
    5: "Acknowledge",
    6: "Server Device Busy",
    10: "Gateway Path Unavailable",
    11: "Gateway Target Failed to Respond",
}


def parse_modbus_tcp(payload):
    """Parse Modbus TCP: the first ADU in the segment, and how many there are.

    A client that pipelines requests, or a server answering them, puts
    several ADUs in one TCP segment; each is the 6-byte MBAP header plus the
    `length` it declares.
    """
    try:
        if len(payload) < 8:
            return None

        transaction_id = int.from_bytes(payload[0:2], 'big')
        protocol_id = int.from_bytes(payload[2:4], 'big')
        length = int.from_bytes(payload[4:6], 'big')
        unit_id = payload[6]
        function_code = payload[7]

        if function_code & 0x80:
            # An exception response: the function code with the top bit set,
            # then one byte saying what went wrong.
            base = function_code & 0x7F
            code = payload[8] if len(payload) > 8 else None
            reason = MODBUS_EXCEPTIONS.get(code, f"0x{code:02x}" if code is not None else "?")
            function_name = f"{MODBUS_FUNCTIONS.get(base, f'0x{base:02x}')} Exception: {reason}"
        else:
            function_name = MODBUS_FUNCTIONS.get(function_code, f"Unknown (0x{function_code:02x})")

        pdu_count = 0
        offset = 0
        while offset + 6 <= len(payload):
            adu_length = int.from_bytes(payload[offset + 4:offset + 6], 'big')
            if adu_length == 0:
                break
            pdu_count += 1
            offset += 6 + adu_length

        return {
            'transaction_id': transaction_id,
            'protocol_id': protocol_id,
            'length': length,
            'unit_id': unit_id,
            'function_code': function_code,
            'function_name': function_name,
            'exception': bool(function_code & 0x80),
            'pdu_count': max(pdu_count, 1),
        }
    except Exception as e:
        logger.debug(f"Error parsing Modbus: {e}")
        return None

COTP_PDU_TYPES = {
    0xE0: "Connection Request",
    0xD0: "Connection Confirm",
    0x80: "Disconnect Request",
    0xC0: "Disconnect Confirm",
    0xF0: "Data",
}


def parse_s7comm(payload):
    """Parse TPKT/COTP and, when the COTP data carries one, the S7comm header.

    Only COTP data PDUs carry S7comm, and its header starts with protocol ID
    0x32. The connection setup before it is COTP alone, which used to be
    labelled S7comm with an unknown message type.
    """
    try:
        if len(payload) < 10 or payload[0] != 3:
            return None

        tpkt_length = int.from_bytes(payload[2:4], 'big')
        cotp_pdu_type = payload[5] & 0xF0
        cotp_name = COTP_PDU_TYPES.get(cotp_pdu_type, f"Unknown (0x{cotp_pdu_type:02x})")

        result = {
            'tpkt_length': tpkt_length,
            'cotp_pdu_type': cotp_pdu_type,
            'message_type_name': cotp_name,
        }
        if cotp_pdu_type != 0xF0 or len(payload) < 12 or payload[7] != 0x32:
            return result

        message_type = payload[8]
        message_types = {
            1: "Job Request",
            2: "Ack",
            3: "Ack-Data",
            7: "Userdata"
        }
        result.update({
            'protocol_id': payload[7],
            'message_type': message_type,
            'message_type_name': message_types.get(message_type, f"Unknown (0x{message_type:02x})"),
        })
        return result
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
