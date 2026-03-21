# 🌐 Network Segmentation

> **MITRE D3FEND:** `Isolate` | [D3-NI - Network Isolation](https://d3fend.mitre.org/technique/d3f:NetworkIsolation/)

## 📋 Overview
Network segmentation is a fundamental security principle that limits lateral movement by dividing a network into isolated zones. In ICS environments, proper segmentation prevents an attacker who compromises one system from easily accessing critical control systems.

In the CybICS testbed, the attack machine (172.18.0.100) currently has unrestricted access to all services on the network. This challenge requires you to implement network-level controls that block the attack machine from reaching critical ICS services.

## 🏗️ Network Architecture

```
┌──────────────────────────────────────────────────────┐
│                 CybICS Network (172.18.0.0/24)       │
│                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │  OpenPLC   │  │   FUXA     │  │  OPC-UA    │    │
│  │ 172.18.0.3 │  │ 172.18.0.4 │  │ 172.18.0.5 │    │
│  │ :8080,:502 │  │   :1881    │  │   :4840    │    │
│  └────────────┘  └────────────┘  └────────────┘    │
│        ▲                                             │
│        │ BLOCK                                       │
│  ┌─────┴──────┐                                     │
│  │  Attacker  │                                      │
│  │172.18.0.100│                                      │
│  └────────────┘                                      │
└──────────────────────────────────────────────────────┘
```

## 🎯 Task

Block the attack machine (172.18.0.100) from accessing the following critical services:
1. **OpenPLC Web UI** (172.18.0.3:8080)
2. **Modbus TCP** (172.18.0.3:502)
3. **OPC-UA Server** (172.18.0.5:4840)

### 📝 Approach 1: Firewall Rules on Target Containers

Apply iptables rules on each target container to drop traffic from the attack machine:

```bash
# On the OpenPLC container:
docker exec -it <openplc_container> bash
iptables -A INPUT -s 172.18.0.100 -j DROP

# On the OPC-UA container:
docker exec -it <opcua_container> bash
iptables -A INPUT -s 172.18.0.100 -j DROP
```

### 📝 Approach 2: Firewall Rules on the Attack Machine

Alternatively, apply outbound rules on the attack machine itself:

```bash
docker exec -it <attack_container> bash
iptables -A OUTPUT -d 172.18.0.3 -j DROP
iptables -A OUTPUT -d 172.18.0.5 -j DROP
```

### Verification

After applying rules, verify from the attack machine:
```bash
# These should all fail/timeout:
docker exec <attack_container> nc -z -w 3 172.18.0.3 8080
docker exec <attack_container> nc -z -w 3 172.18.0.3 502
docker exec <attack_container> nc -z -w 3 172.18.0.5 4840
```

Click **Verify Defense** on this challenge page to confirm.

## ⚠️ Important Notes
- Do not block legitimate traffic between authorized services (hwio, FUXA, etc.)
- These rules are not persistent — they will be lost when containers restart
- In production, you would use a dedicated firewall or SDN (Software-Defined Networking) for segmentation

## 🛡️ Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques Defended Against

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Lateral Movement | Exploitation of Remote Services | [T0866](https://attack.mitre.org/techniques/T0866/) | Preventing lateral movement to ICS devices |
| Discovery | Remote System Discovery | [T0846](https://attack.mitre.org/techniques/T0846/) | Blocking reconnaissance of ICS services |
| Initial Access | External Remote Services | [T0822](https://attack.mitre.org/techniques/T0822/) | Restricting access from external/untrusted hosts |

### MITRE D3FEND - Defensive Techniques Applied

| Technique | ID | Description |
|-----------|-----|-------------|
| Network Isolation | [D3-NI](https://d3fend.mitre.org/technique/d3f:NetworkIsolation/) | Isolating critical systems from untrusted networks |
| Broadcast Domain Isolation | [D3-BDI](https://d3fend.mitre.org/technique/d3f:BroadcastDomainIsolation/) | Segmenting network broadcast domains |
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Filtering inbound traffic from untrusted sources |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **System and Communications Protection (SC)** | SC-7 | Boundary protection and network segmentation |
| **Access Control (AC)** | AC-4 | Information flow enforcement between zones |

**Why NIST 800-82r3 matters here:** NIST 800-82r3 Section 5.1.2 emphasizes defense-in-depth through network segmentation as a primary security control for OT environments. The Purdue Model recommends separating IT and OT networks into distinct security zones with controlled conduits between them. SC-7 (Boundary Protection) is one of the most critical controls for ICS — preventing an attacker from moving between the corporate network and the control system network.

</details>

## 🔍 Defensive Thinking

After completing this challenge, consider:
- What if the attacker compromises an authorized host (e.g., FUXA) first? How does segmentation help then?
- How would you implement the Purdue Model zones in this environment?
- What are the challenges of implementing network segmentation in brownfield (existing) ICS environments?
- How does micro-segmentation differ from traditional VLAN-based segmentation?
