#!/bin/bash
#
# Flash STM32 firmware only if it differs from what's currently on the device
#

BINARY="/CybICS/CybICS.bin"
OPENOCD_CFG="/CybICS/openocd_rpi.cfg"
FLASH_ADDR="0x08000000"

echo "Checking if firmware update is needed..."

# Try to verify the image against what's on the STM32
# verify_image returns success if the flash contents match the file
VERIFY_OUTPUT=$(openocd -f "$OPENOCD_CFG" -c "init; verify_image $BINARY $FLASH_ADDR; shutdown" 2>&1)
VERIFY_RESULT=$?

if echo "$VERIFY_OUTPUT" | grep -q "verified"; then
    echo "Firmware already up to date, skipping flash"
else
    echo "Firmware differs or verification failed, flashing..."
    echo "$VERIFY_OUTPUT" | tail -5

    # Flash the new firmware
    if ! openocd -f "$OPENOCD_CFG" -c "program $BINARY verify reset exit $FLASH_ADDR"; then
        echo "ERROR: Flashing failed!"
        exit 1
    fi

    echo "Firmware flashed successfully"
    sleep 2
fi

echo "Starting OpenOCD GDB server..."
exec openocd -f "$OPENOCD_CFG"
