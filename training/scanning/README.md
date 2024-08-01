# Service scanning

Network scanning in industrial environments involves systematically probing the network to identify connected devices, open ports, and potential vulnerabilities.
This process is crucial for maintaining the security and integrity of industrial control systems (ICS) and Supervisory Control and Data Acquisition (SCADA) networks.
By performing regular network scans, organizations can detect unauthorized devices, assess the security posture of their systems, and identify weak points that could be exploited by attackers.

Effective network scanning helps ensure that only approved devices are connected and that all systems are up-to-date with the latest security patches.
It also aids in discovering misconfigurations and vulnerabilities that could be exploited in a cyber attack.
To maximize security, network scans should be conducted periodically and after any significant changes to the network infrastructure, and results should be analyzed to inform ongoing security measures and improvements.

### nmap
To identify open ports and services within the CybICS testbed you can use nmap.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">Solution</span></strong></summary>
Execute the following map command

```sh
nmap -sV -p- $DEVICE_IP
```

The nmap -sV -p- command is used with Nmap, a popular network scanning tool, to perform a comprehensive service version detection scan on all ports of a target system. Here’s a breakdown of the command:

nmap: The command-line tool for network discovery and security auditing.
* -sV: This option tells Nmap to perform service version detection. It probes open ports to determine the service running on them and, if possible, the version of the service. This provides detailed information about what software and versions are operating on the target system.
* -p-: This specifies that Nmap should scan all 65,535 TCP ports, from port 1 to port 65535. By default, Nmap scans only the most common 1,000 ports, so using -p- ensures a thorough examination of all ports.

In summary, the nmap -sV -p- command will scan all ports on a target system and provide detailed information about the services and their versions running on each port. This is useful for discovering vulnerabilities and understanding the services that might be exposed to potential attackers.

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

Here’s an interpretation of each result:
* 22/tcp - open ssh (OpenSSH 9.2p1 Debian 2+deb12u1, protocol 2.0):

* Port 22 is open and running an SSH (Secure Shell) service. The service version is OpenSSH 9.2p1 on Debian, which supports protocol version 2.0. SSH is commonly used for secure remote access to systems.
502/tcp - open modbus (Modbus TCP):

* Port 502 is open and running Modbus TCP, a protocol used for communication with industrial devices. This port is typically used for industrial control systems and monitoring.
1881/tcp - open http (Node.js Express framework):

* Port 1881 is open and running an HTTP service based on the Node.js Express framework. This is often used for web applications and APIs.
4840/tcp - open opcua-tcp?:

* Port 4840 is open, and the service is likely OPC UA (Open Platform Communications Unified Architecture) TCP. This port is commonly used for industrial automation and control systems, but the exact version or implementation isn’t identified in this scan.

* 8080/tcp - open http-proxy (Werkzeug/2.3.7 Python/3.11.2): Port 8080 is open and running an HTTP proxy service based on Werkzeug (a Python web server library) version 2.3.7 and Python 3.11.2. Port 8080 is often used as an alternative HTTP port or for web proxies.
20000/tcp - open dnp?:

* Port 20000 is open, and the service appears to be related to DNP3 (Distributed Network Protocol), a protocol used in industrial control systems. However, the exact version or details of the service are not determined.
44818/tcp - open EtherNetIP-2?:

* Port 44818 is open, and the service appears to be related to EtherNet/IP, a protocol used for industrial networking. The exact version or specifics of the service are not clear from the scan.
</details>