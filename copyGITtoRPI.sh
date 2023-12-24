#!/bin/bash
IP=192.168.178.141
USER=pi
PASSWORD=raspberry

echo "This script connects to the CybICS Rasperry Pi and copies the complete GIT to /home/pi/gits/CybICS"
size="`du -hs ../CybICS`"
echo "Need to copy $size to $IP"
# get confirmation
echo "Press Enter within 5 seconds to terminate immediately."
read -t 5
read_exit_status=$?

if [ $read_exit_status = 0 ]; then
  echo "Enter pressed. Program terminated."
  exit
fi

echo "Removing old CybICS GIT"
sshpass -p $PASSWORD ssh $USER@$IP 'rm -rf /home/pi/gits/CybICS'
sshpass -p $PASSWORD ssh $USER@$IP 'mkdir -p /home/pi/gits'

echo "Copying CybICS GIT to Raspberry Pi"
sshpass -p $PASSWORD scp -rp ../CybICS $USER@$IP:/home/pi/gits
