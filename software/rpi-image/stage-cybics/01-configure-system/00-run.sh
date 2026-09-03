#!/bin/bash -e

# Copy configuration files to rootfs (runs on host, not in chroot)

# ZRAM configuration
install -m 644 files/zramswap "${ROOTFS_DIR}/etc/default/zramswap"

# NetworkManager configuration
install -d -m 755 "${ROOTFS_DIR}/etc/NetworkManager"
install -m 644 files/NetworkManager.conf "${ROOTFS_DIR}/etc/NetworkManager/NetworkManager.conf"
install -d -m 755 "${ROOTFS_DIR}/etc/NetworkManager/conf.d"
install -m 644 files/10-docker-unmanaged.conf "${ROOTFS_DIR}/etc/NetworkManager/conf.d/10-docker-unmanaged.conf"

# WiFi AP configuration for NetworkManager
install -d -m 755 "${ROOTFS_DIR}/etc/NetworkManager/system-connections"
install -m 600 files/cybics-ap.nmconnection "${ROOTFS_DIR}/etc/NetworkManager/system-connections/"

# Station mode profile. hardwareIO.py switches between this and the AP based on
# the STM32 mode button; without it the switch has nothing to switch to.
install -m 600 files/cybics-station.nmconnection "${ROOTFS_DIR}/etc/NetworkManager/system-connections/"
