# Close the Side Doors

> **MITRE D3FEND:** `Harden` | [D3-ACH - Application Configuration Hardening](https://d3fend.mitre.org/technique/d3f:ApplicationConfigurationHardening/) | `Isolate` | [D3-ITF - Inbound Traffic Filtering](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/)

## Overview

The CybICS PLC speaks six network protocols, and the plant needs two of them.
Four challenges in this lab walk through the other four:

| Port | Service | Who uses it in the plant | Challenge that abuses it |
|------|---------|--------------------------|--------------------------|
| 502 | Modbus/TCP | hwio, FUXA and the OPC-UA gateway | (the plant's own protocol) |
| 8080 | Web interface | engineers, now and then | Password Attack |
| 102 | S7comm (Snap7) | nobody | [S7 Side Door](../s7_sidedoor/README.md), [Stop Means Stop?](../s7_cpu_stop/README.md) |
| 20000 | DNP3 | nobody | [DNP3 Side Door](../dnp3_sidedoor/README.md) |
| 44818 | EtherNet/IP | nobody | found by [Service Scanning](../scanning/README.md) |
| 8443 | REST API (HTTPS) | nobody | [The Forgotten API](../openplc_restapi/README.md) |

A firewall that guards only Modbus (the [Modbus Firewall](../defense_firewall/README.md)
challenge) leaves all four side doors open. This challenge closes them the
way a plant engineer would: **switch off what has a switch, firewall what
has none, and keep everything the plant needs.**

You will first find out yourself which ports are in use, then

- switch off **S7comm, DNP3 and EtherNet/IP** in OpenPLC's **Settings** page;
- block the **REST API on 8443** with a firewall rule on the PLC, because
  OpenPLC has no setting for it;
- leave **Modbus (502)** and the **web interface (8080)** running.

The flag has the format `CybICS(flag)`. **Verify Defense** reveals it when

- OpenPLC's settings switch S7, DNP3 and EtherNet/IP off **and** nothing
  listens on 102, 20000 or 44818 any more. A firewall rule in front of a
  running server does not count: it hides the service, it does not remove it;
- port 8443 does not accept a connection, neither from the board (the landing
  page, 172.18.0.1) nor from the attack shell (172.18.0.100);
- 502 and 8080 still listen and the plant still runs: the PLC's heartbeat
  output keeps toggling as the plant simulation (hwio) reads it over Modbus
  (on a board without hwio's web view, the check reads it over Modbus itself).

> **Doing this closes the side-door challenges.** S7 Side Door, Stop Means
> Stop?, DNP3 Side Door and The Forgotten API cannot be solved while your
> defence is in place, and the automated test suite expects the PLC as it was
> shipped. [Undo it](#undoing-it) when you are done.

## Steps

The Docker commands run in the landing page's **admin shell** (WebShell view,
*Admin shell*), which has access to Docker; the attack shell has none. The
admin shell has no interactive terminal, so every command is a complete
`docker exec`. The scans run in the **attack shell**.

1. **Look from the outside.** In the attack shell, scan every TCP port of the
   PLC, not just the well-known ones:
   ```bash
   nmap -p- -T4 172.18.0.3
   ```
   Note every open port. These are the doors an attacker sees.

2. **Look from the inside: who uses them?** Find the PLC container's name in
   the admin shell, then list its ports together with the hosts that are
   connected to them right now:
   ```bash
   docker ps --format '{{.Names}}' | grep openplc
   docker exec -i <openplc> python3 - < /CybICS/training/defense_unused_protocols/plc_ports.py
   ```
   Use the name from the first command for `<openplc>` (`virtual-openplc-1`
   in the virtual lab). The PLC container has no `ss` or `netstat`, so
   [`plc_ports.py`](plc_ports.py) reads the kernel's socket table
   `/proc/net/tcp` for you; read it if you want to know how. Run it a few
   times. You should see Modbus with three clients, and four ports with
   nobody connected.

   **"Nobody connected" is evidence, not proof.** The web interface on 8080
   usually shows nobody too, yet the engineers need it to upload programs.
   Decide port by port, from what the plant is meant to do: the CybICS plant
   is a Modbus plant; nothing in it is built to speak S7, DNP3, EtherNet/IP or
   the REST API.

3. **Switch off S7, DNP3 and EtherNet/IP.** Open the OpenPLC web interface
   (port 8080 on the CybICS host, or the OpenPLC link on the landing page)
   and log in (`openplc`/`openplc`, or the password you chose in
   [Credential Hardening](../defense_password/README.md)). Go to
   **Settings** and

   - untick **Enable S7 Protocol**,
   - untick **Enable DNP3 Server**,
   - untick **Enable EtherNet/IP Server**,
   - leave **Enable Modbus Server** (port 502) and **Start OpenPLC in RUN
     mode** ticked, and the other fields as they are,

   then click **Save Changes**. OpenPLC stores the settings in its database
   and applies them at once. Saving also restarts the Modbus server, so hwio,
   FUXA and the OPC-UA gateway lose their connection for a moment and
   reconnect on their own.

4. **Block the REST API.** OpenPLC starts the REST API on 8443 every time and
   has no setting for it, so a firewall rule on the PLC has to do it. In the
   admin shell:
   ```bash
   docker exec <openplc> iptables -I INPUT -p tcp --dport 8443 -j REJECT --reject-with tcp-reset
   ```
   `-I` puts the rule at the top of the chain, so no earlier `ACCEPT` rule
   (for example from the Modbus Firewall challenge) can let the traffic
   through first. `REJECT --reject-with tcp-reset` answers like a closed port;
   `DROP` would work too, but makes scanners report the port as *filtered*,
   which tells an attacker something is there.

5. **Look again.** Repeat steps 1 and 2. The scan should show only 502 and
   8080 open. Inside the container, 8443 still appears as listening: the API
   still runs, and only the firewall keeps it unreachable. Modbus has its
   three clients back.

6. Click **Verify Defense**.

### Undoing it

Do this before you play S7 Side Door, Stop Means Stop?, DNP3 Side Door or The
Forgotten API again, and before you run the test suite.

1. In OpenPLC's **Settings**, tick **Enable S7 Protocol**, **Enable DNP3
   Server** (port 20000) and **Enable EtherNet/IP Server** (port 44818) again
   and click **Save Changes**.
2. Remove the firewall rule; the command is the one from step 4 with `-D`
   (delete) instead of `-I`:
   ```bash
   docker exec <openplc> iptables -D INPUT -p tcp --dport 8443 -j REJECT --reject-with tcp-reset
   ```

### Reset

If you are not sure what you changed, or cannot log in to OpenPLC any more,
this puts the three protocol settings back to the shipped values and restarts
the PLC container. A restart also removes **every** firewall rule inside it,
including those from the Modbus Firewall and Network Segmentation
challenges, and resets the PLC's memory; the plant is back after about
twenty seconds.

```bash
P=$(docker ps --filter name=openplc --format '{{.Names}}' | head -n1); docker exec "$P" sqlite3 /CybICS/OpenPLC_v3/webserver/openplc.db "UPDATE Settings SET Value = 'true' WHERE Key = 'snap7'; UPDATE Settings SET Value = '20000' WHERE Key = 'Dnp3_port'; UPDATE Settings SET Value = '44818' WHERE Key = 'Enip_port';" && docker restart "$P"
```

## How long the change lasts

The two halves of the defence behave differently, and that is part of the
lesson.

- **The settings** live in OpenPLC's database inside the container. They
  survive a restart of the container (and of the board), but in the virtual
  lab not its re-creation: `./cybics.sh update` or a new image starts from the
  shipped database with everything enabled again.
- **The firewall rule** lives only in the running container's network
  stack. Any restart of the PLC container brings the REST API back. In a real
  plant the rule belongs in the host's or the network's firewall
  configuration, saved and loaded at boot (`iptables-save` and a restore at
  start-up, nftables, or the plant firewall), and in configuration
  management, so that a rebuild cannot quietly undo it.

## Detect and Defend

- **Start from what the process needs, not from what the device offers.** A
  PLC's datasheet lists every protocol it can speak; the plant's design says
  which ones it does. Keep a list of the expected flows (who talks to whom,
  on which port) and switch off everything else. Here that list has one
  protocol for the process (Modbus) and one for engineering (the web
  interface).
- **Prefer the off switch to the firewall.** A disabled service cannot be
  reached by a host you forgot in your rules, by a firewall that was flushed
  or restarted, or through a bug in the service itself. A firewall rule is
  the fallback for services without a switch, like OpenPLC's REST API, and a
  second layer for the ones you need.
- **Ask the vendor.** A management interface that cannot be switched off is
  worth a support ticket or a feature request.
- **Check after every change.** Updates, re-installations and factory resets
  re-enable defaults. Re-run the outside scan (step 1) after each one, and
  compare it with your list of expected ports.
- **Watch for the doors you closed.** A connection attempt to 102, 20000,
  44818 or 8443 on the PLC now has no legitimate reason at all. The CybICS IDS
  already alerts on S7 access and on DNP3 commands; a port scan raises its
  scan alert.
- **Keep the plant running.** Closing too much is an outage. Verify after
  the change that the HMI still shows live values and the process behaves as
  before.

## Security Framework References

<details>
  <summary>Click to expand</summary>

### MITRE ATT&CK for ICS - Techniques Defended Against

| Tactic | Technique | ID | Description |
|--------|-----------|-----|-------------|
| Impair Process Control | Unauthorized Message: Command Message | [T1692.001](https://attack.mitre.org/techniques/T1692/001/) | Stop commands over S7comm (S7 Side Door) or DNP3 (DNP3 Side Door) no longer reach the PLC |
| Execution, Evasion | Change Operating Mode | [T0858](https://attack.mitre.org/techniques/T0858/) | No S7comm CPU STOP is possible once the S7 server is off (Stop Means Stop?) |
| Initial Access, Lateral Movement | Exploitation of Remote Services | [T0866](https://attack.mitre.org/techniques/T0866/) | The REST API that anyone could claim (The Forgotten API) is unreachable |

### MITRE ATT&CK for ICS - Mitigations Applied

| Mitigation | ID | Description |
|------------|-----|-------------|
| Disable or Remove Feature or Program | [M0942](https://attack.mitre.org/mitigations/M0942/) | S7comm, DNP3 and EtherNet/IP switched off in the PLC's settings |
| Filter Network Traffic | [M0937](https://attack.mitre.org/mitigations/M0937/) | The REST API, which has no setting, blocked on the PLC |

### MITRE D3FEND - Defensive Techniques Applied

| Technique | ID | Description |
|-----------|-----|-------------|
| Application Configuration Hardening | [D3-ACH](https://d3fend.mitre.org/technique/d3f:ApplicationConfigurationHardening/) | Changing the PLC's configuration to reduce its attack surface |
| Inbound Traffic Filtering | [D3-ITF](https://d3fend.mitre.org/technique/d3f:InboundTrafficFiltering/) | Refusing inbound connections to the REST API port |

### NIST SP 800-82r3 Reference

| Control Family | Controls | Relevance |
|----------------|----------|-----------|
| **Configuration Management (CM)** | CM-7 | Least functionality: disable functions, ports and protocols the system does not need |
| **Configuration Management (CM)** | CM-6, CM-8 | Configuration settings and a component inventory that records which services each device runs |
| **System and Communications Protection (SC)** | SC-7 | Boundary protection for the interface that cannot be switched off |

</details>

## Hints

<details>
  <summary>💡 Hint</summary>

Three of the four unused services have a checkbox on OpenPLC's **Settings**
page. The fourth, the REST API on 8443, has none: block it with an
`iptables` rule inside the PLC container, at the top of the `INPUT` chain.
Keep Modbus and the web interface on.

</details>
