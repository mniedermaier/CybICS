# Networks in ten minutes

Every attack in CybICS travels over a network: a scan, a forged Modbus write, a stolen password. To follow them you need a handful of ideas that network engineers take for granted, such as addresses, ports, packets and connections. This lesson explains them in plain words, using the CybICS lab network as the example.

## Addresses: who is who

Every device on a network has an **IP address** (Internet Protocol address), four numbers from 0 to 255 separated by dots. The CybICS PLC, for example, is `172.18.0.3`. A message that should reach the PLC carries that address, just as a letter carries the address of the house it is for.

<div class="callout analogy" markdown="1">
**Analogy:** in the CybICS lab network `172.18.0.0/24`, the first three numbers `172.18.0` name the street and the last number names the house. Every device on the street shares the first three numbers; only the house number differs.
</div>

Such a street is called a **subnet**. The `/24` says how much of the address names the street: the first 24 of its 32 bits, which is the first three numbers. Devices on the same subnet can talk to each other directly. To reach another street, a message goes to the **gateway**, a router that knows the way. In CybICS the gateway is `172.18.0.1`, which is the computer that runs Docker.

| Address | Device |
|---|---|
| 172.18.0.1 | the gateway: the host computer itself |
| 172.18.0.2 | hwio, the simulated physical process |
| 172.18.0.3 | openplc, the PLC |
| 172.18.0.4 | fuxa, the HMI (the operator's screen) |
| 172.18.0.5 | opcua, the OPC-UA server |
| 172.18.0.6 | s7com, a second S7 server |
| 172.18.0.10 | engineeringws, the engineering workstation |
| 172.18.0.11 | cybicsagent, the AI assistant |
| 172.18.0.12 | nginx-proxy, which forwards the web interfaces to the host's ports |
| 172.18.0.100 | the attack machine |

Underneath the IP address there is a second, more local name. Every network card has a **MAC address** (Media Access Control address), six pairs of hex digits such as `02:42:ac:12:00:03`. It works only on the local segment, like the name on a door bell: the postman needs the street address to reach the house, then the name to find the right flat.

How does a computer find the MAC address for an IP address? It shouts a question to the whole segment, "who has 172.18.0.3?", and the owner answers. That is the **Address Resolution Protocol (ARP)**, and because nobody checks the answers, an attacker can lie in them. The [man-in-the-middle lesson](/theory/mitm) shows what follows from that.

<div data-widget="checkpoint" data-id="subnet"></div>

## Ports: which program

An IP address finds the computer, but one computer runs many programs. The **port** says which one a message is for. Think of a large office building: the address gets the letter to the building, and the door number on the envelope gets it to the right office. A port is a number from 0 to 65535, and a program that waits for messages on a port is said to **listen** on it.

Industrial protocols have well-known port numbers, which is why a scanner can guess what a device is from its open ports. These are the ones you will meet in CybICS:

| Port | Service | Runs on |
|---|---|---|
| 502 | Modbus TCP | openplc |
| 102 | S7comm, the Siemens protocol | openplc |
| 1102 | S7comm on a non-standard port | s7com |
| 4840 | OPC-UA | opcua |
| 20000 | DNP3, a protocol from power and water utilities | openplc |
| 44818 | EtherNet/IP | openplc |
| 8080 | OpenPLC web interface | openplc |
| 8090 | 3D view of the plant | hwio |
| 6080, 5901 | desktop in the browser (noVNC) and VNC | engineeringws |
| 6081, 5902 | desktop in the browser (noVNC) and VNC | the attack machine |
| 5000, 11434 | assistant web interface and its language model (Ollama) | cybicsagent |
| 1881 | FUXA HMI web interface | fuxa |
| 80 | CybICS landing page | the host |
| 8443 | IDS web interface | the host |

The program that *starts* a conversation, the **client**, also needs a port for the answers. It gets a random high number, such as 50312, which is forgotten when the conversation ends.

## Packets: envelopes inside envelopes

Data does not flow through a network as one long stream. It is cut into **packets**, small pieces that each carry their own addresses, like envelopes in the post. A single Modbus request fits into one packet.

Each packet is built in layers, and each layer adds the address information it needs. Picture a letter put into an envelope, which goes into a bigger envelope, which goes into a postbag:

<figure class="wide">
<svg viewBox="0 0 520 210" role="img"
     aria-label="A packet drawn as nested envelopes. The outer Ethernet frame carries the MAC addresses of the attack machine and OpenPLC. Inside it the IP packet carries 172.18.0.100 to 172.18.0.3. Inside that the TCP segment carries port 50312 to port 502. In the middle sits the Modbus request: read holding register 1126.">
  <rect x="10" y="10" width="500" height="190" rx="8" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.55"/>
  <text x="24" y="32" font-size="12" font-weight="bold">Ethernet frame</text>
  <text x="24" y="48" font-size="11">from MAC of the attack machine &rarr; to MAC of openplc</text>

  <rect x="40" y="60" width="440" height="128" rx="7" fill="currentColor" fill-opacity="0.1" stroke="currentColor" stroke-opacity="0.55"/>
  <text x="54" y="80" font-size="12" font-weight="bold">IP packet</text>
  <text x="54" y="96" font-size="11">from 172.18.0.100 &rarr; to 172.18.0.3</text>

  <rect x="70" y="106" width="380" height="72" rx="6" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.55"/>
  <text x="84" y="124" font-size="12" font-weight="bold">TCP segment</text>
  <text x="84" y="140" font-size="11">from port 50312 &rarr; to port 502</text>

  <rect x="250" y="116" width="186" height="50" rx="5" fill="#ff6b00"/>
  <text x="343" y="136" text-anchor="middle" font-size="12" font-weight="bold" fill="#1a1a1a">Modbus data</text>
  <text x="343" y="152" text-anchor="middle" font-size="11" fill="#1a1a1a">read register 1126</text>
</svg>
<figcaption>One Modbus request from the attack machine to the PLC. Ethernet (MAC addresses) carries it across the local segment, IP (addresses) to the right computer, TCP (ports) to the right program, and only the innermost envelope holds the Modbus request itself.</figcaption>
</figure>

Each layer only reads its own envelope. The network card checks the MAC address, the operating system checks the IP address and the port, and only the Modbus program opens the innermost envelope. A tool like Wireshark shows you all the envelopes of a packet at once.

## TCP: a handshake before the talk

The envelope with the ports belongs to the **Transmission Control Protocol (TCP)**. TCP turns loose packets into a reliable **connection**: it numbers the packets, asks again for lost ones and delivers them in order. Modbus TCP, S7comm and OPC-UA all run over TCP.

Before any data flows, the two sides shake hands in three steps, the **three-way handshake**:

<figure>
<svg viewBox="0 0 360 200" role="img"
     aria-label="The TCP three-way handshake between a client and OpenPLC on port 502. The client sends SYN, the PLC answers SYN-ACK, the client replies ACK. Only then does the Modbus request follow.">
  <text x="60" y="20" text-anchor="middle" font-size="12" font-weight="bold">Client</text>
  <text x="300" y="20" text-anchor="middle" font-size="12" font-weight="bold">openplc : 502</text>
  <line x1="60" y1="28" x2="60" y2="192" stroke="currentColor" stroke-opacity="0.55"/>
  <line x1="300" y1="28" x2="300" y2="192" stroke="currentColor" stroke-opacity="0.55"/>
  <g font-size="11" text-anchor="middle">
    <line x1="64" y1="48" x2="290" y2="68" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 296 69 L 287 63 L 288 72 Z" fill="#ff6b00"/>
    <text x="180" y="50">1. SYN: "can we talk?"</text>
    <line x1="296" y1="88" x2="70" y2="108" stroke="currentColor" stroke-width="2"/>
    <path d="M 64 109 L 73 103 L 72 112 Z" fill="currentColor"/>
    <text x="180" y="90">2. SYN-ACK: "yes, can you hear me?"</text>
    <line x1="64" y1="128" x2="290" y2="148" stroke="#ff6b00" stroke-width="2"/>
    <path d="M 296 149 L 287 143 L 288 152 Z" fill="#ff6b00"/>
    <text x="180" y="130">3. ACK: "yes"</text>
    <rect x="110" y="164" width="140" height="22" rx="4" fill="#ff6b00"/>
    <text x="180" y="179" fill="#1a1a1a" font-weight="bold">now: Modbus data</text>
  </g>
</svg>
<figcaption>The three-way handshake. SYN asks for a connection, SYN-ACK accepts it, ACK confirms. Only then does the first Modbus byte travel.</figcaption>
</figure>

If nothing listens on the port, the computer answers the SYN with a reset (**RST**) instead: "no one here". This is what a port scanner relies on. It sends a SYN to each port and listens: a SYN-ACK means the port is open, an RST means it is closed, silence often means a firewall swallowed the packet. Many scanners never send the final ACK, so they learn the answer without ever finishing a connection.

Not everything uses TCP. The **User Datagram Protocol (UDP)** sends single packets with no handshake and no delivery check, which is faster but gives no guarantee that anything arrived.

<div data-widget="checkpoint" data-id="handshake"></div>

## Containers and the lab network

In the virtual CybICS lab, each service runs in its own **container**: a small, sealed box with its own programs and files that shares the host computer's operating system. Docker, the software that runs the containers, gives each one its own network card and its own IP address. That is why openplc, fuxa and opcua look like separate computers to you, although they all run on one machine.

All these containers are plugged into one virtual switch, a Docker **bridge network** called `virt-cybics`, with the subnet `172.18.0.0/24`. On that bridge the containers can also find each other by name: FUXA reaches the PLC as `openplc:502` instead of `172.18.0.3:502`.

Two services are different. The landing page and the IDS use **host networking**: they get no container address and share the network of the host computer directly. The landing page answers on the host's port 80. The IDS finds the bridge among the host's network interfaces and listens on it, because every packet between two containers crosses it, and keeps what belongs to `172.18.0.0/24`. That is how it sees a Modbus request between FUXA and the PLC, although it is neither the sender nor the receiver.

<div class="callout tip" markdown="1">
**Published ports:** Docker can also forward a port of the host into a container. CybICS does that for 502, 1881, 4840 and others, so the same services are reachable at the host's own address, not only on the bridge.
</div>

## In CybICS

Now the pieces fit together. The attack machine, `172.18.0.100`, is plugged into the same bridge as the PLC, the HMI and the OPC-UA server. There is no router, no firewall and no second street between them: the network is **flat**. Any packet the attack machine sends to `172.18.0.3:502` arrives, completes the handshake and is handed to the Modbus program.

Combine that with what the [Modbus lesson](/theory/modbus) will show you, a protocol without a login, and you have the core problem of many real plants. Being able to reach a port is the same as being allowed to use it. Click a host below to see its address, its ports and what targets it:

<div data-widget="purdue-explorer"></div>

<div class="callout cybics" markdown="1">
**In CybICS:** the [Service Scanning challenge](/ctf/challenge/scanning) asks you to map this network yourself. Use the address table and the port table above to check what your scanner reports.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: what /24 means in bits</summary>

An IP address is 32 bits, written as four bytes in decimal. `172.18.0.3` is:

```
10101100 . 00010010 . 00000000 . 00000011
  172         18          0          3
```

The `/24` is the **prefix length**: the first 24 bits are the network part, the remaining 8 bits number the hosts. Eight bits give 256 values, 0 to 255. The first one (`172.18.0.0`) names the network itself and the last one (`172.18.0.255`) is the broadcast address that reaches every host, so 254 addresses are left for devices.

The same prefix is often written as a **netmask**: 24 one-bits followed by 8 zero-bits, `255.255.255.0`. A computer ANDs a destination address with this mask. If the result equals its own network, the destination is on the same street and it sends the packet directly, after an ARP lookup; otherwise it sends it to the gateway.

</details>
