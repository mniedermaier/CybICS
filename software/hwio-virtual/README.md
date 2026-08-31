# Virtual Hardware I/O Simulator

## Overview
The virtual hardware I/O component (`hwio-virtual`) is a Python-based simulation of the CybICS physical process. It provides a software alternative to the physical STM32-based hardware, making it easy to run the complete CybICS training environment without physical hardware.

This component simulates:
- Gas Storage Tank (GST) pressure sensor
- High Pressure Tank (HPT) pressure sensor
- Compressor actuator
- System valve actuator
- Safety sensors (system sensor, blowout sensor)
- Physical process dynamics (pressure changes, gas flow, etc.)

## Purpose
The virtual hardware I/O serves several key purposes:

1. **Accessibility**: Run CybICS training without purchasing physical hardware
2. **Scalability**: Deploy multiple virtual instances for classroom environments
3. **Development**: Test and develop PLC programs without hardware
4. **Training**: Learn industrial cybersecurity concepts in a safe, virtual environment

## Architecture

### Communication
- **Protocol**: Modbus TCP
- **Port**: 502
- **Target**: OpenPLC server
- **Role**: Acts as a Modbus client, reading outputs from and writing sensor data to the PLC

### Web Interface
- **Framework**: NiceGUI (Python web framework)
- **Port**: 80
- **Features**:
  - Real-time visualization of the physical process
  - Visual representation matching the physical PCB layout
  - Live pressure readings and valve states
  - Automatic updates every 200ms

### Process Simulation
The simulator runs a continuous background thread that:
1. Reads actuator commands from OpenPLC (compressor, valves)
2. Simulates physical process dynamics (pressure changes, gas flow)
3. Calculates new sensor values based on physical laws
4. Writes sensor data back to OpenPLC
5. Updates the web interface

## How It Differs from Physical Hardware

| Aspect | Physical (STM32) | Virtual (hwio-virtual) |
|--------|------------------|------------------------|
| Hardware | Real STM32 microcontroller | Python application |
| I/O | GPIO pins, I2C bus | Modbus TCP network |
| Display | Physical LCD screen | Web interface |
| LEDs | Real LEDs on PCB | Graphical representation |
| Process | Simulated with real-time constraints | Simulated with timing approximations |
| Deployment | Requires hardware assembly | Docker container |
| Cost | ~50 EUR per unit | Free (software only) |

## Usage

### Running with Docker Compose (Recommended)
The virtual hardware I/O is automatically started as part of the virtual CybICS environment:

```bash
cd .devcontainer/virtual
docker compose up
```

The web interface will be available at [http://localhost/](http://localhost/)

### Running Standalone
```bash
cd software/hwio-virtual
pip install -r requirements.txt
python hardwareAbstraction.py
```

**Note**: Standalone mode requires OpenPLC to be running and accessible at `openplc:502`. Modify the connection settings in the code if needed.

### Accessing the Interface
Once running, open a web browser and navigate to:
- **Local deployment**: [http://localhost/](http://localhost/)
- **Remote deployment**: `http://<server-ip>/`

The interface displays:
- Gas Storage Tank (GST) pressure gauge
- High Pressure Tank (HPT) pressure gauge
- Compressor status indicator
- Valve states (system valve, GST fill valve)
- Safety indicators (blowout valve, system sensor)
- Visual representation matching the physical PCB

## Configuration

### Modbus Connection
By default, the simulator connects to:
- **Host**: `openplc` (Docker service name)
- **Port**: `502`
- **Protocol**: Modbus TCP

To change the connection target, modify `hardwareAbstraction.py:60`:
```python
client = ModbusTcpClient(host="openplc", port=502)
```

### Process Parameters
Physical process parameters (pressure limits, flow rates, timing) are configured in the simulation logic. These match the physical process description in the main [README](../../README.md).

## Logging
The simulator provides detailed logging:
- Connection status to OpenPLC
- Modbus communication errors
- Process state changes
- Sensor value updates

Logs are output to stdout and visible in Docker logs:
```bash
docker compose logs -f hwio-virtual
```

## Troubleshooting

### Cannot Connect to OpenPLC
**Symptom**: "Waiting for OpenPLC to start..." messages in logs

**Solutions**:
1. Ensure OpenPLC container is running: `docker compose ps`
2. Wait 1-2 minutes for OpenPLC to fully initialize
3. Check network connectivity: `docker compose exec hwio-virtual ping openplc`
4. Verify OpenPLC Modbus is enabled in OpenPLC settings

### Web Interface Not Accessible
**Symptom**: Cannot access http://localhost/

**Solutions**:
1. Verify container is running: `docker compose ps`
2. Check port mapping: `docker compose ps` should show `0.0.0.0:80->80/tcp`
3. Try accessing via `http://127.0.0.1/` instead
4. Check firewall settings
5. Ensure no other service is using port 80

### Sensor Values Not Updating
**Symptom**: Process appears frozen, values don't change

**Solutions**:
1. Check OpenPLC status - ensure it's running and has a program loaded
2. Verify Modbus communication in logs
3. Restart both OpenPLC and hwio-virtual containers:
   ```bash
   docker compose restart openplc hwio-virtual
   ```

### High CPU Usage
**Symptom**: Container consuming excessive CPU

**Solutions**:
1. This is normal during active simulation
2. Reduce update frequency if needed (modify timing in code)
3. Ensure host system meets minimum requirements