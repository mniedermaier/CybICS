# Closing unused services

In this challenge you shrink the PLC's attack surface: you find out which of its network services the plant really uses, switch off the ones it does not, and block the one that cannot be switched off. Four attack challenges in this lab enter through services nobody needs. After this module they find the doors closed, while the plant keeps running.

## The idea

Every network service a device offers is a door. A door that nobody uses still has a lock that can be picked, and nobody watches it. The **attack surface** is the sum of all those doors. Making it smaller is one of the cheapest and most effective defences there is, because a service that is switched off cannot be attacked at all.

<div class="callout analogy" markdown="1">
**Analogy:** a building with six entrances, of which staff use two. You could post a guard at each of the four others, but bricking them up is cheaper and never falls asleep. Where a door cannot be bricked up, for example a fire exit, you lock it from the inside.
</div>

Industrial devices ship with many protocols switched on, because the vendor cannot know which ones your plant needs. Turning off the rest is called **hardening**. MITRE ATT&CK for ICS lists it as the mitigation *Disable or Remove Feature or Program* (M0942); in MITRE D3FEND it is *Application Configuration Hardening* (D3-ACH). For a service without an off switch, a firewall rule that refuses the connections is the fallback (*Inbound Traffic Filtering*, D3-ITF).

The order matters. Switching a service off removes it. A firewall rule only hides it: the service still runs behind the rule, and it is reachable again the moment the rule is flushed, the device restarts, or an attacker gets onto a host the rule allows.

## How it looks on CybICS

The PLC, OpenPLC at `172.18.0.3`, offers six services:

| Port | Service | Used by the plant? |
|---|---|---|
| 502 | Modbus/TCP | yes: the plant simulation, the HMI and the OPC-UA gateway |
| 8080 | web interface | yes: engineers upload programs here |
| 102 | S7comm | no |
| 20000 | DNP3 | no |
| 44818 | EtherNet/IP | no |
| 8443 | REST API (HTTPS) | no |

S7comm, DNP3 and EtherNet/IP each have a checkbox on the **Settings** page of OpenPLC's web interface. The REST API has none: OpenPLC starts it every time. A host firewall rule inside the PLC container is the only way to close it.

<div data-widget="checkpoint" data-id="nobody-connected"></div>

## How to approach it

1. **Look from the outside.** Scan every TCP port of the PLC from the attack shell, not only the well-known ones. That is what an attacker sees.
2. **Look from the inside.** List the PLC's listening ports and the hosts connected to them. The challenge provides a small script for that, because the PLC container has no `ss` or `netstat`. Repeat it a few times: some clients connect only now and then.
3. **Decide port by port** from what the plant is designed to do, not only from what you saw in a few seconds.
4. **Switch off** what has a switch, in OpenPLC's Settings page, and save.
5. **Firewall** what has no switch, with a rule at the top of the PLC's `INPUT` chain.
6. **Check twice:** the scan shows only what you meant to keep, and the plant still runs with live values on the HMI.

The check reads OpenPLC's settings and its list of listening ports, tries to connect to port 8443 from the board and from the attack machine, and makes sure Modbus, the web interface and the plant's heartbeat are still alive.

<div data-widget="checkpoint" data-id="hide-or-remove"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: why a firewall rule is not enough on its own</summary>

A rule in the PLC container lives only in the running container's network stack. Restart the container and it is gone, while the settings, stored in OpenPLC's database, stay. In a real plant the rule belongs in a firewall configuration that is loaded at boot and kept in configuration management. Updates and factory resets bring defaults back, so repeat the outside scan after each one and compare it with your list of expected ports.

</details>

## Detect and defend

- **Keep a list of expected flows:** who talks to whom, on which port. It is the basis for switching things off and for spotting what does not belong.
- **Prefer the off switch.** Use a firewall for services without a switch, and as a second layer for the ones you keep.
- **Ask the vendor** for a switch when a management interface cannot be disabled.
- **Watch the closed doors.** After hardening, any connection attempt to 102, 20000, 44818 or 8443 on the PLC has no legitimate reason. The CybICS IDS already alerts on S7comm access, DNP3 commands and port scans.
- **Do not cut what the process needs.** Closing too much is an outage: the HMI, the OPC-UA gateway and the plant simulation all depend on Modbus.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The commands are in training/defense_unused_protocols/README.md, including how to undo the defence and a Reset that restores the three settings in openplc.db and restarts the OpenPLC container (which also removes all firewall rules inside it). While the defence is in place, S7 Side Door, Stop Means Stop?, DNP3 Side Door and The Forgotten API cannot be solved, the scanning challenge shows fewer ports, and the test suite's side-door tests fail (the readiness gate in tests/conftest.py may not notice: on the virtual stack it probes the published port 102, which Docker's proxy accepts even when nothing listens behind it); plan the order of challenges in class, or have students undo it. Saving OpenPLC's Settings page restarts its Modbus server, so the plant's clients reconnect once. The check counts a service as closed only when the setting is off and the PLC no longer listens on the port; a firewall rule in front of S7, DNP3 or EtherNet/IP fails it on purpose. Port 8443 is probed with a bare TCP connect from 172.18.0.1 and from the attack shell. The plant check samples the heartbeat through hwio's /api/state on the virtual stack, and over Modbus from the board where there is no hwio API; on a board whose Modbus is firewalled to the plant's own clients the latter fails.

</details>

## Before you start

- [Network scanning](/theory/scanning): finding open ports from the outside
- [The S7 side door](/theory/s7_sidedoor), [DNP3 Side Door](/theory/dnp3_sidedoor) and [The forgotten API](/theory/openplc_restapi): what an attacker does with the services you close
- [Host firewalling](/theory/defense_firewall): iptables rules and their order
