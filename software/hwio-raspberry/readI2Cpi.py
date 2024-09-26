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
from pymodbus.client import ModbusTcpClient
import nmcli
import RPi.GPIO as GPIO
import logging

GPIO.setmode(GPIO.BCM)
GPIO.setup(8, GPIO.OUT) # compressor
GPIO.setup(4, GPIO.OUT) # heartbeat
GPIO.setup(7, GPIO.OUT) # systemValve
GPIO.setup(20, GPIO.OUT) # gstSig
GPIO.setup(1, GPIO.IN) # System sensor
GPIO.setup(12, GPIO.IN) # BO sensor

# I2C channel 1 is connected to the STM32
channel = 1

# The sensor values are stored in address 0x20
address = 0x20


# Initialize the I2C bus of the RPI
bus = smbus.SMBus(channel)

gst = 0 # variable for the gas storage tank (GST)
hpt = 0 # variable for the high pressure tank (HPT)
countCheckIP = 0 # Variable to check IP every 100 runs
# Connect to OpenPLC
client = ModbusTcpClient(host="openplc",port=502)  # Create client object

attempts = 0

# Try "10" times to connect to the OpenPLC
logging.info("Trying to connect to OpenPLC")
while attempts < 10:
  try:
    client.connect() # connect to device, reconnect automatically
    logging.info("Connected to OpenPLC within " + str(attempts) + " attempts")
    break
  except:
    attempts += 1
    time.sleep(10)
    logging.error("Connection to OpenPLC failed retrying... " + str(attempts) + "/" + "10")


current_connection = ""
nmcli.disable_use_sudo()
for conn in nmcli.connection():
  if conn.device == 'wlan0':
    current_connection = conn.name
    break

current_ssid = nmcli.connection.show('cybics')["802-11-wireless.ssid"]
logging.info(f"Current connection: {current_connection}, ap ssid: {current_ssid}")

# Entering while true loop
while True:
  if countCheckIP == 0:
    # Get IP address of wlan0
    ip = nmcli.device.show('wlan0').get('IP4.ADDRESS[1]', "unknown")
    ip = ip.split('/')[0] # remove the network CIDR suffix
    listIp = list(ip)
    # print(listIp)

    # Format the IP and send it via i2c to the RPI
    listIp = ['I', 'P',':'] + listIp
    for row in range(len(listIp)):
      listIp[row] = ord(listIp[row])
    # print(listIp)
    bus.write_i2c_block_data(address, 0x00, listIp)
  elif countCheckIP > 100:
    countCheckIP=0

  countCheckIP = countCheckIP + 1

  # Read the values for GST and HPT
  data = bus.read_i2c_block_data(address, 0x00, 20)
  # print(data)
  for row in range(len(data)):
    data[row] = chr(data[row])
  # print(data)

  # Simple check, if correct data was received
  if(str(data[0]) == "G" and str(data[1]) == "S" and str(data[2]) == "T"):
    gst = int(str(data[5] + data[6] + data[7]))
    hpt = int(str(data[14] + data[15] + data[16]))

    # print(f"Setting GST to {str(gst)} and HPT to {str(hpt)}")
    
    # write GST and HPT to the OpenPLC
    client.write_registers(1124,gst) #
    client.write_registers(1126,hpt) #
    flag = [17273, 25161, 17235, 10349, 12388, 25205, 9257]
    client.write_registers(1200,flag) #
  
  # read coils from OpenPLC
  try:
    plcCoils=client.read_coils(0,4)
    GPIO.output(4, plcCoils.bits[0])   # heartbeat
    GPIO.output(8, plcCoils.bits[1])   # compressor
    GPIO.output(7, plcCoils.bits[2])   # systemValve
    GPIO.output(20, plcCoils.bits[3])  # gstSig
  except Exception as e:
    logging.error("Read from OpenPLC failed - " + str(e))

  # write input register to OpenPLC
  try:
    client.write_registers(1132,GPIO.input(1))  # System sensor
    client.write_registers(1134,GPIO.input(12)) # BO sensor
  except Exception as e:
    logging.error("Write to OpenPLC failed - " + str(e))

  # Read STM32 ID Code
  data = bus.read_i2c_block_data(address, 0x01, 13)
  for c in range(len(data)):
    data[c] = chr(data[c])
  #id=str(c-"a" for c in id)
  data="".join(data)
  id = data[:12]
  
  # Simple check, if correct data was received
  if data[12] in ['0', '1']:
    ssid = f"cybics-{id}"
    if current_ssid != ssid:
      logging.info(f"Configure ssid {ssid}")
      nmcli.connection.modify('cybics', {'wifi.ssid': ssid})
      current_ssid = ssid

    connection = 'cybics' if data[12] == '1' else 'preconfigured'
    if current_connection != connection:
      logging.info(f"Enable connection {connection}")
      nmcli.connection.up(connection)
      current_connection = connection

  time.sleep(0.02) # OpenPLC has a Cycle time of 50ms

# Should never be reached
client.close()                             # Disconnect device

