# CybICS STM32 Development Container

This devcontainer provides a complete Zephyr RTOS development environment for STM32 microcontrollers.

## Features

### Zephyr RTOS Development
- Zephyr v4.3.0 pre-installed (no download on startup)
- Zephyr SDK (ARM toolchain only, auto-installed via `west sdk install`)
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

The devcontainer opens in the pre-baked Zephyr workspace at `/home/docker/zephyrproject/app`.
Your source code is automatically mounted here.

```bash
# Build (already in the correct directory)
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

- `ZEPHYR_SDK_INSTALL_DIR=$HOME/zephyr-sdk-0.17.4` - Zephyr SDK location
- `ZEPHYR_TOOLCHAIN_VARIANT=zephyr` - Use Zephyr SDK toolchain
- `ZEPHYR_BASE=$HOME/zephyrproject/zephyr` - Zephyr source location

## Directory Structure

```
/CybICS/                    # Full repository (mounted read-write)
├── software/
│   └── stm32/              # Zephyr RTOS firmware source
└── .devcontainer/
    └── stm32/
        ├── Dockerfile      # Container definition (includes pre-baked Zephyr)
        ├── devcontainer.json
        ├── docker-compose.yml
        └── README.md       # This file

/home/docker/zephyrproject/ # Zephyr workspace (pre-installed in image)
├── app/                    # <- Your source mounted here (software/stm32)
├── zephyr/                 # Zephyr v4.3.0 source
├── modules/
│   ├── hal/
│   │   ├── cmsis/          # ARM CMSIS (Cortex-A/R)
│   │   ├── cmsis_6/        # ARM CMSIS-6 (Cortex-M)
│   │   └── stm32/          # STM32 HAL drivers
│   └── lib/
│       └── picolibc/       # C library
└── .west/                  # West workspace config
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

Zephyr version is defined in `software/stm32/west.yml` manifest. To update:

1. Edit `software/stm32/west.yml` and change the revision:
   ```yaml
   - name: zephyr
     revision: v4.3.0  # Change this
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
ls -la ~/zephyr-sdk-0.17.4
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

- Zephyr workspace is pre-baked into the Docker image - no initialization needed on start
- Your source code (software/stm32) is mounted into the pre-baked workspace
- Container starts are instant - no downloads required
- All development uses the Zephyr SDK toolchain (ARM only)
