# CybICS Test Suite

This directory contains automated tests for the CybICS industrial control system training environment.

## Test Files

- **`test_connections.py`** - Tests for connectivity and protocol functionality (Modbus TCP, OPC-UA, S7, HTTP)
- **`test_training.py`** - Tests for training exercises (flood attacks, password attacks)

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest -v test_connections.py
pytest -v test_training.py
```

### Run Specific Test Class or Function

```bash
# Run specific test class
pytest -v test_training.py::TestFloodOverwrite

# Run specific test function
pytest -v test_training.py::TestFloodOverwrite::test_flood_attack_simulation
```

## Configuration

### Testing Against Remote Server

By default, all tests run against `localhost` (127.0.0.1). To test against a remote CybICS instance, set the `TEST_SERVER_IP` environment variable:

```bash
# Linux/Mac
export TEST_SERVER_IP=192.168.1.100
pytest -v

# Or inline
TEST_SERVER_IP=192.168.1.100 pytest -v

# Windows (PowerShell)
$env:TEST_SERVER_IP="192.168.1.100"
pytest -v

# Windows (CMD)
set TEST_SERVER_IP=192.168.1.100
pytest -v
```

### Example: Test Physical Raspberry Pi

```bash
# Set the IP of your Raspberry Pi running CybICS
export TEST_SERVER_IP=192.168.1.50
pytest -v test_connections.py
```

### Example: Quick Remote Test

```bash
# Test a specific remote instance
TEST_SERVER_IP=10.0.0.100 pytest -v test_training.py::TestPasswordAttack

# Test connections to a development server
TEST_SERVER_IP=dev.cybics.local pytest -v test_connections.py
```

### Verify Configuration

You can verify the target IP before running tests:

```bash
# Check what IP will be used
python3 -c "from test_training import SERVER_IP; print(f'Testing against: {SERVER_IP}')"

# Or with environment variable
TEST_SERVER_IP=192.168.1.100 python3 -c "from test_training import SERVER_IP; print(f'Testing against: {SERVER_IP}')"
```

## Test Coverage

### Connection Tests (`test_connections.py`)

- ✅ Web service accessibility (Landing, FUXA, OpenPLC, Virtual HW)
- ✅ Modbus TCP connectivity and operations
- ✅ OPC-UA connectivity and browsing
- ✅ Siemens S7 protocol detection
- ✅ Security headers validation
- ✅ Extended protocol testing

### Training Tests (`test_training.py`)

#### Flood & Overwrite Attack Tests
- ✅ Modbus connection availability
- ✅ HPT register read/write capability
- ✅ Flood attack simulation (1 second burst)
- ✅ Rapid write persistence

#### Password Attack Tests
- ✅ OpenPLC login page accessibility
- ✅ Invalid credential rejection (OpenPLC)
- ✅ Valid credential acceptance (OpenPLC)
- ✅ FUXA web interface accessibility
- ✅ Invalid credential rejection (FUXA)
- ✅ Valid credential acceptance (FUXA)
- ✅ Rapid authentication attempts (rate limiting check)

#### Training Material Validation
- ✅ Flood attack script existence
- ✅ Flood attack README with flags
- ✅ Password attack README with flags
- ✅ Environment configuration validation

## CI/CD Integration

Tests are automatically run via GitHub Actions on:
- Every push
- Daily schedule (cron: "0 0 * * *")

See `.github/workflows/pytest.yml` for CI configuration.

## Troubleshooting

### Connection Timeouts

If tests fail with connection timeouts, the services may need more time to initialize:

```bash
# Wait longer for services to start
docker-compose up -d
sleep 120  # Wait 2 minutes
pytest -v
```

### Modbus Errors

If Modbus tests fail with "slave=" vs "device_id=" errors, check your pymodbus version:

```bash
pip show pymodbus
```

- pymodbus < 3.11: Use `slave=1`
- pymodbus >= 3.11: Use `device_id=1`

### Network Issues

Ensure firewall allows connections to test ports:
- 80 (HTTP - Landing)
- 502 (Modbus TCP)
- 1881 (FUXA)
- 4840 (OPC-UA)
- 8080 (OpenPLC)
- 8090 (Virtual Hardware I/O)

## Development

### Adding New Tests

1. Add test functions to appropriate file (`test_connections.py` or `test_training.py`)
2. Use descriptive names: `test_<feature>_<expected_behavior>`
3. Add docstrings explaining what the test validates
4. Update this README with new test coverage

### Test Naming Convention

- Classes: `TestFeatureName`
- Functions: `test_specific_behavior`
- Use descriptive names that explain the test purpose

### Best Practices

- Always use fixtures for setup/teardown
- Include error messages in assertions
- Use `pytest.skip()` for expected failures
- Add timeouts to prevent hanging tests
- Clean up resources (close connections, restore values)
