# 🔥 Modbus Firewall Rules

> **MITRE D3FEND:** `Harden` | [D3-ITF - Inbound Traffic Filtering](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | [D3-NTF - Network Traffic Filtering](https://d3fend.mitre.org/technique/d3f:NetworkTrafficFiltering/)

## 📋 Overview
Modbus TCP (port 502) is an unauthenticated protocol — any device on the network can read and write PLC registers without credentials. In the previous attack challenges, you exploited this to flood registers and overwrite process values.

This challenge requires you to apply **firewall rules** on the OpenPLC container to restrict Modbus access, ensuring only the authorized HMI (FUXA at 172.18.0.4) can communicate with the PLC.

## 🏗️ Network Architecture

```
172.18.0.2  (hwio)       ──── Authorized (sensor data)
172.18.0.3  (OpenPLC)    ──── TARGET: Apply firewall here
172.18.0.4  (FUXA HMI)   ──── Authorized (HMI control)
172.18.0.5  (OPC-UA)     ──── May need access
172.18.0.100 (Attacker)  ──── BLOCK this
```

## 🎯 Task

Add iptables rules on the **OpenPLC container** to restrict access to Modbus TCP (port 502). Only authorized hosts should be able to reach the PLC.

The flag has the format `CybICS(flag)`.

### ⚙️ Understanding iptables Rule Order

**iptables evaluates rules top to bottom, and the first matching rule wins.** This means the order in which you add rules is critical:

- **ACCEPT rules must come before DROP rules** — if a DROP rule matches first, traffic will be blocked even if a later ACCEPT rule would have allowed it.
- A common pattern is to explicitly ACCEPT traffic from authorized sources first, then add a final DROP rule that blocks everything else.
- If you add the DROP rule first, all traffic to that port will be blocked regardless of any ACCEPT rules added afterward.

### 📝 Steps

1. Access the OpenPLC container shell:
   ```bash
   docker exec -it <openplc_container_name> bash
   ```

2. Allow Modbus access from the hardware I/O service (172.18.0.2) and FUXA HMI (172.18.0.4):
   ```bash
   iptables -A INPUT -p tcp --dport 502 -s 172.18.0.2 -j ACCEPT
   iptables -A INPUT -p tcp --dport 502 -s 172.18.0.4 -j ACCEPT
   ```

3. Block Modbus access from all other sources:
   ```bash
   iptables -A INPUT -p tcp --dport 502 -j DROP
   ```

4. Verify the rules are applied:
   ```bash
   iptables -L INPUT -n
   ```

5. Click **Verify Defense** on this challenge page to confirm.

### ⚠️ Important Notes
- The `hwio` service (172.18.0.2) must be able to write sensor values to OpenPLC via Modbus. Do not block it.
- The `FUXA` HMI (172.18.0.4) needs Modbus access for process monitoring and control. Do not block it.
- These rules are **not persistent** — they will be lost when the container restarts. In production, you would save them with `iptables-save`.

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques Defended Against

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Impair Process Control | Unauthorized Command Message | [T0855](https://attack.mitre.org/techniques/T0855/) | Blocking unauthorized Modbus write commands |
| Impair Process Control | Brute Force I/O | [T0806](https://attack.mitre.org/techniques/T0806/) | Preventing register flooding from unauthorized hosts |
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | Blocking port scanning of Modbus services |

### MITRE D3FEND - Defensive Techniques Applied

| Technique | ID | Description |
|-----------|-----|-------------|
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Filtering inbound traffic based on source IP |
| Network Traffic Filtering | [D3-NTF](https://d3fend.mitre.org/technique/d3f:NetworkTrafficFiltering/) | Restricting network traffic to authorized flows |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Communications Protection (SC)** | SC-7 | Boundary protection — restricting access to industrial protocols |
| **Access Control (AC)** | AC-3, AC-4 | Access enforcement and information flow enforcement |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 6.2.10 addresses the challenges of securing legacy protocols that lack built-in authentication. SC-7 (Boundary Protection) recommends implementing application-layer firewalls and access control lists to restrict which systems can communicate using industrial protocols. Since Modbus TCP has no authentication, network-level controls are the primary defense mechanism.

</details>

## 🔍 Defensive Thinking

After completing this challenge, consider:
- What happens if the FUXA HMI is compromised? The attacker now has authorized Modbus access.
- How would you implement deep packet inspection for Modbus to allow reads but block writes?
- What are the trade-offs between host-based firewalls (iptables) and network firewalls?
- How would you make these rules persistent across container restarts?


## 💡 Hints

Use `docker exec -it <container> bash` to get a shell in the OpenPLC container. Then use `iptables -A INPUT` rules to ACCEPT traffic from authorized IPs (FUXA and hwio) on port 502 first, and DROP everything else to that port last. Remember: iptables processes rules top to bottom, first match wins.

## 🔍 Solution

1. Access the OpenPLC container shell:
   ```bash
   docker exec -it <openplc_container> bash
   ```
2. Allow Modbus (port 502) from authorized hosts only:
   ```bash
   iptables -A INPUT -p tcp --dport 502 -s 172.18.0.2 -j ACCEPT
   iptables -A INPUT -p tcp --dport 502 -s 172.18.0.4 -j ACCEPT
   iptables -A INPUT -p tcp --dport 502 -j DROP
   ```
3. Click **Verify Defense** in the CTF interface to receive the flag.

**Flag:** `CybICS(f1r3w4ll_h4rd3n3d)`
