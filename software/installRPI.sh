#!/bin/bash
set -e

# define colors
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
ENDCOLOR="\e[0m"

GIT_ROOT=$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")

# start time for calculation of the execution time
START=$(date +%s)

echo -ne "${MAGENTA}"
echo "                                    "
echo " Staring the                        "
echo "                                    "
echo "  CCC   Y   Y  BBB   II   CCC  SSSS "
echo " C       Y Y   B  B  II  C     S    "
echo " C        Y    BBB   II  C     SSSS "
echo " C        Y    B  B  II  C        S "
echo "  CCC     Y    BBB   II   CCC  SSSS "
echo "                                    "
echo " Installer                          "
echo "                                    "
echo " ################################## "
echo " Important:                         "
echo " Make sure, that the ENV variables  "
echo " are set correctly! (../.dev.env)   "
echo " ################################## "
echo -ne "${ENDCOLOR}"
echo -ne "${GREEN}"
echo " Grab a coffee, the initial installation "
echo " needs about 1 hour "
echo "     ~       "
echo "     ~       "
echo "   .---.     "
echo "   \`---'=.  "
echo "   |Cyb| |   "
echo "   |ICS|='   "
echo "   \`---'    "
echo -ne "${ENDCOLOR}"
sleep 1

###
### Check if raspberry is up
###
if ping -c 1 -W 5 "$DEVICE_IP" > /dev/null 2>&1; then
    echo -ne "${GREEN}# IP $DEVICE_IP is reachable.\n${ENDCOLOR}"
else
    echo -ne "${RED}#IP $DEVICE_IP is not reachable. Exiting.\n${ENDCOLOR}"
    exit 1
fi

###
### Remove IP from known_hosts and copy ssh key
###
echo -ne "${YELLOW}# Type in Raspberry Pi password, when requested (this will copy your SSH key to it): \n${ENDCOLOR}"
ssh-keygen -f ~/.ssh/known_hosts -R "$DEVICE_IP"
ssh-keyscan -H "$DEVICE_IP" >>~/.ssh/known_hosts
ssh-copy-id -i ~/.ssh/id_*.pub "$DEVICE_USER"@"$DEVICE_IP"

###
### Config locale
###
echo -ne "${GREEN}# Config locale ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    if grep LC_ALL /etc/environment; then
        exit 0
    fi
    echo "LC_ALL=en_US.UTF-8" | sudo tee /etc/environment
    echo "en_US.UTF-8 UTF-8" | sudo tee /etc/locale.gen
    echo "LANG=en_US.UTF-8" | sudo tee -a /etc/locale.conf
    sudo locale-gen en_US.UTF-8
EOF

###
### Stopping containers
###
echo -ne "${GREEN}# Stopping containers ... \n${ENDCOLOR}"
ssh -t "$DEVICE_USER"@"$DEVICE_IP" sudo docker compose -f /home/pi/CybICS/docker-compose.yaml down || true

###
### add some configs to the kernel command line
### this enables e.g. MEM USAGE values in `docker stats` output
###
echo -ne "${GREEN}# Configure kernel command line ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    if grep "cgroup_enable=memory swapaccount=1" /boot/firmware/cmdline.txt; then
        exit 0
    fi
    sudo sed -i ' 1 s/.*/& cgroup_enable=memory swapaccount=1/' /boot/firmware/cmdline.txt
EOF

###
### Increasing swap size
###
echo -ne "${GREEN}# Increasing swap file ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    if grep "CONF_SWAPSIZE=2048" /etc/dphys-swapfile; then
        exit 0
    fi
    sudo dphys-swapfile swapoff
    sudo sed -i s/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/g /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
EOF

###
### Update and upgrade
###
echo -ne "${GREEN}# Update and upgrade ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    sudo apt-get update && sudo apt-get upgrade -y
EOF

###
### Install tools
###
echo -ne "${GREEN}# Install tools ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    if ! which docker; then
        curl -fsSL https://get.Docker.com | bash
    fi

    if ! which tcpdump; then
        sudo apt-get install tcpdump -y
    fi

    if ! which btop; then
        sudo apt-get install btop -y
    fi

    if ! which socat; then
        sudo apt-get install socat -y
    fi

    if ! which lsof; then
        sudo apt-get install lsof -y
    fi
EOF

###
### Setup AP
###
echo -ne "${GREEN}# Setup AP ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF

    set -e
    if nmcli -g GENERAL.STATE c s cybics|grep -q -E '\bactiv';
    then
        exit
    fi

    sudo nmcli c del cybics || true
    sudo nmcli c add connection.id cybics \
     connection.interface-name \
     wlan0 type wifi \
     wifi.mode ap \
     wifi.ssid cybics \
     wifi-sec.key-mgmt wpa-psk \
     wifi-sec.psk 1234567890 \
     ipv4.addresses 10.0.0.1/24 \
     ipv4.method shared
EOF

###
### Enable I2C
###
echo -ne "${GREEN}# Enable I2C on the RPi ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    sudo raspi-config nonint do_i2c 0
EOF

###
### Decrease memmory of GPU
###
echo -ne "${GREEN}# Decrease memmory of GPU ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    grep -qF -- 'gpu_mem=16' '/boot/config.txt' || echo 'gpu_mem=16' | sudo tee -a '/boot/config.txt' > /dev/null
EOF

###
### Build container locally
###
echo -ne "${GREEN}# Build containers ... \n${ENDCOLOR}"
"$GIT_ROOT"/software/build.sh

###
### Install containers on the raspberry
###
echo -ne "${GREEN}# Install containers on the raspberry ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" mkdir -p /home/pi/CybICS
scp "$GIT_ROOT"/software/docker-compose.yaml "$DEVICE_USER"@"$DEVICE_IP":/home/pi/CybICS/docker-compose.yaml
ssh -R 5000:localhost:5000 -t "$DEVICE_USER"@"$DEVICE_IP" sudo docker compose -f /home/pi/CybICS/docker-compose.yaml pull

###
### Starting containers
###
echo -ne "${GREEN}# Starting containers ... \n${ENDCOLOR}"
ssh -t "$DEVICE_USER"@"$DEVICE_IP" sudo docker compose -f /home/pi/CybICS/docker-compose.yaml up -d --remove-orphans

###
### all done
###
END=$(date +%s)
DIFF=$(echo "$END - $START" | bc)
echo -ne "${GREEN}# Total execution time $((DIFF/60)):$((DIFF%60)) \n${ENDCOLOR}"
echo -ne "${GREEN}# All done, ready to rumble ... \n${ENDCOLOR}"

# Ask the user if they want to restart
read -p "Do you want to restart the system? (yes/no): " user_input

# Convert the user input to lowercase for easier matching
user_input=$(echo "$user_input" | tr '[:upper:]' '[:lower:]')

# Check the user input
if [[ "$user_input" == "yes" || "$user_input" == "y" ]]; then
    echo -ne "${RED}# Restarting the raspberry pi ... \n${ENDCOLOR}"
    timeout 20 ssh -t "$DEVICE_USER"@"$DEVICE_IP" sudo reboot -f || true
fi

echo -ne "${GREEN}# done ... \n${ENDCOLOR}"
