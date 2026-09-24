# Virtual Hardware I/O Simulator

## File layout

| File | |
|---|---|
| `hardwareAbstraction.py` | the service: plant model, Modbus bridge, UI wiring |
| `static/plant3d.html` | the 3D plant scene -- HTML, CSS and Three.js |
| `static/js/` | the vendored Three.js and OrbitControls |

The scene used to sit inside `hardwareAbstraction.py` as a 2500-line string
literal, which made the module 3606 lines and left an editor treating the whole
scene as one opaque block. It is read once at import, so a missing asset fails
at startup with a clear path rather than on the first page load.

`physical_process_thread` stays in `hardwareAbstraction.py`. It mutates eleven
module-level globals that the UI also reads, so moving it would mean
introducing a state object and rewiring every reader -- a behavioural change
rather than a move, and one worth doing on its own. It is the function
`tests/test_plant_model_parity.py` parses and the one that must stay in step
with `thread_physical` in `software/stm32/src/main.c`.

## Overview
The virtual hardware I/O component (`hwio-virtual`) is a Python-based simulation of the CybICS physical process. It provides a software alternative to the physical STM32-based hardware, making it easy to run the complete CybICS training environment without physical hardware.

This component simulates:
- Gas Storage Tank (GST) pressure sensor
- High Pressure Tank (HPT) pressure sensor
- Compressor actuator
- System valve actuator
- Safety sensors (system sensor, blowout sensor)
- Physical process dynamics (pressure changes, gas flow, etc.)
- The 16x2 LCD and the 5-way navigation switch on the front panel

## The front panel

The browser shows the same panel as the board: sixteen columns, two rows, the
same five screens in the same order. The five buttons over `SW3` in the
photograph are the navigation switch -- centre, down and right go forward, up
and left go back, which is what `ui_input.c` does on real hardware. The
navigation switch is modelled rather than the v1.0 push-button, because that is
the hardware being built now.

`lcd_render()` mirrors the `switch` in `thread_display()` in
`software/stm32/src/main.c`, including the order the status conditions are
tested in -- that order decides which message wins when several apply at once.

The screen strings are declared in a marked `LCD_SCREENS_BEGIN` block in both
files, and `tests/test_display_parity.py` parses the two and fails if they
drift apart. That guard exists because they already drifted once: the browser
rendered the first screen only, with a hand-written copy of its first line, and
ignored the other four entirely.

Values differ between the two, as they do between any two boards. This plant
has no STM32 unique ID and no WiFi radio, so the network screen always shows
the STA layout with the address the container is reachable on, and the build
screen reports `HW virt` where a board reports its strap-encoded revision.

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