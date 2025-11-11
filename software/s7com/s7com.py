import snap7
import socket
import time
import ctypes
import logging

# Configure logging
format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

# Initialize Snap7 Server
server = snap7.server.Server()

def start_s7_fake_server():
    """
    Start a fake Siemens S7 PLC server that listens on TCP port 102.
    This allows detection by nmap with --script s7-info.
    The CTF flag is stored in Data Block 1 (DB1).
    """
    try:
        # CTF Flag stored in DB1
        flag = b"CybICS(s7comm_analysis_complete)"
        size = 100
        db_data = (snap7.WordLen.Byte.ctype * size)()

        # Write flag into the data block starting at offset 0
        for i, byte in enumerate(flag):
            if i < size:
                db_data[i] = byte

        # Register data block 1 with flag
        server.register_area(snap7.SrvArea.DB, 1, db_data)

        # Start server listening on all interfaces (port 102)
        server.start_to("0.0.0.0")
        logging.info(f"Fake Siemens S7 PLC started on port 102")
        logging.info(f"CTF flag stored in DB1 (Data Block 1), offset 0, length {len(flag)} bytes")

        while True:
            time.sleep(1)  # Keep the server running

    except KeyboardInterrupt:
        logging.info("Stopping fake S7 server...")
        server.stop()
        server.destroy()
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    start_s7_fake_server()
