# CybICS STM32 Development Container

This devcontainer provides a complete development environment for both FreeRTOS and Zephyr RTOS development on STM32 microcontrollers.

## Features

### FreeRTOS Development
- ARM GCC toolchain (`gcc-arm-none-eabi`)
- GDB multiarch for debugging
- STM32-specific VS Code extensions
- Build tools (make, cmake)

### Zephyr RTOS Development
- Zephyr SDK 0.16.5 (ARM Cortex-M support)
- West meta-tool
- KConfig and DeviceTree language support
- CMake and Ninja build system
- Automatic workspace initialization

## Getting Started

### 1. Open in Dev Container

1. Open VS Code in the CybICS repository
2. Press `F1` and select "Dev Containers: Reopen in Container"
3. Choose "CybICS-stm32"
4. Wait for the container to build and initialize (first time takes ~10 minutes)

The Zephyr workspace will be automatically initialized on first launch.

### 2. Building Projects

#### FreeRTOS Build (Original)
```bash
cd /CybICS/software/stm32
make
```

#### Zephyr Build (New Port)
```bash
cd /CybICS/software/stm32-zephyr
west build -b nucleo_g070rb
```

Or clean and rebuild:
```bash
west build -b nucleo_g070rb --pristine
```

### 3. Flashing

#### FreeRTOS
```bash
make flash
# or
openocd -f openocd.cfg -c "program build/cybics.elf verify reset exit"
```

#### Zephyr
```bash
west flash
# or
west flash --runner openocd
```

## Environment Variables

The following environment variables are automatically set:

- `ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk` - Zephyr SDK location
- `ZEPHYR_TOOLCHAIN_VARIANT=zephyr` - Use Zephyr SDK toolchain
- `ZEPHYR_BASE=$HOME/zephyrproject/zephyr` - Zephyr source location

## Directory Structure

```
/CybICS/
├── software/
│   ├── stm32/              # Original FreeRTOS firmware
│   └── stm32-zephyr/       # Zephyr RTOS port
└── .devcontainer/
    └── stm32/
        ├── Dockerfile      # Container definition
        ├── devcontainer.json
        ├── docker-compose.yml
        ├── init-zephyr.sh  # Zephyr initialization script
        └── README.md       # This file

/home/docker/
└── zephyrproject/          # Zephyr workspace (auto-created)
    ├── zephyr/             # Zephyr source
    ├── bootloader/
    ├── modules/
    └── tools/
```

## Installed Tools

### Build Tools
- `make` - GNU Make
- `cmake` - CMake build system
- `ninja` - Fast build system
- `west` - Zephyr meta-tool

### Compilers
- `arm-none-eabi-gcc` - ARM GCC for bare metal
- `arm-zephyr-eabi-gcc` - ARM GCC from Zephyr SDK

### Debugging
- `gdb-multiarch` - Multi-architecture GDB
- `openocd` - On-chip debugger (if available)

### Python Packages
- `west` - Zephyr meta-tool
- `pymodbus` - Modbus library
- `flask` - Web framework
- Various Zephyr dependencies

## VS Code Extensions

The following extensions are automatically installed:

### General
- GitLens
- Python

### C/C++ Development
- C/C++ Extension Pack
- C/C++ Tools
- C/C++ Themes

### STM32/FreeRTOS
- STM32 for VSCode
- MCU Debug Tracker
- RTOS Views
- Peripheral Viewer

### Zephyr
- Kconfig Language Support
- DeviceTree Language Support

## Manual Zephyr Re-initialization

If you need to reinitialize the Zephyr workspace:

```bash
# Remove existing workspace
rm -rf ~/zephyrproject

# Run initialization script
bash /CybICS/.devcontainer/stm32/init-zephyr.sh
```

## Troubleshooting

### "west: command not found"
Restart your terminal or run:
```bash
source ~/.bashrc
```

### Build fails with "ZEPHYR_BASE not set"
Set the environment variable:
```bash
export ZEPHYR_BASE=$HOME/zephyrproject/zephyr
```

### Zephyr SDK not found
Check that the SDK is installed:
```bash
ls -la /opt/zephyr-sdk
```

If missing, rebuild the container.

### Permission issues
The container uses `fixuid` to match host and container user IDs. If you encounter permission issues, check:
```bash
id
ls -la /CybICS
```

## Advanced Configuration

### Changing Zephyr Version

Edit `init-zephyr.sh` and modify the `--mr` parameter:
```bash
west init -m https://github.com/zephyrproject-rtos/zephyr --mr v3.6.0
```

### Using Different Board

To build for a different board:
```bash
west build -b <board_name>
```

List available boards:
```bash
west boards | grep stm32
```

### Menuconfig

Configure Zephyr project options:
```bash
west build -t menuconfig
```

Or edit `prj.conf` directly.

## Resources

- [Zephyr Documentation](https://docs.zephyrproject.org/)
- [Zephyr Getting Started](https://docs.zephyrproject.org/latest/develop/getting_started/index.html)
- [STM32 Nucleo G070RB](https://docs.zephyrproject.org/latest/boards/st/nucleo_g070rb/doc/index.html)
- [West Tool](https://docs.zephyrproject.org/latest/develop/west/index.html)

## Notes

- The container includes both ARM GCC toolchains (bare metal and Zephyr)
- Zephyr workspace initialization happens automatically on first container start
- Both FreeRTOS and Zephyr projects can be developed in the same container
- The workspace is persistent across container restarts (stored in the host filesystem)
