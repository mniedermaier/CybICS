# CybICS STM32 Zephyr Port

This is a port of the CybICS STM32 firmware from FreeRTOS to Zephyr RTOS.

## Overview

The original firmware used FreeRTOS with CMSIS-RTOS v1 API. This port converts all functionality to use Zephyr RTOS native APIs.

### Key Changes

1. **RTOS Migration**:
   - FreeRTOS tasks → Zephyr threads (using `K_THREAD_DEFINE`)
   - CMSIS-RTOS API (`osThreadCreate`, `osDelay`) → Zephyr kernel API (`k_msleep`)
   - FreeRTOS semaphores (`xSemaphoreCreateMutex`) → Zephyr mutexes (`K_MUTEX_DEFINE`)

2. **Hardware Abstraction**:
   - STM32 HAL → Zephyr device drivers
   - Direct GPIO manipulation → Zephyr GPIO API
   - HAL UART/I2C → Zephyr UART/I2C drivers

3. **Priority Mapping**:
   - FreeRTOS uses higher numbers for higher priority
   - Zephyr uses lower numbers for higher priority
   - Priorities have been inverted accordingly

### Thread Mapping

| Original FreeRTOS Task | Priority (FreeRTOS) | Zephyr Thread | Priority (Zephyr) |
|------------------------|---------------------|---------------|-------------------|
| defaultTask            | Normal              | thread_default | 7                |
| heartBeat              | Idle                | thread_heartbeat | 14             |
| display                | Normal              | thread_display | 7                |
| physical               | Above Normal        | thread_physical | 5               |
| i2chandler             | Normal              | thread_i2c | 7                   |
| writeOutput            | Realtime            | thread_write_output | 0           |
| uart                   | Low                 | thread_uart | 10                 |

## Hardware Support

- **Target Board**: STM32 Nucleo G070RB
- **MCU**: STM32G070RBTx
- **Peripherals**:
  - UART1 @ 115200 baud
  - I2C1 @ 100kHz
  - Multiple GPIO pins for LEDs, sensors, and LCD display

## Building

### Method 1: Using VS Code Dev Container (Recommended)

The easiest way to build the firmware is using the provided development container:

1. Open the repository in VS Code
2. Press `F1` and select "Dev Containers: Reopen in Container"
3. Choose "CybICS-stm32"
4. The container will automatically initialize the Zephyr workspace

Once inside the container:
```bash
# Build the firmware (you're already in the correct directory)
west build -b nucleo_g070rb

# Flash to board (if connected via USB)
west flash
```

### Method 2: Docker-based Flashing (Raspberry Pi)

This method builds a Docker container that automatically flashes the STM32 via OpenOCD on a Raspberry Pi.

**Prerequisites:**
- Raspberry Pi with GPIO pins connected to STM32 SWD interface
- Docker installed on the Raspberry Pi

**Build and flash:**
```bash
# Build the Docker image
cd software/stm32
./build-docker.sh

# Push to local registry (if using docker-compose)
docker push localhost:5000/cybics-stm32:latest

# Run the container to flash the board
docker run --privileged -p 3333:3333 localhost:5000/cybics-stm32:latest

# Or use docker-compose (from software/ directory)
cd ..
docker-compose up stm32
```

The container will:
1. Build the Zephyr firmware
2. Flash it to the STM32 via OpenOCD
3. Keep OpenOCD running as a GDB server on port 3333

**SWD Pin Connections (Raspberry Pi → STM32):**
- Pin 23 (GPIO 25) → SWCLK
- Pin 22 (GPIO 24) → SWDIO
- Pin 18 (GPIO 18) → NRST
- Pin 6 (GND) → GND

### Method 3: Manual Build

If you have Zephyr SDK installed locally:

1. Install Zephyr SDK and dependencies:
   ```bash
   # Follow the official Zephyr Getting Started Guide:
   # https://docs.zephyrproject.org/latest/getting_started/index.html
   ```

2. Set up Zephyr environment:
   ```bash
   cd ~/zephyrproject
   source zephyr-env.sh
   ```

3. Build and flash:
   ```bash
   # Navigate to the project directory
   cd software/stm32

   # Build for STM32 Nucleo G070RB
   west build -b nucleo_g070rb

   # Flash to the board
   west flash

   # View serial output
   west attach
   # or
   screen /dev/ttyACM0 115200
   ```

## Project Structure

```
stm32/
├── CMakeLists.txt          # CMake build configuration
├── prj.conf                # Zephyr project configuration
├── README.md               # This file
├── Dockerfile              # Docker build for flashing via OpenOCD
├── build-docker.sh         # Script to build Docker image
├── openocd.cfg             # OpenOCD configuration (standard interface)
├── openocd_rpi.cfg         # OpenOCD configuration (Raspberry Pi GPIO)
├── boards/
│   └── nucleo_g070rb.overlay  # Device tree overlay for GPIO pins
└── src/
    ├── main.c              # Main application (ported from FreeRTOS)
    ├── display.c           # LCD display driver (ported)
    ├── display.h           # LCD display header
    └── colors.h            # ANSI color definitions for logging
```

## Features

- **Industrial Control Simulation**: Simulates a pressure control system with:
  - Gas Storage Tank (GST)
  - High Pressure Tank (HPT)
  - Compressor control
  - Safety valves
  - Blow-out protection

- **LCD Display**: 16x2 character LCD with multiple display screens
  - System information
  - WiFi configuration (STA/AP mode)
  - Real-time pressure readings
  - System status

- **UART Menu Interface**: Password-protected menu system via serial console
  - System status monitoring
  - Control interface
  - Thread statistics
  - MCU information

- **I2C Communication**: I2C slave interface for communication with Raspberry Pi

## Configuration

Key configuration options in `prj.conf`:

- `CONFIG_HEAP_MEM_POOL_SIZE`: Heap size (default: 8192 bytes)
- `CONFIG_MAIN_STACK_SIZE`: Main thread stack size (default: 2048 bytes)
- `CONFIG_LOG_DEFAULT_LEVEL`: Logging level (0-4, default: 3)
- `CONFIG_SYS_CLOCK_HW_CYCLES_PER_SEC`: System clock frequency (64 MHz)

## Differences from FreeRTOS Version

1. **Thread Statistics**: The FreeRTOS task statistics menu has been simplified in the Zephyr version. Full Zephyr thread runtime stats can be enabled with additional configuration.

2. **Unique ID**: The MCU unique ID retrieval uses Zephyr's device-specific APIs instead of direct STM32 LL library calls.

3. **I2C Slave Mode**: I2C slave functionality needs to be implemented using Zephyr's I2C slave API (requires additional work).

4. **System Calls**: The custom newlib syscalls (`_write`, `_read`, etc.) are not needed in Zephyr as it provides its own libc implementation.

## Future Improvements

- [ ] Implement full I2C slave functionality using Zephyr APIs
- [ ] Add thread runtime statistics reporting
- [ ] Implement proper error handling and recovery
- [ ] Add unit tests using Zephyr's testing framework
- [ ] Optimize stack sizes based on actual usage
- [ ] Add power management features
- [ ] Implement shell commands using Zephyr's shell subsystem

## License

Original code: STMicroelectronics
Zephyr port: Apache-2.0

## Notes

- The default login password is: `cyb`
- The system simulates an industrial pressure control system
- All timing delays have been preserved from the original implementation
- LED control uses active-low logic (inverted outputs) as in the original
