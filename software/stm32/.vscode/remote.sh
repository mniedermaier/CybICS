#!/bin/bash

echo start remote openocd
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    pidof openocd || sudo docker compose -f /home/pi/CybICS/docker-compose.yaml exec stm32 bash -c 'openocd -f /CybICS/openocd_rpi.cfg &'
EOF
