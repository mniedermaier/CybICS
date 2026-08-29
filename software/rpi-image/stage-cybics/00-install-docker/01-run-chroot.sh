#!/bin/bash -e

# Enable Docker service to start on boot
systemctl enable docker

# Add pi user to docker group so they can run docker without sudo
usermod -aG docker "${FIRST_USER_NAME}"

# Passwordless sudo, as stock Raspberry Pi OS sets up for its first user.
# pi-gen only writes this from the first-boot wizard, which this image
# deliberately skips (DISABLE_FIRST_BOOT_USER_RENAME=1), so without it the
# account lands in the sudo group but is prompted for a password - which
# breaks every non-interactive "ssh pi@device sudo ..." in installRPI.sh and
# in any remote administration of the board.
install -m 0440 /dev/stdin "/etc/sudoers.d/010_${FIRST_USER_NAME}-nopasswd" <<SUDOERS
${FIRST_USER_NAME} ALL=(ALL) NOPASSWD: ALL
SUDOERS
visudo -c -f "/etc/sudoers.d/010_${FIRST_USER_NAME}-nopasswd"
