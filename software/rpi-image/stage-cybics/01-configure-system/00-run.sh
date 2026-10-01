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

# Uplink to a central CTF server through a USB Wi-Fi dongle: keep the onboard
# radio on wlan0 and name the dongle ctfwlan0, ship its profile (autoconnect
# off until it is configured from the landing page), and isolate it.
install -d -m 755 "${ROOTFS_DIR}/etc/udev/rules.d"
install -m 644 files/70-cybics-wifi.rules "${ROOTFS_DIR}/etc/udev/rules.d/70-cybics-wifi.rules"
install -m 600 files/cybics-ctf-uplink.nmconnection "${ROOTFS_DIR}/etc/NetworkManager/system-connections/"
install -d -m 755 "${ROOTFS_DIR}/etc/cybics"
install -m 644 files/cybics-ctf-uplink.nft "${ROOTFS_DIR}/etc/cybics/cybics-ctf-uplink.nft"
install -m 644 files/cybics-ctf-uplink-firewall.service "${ROOTFS_DIR}/etc/systemd/system/cybics-ctf-uplink-firewall.service"
