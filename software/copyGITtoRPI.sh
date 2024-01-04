#!/bin/bash
export $(grep -v '^#' ../.dev.env | xargs)

echo "This script connects to the CybICS Rasperry Pi and copies the complete GIT to /home/pi/gits/CybICS"
size="`du -hs ../../CybICS`"
echo "Need to copy $size to $DEVICE_IP"
# get confirmation
echo "Press Enter within 5 seconds to terminate immediately."
read -t 5
read_exit_status=$?

if [ $read_exit_status = 0 ]; then
  echo "Enter pressed. Program terminated."
  exit
fi

echo "Removing old CybICS GIT"
sshpass -p $DEVIDE_PASSWORD ssh $DEVICE_USER@$DEVICE_IP 'rm -rf /home/pi/gits/CybICS'
sshpass -p $DEVIDE_PASSWORD ssh $DEVICE_USER@$DEVICE_IP 'mkdir -p /home/pi/gits'

echo "Copying CybICS GIT to Raspberry Pi"
sshpass -p $DEVIDE_PASSWORD scp -rp ../../CybICS $DEVICE_USER@$DEVICE_IP:/home/pi/gits
