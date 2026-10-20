#!/bin/bash -e

# Configure kernel command line for Docker memory cgroups
CMDLINE_FILE="/boot/firmware/cmdline.txt"
if [ -f "$CMDLINE_FILE" ]; then
    if ! grep -q "cgroup_enable=memory" "$CMDLINE_FILE"; then
        sed -i 's/$/ cgroup_enable=memory swapaccount=1/' "$CMDLINE_FILE"
    fi
fi

# Configure APT to avoid interactive prompts
echo 'Dpkg::Options {"--force-confdef";"--force-confold";};' > /etc/apt/apt.conf.d/local-config

# Enable I2C and load kernel modules
if command -v raspi-config &> /dev/null; then
    raspi-config nonint do_i2c 0
fi

# Ensure I2C kernel modules are loaded
cat > /etc/modules-load.d/i2c.conf << 'EOF'
i2c-dev
i2c_bcm2835
EOF

# Enable UART (hardware serial, disable console)
if command -v raspi-config &> /dev/null; then
    raspi-config nonint do_serial_hw 0
    raspi-config nonint do_serial_cons 1
fi

# Reduce GPU memory to minimum (headless system)
CONFIG_FILE="/boot/firmware/config.txt"
if [ -f "$CONFIG_FILE" ]; then
    if ! grep -q "^gpu_mem=" "$CONFIG_FILE"; then
        echo 'gpu_mem=16' >> "$CONFIG_FILE"
    fi
    # The board is headless. The Zero 2 W's device tree reserves 256 MB of CMA
    # by default - more than half its RAM - for the camera and display stack.
    # Unmovable kernel allocations cannot use it, so they compete for the other
    # ~190 MB, and the stack swapped heavily. Shrink it to cma-64, the overlay's
    # smallest preset (an unknown value such as cma-32 is silently ignored and
    # leaves 256 MB), drop the KMS driver, and stop probing for cameras,
    # displays and audio nobody connects.
    sed -i -e 's/^dtoverlay=vc4-kms-v3d.*$/dtoverlay=cma,cma-64/' \
           -e 's/^camera_auto_detect=1/camera_auto_detect=0/' \
           -e 's/^display_auto_detect=1/display_auto_detect=0/' \
           -e 's/^dtparam=audio=on/dtparam=audio=off/' "$CONFIG_FILE"
fi

# Services the board never uses; each holds memory on a 512 MB device.
for unit in bluetooth.service hciuart.service ModemManager.service udisks2.service; do
    systemctl disable "$unit" 2>/dev/null || true
done

# Enable NetworkManager
systemctl enable NetworkManager

# Configure dhcpcd to not manage wlan0 (let NetworkManager handle it)
# This prevents conflicts between dhcpcd and NetworkManager for WiFi
cat > /etc/dhcpcd.conf << 'EOF'
# Don't manage wlan0 - NetworkManager handles it
denyinterfaces wlan0
EOF

# Isolate the central CTF uplink (ctfwlan0) before any interface comes up.
# Only this table is loaded: Debian's nftables.service would flush the whole
# ruleset, including Docker's, so it stays disabled.
systemctl enable cybics-ctf-uplink-firewall.service
