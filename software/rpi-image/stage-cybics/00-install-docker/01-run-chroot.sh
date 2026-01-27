#!/bin/bash -e

# Enable Docker service to start on boot
systemctl enable docker

# Add pi user to docker group so they can run docker without sudo
usermod -aG docker "${FIRST_USER_NAME}"
