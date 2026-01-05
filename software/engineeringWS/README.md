# Engineering Workstation (engineeringWS)

## Overview
The Engineering Workstation is a Windows-compatible Docker container that provides a full desktop environment with the OpenPLC Editor pre-installed. This allows engineers to program and configure the CybICS PLC from a graphical interface accessible via web browser.

## Features
- **XFCE Desktop Environment**: Lightweight desktop accessible via VNC
- **OpenPLC Editor**: Official IEC 61131-3 PLC programming tool
- **Web Browser Access**: No VNC client needed - access via http://localhost:6080
- **Pre-configured**: Desktop shortcut for quick OpenPLC Editor launch

## Access

### Via Web Browser (Recommended)
1. Start the container:
   ```bash
   docker compose up -d engineeringws
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:6080
   ```

3. Click "Connect" (password: `cybics`)

4. Double-click the "OpenPLC Editor" icon on the desktop

### Via VNC Client
Alternatively, use any VNC client:
- **Host**: localhost
- **Port**: 5901
- **Password**: cybics

## Usage

### Programming the PLC

1. **Create a new project**:
   - Open OpenPLC Editor
   - File → New
   - Choose project name and location

2. **Write your PLC program**:
   - Use Ladder Diagram (LD), Function Block Diagram (FBD), or Structured Text (ST)
   - Define variables in the resource editor
   - Map I/O addresses to match CybICS hardware

3. **Generate code**:
   - File → Generate Program for OpenPLC
   - Save the .st file

4. **Upload to OpenPLC**:
   - Open OpenPLC web interface (http://localhost:8080)
   - Programs → Upload Program
   - Select the generated .st file
   - Compile and start

### I/O Mapping for CybICS

Use these addresses in your PLC programs:

#### Inputs (Sensors)
```
%MW100  - GST (Gas Storage Tank) pressure
%MW102  - HPT (High Pressure Tank) pressure
%MW104  - Stop flag
%MW106  - Manual mode flag
%MW108  - System sensor
%MW110  - Blowout sensor
```

#### Outputs (Actuators)
```
%QX0.0  - Heartbeat LED
%QX0.1  - Compressor
%QX0.2  - System valve
%QX0.3  - GST fill signal
```

## Included Software

- **OpenPLC Editor**: PLC programming tool
- **Firefox**: Web browser for accessing OpenPLC/FUXA
- **Text Editor**: For viewing/editing configuration files
- **Terminal**: Command line access

## Container Details

### Base Image
- Ubuntu 22.04 LTS

### Exposed Ports
- **5901**: VNC server
- **6080**: noVNC web interface

### Default Password
- VNC Password: `cybics`

## Building the Image

```bash
cd software/engineeringWS
docker build -t cybics-engineeringws .
```

## Running Standalone

```bash
docker run -d \
  --name engineeringws \
  -p 6080:6080 \
  -p 5901:5901 \
  cybics-engineeringws
```

## Troubleshooting

### Cannot connect to web interface
- Ensure port 6080 is not in use
- Wait 30 seconds for services to fully start
- Check container logs: `docker logs engineeringws`

### VNC shows black screen
- Restart the container: `docker restart engineeringws`
- Check supervisor logs inside container

### OpenPLC Editor won't start
- Ensure X11 dependencies are installed (should be automatic)
- Check for errors in terminal: `/opt/OpenPLC_Editor/editor.py`

## Integration with CybICS

The Engineering Workstation is designed to work alongside other CybICS services:

1. **Program Development**: Write PLC programs in OpenPLC Editor
2. **Upload to OpenPLC**: Deploy programs to the PLC runtime
3. **Monitor via FUXA**: View process behavior in the HMI
4. **Test & Debug**: Iterate on control logic

## Development

### Adding Tools
Edit the Dockerfile to install additional engineering tools:
```dockerfile
RUN apt-get update && apt-get install -y \
    your-tool-here \
    && rm -rf /var/lib/apt/lists/*
```

### Changing Desktop Environment
Replace XFCE with another desktop by modifying the Dockerfile:
- XFCE (current) - Lightweight
- LXDE - Even lighter
- MATE - More features

## Security Notes

⚠️ **For Training Use Only**
- Default VNC password is intentionally simple
- Not hardened for production use
- Runs as root for compatibility

For production deployments:
- Change VNC password
- Use SSH tunneling for VNC access
- Run as non-root user
- Enable SSL/TLS

## Related Documentation
- [OpenPLC Editor Documentation](https://autonomylogic.com/)
- [OpenPLC Integration](../OpenPLC/README.md)
- [FUXA HMI](../FUXA/README.md)

## License
- Ubuntu: Canonical's licensing
- OpenPLC Editor: GPL-3.0
- CybICS integration: MIT License
