#!/bin/bash

# Create destination directory and copy the built firmware to the Raspberry Pi
echo "Copying firmware to Raspberry Pi..."
ssh "$DEVICE_USER"@"$DEVICE_IP" "mkdir -p /home/pi/CybICS/software/stm32/build/zephyr"
scp build/zephyr/zephyr.bin "$DEVICE_USER"@"$DEVICE_IP":/home/pi/CybICS/software/stm32/build/zephyr/

# Start remote OpenOCD
echo "Starting remote OpenOCD..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    pidof openocd || sudo docker compose -f /home/pi/CybICS/docker-compose.yaml exec stm32 bash -c 'openocd -f /CybICS/openocd_rpi.cfg &'
EOF
