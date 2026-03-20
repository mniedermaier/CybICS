# IDS Forensics Challenge

## Objective

Analyze IDS alert data to investigate a security incident on the CybICS industrial network. Demonstrate your ability to use IDS APIs for incident response and forensic analysis.

## Background

Security Operations Center (SOC) analysts regularly triage alerts from intrusion detection systems to understand the scope and nature of attacks. This challenge simulates a real-world incident investigation where you must analyze IDS data programmatically.

The CybICS IDS exposes a REST API that provides alert data, summary statistics, and aggregated metrics. Your task is to query these endpoints, analyze the data, and answer three investigation questions.

## MITRE ATT&CK for ICS Alignment

| Technique | ID | Relevance |
|---|---|---|
| Remote System Discovery | T0846 | Identifying reconnaissance patterns |
| Unauthorized Command Message | T0855 | Detecting unauthorized Modbus writes |
| Denial of Service | T0836 | Identifying flooding attacks |

## MITRE D3FEND Alignment

| Technique | ID | Description |
|---|---|---|
| Network Traffic Analysis | D3-NTA | Analyzing captured network alert data |
| Alert Triage | D3-AT | Prioritizing and classifying security alerts |

## Prerequisites

Before starting this challenge, you need alert data in the IDS. Complete the **IDS Challenge** first or trigger multiple different attacks to generate diverse alerts:

- **Port scan**: `nmap -sS 172.18.0.3` (triggers `port_scan` rule)
- **Modbus writes**: Send unauthorized writes to port 502 (triggers `modbus_unauth_write` rule)
- **S7comm access**: `nmap --script s7-info -p 102 172.18.0.3` (triggers `s7_enumeration` rule)
- **HTTP brute force**: Multiple login attempts on OpenPLC (triggers `http_brute_force` rule)

You need at least **5 alerts** from at least **3 different rule types**.

## Task

### Step 1: Check Investigation Readiness

Query the forensics endpoint to see if enough data is available:

```bash
curl http://localhost:8443/api/forensics
```

If `ready` is `false`, trigger more attacks until the requirements are met.

### Step 2: Gather Intelligence

Use the IDS API endpoints to analyze the alert data:

#### Get Summary Statistics
```bash
curl http://localhost:8443/api/summary | python3 -m json.tool
```

Key fields in the response:
- `severity`: Count of alerts by severity level (low, medium, high, critical)
- `rules`: Count of alerts by detection rule name
- `top_sources`: List of source IPs ranked by alert count
- `total`: Total number of alerts

#### Get Raw Alert Data
```bash
curl http://localhost:8443/api/alerts | python3 -m json.tool
```

Each alert contains:
- `id`: Unique alert identifier
- `timestamp`: When the alert was generated
- `severity`: Alert severity (low, medium, high, critical)
- `rule`: Detection rule that triggered the alert
- `src`: Source IP address of the attacker
- `dst`: Target IP address
- `message`: Human-readable description
- `mitre`: MITRE ATT&CK technique ID

### Step 3: Answer Investigation Questions

Analyze the data to answer these three questions:

1. **Top Attacker**: What is the IP address of the source with the most alerts?
2. **Unique Rules**: How many distinct detection rule types have been triggered?
3. **Critical Alerts**: How many alerts with `critical` severity have been recorded?

### Step 4: Submit Your Analysis

Submit your answers via the forensics API:

```bash
curl -X POST http://localhost:8443/api/forensics/submit \
  -H "Content-Type: application/json" \
  -d '{
    "top_attacker": "172.18.0.x",
    "unique_rules": N,
    "critical_count": N
  }'
```

If all answers are correct, the flag will be revealed.

You can also submit via the **Challenges tab** on the IDS dashboard.

### Python Scripting Approach

For a more programmatic approach:

```python
import requests

BASE = "http://localhost:8443"

# Get summary data
summary = requests.get(f"{BASE}/api/summary").json()

# Find top attacker
top_source = summary["top_sources"][0]["ip"] if summary["top_sources"] else "unknown"

# Count unique rules
unique_rules = len(summary["rules"])

# Count critical alerts
critical_count = summary["severity"]["critical"]

print(f"Top attacker: {top_source}")
print(f"Unique rules: {unique_rules}")
print(f"Critical alerts: {critical_count}")

# Submit
result = requests.post(f"{BASE}/api/forensics/submit", json={
    "top_attacker": top_source,
    "unique_rules": unique_rules,
    "critical_count": critical_count,
}).json()

print(result)
```

## Key Takeaways

- SOC analysts must efficiently query and correlate alert data from multiple sources
- API-based analysis enables automation and faster incident response
- Understanding alert severity, source attribution, and rule classification is fundamental to triage
- The same API skills apply to commercial SIEMs (Splunk, QRadar, Elastic Security)

## NIST SP 800-82r3 Alignment

| Control Family | Control | Description |
|---|---|---|
| SI (System and Information Integrity) | SI-4 | Information System Monitoring |
| IR (Incident Response) | IR-4 | Incident Handling |
| IR (Incident Response) | IR-5 | Incident Monitoring |
| AU (Audit and Accountability) | AU-6 | Audit Review, Analysis, and Reporting |
