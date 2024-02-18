#!/bin/bash
set -e

# define colors
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
ENDCOLOR="\e[0m"

GIT_ROOT=$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")

echo "$GIT_ROOT"
source "$GIT_ROOT"/.dev.env

# start time for calculation of the execution time
START=$(date +%s.%N)

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
sleep 1
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
### Remove IP from known_hosts and copy ssh key
###
echo -ne "${YELLOW}# Type in Raspberry Pi password, when requested (this will copy your SSH key to it): \n${ENDCOLOR}"
ssh-keygen -f ~/.ssh/known_hosts -R "$DEVICE_IP"
ssh-keyscan -H "$DEVICE_IP" >>~/.ssh/known_hosts
ssh-copy-id -i ~/.ssh/id_rsa.pub "$DEVICE_USER"@"$DEVICE_IP"

###
### Install docker
###
echo -ne "${GREEN}# Install docker ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    if ! which docker; then
        curl -fsSL https://get.Docker.com | bash
    fi
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
### Build container local and install on rasperry pi
###
echo -ne "${GREEN}# Build containers ... \n${ENDCOLOR}"
"$GIT_ROOT"/software/build.sh

echo -ne "${GREEN}# Install container ... \n${ENDCOLOR}"
ssh "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    mkdir -p /home/pi/CybICS
EOF

scp "$GIT_ROOT"/software/docker-compose.yaml "$DEVICE_USER"@"$DEVICE_IP":/home/pi/CybICS/docker-compose.yaml
ssh -R 5000:cybics-registry:5000 "$DEVICE_USER"@"$DEVICE_IP" /bin/bash <<EOF
    set -e
    cd /home/pi/CybICS
    sudo docker compose pull
    sudo docker compose up -d
EOF

###
### all done
###
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo -ne "${GREEN}# Total execution time $DIFF \n${ENDCOLOR}"
echo -ne "${GREEN}# All done, ready to rubmle ... \n${ENDCOLOR}"
