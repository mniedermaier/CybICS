#!/bin/bash
set -e

GIT_ROOT=$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")

echo "$GIT_ROOT"
source "$GIT_ROOT"/.dev.env

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

echo " Important:                         "
echo " Make sure, that the ENV variables  "
echo " are set correctly! (../.dev.env)   "


###
### Remove IP from known_hosts
###
ssh-keygen -f "/home/matt/.ssh/known_hosts" -R "$DEVICE_IP"
ssh-keyscan -H "$DEVICE_IP" >> ~/.ssh/known_hosts
ssh-copy-id -i ~/.ssh/id_rsa.pub "$DEVICE_USER"@"$DEVICE_IP"


###
### Copying CybICS Git to the target
###
echo "# Removing old CybICS GIT, if existing:" 
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    rm -rf /home/pi/gits/CybICS
    mkdir -p /home/pi/gits
EOF

echo "# Copying CybICS GIT to Raspberry Pi"
scp -rp "$GIT_ROOT" "$DEVICE_USER"@"$DEVICE_IP":/home/pi/gits


###
### FUXA installation
###
echo "# Increasing swap file ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    sudo dphys-swapfile swapoff
    sudo sed -i s/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/g /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
EOF

echo "# Installing FUXA ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    sudo apt-get update
    sudo apt-get install npm -y
    sudo npm install -g --unsafe-perm @frangoteam/fuxa
EOF

echo "# Config FUXA ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    sudo systemctl stop fuxa.service | true    
    sudo tee /lib/systemd/system/fuxa.service <<EOL
[Unit]
Description=FUXA Service
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=1
User=pi
WorkingDirectory=/home/pi
ExecStart=sudo /usr/local/bin/fuxa

[Install]
WantedBy=multi-user.target
EOL
    sudo systemctl daemon-reload
    sudo systemctl start fuxa.service
    sudo systemctl enable fuxa.service
EOF

echo "# Config FUXA project ..."
while ! curl -X POST -H "Content-Type: application/json" -d @"$GIT_ROOT"/software/FUXA/fuxa-project.json http://"$DEVICE_IP":1881/api/project
do
    echo "Waiting till FUXA is online ..."
    sleep 1
done


###
### OpenPLC installation
###
echo "# Cloning OpenPLC ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    mkdir -p /home/pi/gits
    cd /home/pi/gits
    rm -rf OpenPLC_v3
    git clone https://github.com/thiagoralves/OpenPLC_v3.git
    cp /home/pi/gits/CybICS/software/OpenPLC/raspberrypi.cpp /home/pi/gits/OpenPLC_v3/webserver/core/hardware_layers/raspberrypi.cpp
    cd /home/pi/gits/OpenPLC_v3
    ./install.sh rpi
EOF

echo "# Configuring OpenPLC ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    cd /home/pi/gits/OpenPLC_v3/webserver
    cp /home/pi/gits/CybICS/software/OpenPLC/cybICS.st st_files/ 
    rm -rf st_files/blank_program.st
    ./scripts/compile_program.sh cybICS.st
EOF


###
### Enable I2C
###
echo "# Enable I2C on the RPi ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo raspi-config nonint do_i2c 0
EOF


###
### Installing GCC ARM
###
echo "# Installing GCC ARM NONE EABI on the RPi ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo apt-get install gcc-arm-none-eabi
EOF


###
### Installing openocd
###
echo "# EInstalling openocd on the RPi ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo apt-get install openocd
EOF