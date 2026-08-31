# CybICS STM32 Firmware

## Overview
The STM32 firmware runs on the CybICS PCB and simulates the physical process (gas pressure control system). It runs on a STM32G070RB microcontroller using Zephyr RTOS.

## Hardware
- **Board**: STM32 Nucleo G070RB
- **MCU**: STM32G070RBTx (ARM Cortex-M0+, 64MHz)
- **Memory**: 128KB Flash, 36KB RAM
- **Communication**: UART (115200 baud), I2C (100kHz)

## Features
- Simulates industrial pressure control system
- 16x2 LCD display with system information
- LED indicators for process visualization
- UART menu interface (password: `cyb`)
- I2C communication with Raspberry Pi

## Building the Firmware

### Using VS Code Dev Container (Recommended)

1. Open the repository in VS Code
2. Press `F1` → "Dev Containers: Reopen in Container"
3. Choose "CybICS-stm32"
4. Build and flash:
   ```bash
   west build -b nucleo_g070rb
   west flash
   ```

### Using Docker (Raspberry Pi)

For automated flashing via Raspberry Pi GPIO:

```bash
cd software/stm32
./build-docker.sh
docker run --privileged -p 3333:3333 localhost:5050/cybics-stm32:latest
```

**SWD Connections (Raspberry Pi → STM32):**
- GPIO 25 → SWCLK
- GPIO 24 → SWDIO
- GPIO 18 → NRST
- GND → GND

### Manual Build

If you have Zephyr SDK installed:

```bash
cd software/stm32
west build -b nucleo_g070rb
west flash
west attach  # View serial output
```

## Configuration

Edit `prj.conf` to change settings:

```ini
CONFIG_HEAP_MEM_POOL_SIZE=8192        # Heap size
CONFIG_MAIN_STACK_SIZE=2048           # Stack size
CONFIG_LOG_DEFAULT_LEVEL=3            # Log level (0-4)
CONFIG_SYS_CLOCK_HW_CYCLES_PER_SEC=64000000  # 64 MHz
```

## Debugging

### Enable debug logging
Edit `prj.conf`:
```ini
CONFIG_LOG_DEFAULT_LEVEL=4
CONFIG_LOG_MODE_IMMEDIATE=y
```

## Related Documentation
- [Hardware Overview](../../hardware/README.md)
- [Raspberry Pi I/O Bridge](../hwio-raspberry/README.md)
- [Zephyr Documentation](https://docs.zephyrproject.org/)