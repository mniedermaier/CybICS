#!/bin/bash
#
# flash_firmware.sh – Flash STM32 firmware via the running OpenOCD telnet server.
#
# This script is the firmware-updater counterpart to flash_if_needed.sh in the
# stm32 container.  While flash_if_needed.sh starts a new OpenOCD instance
# with a local Raspberry Pi GPIO hardware adapter:
#
#   openocd -f "$OPENOCD_CFG" -c "program $BIN_FILE verify reset exit $FLASH_BASE"
#
# this script sends the equivalent `program` command to the already-running
# OpenOCD server over its telnet interface (port 4444).  This is necessary
# because the firmware-updater runs in a separate container and has no direct
# access to the SWD/JTAG hardware adapter.
#
# Usage: flash_firmware.sh <firmware_path>
#
# Environment variables:
#   OPENOCD_HOST        – hostname/IP of the OpenOCD server (default: stm32)
#   OPENOCD_TELNET_PORT – OpenOCD telnet port            (default: 4444)
#   FLASH_BASE          – flash start address            (default: 0x08000000)
#   FLASH_TIMEOUT       – maximum wait in seconds        (default: 120)

set -euo pipefail

FIRMWARE_PATH="${1:?usage: flash_firmware.sh <firmware_path>}"
OPENOCD_HOST="${OPENOCD_HOST:-stm32}"
OPENOCD_PORT="${OPENOCD_TELNET_PORT:-4444}"
FLASH_BASE="${FLASH_BASE:-0x08000000}"
FLASH_TIMEOUT="${FLASH_TIMEOUT:-120}"

echo "=== CybICS Firmware Flash ==="
echo "Firmware  : $FIRMWARE_PATH"
echo "OpenOCD   : $OPENOCD_HOST:$OPENOCD_PORT"
echo "Flash base: $FLASH_BASE"

# Pipe the program command to the running OpenOCD telnet server and capture
# the full output.  When nc's stdin (the printf pipe) closes, OpenOCD
# processes the `exit` command and terminates the session, allowing nc to
# exit cleanly.
OUTPUT=$(printf "program %s verify reset %s\nexit\n" \
        "$FIRMWARE_PATH" "$FLASH_BASE" | \
    timeout "$FLASH_TIMEOUT" nc -q 1 "$OPENOCD_HOST" "$OPENOCD_PORT" 2>&1) || {
    echo "ERROR: Could not connect to OpenOCD at $OPENOCD_HOST:$OPENOCD_PORT" >&2
    exit 1
}

echo "$OUTPUT"

if echo "$OUTPUT" | grep -q "Programming Finished"; then
    echo "Flashing completed successfully"
    exit 0
else
    echo "ERROR: Flashing may have failed. See OpenOCD output above." >&2
    exit 1
fi
