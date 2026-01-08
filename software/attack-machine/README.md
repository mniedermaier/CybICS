# CybICS Attack Machine

The Attack Machine is a comprehensive security testing environment designed for ICS/OT cybersecurity training. It provides a full Kali Linux desktop environment with a wide range of penetration testing tools specifically tailored for industrial control systems.


## Included Tools

### Network Scanning & Enumeration
- **nmap** - Network scanner with ICS protocol detection scripts
- **masscan** - Fast port scanner
- **netcat** (nc) - Network utility for reading/writing network connections
- **socat** - Advanced networking tool
- **tcpdump** - Network packet analyzer

### Protocol Analysis
- **Wireshark/tshark** - Protocol analyzer supporting Modbus, S7comm, OPC-UA
- **scapy** - Python packet manipulation library

### ICS/OT Specific Tools

#### Industrial Exploitation Framework (ISF)
Location: `/opt/isf`

Framework similar to Metasploit but specifically designed for industrial control systems. Includes exploits for:
- Siemens S7 PLCs
- Modbus devices
- BACnet systems
- And more

Usage:
```bash
cd /opt/isf
python3 isf.py
```

#### SMOD (Modbus Penetration Testing Framework)
Location: `/opt/smod`

Specialized framework for Modbus protocol security testing.

Usage:
```bash
cd /opt/smod
python3 smod.py
```

#### S7scan
Location: `/opt/s7scan`

Tool for scanning and fingerprinting Siemens S7 PLCs.

Usage:
```bash
cd /opt/s7scan
python3 s7scan.py <target_ip>
```

#### PLCinject
Location: `/opt/PLCinject`

Tool for injecting malicious code into PLCs via Modbus.

### Python Libraries for ICS
- **pymodbus** - Modbus protocol implementation
- **python-snap7** - S7 protocol communication library
- **opcua** - OPC UA protocol library
- **scapy** - Packet manipulation

### General Penetration Testing

#### Exploitation Frameworks
- **Metasploit Framework** - Comprehensive exploitation framework
  - Launch with: `msfconsole`

#### Web Application Testing
- **sqlmap** - SQL injection tool
- **nikto** - Web server scanner
- **dirb** - Web content scanner
- **curl/wget** - HTTP clients

#### Password Attacks
- **hydra** - Network login cracker
- **john** - John the Ripper password cracker
- **hashcat** - Advanced password recovery

**Access Methods:**

1. **Via Landing Page (Recommended)**: Navigate to http://localhost in your browser and click on "Attack Machine" in the Virtual Environment section

2. **Direct Browser Access**: Open http://localhost:6081/vnc.html?autoconnect=true&resize=scale in your browser

3. **VNC Client**: Connect to `localhost:5902` using any VNC client with password `cybics`

4. **Command Line**: Access the terminal directly via Docker:
   ```bash
   docker exec -it virtual-attack-machine-1 /bin/bash
   ```

The attack machine is connected to the CybICS network (172.18.0.0/24) with IP address **172.18.0.100**.

### Common Attack Scenarios

**Note**: All these commands can be executed in the desktop terminal. For protocol analysis, you can use the Wireshark GUI directly from the desktop.

#### 1. Network Discovery
```bash
# Scan CybICS virtual network
nmap -sV 172.18.0.0/24

# Fast scan for open Modbus ports
masscan -p502 172.18.0.0/24 --rate=1000

#### 2. Modbus Enumeration
```bash
# Scan for Modbus devices on OpenPLC (172.18.0.3)
nmap --script modbus-discover -p 502 172.18.0.3

# Read Modbus coils using pymodbus
python3 -c "from pymodbus.client import ModbusTcpClient; \
client = ModbusTcpClient('172.18.0.3', port=502); \
client.connect(); \
print(client.read_coils(0, 10))"

# Write to a coil (control output)
python3 -c "from pymodbus.client import ModbusTcpClient; \
client = ModbusTcpClient('172.18.0.3', port=502); \
client.connect(); \
client.write_coil(0, True)"
```

#### 3. S7comm PLC Interaction
```bash
# Scan for S7 PLCs
nmap --script s7-info -p 102 172.18.0.0/24

# Use s7scan for detailed information
cd /opt/s7scan
python3 s7scan.py 172.18.0.3
```

#### 4. Web Application Testing
```bash
# Scan FUXA HMI for vulnerabilities (172.18.0.4)
nikto -h http://172.18.0.4:1881

# Directory enumeration
dirb http://172.18.0.4:1881

# Test OpenPLC web interface (172.18.0.3)
nikto -h http://172.18.0.3:8080
```

#### 5. Protocol Analysis with Wireshark
```bash
# Capture Modbus traffic
tcpdump -i any -w /workspace/modbus_capture.pcap port 502

# Analyze in Wireshark (filter: modbus)
tshark -r /workspace/modbus_capture.pcap -Y modbus
```

#### 6. OPC-UA Testing
```bash
# Scan OPC-UA server (172.18.0.5)
nmap -p 4840 172.18.0.5

# Connect with Python opcua library
python3 -c "from opcua import Client; \
client = Client('opc.tcp://172.18.0.5:4840'); \
client.connect(); \
print(client.get_root_node())"
```

## Additional Resources

### Documentation
- [Modbus Protocol Specification](http://www.modbus.org/specs.php)
- [Siemens S7 Protocol](https://support.industry.siemens.com/)
- [OWASP ICS Security](https://owasp.org/www-project-ics-security/)

### Tool Documentation
- [Nmap Scripting Engine](https://nmap.org/book/nse.html)
- [Metasploit Unleashed](https://www.offensive-security.com/metasploit-unleashed/)
- [ISF Framework](https://github.com/dark-lbp/isf)
