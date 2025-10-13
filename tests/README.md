# CybICS Test Suite

Automated tests for the CybICS industrial control system training environment.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest -v

# Run specific test file
pytest -v test_connections.py
pytest -v test_training.py
```

## Test Files

- **`test_connections.py`** - Protocol connectivity tests (Modbus TCP, OPC-UA, S7, HTTP)
- **`test_training.py`** - Training exercise validation (flood attacks, password attacks)

## Remote Testing

By default, tests run against `localhost`. To test a remote instance:

```bash
# Linux/Mac
TEST_SERVER_IP=192.168.1.100 pytest -v

# Windows (PowerShell)
$env:TEST_SERVER_IP="192.168.1.100"
pytest -v
```

## Test Coverage

### Connection Tests
- Web service accessibility (Landing, FUXA, OpenPLC, Virtual HW)
- Modbus TCP connectivity and operations
- OPC-UA connectivity and browsing
- Siemens S7 protocol detection

### Training Tests
- Flood attack simulation (Modbus register flooding)
- Password attack validation (OpenPLC and FUXA)
- Training material validation

## Troubleshooting

### Connection Timeouts
Wait for services to initialize:
```bash
docker-compose up -d
sleep 120
pytest -v
```

### Modbus API Version
Tests use `device_id=1` (pymodbus >= 3.11). For older versions, use `slave=1`.

### Network Issues
Ensure firewall allows connections to test ports: 80, 502, 1881, 4840, 8080, 8090.

## CI/CD

Tests run automatically via GitHub Actions on every push and daily schedule.
