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
ssh-keygen -f ~/.ssh/known_hosts -R "$DEVICE_IP"
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
    set -e
    sudo dphys-swapfile swapoff
    sudo sed -i s/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/g /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
EOF

echo "# Installing FUXA ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo apt-get update
    sudo apt-get install npm -y
    sudo npm install -g --unsafe-perm @frangoteam/fuxa
EOF

echo "# Config FUXA ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
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
echo "# Installing OpenPLC ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo apt-get install pigpio git -y
    mkdir -p /home/pi/gits
    cd /home/pi/gits
    sudo rm -rf OpenPLC_v3
    git clone https://github.com/thiagoralves/OpenPLC_v3.git
    cd /home/pi/gits/OpenPLC_v3

    git checkout 6621e30830e256dd271a5cf60e430164e080e7b0
    git apply /home/pi/gits/CybICS/software/OpenPLC/openplc.patch
    cp /home/pi/gits/CybICS/software/OpenPLC/openplc.db /home/pi/gits/OpenPLC_v3/webserver/openplc.db
    cp /home/pi/gits/CybICS/software/OpenPLC/cybICS.st /home/pi/gits/OpenPLC_v3/webserver/st_files/724870.st
    ./install.sh rpi
    cd /home/pi/gits/OpenPLC_v3/webserver
    ./scripts/change_hardware_layer.sh rpi
    ./scripts/compile_program.sh 724870.st
    sudo systemctl restart openplc.service
EOF


###
### Enable I2C
###
echo "# Enable I2C on the RPi ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo raspi-config nonint do_i2c 0
EOF

echo "# Config I2C script ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo apt-get install python3-netifaces python3-pymodbus python3-smbus -y

    sudo systemctl stop readI2Cpi.service | true    
    sudo tee /lib/systemd/system/readI2Cpi.service <<EOL
[Unit]
Description=readI2Cpi Service
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=1
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/gits/CybICS/software/scripts/readI2Cpi.py

[Install]
WantedBy=multi-user.target
EOL
    sudo systemctl daemon-reload
    sudo systemctl start readI2Cpi.service
    sudo systemctl enable readI2Cpi.service
EOF

###
### Installing GCC ARM
###
echo "# Installing GCC ARM NONE EABI on the RPi ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo apt-get install gcc-arm-none-eabi -y
EOF


###
### Installing openocd
###
echo "# Installing openocd on the RPi ..."
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash << EOF
    set -e
    sudo apt-get install openocd -y
EOF