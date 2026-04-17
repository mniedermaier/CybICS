#!/bin/bash -e

# Copy configuration files to rootfs (runs on host, not in chroot)

# ZRAM configuration
install -m 644 files/zramswap "${ROOTFS_DIR}/etc/default/zramswap"

# NetworkManager configuration
install -d -m 755 "${ROOTFS_DIR}/etc/NetworkManager"
install -m 644 files/NetworkManager.conf "${ROOTFS_DIR}/etc/NetworkManager/NetworkManager.conf"

# WiFi AP configuration for NetworkManager
install -d -m 755 "${ROOTFS_DIR}/etc/NetworkManager/system-connections"
install -m 600 files/cybics-ap.nmconnection "${ROOTFS_DIR}/etc/NetworkManager/system-connections/"
