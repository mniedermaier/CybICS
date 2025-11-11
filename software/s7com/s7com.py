#!/usr/bin/env python3
"""
S7 Communication Server
Uses custom S7 protocol implementation to embed CTF flag in module identification
"""

from s7_server_custom import S7Server

if __name__ == "__main__":
    server = S7Server(host='0.0.0.0', port=1102)
    server.start()
