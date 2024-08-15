#!/usr/bin/env python3

import logging
import time 
from pymodbus.client import ModbusTcpClient
from nicegui import ui
import threading
import random

# Connect to OpenPLC
client = ModbusTcpClient(host="openplc",port=502)  # Create client object
client.connect() # connect to device, reconnect automatically

def thread_nicegui():
  ui.run(port=8090,reload=False,show=False,dark=True,favicon="favicon.ico",title="CybICS VIRT")

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
    {'variable': 'System', 'value': sysSen},    
  ]
  

  # Build a visual representation of the process
  with ui.row():
    with ui.column():
      variableTable = ui.table(columns=columns, rows=rows, row_key='name')
    with ui.column():
      ui.label('Gas Storage Tank (GST)')
      with ui.card().style(f'background-color: grey; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;') as gstCard:
        gstLabel = ui.label(str(gst)).style('color: black;')
      ui.label('System Valve ')
      with ui.card().style(f'background-color: grey; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;') as systemValveCard:
        systemValveLabel = ui.label(str(systemValve)).style('color: black;')
    with ui.column():
      ui.label('Compressor (C)')
      with ui.card().style(f'background-color: grey; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;') as cCard:
        cLabel = ui.label(str(compressor)).style('color: black;')
      ui.label('System (Sys)')
      with ui.card().style(f'background-color: grey; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;') as sysCard:
        sysLabel = ui.label(str(sysSen)).style('color: black;')
    with ui.column():
      ui.label('High Pressure Tank (HPT)')
      with ui.card().style(f'background-color: grey; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;') as hptCard:
        hptLabel = ui.label(str(hpt)).style('color: black;')
      ui.label('Blow Out (BO)')
      with ui.card().style(f'background-color: grey; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;') as boCard:
        boLabel = ui.label(str(boSen)).style('color: black;')

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
        gst = gst+random.randint(0, 5)
      if compressor > 0:
        gst = gst-2
        hpt = hpt+1
      if systemValve > 0:
        hpt = hpt-random.randint(0, 1)
    delay = delay+1

    # System Valve
    if systemValve > 0:
      systemValveCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      systemValveLabel.set_text("Open: " + str(systemValve))
    else:
      systemValveCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      systemValveLabel.set_text("Closed: " + str(systemValve))

    # System operational if HPT > 50 and HPT < 100 and systemValve true
    if hpt>50 and hpt<100 and systemValve>0:
      sysSen=1
      sysCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      sysLabel.set_text("Operational: " + str(sysSen))
    else:
      sysSen=0
      sysCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      sysLabel.set_text("Non operational: " + str(sysSen))
    

    # Blowout if the HPTpressure if over 220 until HTP pressure < 201
    if hpt>220 or (boSen==1 and hpt>200):
      boSen=1
      boCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      boLabel.set_text("Open: " + str(boSen))
      hpt=hpt-random.randint(0, 5)
    else:
      boSen=0
      boCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      boLabel.set_text("Closed: " + str(boSen))

    if gst>255:
      gst=255
    if hpt>255:
      hpt=255
    if gst<0:
      gst=0
    if hpt<0:
      hpt=0

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



    rows[0]['value'] = gst
    rows[1]['value'] = hpt
    rows[2]['value'] = boSen
    rows[3]['value'] = heartbeat
    rows[4]['value'] = compressor
    rows[5]['value'] = systemValve
    rows[6]['value'] = gstSig
    rows[7]['value'] = sysSen
    variableTable.update()

    
    cLabel.set_text(str(compressor))
    hptLabel.set_text(str(hpt))

    if hpt == 0:
      hptCard.style(f'background-color: blue; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("Empty: " + str(hpt))
    elif hpt < 50:
      hptCard.style(f'background-color: white; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("Low: " + str(hpt))
    elif hpt < 100:
      hptCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("Normal: " + str(hpt))
    elif hpt < 150:
      hptCard.style(f'background-color: orange; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("High: " + str(hpt))
    else:
      hptCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("Critical: " + str(hpt))

    if compressor:
      cCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      cLabel.set_text("ON: " + str(compressor))
    else:
      cCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      cLabel.set_text("OFF: " + str(compressor))

    if gst < 50:
      gstCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      gstLabel.set_text("Low: " + str(gst))
    elif gst < 150:
      gstCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      gstLabel.set_text("Normal: " + str(gst))
    else:
      gstCard.style(f'background-color: blue; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      gstLabel.set_text("Full: " + str(gst))
     
    time.sleep(0.001) # OpenPLC has a Cycle time of 50ms

