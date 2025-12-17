# CybICS STM32 Development - Quick Start

## 🚀 Quick Commands

### Build Commands

```bash
# Build
cd /CybICS/software/stm32
west build -b nucleo_g070rb

# Clean build
west build -b nucleo_g070rb --pristine
```

### Flash Commands

```bash
# Flash to board
cd /CybICS/software/stm32
west flash
```

### Serial Monitor

```bash
# View serial output
screen /dev/ttyACM0 115200

# Or use minicom
minicom -D /dev/ttyACM0 -b 115200

# Exit screen: Ctrl+A, then K
```

## 📁 Project Locations

```
/CybICS/software/stm32/         # Zephyr project
~/zephyrproject/                # Zephyr workspace
```

## 🔧 Common West Commands

```bash
# Build
west build -b nucleo_g070rb

# Clean build
west build -b nucleo_g070rb --pristine

# Flash
west flash

# Debug
west debug

# Menuconfig
west build -t menuconfig

# List boards
west boards | grep stm32

# Update Zephyr
cd ~/zephyrproject
west update
```

## 🐛 Debugging

### GDB Debugging
```bash
cd /CybICS/software/stm32
west debug
```

## 📊 System Information

### Check Toolchains
```bash
# ARM GCC for Zephyr
arm-zephyr-eabi-gcc --version

# West
west --version
```

### Check Environment
```bash
# Show Zephyr environment
echo $ZEPHYR_BASE
echo $ZEPHYR_SDK_INSTALL_DIR

# Show build info
west list
```

## 🔑 Login Credentials

Default password for UART menu: `cyb`

## 🎯 Quick Test

After container starts:

```bash
# 1. Verify Zephyr is initialized
ls ~/zephyrproject/zephyr

# 2. Build Zephyr project
cd /CybICS/software/stm32
west build -b nucleo_g070rb

# 3. Check output
ls build/zephyr/zephyr.elf
```

## 💡 Tips

1. **Zephyr is pre-installed** - No download needed, instant container start
2. **Use ccache** - Subsequent builds are much faster
3. **Clean builds** - Use `--pristine` if you change major config options
4. **Parallel builds** - West uses all CPU cores by default
5. **VS Code tasks** - Use `Ctrl+Shift+B` for build tasks

## 🆘 Troubleshooting

### Build fails with missing SDK
```bash
ls /opt/zephyr-sdk/
# If empty, rebuild container
```

### West command not found
```bash
source ~/.bashrc
```

### Serial port not accessible
```bash
# Add your user to dialout group (on host)
sudo usermod -a -G dialout $USER
# Then logout/login
```

## 📚 Learn More

- Full documentation: `.devcontainer/stm32/README.md`
- Project details: `software/stm32/README.md`
- [Zephyr Docs](https://docs.zephyrproject.org/)
