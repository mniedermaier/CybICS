# CybICS STM32 Development Container

This devcontainer provides a complete Zephyr RTOS development environment for STM32 microcontrollers.

## Features

### Zephyr RTOS Development
- Zephyr v4.3.0 pre-installed (no download on startup)
- Zephyr SDK 0.17.4 (ARM Cortex-M support)
- West meta-tool
- KConfig and DeviceTree language support
- CMake and Ninja build system

## Getting Started

### 1. Open in Dev Container

1. Open VS Code in the CybICS repository
2. Press `F1` and select "Dev Containers: Reopen in Container"
3. Choose "CybICS-stm32"
4. First build takes ~15-20 minutes (Zephyr is pre-baked into the image)

Subsequent container starts are instant - no downloads required.

### 2. Building Projects

```bash
cd /CybICS/software/stm32
west build -b nucleo_g070rb
```

Or clean and rebuild:
```bash
west build -b nucleo_g070rb --pristine
```

### 3. Flashing

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
│   └── stm32/              # Zephyr RTOS firmware
└── .devcontainer/
    └── stm32/
        ├── Dockerfile      # Container definition (includes pre-baked Zephyr)
        ├── devcontainer.json
        ├── docker-compose.yml
        └── README.md       # This file

/home/docker/
└── zephyrproject/          # Zephyr workspace (pre-installed in image)
    ├── zephyr/             # Zephyr v4.3.0 source
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
- `arm-zephyr-eabi-gcc` - ARM GCC from Zephyr SDK

### Debugging
- `gdb-multiarch` - Multi-architecture GDB (via Zephyr SDK)
- `openocd` - On-chip debugger (if available)

### Python Packages
- `west` - Zephyr meta-tool
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

### Zephyr
- Kconfig Language Support
- DeviceTree Language Support

## Updating Zephyr Version

Zephyr is pre-baked into the Docker image. To update:

1. Edit `.devcontainer/stm32/Dockerfile` and change `ZEPHYR_VERSION`:
   ```dockerfile
   ARG ZEPHYR_VERSION=v4.3.0
   ```

2. Rebuild the container:
   - VS Code: `F1` → "Dev Containers: Rebuild Container"
   - Or: `docker compose build --no-cache`

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

- Zephyr workspace initialization happens automatically on first container start
- The workspace is persistent across container restarts (stored in the host filesystem)
- All development uses the Zephyr SDK toolchain
