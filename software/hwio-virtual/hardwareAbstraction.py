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

# Global variables
gst=0
hpt=0
sysSen=0
boSen=0
heartbeat=0
compressor=0
systemValve=0
gstSig=0
delay=0
timer=0

# definiton for button reset
def button_reset():
  # use global variables
  global gst
  global hpt
  global sysSen
  global boSen
  global heartbeat
  global compressor
  global systemValve
  global gstSig
  global delay
  global timer
  logging.info("button_rest: clicked")
  gst=0
  hpt=0
  sysSen=0
  boSen=0
  heartbeat=0
  compressor=0
  systemValve=0
  gstSig=0
  delay=0
  timer=0
  logging.info("button_rest: all reseted")

# thread for nicegui
def thread_nicegui():
  ui.run(port=8090,reload=False,show=False,dark=True,favicon="pics/favicon.ico",title="CybICS VIRT")

# main function
if __name__ == "__main__":
  flag = [17273, 25161, 17235, 10349, 12388, 25205, 9257]

  format = "%(asctime)s: %(message)s"
  logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

  

  logging.info("Main    : before creating thread")
  x = threading.Thread(target=thread_nicegui, args=())
  logging.info("Main    : before running thread")
  x.start()

  # Create container for the content
  with ui.element('div').style('text-align: center; min-width: 1024; width: 1024;'):

    # NiceGUI setup
    with ui.row().style('width: 900px; text-align: center; align-items: center; justify-content: center;'):
      ui.spinner('dots', size='lg', color='red')
      ui.image('pics/CybICS_logo.png').classes('w-64')
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
  
    # add horizontal line
    with ui.element('div').style('display: flex; justify-content: center;'):
        ui.element('div').style(
            'height: 1px; background-color: white; width: 80%; margin: 20px 0;'
        )

    # Add PCB as a PNG image
    with ui.element('div').style('position: relative; display: inline-block;'):
      # Display the PNG image
      ui.image('pics/pcb.png').style('width: 100%; height: auto; display: block; width: 800px; height: 500px; margin: auto;')

      # Reset button
      ui.button('reset', on_click=button_reset).style(
        'position: absolute; top: 240px; left: 0px;'
        'background-color: red; color: white; width: 40px; height: 5px;'
        'display: block;'
      )

      # Overlay Display
      DISPLAYoverlay1 = ui.label('CybICS v1.0.0').style(
        'position: absolute; top: 370px; left: 430px; border-radius: 50%; color=black'
        'background-color: transparent; font-size: 40px;'
        'display: block;'
      )
      DISPLAYoverlay2 = ui.label('0').style(
        'position: absolute; top: 415px; left: 430px; border-radius: 50%; color=black'
        'background-color: transparent; font-size: 40px; width:330px; text-align: right;'
        'display: block;'
      )

      # Overlay GST
      GSToverlayLow=ui.card().style(
        'position: absolute; top: 140px; left: 115px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )
      GSToverlayNormal=ui.card().style(
        'position: absolute; top: 110px; left: 115px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      GSToverlayHigh=ui.card().style(
        'position: absolute; top: 80px; left: 115px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: block;'
      )

      # Overlay Compressor
      CoverlayOn=ui.card().style(
        'position: absolute; top: 95px; left: 355px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      CoverlayOff=ui.card().style(
        'position: absolute; top: 125px; left: 355px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )
            
      # Overlay HPT
      HPToverlayEmpty=ui.card().style(
        'position: absolute; top: 210px; left: 495px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: block;'
      )
      HPToverlayLow=ui.card().style(
        'position: absolute; top: 184px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: block;'
      )
      HPToverlayNormal=ui.card().style(
        'position: absolute; top: 158px; left: 495px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      HPToverlayHigh=ui.card().style(
        'position: absolute; top: 132px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: block;'
      )
      HPToverlayCritical=ui.card().style(
        'position: absolute; top: 106px; left: 495px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )

      # Overlay Blow Out
      BOoverlayOpen=ui.card().style(
        'position: absolute; top: 55px; left: 680px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )
      BOoverlayClosed=ui.card().style(
        'position: absolute; top: 80px; left: 680px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )

      # Overlay System
      SoverlayWorking=ui.card().style(
        'position: absolute; top: 140px; left: 680px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      SoverlayError=ui.card().style(
        'position: absolute; top: 165px; left: 680px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )

      # Overlay System Valve
      SVoverlayOpen=ui.card().style(
        'position: absolute; top: 245px; left: 620px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      SVoverlayClosed=ui.card().style(
        'position: absolute; top: 270px; left: 620px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )

    # add horizontal line
    with ui.element('div').style('display: flex; justify-content: center;'):
        ui.element('div').style(
            'height: 1px; background-color: white; width: 80%; margin: 20px 0;'
        )

    # Build a visual representation of the process
    with ui.row().style('width: 900px; text-align: center; align-items: center; justify-content: center;'):
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
      plcCoils=client.read_coils(0,count=4, slave=1)
      heartbeat=plcCoils.bits[0]
      compressor=plcCoils.bits[1]
      systemValve=plcCoils.bits[2]
      gstSig=plcCoils.bits[3]    
    except Exception as e:
      logging.error("Main    : Read from OpenPLC failed - " + str(e))

    # get roughly one second
    if delay > 50:
      delay = 0
      timer = timer + 1
      DISPLAYoverlay2.set_text(str(timer))
      if gstSig > 0:
        gst = gst+random.randint(0, 5)
      if compressor > 0:
        gst = gst-2
        hpt = hpt+1
      if systemValve > 0:
        hpt = hpt-random.randint(0, 1)
      if boSen > 0:
        hpt=hpt-random.randint(0, 5)
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
      SoverlayWorking.style(
        'position: absolute; top: 140px; left: 680px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      SoverlayError.style(
        'position: absolute; top: 165px; left: 680px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
    else:
      sysSen=0
      sysCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      sysLabel.set_text("Non operational: " + str(sysSen))
      SoverlayWorking.style(
        'position: absolute; top: 140px; left: 680px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      SoverlayError.style(
        'position: absolute; top: 165px; left: 680px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )

    # Control System Valve Overlay
    if systemValve>0:
      SVoverlayOpen.style(
        'position: absolute; top: 245px; left: 620px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      SVoverlayClosed.style(
        'position: absolute; top: 270px; left: 620px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
    else:
      SVoverlayOpen.style(
        'position: absolute; top: 245px; left: 620px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      SVoverlayClosed.style(
        'position: absolute; top: 270px; left: 620px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )
    

    # Blowout if the HPTpressure if over 220 until HTP pressure < 201
    if hpt>220 or (boSen==1 and hpt>200):
      boSen=1
      boCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      boLabel.set_text("Open: " + str(boSen))      
      BOoverlayOpen.style(
        'position: absolute; top: 55px; left: 680px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )
      BOoverlayClosed.style(
        'position: absolute; top: 80px; left: 680px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
    else:
      boSen=0
      boCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      boLabel.set_text("Closed: " + str(boSen))
      BOoverlayOpen.style(
        'position: absolute; top: 55px; left: 680px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
      BOoverlayClosed.style(
        'position: absolute; top: 80px; left: 680px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )

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
      client.write_register(1132,sysSen)
      client.write_register(1134,boSen)
      # write GST and HPT to the OpenPLC
      client.write_register(1124,gst)
      client.write_register(1126,hpt)    
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

    # HPT status
    if hpt == 0:
      hptCard.style(f'background-color: blue; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("Empty: " + str(hpt))
      HPToverlayEmpty.style(
        'position: absolute; top: 210px; left: 495px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: block;'
      )
      HPToverlayLow.style(
        'position: absolute; top: 184px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayNormal.style(
        'position: absolute; top: 158px; left: 495px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayHigh.style(
        'position: absolute; top: 132px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayCritical.style(
        'position: absolute; top: 106px; left: 495px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
    elif hpt < 50:
      hptCard.style(f'background-color: white; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("Low: " + str(hpt))
      HPToverlayEmpty.style(
        'position: absolute; top: 210px; left: 495px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayLow.style(
        'position: absolute; top: 184px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: block;'
      )
      HPToverlayNormal.style(
        'position: absolute; top: 158px; left: 495px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayHigh.style(
        'position: absolute; top: 132px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayCritical.style(
        'position: absolute; top: 106px; left: 495px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
    elif hpt < 100:
      hptCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("Normal: " + str(hpt))
      HPToverlayEmpty.style(
        'position: absolute; top: 210px; left: 495px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayLow.style(
        'position: absolute; top: 184px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayNormal.style(
        'position: absolute; top: 158px; left: 495px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      HPToverlayHigh.style(
        'position: absolute; top: 132px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayCritical.style(
        'position: absolute; top: 106px; left: 495px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
    elif hpt < 150:
      hptCard.style(f'background-color: orange; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("High: " + str(hpt))
      HPToverlayEmpty.style(
        'position: absolute; top: 210px; left: 495px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayLow.style(
        'position: absolute; top: 184px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayNormal.style(
        'position: absolute; top: 158px; left: 495px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayHigh.style(
        'position: absolute; top: 132px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: block;'
      )
      HPToverlayCritical.style(
        'position: absolute; top: 106px; left: 495px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
    else:
      hptCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      hptLabel.set_text("Critical: " + str(hpt))
      HPToverlayEmpty.style(
        'position: absolute; top: 210px; left: 495px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayLow.style(
        'position: absolute; top: 184px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayNormal.style(
        'position: absolute; top: 158px; left: 495px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayHigh.style(
        'position: absolute; top: 132px; left: 495px; border-radius: 50%;'
        'background-color: white; width: 5px; height: 5px;'
        'display: none;'
      )
      HPToverlayCritical.style(
        'position: absolute; top: 106px; left: 495px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )

    # Display for compressor
    if compressor:
      cCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      cLabel.set_text("ON: " + str(compressor))
      CoverlayOn.style(
        'position: absolute; top: 95px; left: 355px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      CoverlayOff.style(
        'position: absolute; top: 125px; left: 355px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
    else:
      cCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      cLabel.set_text("OFF: " + str(compressor))
      CoverlayOn.style(
        'position: absolute; top: 95px; left: 355px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      CoverlayOff.style(
        'position: absolute; top: 125px; left: 355px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )

    # Display style for GST
    if gst < 50:
      gstCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      gstLabel.set_text("Low: " + str(gst))
      GSToverlayLow.style(
        'position: absolute; top: 140px; left: 115px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: block;'
      )
      GSToverlayNormal.style(
        'position: absolute; top: 110px; left: 115px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      GSToverlayHigh.style(
        'position: absolute; top: 80px; left: 115px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: none;'
      )
    elif gst < 150:
      gstCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      gstLabel.set_text("Normal: " + str(gst))
      GSToverlayLow.style(
        'position: absolute; top: 140px; left: 115px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
      GSToverlayNormal.style(
        'position: absolute; top: 110px; left: 115px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: block;'
      )
      GSToverlayHigh.style(
        'position: absolute; top: 80px; left: 115px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: none;'
      )
    else:
      gstCard.style(f'background-color: blue; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      gstLabel.set_text("Full: " + str(gst))
      GSToverlayLow.style(
        'position: absolute; top: 140px; left: 115px; border-radius: 50%;'
        'background-color: red; width: 5px; height: 5px;'
        'display: none;'
      )
      GSToverlayNormal.style(
        'position: absolute; top: 110px; left: 115px; border-radius: 50%;'
        'background-color: green; width: 5px; height: 5px;'
        'display: none;'
      )
      GSToverlayHigh.style(
        'position: absolute; top: 80px; left: 115px; border-radius: 50%;'
        'background-color: blue; width: 5px; height: 5px;'
        'display: block;'
      )
     
    time.sleep(0.02) # OpenPLC has a Cycle time of 50ms

