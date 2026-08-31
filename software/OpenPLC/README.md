# OpenPLC Integration

## Overview
OpenPLC is an open-source Programmable Logic Controller (PLC) that serves as the control system in the CybICS testbed. It reads sensor data from the physical process (real or simulated) and controls actuators based on the programmed control logic. The OpenPLC provides a web-based interface for programming, monitoring, and debugging the control system.

## Purpose
In the CybICS testbed, OpenPLC serves several critical functions:

1. **Process Control**: Implements the automatic control logic for the gas pressure system
2. **Manual Override**: Allows operators to manually control valves and compressors
3. **Training Platform**: Provides a realistic ICS environment for cybersecurity training
4. **Protocol Support**: Supports multiple industrial protocols (Modbus TCP, DNP3, EtherNet/IP, S7)
5. **Vulnerability Target**: Serves as a target for security testing and penetration exercises

## Architecture

### Communication Protocols
OpenPLC in CybICS is configured to support multiple industrial protocols:

- **Modbus TCP** (Port 502): Primary communication protocol
- **DNP3** (Port 20000): Distributed Network Protocol for SCADA
- **EtherNet/IP** (Port 44818): Industrial Ethernet protocol
- **S7comm** (Port 102): Siemens S7 protocol
- **HTTP** (Port 8080): Web interface for programming and monitoring



## Default Configuration

### Web Interface Access
- **URL**: `http://<device-ip>:8080`
- **Default Credentials**:

### Pre-installed Program
The CybICS OpenPLC comes with a pre-installed control program (`cybICS.st`) that implements:

- **Automatic Control Mode**: Maintains GST between 60-240 bar and HPT between 60-90 bar
- **Manual Control Mode**: Allows operator to manually control compressor and valves
- **Safety Interlocks**: Prevents compressor operation when GST is too low
- **Heartbeat**: Visual indicator that the PLC is running
- **Emergency Stop**: System stop functionality

### I/O Mapping

#### Input Registers (Sensors)
| Address | Variable | Description | Range |
|---------|----------|-------------|-------|
| %MW100 | gst | Gas Storage Tank pressure | 0-255 bar |
| %MW102 | hpt | High Pressure Tank pressure | 0-255 bar |
| %MW104 | stop | Emergency stop flag | 0=run, 1=stop |
| %MW106 | manual | Manual mode flag | 0=auto, 1=manual |
| %MW108 | systemSen | System sensor state | Boolean |
| %MW110 | boSen | Blowout sensor state | Boolean |

**Modbus Register Mapping**:
- Register 1124: GST pressure (written by hwio)
- Register 1126: HPT pressure (written by hwio)

#### Output Coils (Actuators)
| Address | Variable | Description | Control |
|---------|----------|-------------|---------|
| %QX0.0 | heartbeat | System alive indicator | Auto (PLC) |
| %QX0.1 | compressor | Compressor control | Auto/Manual |
| %QX0.2 | systemValve | System valve control | Auto/Manual |
| %QX0.3 | gstSig | GST fill signal | Auto/Manual |

## Usage

### Accessing the Web Interface
1. Open a web browser
2. Navigate to `http://<device-ip>:8080`

### Programming the PLC

#### Uploading a New Program
1. Click "Programs" in the navigation menu
2. Click "Upload Program"
3. Select your `.st` (Structured Text) file
4. Click "Upload"
5. Click "Compile" to build the program
6. Click "Start PLC" to run

#### Monitoring Values
1. Click "Monitoring" in the navigation menu
2. Select the location to monitor (e.g., %MW100 for GST)
3. View real-time values and graphs

## Troubleshooting

### Cannot Access Web Interface
**Symptom**: Browser shows "Connection refused" or timeout

**Solutions**:
1. Verify OpenPLC container is running:
   ```bash
   docker ps | grep openplc
   # or
   sudo systemctl status openplc
   ```
2. Check if port 8080 is accessible:
   ```bash
   curl http://localhost:8080
   ```
3. Verify firewall allows port 8080:
   ```bash
   sudo iptables -L -n | grep 8080
   ```
4. Check OpenPLC logs:
   ```bash
   docker logs openplc
   # or
   sudo journalctl -u openplc -n 50
   ```

### PLC Program Won't Compile
**Symptom**: Compilation errors when uploading program

**Solutions**:
1. Check syntax of Structured Text program
2. Verify all variable declarations are correct
3. Review compilation logs in the web interface
4. Ensure no special characters in variable names
5. Try uploading a simple test program to verify compiler works

### Modbus Connection Fails
**Symptom**: hwio cannot connect to OpenPLC via Modbus

**Solutions**:
1. Verify Modbus TCP is enabled in Settings → Slave Devices
2. Check port 502 is exposed:
   ```bash
   netstat -tuln | grep 502
   # or
   ss -tuln | grep 502
   ```
3. Test Modbus connection:
   ```python
   from pymodbus.client import ModbusTcpClient
   c = ModbusTcpClient('localhost', 502)
   c.connect()
   print(c.connected)  # Should be True
   ```
4. Review OpenPLC runtime logs
5. Restart OpenPLC service

### PLC Not Reading Sensor Values
**Symptom**: Input registers show 0 or don't update

**Solutions**:
1. Verify hwio-raspberry or hwio-virtual is running and connected
2. Check Modbus register mapping (1124 → %MW100, 1126 → %MW102)
3. Use Modbus client to verify values are being written:
   ```python
   from pymodbus.client import ModbusTcpClient
   c = ModbusTcpClient('localhost', 502)
   c.connect()
   print(c.read_holding_registers(1124, 2))  # Should show GST and HPT
   ```
4. Verify PLC is in RUN mode (not STOP)
5. Check for program logic errors

### Actuators Not Responding
**Symptom**: Physical LEDs or simulated process doesn't respond to PLC outputs

**Solutions**:
1. Verify PLC outputs are changing in Monitoring view
2. Check hwio service is reading from OpenPLC coils
3. Verify Modbus coil addresses are correct (512, 513, 514, 515)
4. Test coil reading:
   ```python
   from pymodbus.client import ModbusTcpClient
   c = ModbusTcpClient('localhost', 502)
   c.connect()
   print(c.read_coils(512, 4))  # Should show actuator states
   ```
5. Review control logic in PLC program

## Advanced Configuration

### Changing Scan Cycle Time
Default: 100ms (10 Hz)

Modify in Settings → Hardware → Scan Cycle Time

For faster control: 50ms
For less CPU usage: 200ms

## Related Documentation
- [FUXA HMI Documentation](../FUXA/README.md)
- [Virtual Hardware I/O](../hwio-virtual/README.md)
- [Raspberry Pi Hardware I/O](../hwio-raspberry/README.md)
- [STM32 Firmware](../stm32/README.md)
- [Official OpenPLC Documentation](https://autonomylogic.com/)


