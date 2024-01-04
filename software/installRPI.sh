#!/bin/bash
export $(grep -v '^#' ../.dev.env | xargs)

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
### Installing sshpass on the host
###
echo "# Installing sshpass on the host (root requried):"
sudo apt update  # To get the latest package lists
sudo apt install sshpass -y

###
### Copying CybICS Git to the target
###
echo "# Removing old CybICS GIT, if existing:" 
sshpass -p $DEVIDE_PASSWORD ssh $DEVICE_USER@$DEVICE_IP <<'EOL'
    "rm -rf /home/pi/gits/CybICS'
    "mkdir -p /home/pi/gits"
EOL

echo "# Copying CybICS GIT to Raspberry Pi"
sshpass -p $DEVIDE_PASSWORD scp -rp ../../CybICS $DEVICE_USER@$DEVICE_IP:/home/pi/gits
