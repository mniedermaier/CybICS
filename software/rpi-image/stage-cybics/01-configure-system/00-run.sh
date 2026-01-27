#!/bin/bash -e

# Copy configuration files to rootfs (runs on host, not in chroot)

# ZRAM configuration
install -m 644 files/zramswap "${ROOTFS_DIR}/etc/default/zramswap"

# WiFi AP configuration for NetworkManager
mkdir -p "${ROOTFS_DIR}/etc/NetworkManager/system-connections"
install -m 600 files/cybics-ap.nmconnection "${ROOTFS_DIR}/etc/NetworkManager/system-connections/"
