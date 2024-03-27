# Service scanning

To identify open ports and services within the CybICS testbed you can
use nmap.
Execute the following map command
```sh
nmap -sV -p- $DEVICE_IP
```

The scan will take several minutes.
Results from the scan:
```sh
PORT      STATE SERVICE       VERSION
22/tcp    open  ssh           OpenSSH 9.2p1 Debian 2+deb12u1 (protocol 2.0)
502/tcp   open  modbus        Modbus TCP
1881/tcp  open  http          Node.js Express framework
4840/tcp  open  opcua-tcp?
8080/tcp  open  http-proxy    Werkzeug/2.3.7 Python/3.11.2
20000/tcp open  dnp?
44818/tcp open  EtherNetIP-2?
```

The results show open http ports as well as sever industrial protocols.