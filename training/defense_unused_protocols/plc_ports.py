#!/usr/bin/env python3
"""Which TCP ports does the PLC offer, and who actually uses them?

Runs INSIDE the OpenPLC container, which has Python but no ss or netstat.
From the landing page's admin shell:

    docker exec -i <openplc> python3 - < /CybICS/training/defense_unused_protocols/plc_ports.py

It reads the kernel's socket tables (/proc/net/tcp and tcp6) and prints

* every port the PLC listens on, and
* every open connection to one of those ports, with the address and, for the
  CybICS lab, the name of the host on the other end.

A port with a server behind it but nobody connected is a candidate for
switching off. One snapshot can miss a client that connects only now and
then, so run it a few times, and in a real plant watch for days or weeks.
Standard library only; it changes nothing.
"""
import socket
import struct

SERVICES = {102: "S7comm (Snap7)", 502: "Modbus/TCP", 8080: "web interface (HTTP)",
            8443: "REST API (HTTPS)", 20000: "DNP3", 44818: "EtherNet/IP",
            43628: "runtime control"}
HOSTS = {"172.18.0.1": "the board itself (landing, IDS)", "172.18.0.2": "hwio",
         "172.18.0.3": "openplc", "172.18.0.4": "fuxa", "172.18.0.5": "opcua",
         "172.18.0.6": "s7com", "172.18.0.10": "engineeringws",
         "172.18.0.11": "cybicsagent", "172.18.0.12": "nginx-proxy",
         "172.18.0.100": "attack-machine"}
LISTEN, ESTABLISHED = "0A", "01"


def _address(hex_addr):
    host, port = hex_addr.split(":")
    if len(host) == 8:
        ip = socket.inet_ntoa(struct.pack("<I", int(host, 16)))
    else:   # tcp6: four little-endian words; show IPv4-mapped addresses as IPv4
        raw = b"".join(struct.pack("<I", int(host[i:i + 8], 16)) for i in range(0, 32, 8))
        ip = socket.inet_ntop(socket.AF_INET6, raw)
        ip = ip[7:] if ip.startswith("::ffff:") else ip
    return ip, int(port, 16)


def sockets():
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            lines = open(path).read().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            yield _address(fields[1]), _address(fields[2]), fields[3]


def main():
    entries = list(sockets())
    listening = sorted({local for local, _, state in entries if state == LISTEN},
                       key=lambda a: a[1])
    print(f"  {'port':>5}  {'service':<22} {'reachable from':<15} connected clients")
    for ip, port in listening:
        where = "container only" if ip.startswith("127.") else "network"
        name = "Docker's internal DNS" if ip == "127.0.0.11" else SERVICES.get(port, "?")
        clients = sorted({remote[0] for local, remote, state in entries
                          if state == ESTABLISHED and local[1] == port})
        used = ", ".join(f"{c} ({HOSTS.get(c, '?')})" for c in clients) or "nobody connected"
        print(f"  {port:>5}  {name:<22} {where:<15} {used}")


if __name__ == "__main__":
    main()
