import snap7
import socket
import time
import ctypes
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure logging
format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

# Initialize Snap7 Server
server = snap7.server.Server()

# CTF Flag
FLAG = "CybICS(s7comm_analysis_complete)"

class FlagHandler(BaseHTTPRequestHandler):
    """HTTP handler that returns the CTF flag"""
    def version_string(self):
        """Override version string to return flag"""
        return FLAG

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(FLAG.encode())

    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

def start_flag_server():
    """Start HTTP server with flag on port 1102"""
    try:
        flag_server = HTTPServer(('0.0.0.0', 1102), FlagHandler)
        logging.info(f"HTTP flag server started on port 1102")
        flag_server.serve_forever()
    except Exception as e:
        logging.error(f"Flag server error: {e}")

def start_s7_fake_server():
    """
    Start a fake Siemens S7 PLC server that listens on TCP port 102.
    This allows detection by nmap with --script s7-info.
    """
    try:
        # Create data block with CTF flag embedded
        flag_data = b"CybICS(s7comm_analysis_complete)"
        size = 100
        db_data: CDataArrayType = (snap7.WordLen.Byte.ctype * size)()

        # Write flag into the data block
        for i, byte in enumerate(flag_data):
            if i < size:
                db_data[i] = byte

        # Register data block with flag
        server.register_area(snap7.SrvArea.DB, 1, db_data)

        # Start server listening on all interfaces (port 102)
        server.start_to("0.0.0.0")
        logging.info("Fake Siemens S7 PLC started on port 102 with CTF flag in data block...")

        while True:
            time.sleep(1)  # Keep the server running

    except KeyboardInterrupt:
        logging.info("Stopping fake S7 server...")
        server.stop()
        server.destroy()
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    # Start HTTP flag server in background thread
    flag_thread = threading.Thread(target=start_flag_server, daemon=True)
    flag_thread.start()

    # Start S7 server in main thread
    start_s7_fake_server()
