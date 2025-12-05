# CybICS STM32 Development - Quick Start

## 🚀 Quick Commands

### Build Commands

```bash
# FreeRTOS (original)
cd /CybICS/software/stm32
make

# Zephyr (new port)
cd /CybICS/software/stm32-zephyr
west build -b nucleo_g070rb

# Clean build
west build -b nucleo_g070rb --pristine
```

### Flash Commands

```bash
# FreeRTOS
cd /CybICS/software/stm32
make flash

# Zephyr
cd /CybICS/software/stm32-zephyr
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
/CybICS/software/stm32/         # FreeRTOS project
/CybICS/software/stm32-zephyr/  # Zephyr project
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

### GDB Debugging (FreeRTOS)
```bash
cd /CybICS/software/stm32
arm-none-eabi-gdb build/cybics.elf
```

### GDB Debugging (Zephyr)
```bash
cd /CybICS/software/stm32-zephyr
west debug
```

## 📊 System Information

### Check Toolchains
```bash
# ARM GCC for FreeRTOS
arm-none-eabi-gcc --version

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

## 📝 Project Structure Comparison

| Feature | FreeRTOS | Zephyr |
|---------|----------|--------|
| RTOS API | CMSIS-RTOS v1 | Zephyr Kernel |
| HAL | STM32 HAL | Zephyr Drivers |
| Build | Make | West/CMake |
| Config | FreeRTOSConfig.h | prj.conf |
| Pins | main.h | DeviceTree |
| Threads | 7 tasks | 7 threads |

## 🎯 Quick Test

After container starts:

```bash
# 1. Verify Zephyr is initialized
ls ~/zephyrproject/zephyr

# 2. Build Zephyr project
cd /CybICS/software/stm32-zephyr
west build -b nucleo_g070rb

# 3. Check output
ls build/zephyr/zephyr.elf
```

## 💡 Tips

1. **First build takes longer** - Zephyr downloads and builds all dependencies
2. **Use ccache** - Subsequent builds are much faster
3. **Clean builds** - Use `--pristine` if you change major config options
4. **Parallel builds** - West uses all CPU cores by default
5. **VS Code tasks** - Use `Ctrl+Shift+B` for build tasks

## 🆘 Troubleshooting

### Zephyr not initialized
```bash
bash /CybICS/.devcontainer/stm32/init-zephyr.sh
```

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
- Zephyr port details: `software/stm32-zephyr/README.md`
- [Zephyr Docs](https://docs.zephyrproject.org/)
