#!/bin/bash
#
# Flash STM32 firmware only if it differs from what's on the device.
# Compares only ELF LOAD segments (not padding) to avoid false mismatches.
# This avoids unnecessary flashing on every container restart.
#

ELF_FILE="/CybICS/CybICS.elf"
BIN_FILE="/CybICS/CybICS.bin"
OPENOCD_CFG="/CybICS/openocd_rpi.cfg"
FLASH_BASE="0x08000000"

echo "=== CybICS Firmware Flash Check ==="

# Parse ELF LOAD segments to get actual programmed regions
# Filter only flash segments (0x08xxxxxx)
# Format: PhysAddr FileSiz
SEGMENTS=$(readelf -l "$ELF_FILE" 2>/dev/null | grep "LOAD" | grep "0x080" | awk '{ print $4, $5 }')

if [ -z "$SEGMENTS" ]; then
    echo "Failed to parse ELF segments - reflashing required"
    NEEDS_FLASH="yes"
else
    echo "ELF LOAD segments:"
    echo "$SEGMENTS"

    NEEDS_FLASH="no"
    SEGMENT_NUM=0

    while read -r VADDR FILESZ; do
        SEGMENT_NUM=$((SEGMENT_NUM + 1))

        # Convert hex to decimal
        ADDR_DEC=$((VADDR))
        SIZE_DEC=$((FILESZ))

        # Skip zero-size segments
        if [ "$SIZE_DEC" -eq 0 ]; then
            continue
        fi

        # Calculate offset in binary file
        BIN_OFFSET=$((ADDR_DEC - FLASH_BASE))

        echo "Checking segment $SEGMENT_NUM: addr=$VADDR size=$SIZE_DEC offset=$BIN_OFFSET"

        FLASH_DUMP="/tmp/flash_seg${SEGMENT_NUM}.bin"
        BIN_EXTRACT="/tmp/bin_seg${SEGMENT_NUM}.bin"

        # Dump this segment from flash
        DUMP_OUTPUT=$(openocd -f "$OPENOCD_CFG" -c "
init
halt
dump_image $FLASH_DUMP $VADDR $SIZE_DEC
resume
shutdown
" 2>&1)

        if [ ! -f "$FLASH_DUMP" ]; then
            echo "Failed to dump segment $SEGMENT_NUM"
            NEEDS_FLASH="yes"
            break
        fi

        # Extract same region from binary
        dd if="$BIN_FILE" of="$BIN_EXTRACT" bs=1 skip="$BIN_OFFSET" count="$SIZE_DEC" 2>/dev/null

        # Compare
        if ! cmp -s "$BIN_EXTRACT" "$FLASH_DUMP"; then
            echo "Segment $SEGMENT_NUM differs"
            NEEDS_FLASH="yes"
            rm -f "$FLASH_DUMP" "$BIN_EXTRACT"
            break
        fi

        echo "Segment $SEGMENT_NUM matches"
        rm -f "$FLASH_DUMP" "$BIN_EXTRACT"

    done <<< "$SEGMENTS"
fi

# Perform flash if needed
if [ "$NEEDS_FLASH" = "no" ]; then
    echo "Skipping flash, firmware is up to date"
else
    echo "Flashing firmware..."
    # Use BIN file with explicit erase to ensure padding bytes are written as 0xFF
    if ! openocd -f "$OPENOCD_CFG" -c "program $BIN_FILE verify reset exit $FLASH_BASE"; then
        echo "ERROR: Flashing failed!"
        exit 1
    fi
    echo "Firmware flashed successfully"
    sleep 2
fi

echo "Starting OpenOCD GDB server..."
exec openocd -f "$OPENOCD_CFG"
