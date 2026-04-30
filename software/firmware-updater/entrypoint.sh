#!/bin/bash
# CybICS Firmware Update Service – container entrypoint
#
# 1. Generates a random 16-byte MAC secret key on first run.
# 2. Starts the Python update daemon.

set -e

KEY_FILE="/opt/cybics/keys/update.key"
KEY_DIR="$(dirname "$KEY_FILE")"

if [ ! -f "$KEY_FILE" ]; then
    echo "[entrypoint] Generating 16-byte MAC secret key..."
    mkdir -p "$KEY_DIR"
    dd if=/dev/urandom bs=16 count=1 of="$KEY_FILE" 2>/dev/null
    chmod 600 "$KEY_FILE"
    echo "[entrypoint] MAC key written to $KEY_FILE"
fi

mkdir -p /opt/cybics/firmware /opt/cybics/logs

exec python3 /opt/cybics/update-service/update_daemon.py
