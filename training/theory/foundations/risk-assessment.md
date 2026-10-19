# Asset inventory, risk and IEC 62443

You cannot protect what you do not know you have, and you cannot protect everything equally well. This article walks through the three questions every OT security programme starts with: what is on the network, which risks matter most, and how to split the network so that one compromised device does not mean a compromised plant.

## Step 1: know what you have

An **asset inventory** is a list of every device and service in the plant: what it is, where it sits on the network, which protocols it speaks, who maintains it and what it controls. It sounds like paperwork, but almost every later decision depends on it. A firewall rule for a PLC you do not know about is a rule nobody writes.

There are two ways to build the list.

- **Passive discovery** listens. A sensor on a mirror port of a switch records which addresses talk to which, on which ports, using which protocols. It sends nothing, so it cannot disturb the process. Its weakness: a device that stays silent stays invisible.
- **Active discovery** asks. A scanner such as nmap sends packets to every address and port and reads the answers. It is fast and finds silent devices, but it puts unusual traffic on the network.

<div class="callout warning" markdown="1">
**Why active scanning is risky in OT:** many controllers run small, old network stacks that were only ever tested with the traffic their vendor expected. A burst of half-open connections or a malformed probe can make such a device hang or reboot, and a rebooting PLC stops controlling its process. NIST SP 800-82, the US guide to OT security, therefore recommends passive methods first and active scans only with care, coordination with operations and ideally on a test system.
</div>

In practice teams combine both: passive listening for the baseline, then carefully scoped active queries, often using the device's own protocol (for example a single identity request) instead of a full port scan.

<div data-widget="checkpoint" data-id="passive"></div>

## Step 2: decide what matters most

A **risk** is a bad thing that could happen, together with an estimate of how bad it is. The common working formula is:

**risk = likelihood × impact**

- **Likelihood:** how probable is it that the scenario happens? Think about how reachable the target is, how much skill it takes and whether tools exist.
- **Impact:** how bad is it if it does happen? In OT, impact is measured first in harm to people and the environment, then in damage to equipment, then in lost production and only then in data.

Teams usually score both on a simple scale, for example 1 (very low) to 5 (very high), and multiply. The numbers are not measurements. They are a structured way to argue about priorities and to write down why.

### A worked example on CybICS

Here are four scenarios for the CybICS gas plant, scored on that 1 to 5 scale. The scores are a teaching example: your class may well argue for different ones, and that discussion is the point.

| Scenario | Likelihood | Impact | Risk |
|---|---|---|---|
| A host on the plant network sends Modbus writes that keep the compressor on, driving the HPT past what the blow-out valve can vent | 5: no authentication, one free tool | 5: overpressure, physical damage | **25** |
| Someone guesses the FUXA HMI login on port 1881 and switches the plant to manual mode | 4: web login, weak passwords are common | 4: full operator control | **16** |
| Someone reads values from the S7 server on port 1102 | 5: no authentication | 2: information only | **10** |
| Someone with physical access connects to the board's serial console (UART) | 2: needs to be in the room | 4: device-level access | **8** |

The top row wins clearly, and it tells you where to spend effort first. Now ask what a control would change. Blocking every host except FUXA, OPC-UA and `hwio` from reaching port 502 does not make an overpressure any less dangerous, so impact stays at 5. It makes the scenario much harder to reach, so likelihood might drop to 2, and the risk to 10. Most network controls work this way: they lower likelihood. Lowering impact needs changes to the plant itself, such as a separate safety system (see [Safety systems](/theory/safety-systems)).

<div data-widget="checkpoint" data-id="factor"></div>

## Step 3: zones and conduits with IEC 62443

**IEC 62443** is the international series of standards for the security of Industrial Automation and Control Systems (IACS). It covers everyone involved: the asset owner, the system integrator and the product vendor. Three of its ideas are worth knowing from day one.

**Zones and conduits.** A **zone** is a group of assets that share the same security requirements, for example "all controllers of the compression unit". A **conduit** is the path that connects two zones, together with the rules for what may travel along it. Instead of protecting every device separately, you protect the borders of each zone and keep conduits as narrow as possible.

<div class="callout analogy" markdown="1">
**Analogy:** a zone is a room with a locked door; a conduit is a hatch in the wall with a guard who only lets certain parcels through. Someone who gets into the office does not automatically get into the control room.
</div>

**Security levels.** Each zone gets a target **Security Level (SL)** that says which attacker it must withstand:

| Level | Protects against |
|---|---|
| SL 1 | Casual or accidental violation, such as a mistake |
| SL 2 | Intentional attack with simple means, few resources and general skills |
| SL 3 | Sophisticated attack with moderate resources and ICS-specific skills |
| SL 4 | Sophisticated attack with extended resources, ICS-specific skills and high motivation, such as a state-funded team |

**Foundational requirements.** The standard groups its technical requirements into seven **Foundational Requirements (FR)**: identification and authentication control, use control, system integrity, data confidentiality, restricted data flow, timely response to events, and resource availability. "Restricted data flow" is the one zones and conduits implement.

## Applied to the CybICS network

Explore the CybICS hosts on the Purdue levels. Click a host to see its address, its ports and the attacks that target it. That is a small asset inventory.

<div data-widget="purdue-explorer"></div>

Today all CybICS containers share one flat network, `172.18.0.0/24`. In IEC 62443 terms that is a single zone with no conduits: the attack machine at `.100` can talk to the PLC exactly as freely as the HMI can. A zone model for the plant could look like this:

| Zone | Members | Allowed conduits in |
|---|---|---|
| Control | OpenPLC `.3`, `hwio` `.2` (and the STM32 on the board) | Modbus 502 from the supervisory zone only |
| Supervisory | FUXA `.4`, OPC-UA `.5`, S7 server `.6` | HMI and OPC-UA client access from operations |
| Engineering | Engineering workstation `.10` | Maintenance access to the PLC's web interface on 8080, during planned changes |
| Untrusted | Attack machine `.100`, standing in for any office host | None into the control zone |

The *Network segmentation* defence challenge asks you to build the most important part of that last row: stop the attack machine from reaching the PLC and the OPC-UA server. When you solve it, rescore the first row of the risk table and see what changed.

<details class="deep-dive" markdown="1">
<summary>Deep dive: which part of IEC 62443 says what</summary>

The series is split into four groups. Parts 1-x define concepts and terms. Parts 2-x are for the asset owner: how to run a security programme and manage patches. Parts 3-x are about the system: **IEC 62443-3-2** describes the risk assessment that divides a system into zones and conduits and sets a target security level for each, and **IEC 62443-3-3** lists the system requirements per foundational requirement and security level. Parts 4-x are for product vendors: **4-1** for a secure development process and **4-2** for the requirements on individual components such as a PLC.

The standard also distinguishes three kinds of security level. **SL-T** (target) is what a zone needs, **SL-C** (capability) is what a product or system can deliver when configured correctly, and **SL-A** (achieved) is what the installed system actually reaches. A zone is in good shape when SL-A meets SL-T.

</details>
