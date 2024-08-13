#!/usr/bin/env python3

import logging
import time 
from pymodbus.client import ModbusTcpClient
from nicegui import ui
import threading

# Connect to OpenPLC
client = ModbusTcpClient(host="openplc",port=502)  # Create client object
client.connect() # connect to device, reconnect automatically

def thread_nicegui():
  ui.run(port=8090,reload=False,show=False,dark=True,favicon="🚀",title="CybICS VIRT")
 

if __name__ == "__main__":
  gst=0
  hpt=0
  sysSen=0
  boSen=0
  heartbeat=0
  compressor=0
  systemValve=0
  gstSig=0
  delay=0
  flag = [17273, 25161, 17235, 10349, 12388, 25205, 9257]

  format = "%(asctime)s: %(message)s"
  logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

  

  logging.info("Main    : before creating thread")
  x = threading.Thread(target=thread_nicegui, args=())
  logging.info("Main    : before running thread")
  x.start()

  # NiceGUI setup
  with ui.row():
    ui.spinner('dots', size='lg', color='red')
    ui.image('CybICS_logo.png').classes('w-64')
    ui.spinner('dots', size='lg', color='red')

  columns = [
    {'name': 'variable', 'label': 'Variable', 'field': 'variable', 'required': True, 'align': 'left'},
    {'name': 'value', 'label': 'Value', 'field': 'value', 'sortable': True},
  ]
  rows = [
    {'variable': 'GST', 'value': gst},
    {'variable': 'HPT', 'value': hpt},
    {'variable': 'boSen', 'value': boSen},
    {'variable': 'heartbeat', 'value': heartbeat},
    {'variable': 'compressor', 'value': compressor},
    {'variable': 'systemValve', 'value': systemValve},
    {'variable': 'gstSig', 'value': gstSig},
  ]
  variableTable = ui.table(columns=columns, rows=rows, row_key='name')

  while True:

    # read coils from OpenPLC
    try:
      plcCoils=client.read_coils(0,4)
      heartbeat=plcCoils.bits[0]
      compressor=plcCoils.bits[1]
      systemValve=plcCoils.bits[2]
      gstSig=plcCoils.bits[3]    
    except Exception as e:
      logging.error("Main    : Read from OpenPLC failed - " + str(e))

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

    # Write to OpenPLC
    try:
      # write SystemSensor and BlowOutSensor to the OpenPLC
      client.write_registers(1132,sysSen)
      client.write_registers(1134,boSen)
      # write GST and HPT to the OpenPLC
      client.write_registers(1124,gst)
      client.write_registers(1126,hpt)    
      client.write_registers(1200,flag)
    except Exception as e:
      logging.error("Main    : Write to OpenPLC failed - " + str(e))

    if gst>255:
      gst=255
    if hpt>255:
      hpt=255

    rows[0]['value'] = gst
    rows[1]['value'] = hpt
    rows[2]['value'] = boSen
    rows[3]['value'] = heartbeat
    rows[4]['value'] = compressor
    rows[5]['value'] = systemValve
    rows[6]['value'] = gstSig
    variableTable.update()

    time.sleep(0.001) # OpenPLC has a Cycle time of 50ms

