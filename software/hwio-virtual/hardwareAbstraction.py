#!/usr/bin/env python3

import time 
from pymodbus.client import ModbusTcpClient

# Connect to OpenPLC
client = ModbusTcpClient(host="openplc",port=502)  # Create client object
client.connect() # connect to device, reconnect automatically

gst=0
hpt=0
sysSen=1
boSen=1

delay=0

# Entering while true loop
while True:  
  plcCoils=client.read_coils(0,4)
  heartbeat=plcCoils.bits[0]
  compressor=plcCoils.bits[1]
  systemValve=plcCoils.bits[2]
  gstSig=plcCoils.bits[3]

  

  # write GST and HPT to the OpenPLC
  client.write_registers(1124,gst)
  client.write_registers(1126,hpt)
  flag = [17273, 25161, 17235, 10349, 12388, 25205, 9257]
  client.write_registers(1200,flag)

  print(heartbeat)

  # get roughly one second
  if delay > 1000:
    delay = 0
    if gstSig > 0:
      gst = gst+3
    if compressor > 0:
      gst = gst-1
      hpt = hpt+2
    if systemValve > 0:
      hpt = hpt-1
  delay = delay+1

  # System operational if HPT > 50 and HPT < 100 and systemValve true
  if hpt>50 and hpt<100 and systemValve>0:
    sysSen=1
  else:
    sysSen=0

  # Blowout if the HPTpressure if over 220 until HTP pressure < 201
  if hpt>220 or (boSen==1 and hpt>200):
    boSen=1
  else:
    boSen=0

  # write SystemSensor and BlowOutSensor to the OpenPLC
  client.write_registers(1132,sysSen)
  client.write_registers(1134,boSen)

  if gst>255:
    gst=255
  if hpt>255:
    hpt=255

  time.sleep(0.001) # OpenPLC has a Cycle time of 50ms

# Should never be reached
client.close()                             # Disconnect device

