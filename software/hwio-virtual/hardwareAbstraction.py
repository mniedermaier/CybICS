#!/usr/bin/env python3

import logging
import time
import sys
import os

# Configure logging FIRST before importing pymodbus
# Use the same format as the landing page
log_format = '%(asctime)s - HWIO - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Create a handler that forces output to stdout with immediate flush
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
handler.setLevel(logging.INFO)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Clear any existing handlers to avoid duplicates
if root_logger.handlers:
    root_logger.handlers.clear()
root_logger.addHandler(handler)

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Suppress ALL verbose third-party logging
logging.getLogger('pymodbus').setLevel(logging.CRITICAL)
logging.getLogger('pymodbus.client').setLevel(logging.CRITICAL)
logging.getLogger('pymodbus.client.base').setLevel(logging.CRITICAL)
logging.getLogger('pymodbus.logging').setLevel(logging.CRITICAL)
logging.getLogger('nicegui').setLevel(logging.WARNING)

# Test that logging works
logging.info("HWIO logging initialized")

# Redirect stderr to suppress any print statements from pymodbus
class SuppressedStderr:
    """Context manager to suppress stderr output from pymodbus"""
    def __init__(self):
        self.null = open(os.devnull, 'w')
        self.original_stderr = sys.stderr

    def __enter__(self):
        sys.stderr = self.null
        return self

    def __exit__(self, *args):
        sys.stderr = self.original_stderr
        self.null.close()

from pymodbus.client import ModbusTcpClient
from nicegui import ui
import threading
import random

# Connect to OpenPLC
client = ModbusTcpClient(host="openplc",port=502)  # Create client object
# Don't connect yet - will connect in background thread to avoid blocking

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

# Initialize failure counter for Modbus TCP connection
consecutive_failures = 0
MAX_FAILURES = 10

# Background process simulation thread
def physical_process_thread():
  """Runs the physical process simulation independently of UI"""
  global gst, hpt, sysSen, boSen, heartbeat, compressor, systemValve, gstSig, delay, timer, consecutive_failures

  logging.info("Physical process thread started")

  # Initial connection to OpenPLC
  connection_attempts = 0
  while not client.connected:
    try:
      with SuppressedStderr():
        client.connect()
      if client.connected:
        logging.info("Physical process: Successfully connected to OpenPLC")
        break
    except Exception as e:
      connection_attempts += 1
      if connection_attempts == 1:
        logging.warning("Physical process: Waiting for OpenPLC to start...")
      elif connection_attempts % 30 == 0:
        logging.warning(f"Physical process: Still waiting for OpenPLC (attempt {connection_attempts})...")
      time.sleep(1)

  while True:
    # Ensure connection to OpenPLC
    if not client.connected:
      try:
        with SuppressedStderr():
          client.connect()
        if client.connected:
          logging.info("Physical process: Reconnected to OpenPLC")
          consecutive_failures = 0
      except Exception as e:
        consecutive_failures += 1
        if consecutive_failures % 50 == 0:
          logging.warning(f"Physical process: Cannot connect to OpenPLC - {str(e)} (Attempt {consecutive_failures})")
        time.sleep(0.1)
        continue

    # read coils from OpenPLC
    try:
      plcCoils=client.read_coils(0,count=4, device_id=1)
      heartbeat=plcCoils.bits[0]
      compressor=plcCoils.bits[1]
      systemValve=plcCoils.bits[2]
      gstSig=plcCoils.bits[3]
      consecutive_failures = 0
    except Exception as e:
      consecutive_failures += 1
      # Only log every 50th failure to reduce log spam
      if consecutive_failures == 1 or consecutive_failures % 50 == 0:
        logging.error(f"Physical process: Read from OpenPLC failed - {str(e)} (Failure {consecutive_failures}/{MAX_FAILURES})")

      if consecutive_failures >= MAX_FAILURES:
        if consecutive_failures == MAX_FAILURES:
          logging.warning("Physical process: Maximum consecutive failures reached. Attempting to reconnect...")
        try:
          with SuppressedStderr():
            client.close()
            client.connect()
          consecutive_failures = 0
          logging.info("Physical process: Successfully reconnected to OpenPLC")
        except Exception as reconnect_error:
          # Only log reconnection failures every 100 attempts
          if consecutive_failures % 100 == 0:
            logging.error(f"Physical process: Failed to reconnect - {str(reconnect_error)}")

    # Physical simulation logic
    if delay > 50:
      delay = 0
      timer = timer + 1
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

    # System operational if HPT > 50 and HPT < 100 and systemValve true
    if hpt>50 and hpt<100 and systemValve>0:
      sysSen=1
    else:
      sysSen=0

    # Blowout if the HPT pressure if over 220 until HTP pressure < 201
    if hpt>220 or (boSen==1 and hpt>200):
      boSen=1
    else:
      boSen=0

    # Limit values
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
      client.write_register(1132,sysSen)
      client.write_register(1134,boSen)
      client.write_register(1124,gst)
      client.write_register(1126,hpt)
      client.write_registers(1200,[17273, 25161, 17235, 10349, 12388, 25205, 9257])
    except Exception as e:
      # Only log write errors occasionally to reduce log spam
      if consecutive_failures == 1 or consecutive_failures % 50 == 0:
        logging.error("Physical process: Write to OpenPLC failed - " + str(e))

    time.sleep(0.02)  # 50Hz to match OpenPLC cycle time

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

