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
    """
    try:
        size = 100
        db_data: CDataArrayType = (snap7.WordLen.Byte.ctype * size)()
        
        # Register fake data block
        server.register_area(snap7.SrvArea.DB, 1, db_data)

        # Start server listening on all interfaces (port 102)
        server.start_to("0.0.0.0")
        logging.info("Fake Siemens S7 PLC started on port 102...")

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
