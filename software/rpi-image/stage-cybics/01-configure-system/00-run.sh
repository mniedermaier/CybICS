#!/bin/bash -e

# Copy configuration files to rootfs (runs on host, not in chroot)

# No zram configuration here: on Trixie rpi-swap sets up /dev/zram0 (zstd, with
# writeback to /var/swap). zram-tools used to be installed next to it with an
# lz4 config, and its zramswap.service failed on every boot because the device
# was already in use - the lz4 setting never took effect.

# Docker: route published ports with iptables only. The userland proxy starts
# one docker-proxy process per port and address family, 35 on this stack,
# which held ~50 MB on a board with 463 MB of RAM.
install -d -m 755 "${ROOTFS_DIR}/etc/docker"
install -m 644 files/daemon.json "${ROOTFS_DIR}/etc/docker/daemon.json"

# Keep the journal across reboots (Raspberry Pi OS makes it volatile), capped so
# it costs little on the SD card. Without it a watchdog reset leaves no trace.
install -d -m 755 "${ROOTFS_DIR}/etc/systemd/journald.conf.d"
install -m 644 files/50-cybics-persistent.conf "${ROOTFS_DIR}/etc/systemd/journald.conf.d/"

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

# Uplink to a CybICS-mgmt server through a USB Wi-Fi dongle: keep the onboard
# radio on wlan0 and name the dongle ctfwlan0, ship its profile (the default
# network cybics-mgmt, autoconnect on; changeable from the landing page), and
# isolate it.
install -d -m 755 "${ROOTFS_DIR}/etc/udev/rules.d"
install -m 644 files/70-cybics-wifi.rules "${ROOTFS_DIR}/etc/udev/rules.d/70-cybics-wifi.rules"
install -m 600 files/cybics-ctf-uplink.nmconnection "${ROOTFS_DIR}/etc/NetworkManager/system-connections/"
install -d -m 755 "${ROOTFS_DIR}/etc/cybics"
install -m 644 files/cybics-ctf-uplink.nft "${ROOTFS_DIR}/etc/cybics/cybics-ctf-uplink.nft"
install -m 644 files/cybics-ctf-uplink-firewall.service "${ROOTFS_DIR}/etc/systemd/system/cybics-ctf-uplink-firewall.service"
