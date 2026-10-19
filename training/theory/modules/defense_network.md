# Network segmentation

In this challenge you cut the attack machine off from the controllers: not just from one port, but from every service on the PLC and on the OPC-UA server. That is the idea behind network segmentation, the control that standards for industrial security put near the top of every list.

## The idea

A hospital does not let visitors wander into the operating theatre. The building is divided into **zones**, such as the public lobby, the wards and the theatres, and only a few controlled doors connect them. Even someone who got into the lobby cannot simply walk to the theatre.

A segmented network works the same way. Devices are grouped into zones by how critical they are, and traffic between zones has to pass through controlled connections called **conduits**. The Purdue model, a common reference for industrial networks, stacks these zones in levels from the physical process at the bottom to the office network at the top. The international standard IEC 62443 uses the same zone-and-conduit language.

<figure>
<svg viewBox="0 0 520 160" role="img" aria-label="The attack box sits in an attacker zone on the left. The PLC and the OPC-UA server sit in a control zone on the right. The line between the zones is cut, so there is no path from the attacker to the controllers.">
  <rect x="20" y="34" width="150" height="96" rx="8" fill="currentColor" fill-opacity="0.06" stroke="currentColor" stroke-opacity="0.7"/>
  <rect x="45" y="66" width="100" height="34" rx="6" fill="none" stroke="#ff6b00" stroke-width="2" stroke-dasharray="5 3"/>
  <rect x="350" y="34" width="150" height="96" rx="8" fill="currentColor" fill-opacity="0.06" stroke="currentColor" stroke-opacity="0.7"/>
  <rect x="370" y="50" width="110" height="30" rx="5" fill="none" stroke="currentColor" stroke-width="2"/>
  <rect x="370" y="88" width="110" height="30" rx="5" fill="none" stroke="currentColor" stroke-width="2"/>
  <g font-size="13" text-anchor="middle" fill="currentColor">
    <text x="95" y="26">attacker zone</text>
    <text x="95" y="88">attack box</text>
    <text x="425" y="26">control zone</text>
    <text x="425" y="70">PLC</text>
    <text x="425" y="108">OPC-UA</text>
    <text x="260" y="150" opacity="0.85">no path from the attacker to the controllers</text>
  </g>
  <line x1="170" y1="82" x2="350" y2="82" stroke="currentColor" stroke-width="2" stroke-opacity="0.6"/>
  <line x1="250" y1="62" x2="270" y2="102" stroke="#ff6b00" stroke-width="4"/>
</svg>
<figcaption>Segmentation removes the attacker's route to the whole control zone, not just to one service.</figcaption>
</figure>

## How it looks on CybICS

The virtual CybICS lab is a **flat network**: every container sits on the same Docker network, `172.18.0.0/24`, and every host can reach every other. You can see the hosts on their Purdue levels here; click one to see its ports:

<div data-widget="purdue-explorer"></div>

The challenge asks you to keep the attack machine (`172.18.0.100`) away from three services:

| Service | Address and port |
|---|---|
| OpenPLC web interface | `172.18.0.3:8080` |
| Modbus TCP | `172.18.0.3:502` |
| OPC-UA server | `172.18.0.5:4840` |

Real segmentation would put a firewall between two separate networks. In the lab you simulate that boundary with `iptables` rules on the target containers themselves. The check looks at the `INPUT` chain of both the OpenPLC and the OPC-UA container for a `DROP` or `REJECT` rule that names the attack machine's address.

## How to approach it

1. **Decide the rule type.** The firewall module used an allow list for one port. Here you block one source across services. Think about which is simpler and which is stronger.
2. **Open a shell on each target** with `docker exec`. The OPC-UA container is based on Alpine Linux and has no `bash`, so run `iptables` directly through `docker exec`.
3. **Add your rule** and list the chain with `iptables -L INPUT -n` to see it as the kernel does.
4. **Test from the attacker's side.** From the attack machine, try the web interface, a Modbus read and an OPC-UA connection. All three should time out.
5. **Test the plant.** The HMI must still show live values, and the OPC-UA server must still read the PLC.

<div data-widget="checkpoint" data-id="scope"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: block lists versus allow lists</summary>

Blocking one address is a **block list**: everything is allowed except what you name. It is quick to write but fragile. An attacker who can pick a new IP address on the same network, which a machine with administrator rights can often do, is no longer on the list.

An **allow list** turns this around: nothing is allowed except the peers you name. It takes more thought, because you must know every legitimate connection, but a new or changed address gets nothing. Real zone boundaries are built as allow lists, with "deny everything else" as the last rule.

</details>

## Detect and defend

Segmentation limits how far an attacker can move after the first foothold, which ATT&CK for ICS describes as Lateral Movement. It defends against techniques such as Remote System Discovery (T0846) and Exploitation of Remote Services (T0866).

- **Confirm the boundary from both sides.** Blocked traffic should never get an answer. The IDS still sees the attempts as unanswered connection requests, which is useful evidence that someone is knocking.
- **Watch the allowed paths.** A compromised host inside the control zone, such as the engineering workstation, is not stopped by a rule against `172.18.0.100`. Monitoring covers that gap.
- **Make it permanent and central.** In a plant, the boundary is a dedicated firewall or separate VLANs (virtual networks on shared switches), configured once and audited, not rules typed into each device.

NIST SP 800-82 lists this under Boundary Protection (SC-7); D3FEND calls it Network Isolation (D3-NI).

## Before you start

- [Defense in depth](/theory/defense-hardening): why one layer is never enough
- [Host firewalling](/theory/defense_firewall): iptables, chains and rule order
- [Network scanning](/theory/scanning): how an attacker finds these services in the first place
