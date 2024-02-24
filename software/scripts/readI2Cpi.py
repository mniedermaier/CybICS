#!/usr/bin/env python3

# readI2C.py
#
# This script reads i2c sensor values from the STM32
# and writes these values to the OpenPLC registers.
# Additionally, the IP address of wlan0 will be transferred
# to the STM32, to show it in the display
# 
# The script runs as a systemd service
# /lib/systemd/system/readI2Cpi.service
# with autostart and restart=always

import smbus
import time 
import netifaces as ni
from pymodbus.client import ModbusTcpClient
import subprocess

# I2C channel 1 is connected to the STM32
channel = 1

# The sensor values are stored in address 0x20
address = 0x20


# Initialize the I2C bus of the RPI
bus = smbus.SMBus(channel)

gst = 0 # variable for the gas storage tank (GST)
hpt = 0 # variable for the high pressure tank (HPT)

# Connect to OpenPLC
client = ModbusTcpClient(host="127.0.0.1",port=502)  # Create client object
client.connect() # connect to device, reconnect automatically

# Entering while true loop
nmconfig = False
apmode = '1'
while True:
  # Get IP address of wlan0
  ip = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
  listIp = list(ip)
  print(listIp)

  # Format the IP and send it via i2c to the RPI
  listIp = ['I', 'P',':'] + listIp
  for row in range(len(listIp)):
    listIp[row] = ord(listIp[row])
  print(listIp)
  bus.write_i2c_block_data(address, 0x00, listIp)

  # Read the values for GST and HPT
  data = bus.read_i2c_block_data(address, 0x00, 20)
  print(data)
  for row in range(len(data)):
    data[row] = chr(data[row])
  print(data)

  # Simple check, if correct data was received
  if(str(data[0]) == "G" and str(data[1]) == "S" and str(data[2]) == "T"):
    gst = int(str(data[5] + data[6] + data[7]))
    hpt = int(str(data[14] + data[15] + data[16]))

    print(f"Setting GST to {str(gst)} and HPT to {str(hpt)}")
    
    # write GST and HPT to the OpenPLC
    client.write_registers(1124,gst) #(register, value, unit)
    client.write_registers(1126,hpt) #(register, value, unit)
  
  # Read STM32 ID Code
  data = bus.read_i2c_block_data(address, 0x01, 13)
  print(data)
  for c in range(len(data)):
    data[c] = chr(data[c])
  #id=str(c-"a" for c in id)
  data="".join(data)
  id = data[:12]
  ap = data[12]

  if not nmconfig:
    nmconfig = True
    subprocess.run(["nmcli", "con", "mod", "cybics", "wifi.ssid", f"cybics-{id}"])
  if ap != apmode:
    apmode = ap
    subprocess.run(["nmcli", "con", "up", "cybics" if ap=='1' else "preconfigured"])
  time.sleep(0.02) # OpenPLC has a Cycle time of 50ms

# Should never be reached
client.close()                             # Disconnect device