# API endpoint for 3D visualization data
@ui.page('/api/state')
def api_state():
  global gst, hpt, sysSen, boSen, heartbeat, compressor, systemValve, gstSig
  from starlette.responses import JSONResponse

  return JSONResponse({
    'gst': gst,
    'hpt': hpt,
    'sysSen': sysSen,
    'boSen': boSen,
    'heartbeat': heartbeat,
    'compressor': compressor,
    'systemValve': systemValve,
    'gstSig': gstSig
  })

# Create the main UI page
@ui.page('/')
def index_page():
  global gst, hpt, sysSen, boSen, heartbeat, compressor, systemValve, gstSig, delay, timer, consecutive_failures

  # Create container for the content
  with ui.element('div').style('text-align: center; min-width: 1024px; width: 1200px; margin: 0 auto;'):

    # NiceGUI setup - Header
    with ui.row().style('width: 100%; text-align: center; align-items: center; justify-content: center;'):
      ui.spinner('dots', size='lg', color='red')
      ui.image('pics/CybICS_logo.png').classes('w-64')
      ui.spinner('dots', size='lg', color='red')

    # Create tabs for Classic and 3D views
    with ui.tabs().classes('w-full').style('background-color: #1a1a2e; margin-bottom: 20px;') as tabs:
      classic_tab = ui.tab('Classic View', icon='dashboard').style('color: white; font-size: 16px;')
      viz_3d_tab = ui.tab('3D Visualization', icon='view_in_ar').style('color: white; font-size: 16px;')

    # Tab panels
    with ui.tab_panels(tabs, value=classic_tab).classes('w-full').props('keep-alive'):
      # Classic View Tab Panel
      with ui.tab_panel(classic_tab):
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
          DISPLAYoverlay1 = ui.label('CybICS v1.1.2').style(
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

      # 3D Visualization Tab Panel
      with ui.tab_panel(viz_3d_tab):
        # Create 3D container
        container_3d = ui.element('div').props('id=container3d').style('width: 100%; height: 800px; position: relative; background-color: #0a0a0f;')

  # Three.js 3D Visualization - Clean implementation
  ui.add_body_html('''
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script>
          window.CYBICS_3D_VERSION = "7.0.0-CLEAN";
          document.title = "CybICS 3D Visualization";

          function init3DScene() {
            const container = document.getElementById('container3d');
            if (!container) {
              setTimeout(init3DScene, 100);
              return;
            }

            if (typeof THREE === 'undefined') {
              setTimeout(init3DScene, 100);
              return;
            }

            // Clear container
            container.innerHTML = '';

            // Create scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a1a2e);

            // Create camera
            const camera = new THREE.PerspectiveCamera(
              60,
              container.clientWidth / container.clientHeight,
              0.1,
              1000
            );
            camera.position.set(0, 10, 25);
            camera.lookAt(0, 0, 0);

            // Create renderer
            const canvas = document.createElement('canvas');
            const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(canvas);

            // Add lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);

            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 20, 10);
            scene.add(directionalLight);

            // Ground
            const groundGeometry = new THREE.PlaneGeometry(60, 60);
            const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x2a2a3e });
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            scene.add(ground);

            // Grid
            const gridHelper = new THREE.GridHelper(60, 30, 0x444466, 0x333344);
            gridHelper.position.y = 0.01;
            scene.add(gridHelper);

            // Helper function to create text sprite
            function createTextSprite(text, color = '#000000', backgroundColor = '#ffff00') {
              const canvas = document.createElement('canvas');
              const context = canvas.getContext('2d');
              canvas.width = 512;
              canvas.height = 128;

              // Background
              context.fillStyle = backgroundColor;
              context.fillRect(0, 0, canvas.width, canvas.height);

              // Text
              context.font = 'bold 80px Arial';
              context.fillStyle = color;
              context.textAlign = 'center';
              context.textBaseline = 'middle';
              context.fillText(text, canvas.width / 2, canvas.height / 2);

              const texture = new THREE.CanvasTexture(canvas);
              const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
              const sprite = new THREE.Sprite(spriteMaterial);
              sprite.scale.set(4, 1, 1);
              return sprite;
            }

            // GST Tank (left)
            const gstGroup = new THREE.Group();
            gstGroup.position.set(-7, 0, 0);

            const gstBody = new THREE.Mesh(
              new THREE.CylinderGeometry(2, 2, 8, 32),
              new THREE.MeshStandardMaterial({ color: 0x4a90e2, metalness: 0.7, roughness: 0.3 })
            );
            gstBody.position.y = 4;
            gstGroup.add(gstBody);

            // GST fill level (animated based on pressure)
            const gstFill = new THREE.Mesh(
              new THREE.CylinderGeometry(1.95, 1.95, 8, 32),
              new THREE.MeshStandardMaterial({
                color: 0x2196f3,
                transparent: true,
                opacity: 0.6,
                emissive: 0x1976d2,
                emissiveIntensity: 0.3
              })
            );
            gstFill.position.y = 0;
            gstGroup.add(gstFill);

            // GST Label with text
            const gstLabel = createTextSprite('GST');
            gstLabel.position.set(0, 9, 0);
            gstGroup.add(gstLabel);

            scene.add(gstGroup);

            // HPT Tank (right)
            const hptGroup = new THREE.Group();
            hptGroup.position.set(7, 0, 0);

            const hptBody = new THREE.Mesh(
              new THREE.CylinderGeometry(2, 2, 8, 32),
              new THREE.MeshStandardMaterial({ color: 0xe24a4a, metalness: 0.7, roughness: 0.3 })
            );
            hptBody.position.y = 4;
            hptGroup.add(hptBody);

            // HPT fill level (animated based on pressure)
            const hptFill = new THREE.Mesh(
              new THREE.CylinderGeometry(1.95, 1.95, 8, 32),
              new THREE.MeshStandardMaterial({
                color: 0xf44336,
                transparent: true,
                opacity: 0.6,
                emissive: 0xd32f2f,
                emissiveIntensity: 0.3
              })
            );
            hptFill.position.y = 0;
            hptGroup.add(hptFill);

            // HPT Label with text
            const hptLabel = createTextSprite('HPT');
            hptLabel.position.set(0, 9, 0);
            hptGroup.add(hptLabel);

            scene.add(hptGroup);

            // Compressor (center front) with rotating fan
            const compressorGroup = new THREE.Group();
            compressorGroup.position.set(0, 0, 8);

            const compressorBody = new THREE.Mesh(
              new THREE.BoxGeometry(3, 2, 2),
              new THREE.MeshStandardMaterial({ color: 0x666666, metalness: 0.8 })
            );
            compressorBody.position.y = 1;
            compressorGroup.add(compressorBody);

            // Rotating fan
            const fanGroup = new THREE.Group();
            fanGroup.position.set(0, 1, 1.2);

            for(let i = 0; i < 4; i++) {
              const blade = new THREE.Mesh(
                new THREE.BoxGeometry(0.1, 0.8, 0.05),
                new THREE.MeshStandardMaterial({ color: 0x333333 })
              );
              blade.rotation.z = (Math.PI / 2) * i;
              fanGroup.add(blade);
            }

            compressorGroup.add(fanGroup);
            scene.add(compressorGroup);

            // Chimney (beside HPT)
            const chimneyGroup = new THREE.Group();
            chimneyGroup.position.set(11, 0, 0);

            const chimneyStack = new THREE.Mesh(
              new THREE.CylinderGeometry(0.6, 0.8, 10, 12),
              new THREE.MeshStandardMaterial({ color: 0xff6600 })
            );
            chimneyStack.position.y = 5;
            chimneyGroup.add(chimneyStack);

            scene.add(chimneyGroup);

            // System Cabinet (right of HPT)
            const cabinetGroup = new THREE.Group();
            cabinetGroup.position.set(13, 0, -3);

            const cabinetBody = new THREE.Mesh(
              new THREE.BoxGeometry(2, 4, 1.5),
              new THREE.MeshStandardMaterial({ color: 0x555555, metalness: 0.6 })
            );
            cabinetBody.position.y = 2;
            cabinetGroup.add(cabinetBody);

            scene.add(cabinetGroup);

            // LED Panel
            const ledPanel = new THREE.Group();
            ledPanel.position.set(-12, 3, 0);

            const ledBoard = new THREE.Mesh(
              new THREE.BoxGeometry(2, 3, 0.2),
              new THREE.MeshStandardMaterial({ color: 0x222222 })
            );
            ledPanel.add(ledBoard);

            const leds = [];
            const ledPositions = [
              [-0.7, 1.2], [-0.35, 1.2], [0, 1.2], [0.35, 1.2], [0.7, 1.2],
              [-0.7, 0.6], [-0.35, 0.6], [0, 0.6], [0.35, 0.6], [0.7, 0.6],
              [-0.7, 0], [-0.35, 0], [0, 0], [0.35, 0], [0.7, 0],
              [-0.35, -0.6]
            ];

            ledPositions.forEach((pos, i) => {
              const led = new THREE.Mesh(
                new THREE.CircleGeometry(0.1, 16),
                new THREE.MeshStandardMaterial({
                  color: 0x330000,
                  emissive: 0x330000,
                  emissiveIntensity: 0.1
                })
              );
              led.position.set(pos[0], pos[1], 0.11);
              ledPanel.add(led);
              leds.push(led);
            });

            scene.add(ledPanel);

            // Particle system for gas flow (from compressor to tanks)
            const particleCount = 100;
            const particles = new Float32Array(particleCount * 3);
            const particleVelocities = [];

            for(let i = 0; i < particleCount; i++) {
              particles[i * 3] = (Math.random() - 0.5) * 8 - 3;
              particles[i * 3 + 1] = 1;
              particles[i * 3 + 2] = (Math.random() - 0.5) * 2;
              particleVelocities.push({
                x: (Math.random() - 0.5) * 0.02,
                y: 0.05 + Math.random() * 0.05,
                z: (Math.random() - 0.5) * 0.02
              });
            }

            const particleGeometry = new THREE.BufferGeometry();
            particleGeometry.setAttribute('position', new THREE.BufferAttribute(particles, 3));

            const particleMaterial = new THREE.PointsMaterial({
              color: 0x00ff88,
              size: 0.15,
              transparent: true,
              opacity: 0.6
            });

            const particleSystem = new THREE.Points(particleGeometry, particleMaterial);
            particleSystem.visible = false;
            scene.add(particleSystem);

            // Flame particle system (from chimney)
            const flameCount = 150;
            const flameParticles = new Float32Array(flameCount * 3);
            const flameColors = new Float32Array(flameCount * 3);
            const flameVelocities = [];

            for(let i = 0; i < flameCount; i++) {
              flameParticles[i * 3] = 11 + (Math.random() - 0.5) * 0.4;
              flameParticles[i * 3 + 1] = 10 + Math.random() * 0.5;
              flameParticles[i * 3 + 2] = (Math.random() - 0.5) * 0.4;

              flameVelocities.push({
                x: (Math.random() - 0.5) * 0.04,
                y: 0.1 + Math.random() * 0.1,
                z: (Math.random() - 0.5) * 0.04,
                life: 1.0
              });

              const colorChoice = Math.random();
              if(colorChoice < 0.5) {
                flameColors[i * 3] = 1.0;
                flameColors[i * 3 + 1] = 0.6 + Math.random() * 0.4;
                flameColors[i * 3 + 2] = 0.0;
              } else {
                flameColors[i * 3] = 1.0;
                flameColors[i * 3 + 1] = 0.2 + Math.random() * 0.3;
                flameColors[i * 3 + 2] = 0.0;
              }
            }

            const flameGeometry = new THREE.BufferGeometry();
            flameGeometry.setAttribute('position', new THREE.BufferAttribute(flameParticles, 3));
            flameGeometry.setAttribute('color', new THREE.BufferAttribute(flameColors, 3));

            const flameMaterial = new THREE.PointsMaterial({
              size: 0.3,
              vertexColors: true,
              transparent: true,
              opacity: 0.8,
              blending: THREE.AdditiveBlending
            });

            const flameSystem = new THREE.Points(flameGeometry, flameMaterial);
            flameSystem.visible = false;
            scene.add(flameSystem);

            // Flame light
            const flameLight = new THREE.PointLight(0xff6600, 0, 10);
            flameLight.position.set(11, 10, 0);
            scene.add(flameLight);

            // Status overlay
            const statusOverlay = document.createElement('div');
            statusOverlay.style.cssText = 'position: absolute; bottom: 20px; left: 20px; background: rgba(0,0,0,0.8); padding: 15px; border-radius: 10px; color: white; font-family: monospace; z-index: 10;';
            statusOverlay.innerHTML = '<h3 style="margin: 0 0 10px 0; color: #ff8c42;">System Status</h3><div>GST: <span id="gst-value">0</span></div><div>HPT: <span id="hpt-value">0</span></div>';
            container.appendChild(statusOverlay);

            // Variables for smooth animations
            let fanRotationSpeed = 0;
            let targetFanSpeed = 0;

            // Fetch live data from server
            async function fetchData() {
              try {
                const response = await fetch('/api/state');
                const data = await response.json();

                // Update tank fill levels
                const gstPercent = data.gst / 100;
                const hptPercent = data.hpt / 100;

                gstFill.scale.y = Math.max(0.1, gstPercent);
                gstFill.position.y = 4 - 4 * (1 - gstPercent);

                hptFill.scale.y = Math.max(0.1, hptPercent);
                hptFill.position.y = 4 - 4 * (1 - hptPercent);

                // Update compressor fan speed
                targetFanSpeed = data.compressor ? 0.15 : 0;

                // Update particle visibility
                particleSystem.visible = data.compressor > 0;

                // Update flame system
                flameSystem.visible = data.boSen > 0;
                flameLight.intensity = data.boSen > 0 ? 6 : 0;

                // Update LED indicators
                leds.forEach((led, idx) => {
                  let intensity = 0;
                  let color = 0x330000;

                  switch(idx) {
                    case 0: case 1: case 2: // GST row
                      intensity = data.gstSig ? 1.0 : 0.1;
                      color = data.gstSig ? 0x00ff00 : 0x003300;
                      break;
                    case 5: case 6: case 7: // Compressor row
                      intensity = data.compressor ? 1.0 : 0.1;
                      color = data.compressor ? 0x00ff00 : 0x003300;
                      break;
                    case 10: case 11: case 12: // System row
                      intensity = data.sysSen ? 1.0 : 0.1;
                      color = data.sysSen ? 0x00ff00 : 0xff0000;
                      break;
                    case 15: // Blow-out LED
                      intensity = data.boSen > 0 ? 1.0 : 0.1;
                      color = data.boSen > 0 ? 0xff0000 : 0x330000;
                      break;
                  }

                  led.material.color.setHex(color);
                  led.material.emissive.setHex(color);
                  led.material.emissiveIntensity = intensity;
                });

                // Update status overlay
                document.getElementById('gst-value').textContent = data.gst;
                document.getElementById('hpt-value').textContent = data.hpt;
              } catch (e) {
                // Silent fail - will retry on next frame
              }
            }

            // Animation loop
            function animate() {
              requestAnimationFrame(animate);

              // Smooth fan rotation
              fanRotationSpeed += (targetFanSpeed - fanRotationSpeed) * 0.1;
              fanGroup.rotation.z += fanRotationSpeed;

              // Animate gas particles
              if(particleSystem.visible) {
                const positions = particleGeometry.attributes.position.array;
                for(let i = 0; i < particleCount; i++) {
                  positions[i * 3] += particleVelocities[i].x;
                  positions[i * 3 + 1] += particleVelocities[i].y;
                  positions[i * 3 + 2] += particleVelocities[i].z;

                  if(positions[i * 3 + 1] > 10) {
                    positions[i * 3] = (Math.random() - 0.5) * 8 - 3;
                    positions[i * 3 + 1] = 1;
                    positions[i * 3 + 2] = (Math.random() - 0.5) * 2;
                  }
                }
                particleGeometry.attributes.position.needsUpdate = true;
              }

              // Animate flames
              if(flameSystem.visible) {
                const flamePos = flameGeometry.attributes.position.array;
                const flameCol = flameGeometry.attributes.color.array;

                for(let i = 0; i < flameCount; i++) {
                  flamePos[i * 3] += flameVelocities[i].x;
                  flamePos[i * 3 + 1] += flameVelocities[i].y;
                  flamePos[i * 3 + 2] += flameVelocities[i].z;

                  flameVelocities[i].life -= 0.015;

                  if(flameVelocities[i].life <= 0 || flamePos[i * 3 + 1] > 13) {
                    flamePos[i * 3] = 11 + (Math.random() - 0.5) * 0.4;
                    flamePos[i * 3 + 1] = 10 + Math.random() * 0.5;
                    flamePos[i * 3 + 2] = (Math.random() - 0.5) * 0.4;

                    flameVelocities[i].x = (Math.random() - 0.5) * 0.04;
                    flameVelocities[i].y = 0.1 + Math.random() * 0.1;
                    flameVelocities[i].z = (Math.random() - 0.5) * 0.04;
                    flameVelocities[i].life = 1.0;

                    const colorChoice = Math.random();
                    if(colorChoice < 0.5) {
                      flameCol[i * 3] = 1.0;
                      flameCol[i * 3 + 1] = 0.6 + Math.random() * 0.4;
                      flameCol[i * 3 + 2] = 0.0;
                    } else {
                      flameCol[i * 3] = 1.0;
                      flameCol[i * 3 + 1] = 0.2 + Math.random() * 0.3;
                      flameCol[i * 3 + 2] = 0.0;
                    }
                  } else {
                    const life = flameVelocities[i].life;
                    flameCol[i * 3] = 1.0 * life;
                    flameCol[i * 3 + 1] *= life * 0.8;
                  }
                }

                flameGeometry.attributes.position.needsUpdate = true;
                flameGeometry.attributes.color.needsUpdate = true;

                flameLight.intensity = 5 + Math.sin(Date.now() * 0.01) * 2 + Math.random();
              }

              renderer.render(scene, camera);
            }

            // Fetch data every 500ms
            setInterval(fetchData, 500);
            fetchData();

            // Handle resize
            window.addEventListener('resize', function() {
              camera.aspect = container.clientWidth / container.clientHeight;
              camera.updateProjectionMatrix();
              renderer.setSize(container.clientWidth, container.clientHeight);
            });

            // Start animation
            animate();
          }

          // Initialize when ready
          if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
              setTimeout(init3DScene, 500);
            });
          } else {
            setTimeout(init3DScene, 500);
          }
        </script>
        ''')

  # Update function called periodically (UI updates only)
  async def update():
    global gst, hpt, sysSen, boSen, heartbeat, compressor, systemValve, gstSig, delay, timer, consecutive_failures

    # Update display timer
    DISPLAYoverlay2.set_text(str(timer))

    # System Valve
    if systemValve > 0:
      systemValveCard.style(f'background-color: green; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      systemValveLabel.set_text("Open: " + str(systemValve))
    else:
      systemValveCard.style(f'background-color: red; width: 200px; height: 100px; display: flex; justify-content: center; align-items: center;')
      systemValveLabel.set_text("Closed: " + str(systemValve))

    # System operational display (sysSen computed in background thread)
    if sysSen > 0:
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


    # Blowout display (boSen computed in background thread)
    if boSen > 0:
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



    # Update table rows
    variableTable.rows[0]['value'] = gst
    variableTable.rows[1]['value'] = hpt
    variableTable.rows[2]['value'] = boSen
    variableTable.rows[3]['value'] = heartbeat
    variableTable.rows[4]['value'] = compressor
    variableTable.rows[5]['value'] = systemValve
    variableTable.rows[6]['value'] = gstSig
    variableTable.rows[7]['value'] = sysSen
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

    # Update 3D visualization
    try:
      ui.run_javascript(f'''
        if(typeof window.updateHWIOData === 'function') {{
          window.updateHWIOData({{
            gst: {gst},
            hpt: {hpt},
            compressor: {compressor},
            systemValve: {systemValve},
            sysSen: {sysSen},
            boSen: {boSen}
          }});
        }}
      ''')
    except:
      pass  # 3D visualization tab not loaded yet

  # Create a timer to update every 20ms (50Hz to match OpenPLC cycle time)
  ui.timer(0.02, update)

# main function
if __name__ == "__main__":
  # Logging already configured at module level

  # Start physical process in background thread
  process_thread = threading.Thread(target=physical_process_thread, daemon=True)
  process_thread.start()
  logging.info("Main    : Physical process thread started")

  logging.info("Main    : starting NiceGUI")
  ui.run(port=8090,reload=False,show=False,dark=True,favicon="pics/favicon.ico",title="CybICS VIRT")
