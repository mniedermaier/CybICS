#!/bin/bash -e

# Configure kernel command line for Docker memory cgroups
CMDLINE_FILE="/boot/firmware/cmdline.txt"
if [ -f "$CMDLINE_FILE" ]; then
    if ! grep -q "cgroup_enable=memory" "$CMDLINE_FILE"; then
        sed -i 's/$/ cgroup_enable=memory swapaccount=1/' "$CMDLINE_FILE"
    fi
fi

# Enable ZRAM swap service
systemctl enable zramswap

# Configure APT to avoid interactive prompts
echo 'Dpkg::Options {"--force-confdef";"--force-confold";};' > /etc/apt/apt.conf.d/local-config

# Enable I2C
if command -v raspi-config &> /dev/null; then
    raspi-config nonint do_i2c 0
fi

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
fi

# Enable NetworkManager
systemctl enable NetworkManager
