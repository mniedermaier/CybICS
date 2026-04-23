#!/usr/bin/env python3
"""
Minimal OpenOCD-compatible telnet server for virtual STM32 mode.

Implements only the subset used by firmware-updater:
- program <path> verify reset 0x08000000
- exit
"""

import os
import shutil
import socketserver


FLASH_DIR = "/opt/cybics/firmware"
CURRENT_FW = os.path.join(FLASH_DIR, "current.bin")


class OpenOCDHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.wfile.write(b"Open On-Chip Debugger 0.12.0 (virtual)\n> ")
        self.wfile.flush()
        while True:
            line = self.rfile.readline()
            if not line:
                break

            cmd = line.decode(errors="ignore").strip()
            if not cmd:
                self.wfile.write(b"> ")
                self.wfile.flush()
                continue

            if cmd.startswith("program "):
                parts = cmd.split()
                if len(parts) < 2:
                    self.wfile.write(b"Error: missing firmware path\n> ")
                    self.wfile.flush()
                    continue

                source = parts[1]
                try:
                    os.makedirs(FLASH_DIR, exist_ok=True)
                    shutil.copyfile(source, CURRENT_FW)
                except OSError as exc:
                    self.wfile.write(f"Error: {exc}\n> ".encode())
                    self.wfile.flush()
                    continue

                self.wfile.write(b"** Programming Finished **\nverified\n> ")
                self.wfile.flush()
                continue

            if cmd == "exit":
                self.wfile.write(b"shutdown command invoked\n")
                self.wfile.flush()
                break

            self.wfile.write(b"Error: unsupported command\n> ")
            self.wfile.flush()


if __name__ == "__main__":
    with socketserver.ThreadingTCPServer(("0.0.0.0", 4444), OpenOCDHandler) as server:
        server.serve_forever()
