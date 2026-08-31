# Raspberry Pi Hardware I/O Bridge

## Overview
The Raspberry Pi hardware I/O bridge (`hwio-raspberry`) is a Python-based service that acts as an interface between the physical STM32 hardware and the OpenPLC controller. It runs on the Raspberry Pi and enables communication between the microcontroller-based physical process simulation and the PLC software.

## Purpose
This component serves as the critical communication bridge in the physical CybICS setup:

1. **I2C Communication**: Reads sensor data from the STM32 microcontroller via I2C bus
2. **Modbus Bridge**: Writes sensor data to OpenPLC via Modbus TCP
3. **GPIO Control**: Controls indicator LEDs and actuator signals via Raspberry Pi GPIO pins
4. **Network Info**: Sends Raspberry Pi IP address to STM32 for display on LCD
5. **Heartbeat**: Provides visual indication that the system is running

## Architecture

### Communication Interfaces

#### I2C Bus (STM32 ↔ Raspberry Pi)
- **Protocol**: I2C (Inter-Integrated Circuit)
- **Bus**: I2C1 (Raspberry Pi channel 1)
- **STM32 Address**: 0x20 (I2C slave)
- **Data Transfer**:
  - **Read**: Sensor values (GST, HPT pressures)
  - **Write**: IP address for LCD display

#### Modbus TCP (Raspberry Pi → OpenPLC)
- **Protocol**: Modbus TCP
- **Target Host**: `openplc` (Docker service) or `localhost` (standalone)
- **Port**: 502
- **Register Mapping**:
  - Register 1124: GST (Gas Storage Tank) pressure
  - Register 1126: HPT (High Pressure Tank) pressure
  - Registers 1200-1206: Flag data
  - Registers 512-515: Actuator states (compressor, valves)


