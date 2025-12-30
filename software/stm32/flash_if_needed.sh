#!/bin/bash
#
# Flash STM32 firmware only if build differs from what's on the device.
# Reads build timestamp from STM32 flash and compares with binary.
# This avoids halting the CPU unnecessarily on every container restart.
# Every new build gets a new timestamp, so development builds always flash.
#

BINARY="/CybICS/CybICS.bin"
OPENOCD_CFG="/CybICS/openocd_rpi.cfg"
FLASH_ADDR="0x08000000"

# Version magic marker: "CYBI" = 0x43594249 (little-endian: 49 42 59 43)
# Followed by "20" for year 20xx (32 30 in hex)
VERSION_MAGIC="494259433230"

# Build ID size (after magic): 24 bytes for timestamp string
BUILD_ID_SIZE=24

echo "=== CybICS Firmware Build Check ==="

# Find the version block offset in the binary by searching for magic + year prefix
MAGIC_OFFSET=$(xxd -p "$BINARY" | tr -d '\n' | grep -bo "$VERSION_MAGIC" | head -1 | cut -d: -f1)

if [ -z "$MAGIC_OFFSET" ]; then
    echo "WARNING: Version magic not found in binary, falling back to full verify"
    NEEDS_FLASH="unknown"
else
    # xxd output is hex, so offset is in hex characters (2 per byte)
    BYTE_OFFSET=$((MAGIC_OFFSET / 2))
    FLASH_VERSION_ADDR=$(printf "0x%08x" $((0x08000000 + BYTE_OFFSET)))

    echo "Binary version block at offset: $BYTE_OFFSET (flash: $FLASH_VERSION_ADDR)"

    # Extract expected build ID from binary (24 bytes after 4-byte magic)
    EXPECTED_BUILD_ID=$(xxd -p -s $((BYTE_OFFSET + 4)) -l $BUILD_ID_SIZE "$BINARY" | tr -d '\n')
    EXPECTED_BUILD_STR=$(xxd -r -p <<< "$EXPECTED_BUILD_ID" | tr -d '\0')
    echo "Expected build: $EXPECTED_BUILD_STR"

    # Read build ID from STM32 flash (magic + build_id = 28 bytes = 7 words)
    echo "Reading build ID from STM32 flash..."
    FLASH_DATA=$(openocd -f "$OPENOCD_CFG" -c "init; mdb $FLASH_VERSION_ADDR 28; shutdown" 2>&1)

    if echo "$FLASH_DATA" | grep -q "Error\|error\|failed"; then
        echo "WARNING: Failed to read from STM32, will attempt flash"
        NEEDS_FLASH="yes"
    else
        # Extract hex bytes from mdb output and convert to string
        FLASH_HEX=$(echo "$FLASH_DATA" | grep -oE '[0-9a-fA-F]{2}' | tr -d '\n')

        # First 8 hex chars (4 bytes) are magic
        FLASH_MAGIC="${FLASH_HEX:0:8}"
        # Next 48 hex chars (24 bytes) are build ID
        FLASH_BUILD_HEX="${FLASH_HEX:8:48}"
        FLASH_BUILD_STR=$(xxd -r -p <<< "$FLASH_BUILD_HEX" | tr -d '\0')

        echo "Flash magic: 0x$FLASH_MAGIC (expected: 0x49425943)"
        echo "Flash build: $FLASH_BUILD_STR"

        if [ "$FLASH_MAGIC" = "49425943" ] && [ "$FLASH_BUILD_HEX" = "$EXPECTED_BUILD_ID" ]; then
            echo "Build ID matches - no flash needed"
            NEEDS_FLASH="no"
        else
            echo "Build ID mismatch or invalid magic - flash required"
            NEEDS_FLASH="yes"
        fi
    fi
fi

# Perform flash if needed
if [ "$NEEDS_FLASH" = "no" ]; then
    echo "Skipping flash, firmware is up to date"
elif [ "$NEEDS_FLASH" = "unknown" ]; then
    # Fall back to full verify_image if we couldn't do version check
    echo "Performing full firmware verification..."
    VERIFY_OUTPUT=$(openocd -f "$OPENOCD_CFG" -c "init; verify_image $BINARY $FLASH_ADDR; shutdown" 2>&1)

    if echo "$VERIFY_OUTPUT" | grep -q "verified"; then
        echo "Firmware verified - already up to date"
    else
        echo "Firmware differs, flashing..."
        if ! openocd -f "$OPENOCD_CFG" -c "program $BINARY verify reset exit $FLASH_ADDR"; then
            echo "ERROR: Flashing failed!"
            exit 1
        fi
        echo "Firmware flashed successfully"
        sleep 2
    fi
else
    # Build mismatch - flash new firmware
    echo "Flashing new firmware..."
    if ! openocd -f "$OPENOCD_CFG" -c "program $BINARY verify reset exit $FLASH_ADDR"; then
        echo "ERROR: Flashing failed!"
        exit 1
    fi
    echo "Firmware flashed successfully"
    sleep 2
fi

echo "Starting OpenOCD GDB server..."
exec openocd -f "$OPENOCD_CFG"
