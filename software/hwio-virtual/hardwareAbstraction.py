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
          DISPLAYoverlay1 = ui.label('CybICS v1.2.0').style(
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
        <script src="/static/js/three.min.js"></script>
        <script src="/static/js/OrbitControls.js"></script>
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

            // Create scene with stunning gradient background
            const scene = new THREE.Scene();

            // Create enhanced CybICS background with radial gradients
            const bgCanvas = document.createElement('canvas');
            bgCanvas.width = 2048;
            bgCanvas.height = 2048;
            const ctx = bgCanvas.getContext('2d');

            // Base gradient (dark blue to dark)
            const baseGradient = ctx.createLinearGradient(0, 0, 0, bgCanvas.height);
            baseGradient.addColorStop(0, '#0f1520');
            baseGradient.addColorStop(0.3, '#1a1a2e');
            baseGradient.addColorStop(0.6, '#16213e');
            baseGradient.addColorStop(1, '#0a0a10');
            ctx.fillStyle = baseGradient;
            ctx.fillRect(0, 0, bgCanvas.width, bgCanvas.height);

            // Add warm orange radial glow (top left)
            const glow1 = ctx.createRadialGradient(400, 400, 200, 400, 400, 800);
            glow1.addColorStop(0, 'rgba(255, 107, 0, 0.15)');
            glow1.addColorStop(0.5, 'rgba(255, 140, 66, 0.08)');
            glow1.addColorStop(1, 'rgba(255, 107, 0, 0)');
            ctx.fillStyle = glow1;
            ctx.fillRect(0, 0, bgCanvas.width, bgCanvas.height);

            // Add warm orange radial glow (bottom right)
            const glow2 = ctx.createRadialGradient(1648, 1648, 200, 1648, 1648, 800);
            glow2.addColorStop(0, 'rgba(255, 165, 0, 0.12)');
            glow2.addColorStop(0.5, 'rgba(255, 140, 66, 0.06)');
            glow2.addColorStop(1, 'rgba(255, 107, 0, 0)');
            ctx.fillStyle = glow2;
            ctx.fillRect(0, 0, bgCanvas.width, bgCanvas.height);

            // Add subtle texture with small dots
            ctx.fillStyle = 'rgba(255, 255, 255, 0.02)';
            for(let i = 0; i < 300; i++) {
              const x = Math.random() * bgCanvas.width;
              const y = Math.random() * bgCanvas.height;
              const size = Math.random() * 2;
              ctx.beginPath();
              ctx.arc(x, y, size, 0, Math.PI * 2);
              ctx.fill();
            }

            const bgTexture = new THREE.CanvasTexture(bgCanvas);
            scene.background = bgTexture;
            scene.fog = new THREE.FogExp2(0x0f1520, 0.010);

            // Create camera
            const camera = new THREE.PerspectiveCamera(
              60,
              container.clientWidth / container.clientHeight,
              0.1,
              1000
            );
            camera.position.set(0, 10, 25);
            camera.lookAt(0, 0, 0);

            // Create renderer with shadows enabled
            const canvas = document.createElement('canvas');
            const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.sortObjects = true;
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.1;
            renderer.physicallyCorrectLights = true;
            container.appendChild(canvas);

            // Realistic industrial lighting setup
            const ambientLight = new THREE.AmbientLight(0x5a6a7a, 0.5);
            scene.add(ambientLight);

            // Main overhead directional light (soft daylight)
            const directionalLight = new THREE.DirectionalLight(0xfff8f0, 1.0);
            directionalLight.position.set(12, 20, 8);
            directionalLight.castShadow = true;
            directionalLight.shadow.mapSize.width = 4096;
            directionalLight.shadow.mapSize.height = 4096;
            directionalLight.shadow.camera.left = -25;
            directionalLight.shadow.camera.right = 25;
            directionalLight.shadow.camera.top = 25;
            directionalLight.shadow.camera.bottom = -25;
            directionalLight.shadow.bias = -0.0001;
            directionalLight.shadow.radius = 2;
            scene.add(directionalLight);

            // Soft fill light from side (subtle blue)
            const fillLight = new THREE.DirectionalLight(0xa8c5dd, 0.35);
            fillLight.position.set(-15, 12, -8);
            scene.add(fillLight);

            // Warm accent light from opposite side (CybICS orange)
            const accentLight = new THREE.DirectionalLight(0xff9955, 0.3);
            accentLight.position.set(8, 10, -15);
            scene.add(accentLight);

            // Accent spotlights for dramatic atmosphere - reduced intensities
            const createSpotlight = (color, intensity, x, y, z, targetX, targetY, targetZ) => {
              const spotlight = new THREE.SpotLight(color, intensity, 50, Math.PI / 6, 0.5, 2);
              spotlight.position.set(x, y, z);
              spotlight.castShadow = true;
              spotlight.shadow.mapSize.width = 1024;
              spotlight.shadow.mapSize.height = 1024;

              const target = new THREE.Object3D();
              target.position.set(targetX, targetY, targetZ);
              scene.add(target);
              spotlight.target = target;

              return spotlight;
            };

            // Subtle equipment spotlights (realistic industrial lighting)
            scene.add(createSpotlight(0xffffff, 0.8, -7, 12, 5, -7, 2, 0));    // GST
            scene.add(createSpotlight(0xffffff, 0.8, 7, 12, 5, 7, 2, 0));     // HPT
            scene.add(createSpotlight(0xffffff, 0.6, 0, 8, 3, 0, 1.5, 0));    // Compressor

            // Industrial concrete floor
            const groundGeometry = new THREE.PlaneGeometry(60, 60);
            const groundMaterial = new THREE.MeshStandardMaterial({
              color: 0x3a3f47,
              roughness: 0.9,
              metalness: 0.1
            });
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

            // Subtle grid lines (like expansion joints in concrete)
            const gridHelper = new THREE.GridHelper(60, 20, 0x555a62, 0x404550);
            gridHelper.position.y = 0.01;
            gridHelper.material.opacity = 0.4;
            gridHelper.material.transparent = true;
            scene.add(gridHelper);

            // Industrial steel platform with grating
            const platformGroup = new THREE.Group();

            // Platform grating (industrial diamond plate pattern)
            const gratingMaterial = new THREE.MeshStandardMaterial({
              color: 0x6b7280,
              metalness: 0.8,
              roughness: 0.4
            });

            // Create grating bars (multiple bars to simulate grating)
            const numBars = 40;
            for(let i = 0; i < numBars; i++) {
              const bar = new THREE.Mesh(
                new THREE.BoxGeometry(20, 0.08, 0.15),
                gratingMaterial
              );
              bar.position.set(0, 0.3, -6 + (i * 12 / numBars));
              bar.castShadow = true;
              bar.receiveShadow = true;
              platformGroup.add(bar);
            }

            // Cross bars
            const numCrossBars = 25;
            for(let i = 0; i < numCrossBars; i++) {
              const bar = new THREE.Mesh(
                new THREE.BoxGeometry(0.15, 0.08, 12),
                gratingMaterial
              );
              bar.position.set(-10 + (i * 20 / numCrossBars), 0.3, 0);
              bar.castShadow = true;
              bar.receiveShadow = true;
              platformGroup.add(bar);
            }

            // Platform frame/edge beams
            const frameMaterial = new THREE.MeshStandardMaterial({
              color: 0x555a62,
              metalness: 0.85,
              roughness: 0.3
            });

            const frameBeams = [
              { w: 20.4, h: 0.15, d: 0.2, x: 0, y: 0.22, z: 6 },    // Front
              { w: 20.4, h: 0.15, d: 0.2, x: 0, y: 0.22, z: -6 },   // Back
              { w: 0.2, h: 0.15, d: 12.4, x: 10, y: 0.22, z: 0 },   // Right
              { w: 0.2, h: 0.15, d: 12.4, x: -10, y: 0.22, z: 0 }   // Left
            ];

            frameBeams.forEach(beam => {
              const beamMesh = new THREE.Mesh(
                new THREE.BoxGeometry(beam.w, beam.h, beam.d),
                frameMaterial
              );
              beamMesh.position.set(beam.x, beam.y, beam.z);
              beamMesh.castShadow = true;
              beamMesh.receiveShadow = true;
              platformGroup.add(beamMesh);
            });

            // Orange safety edge strips (CybICS branding)
            const edgeStripMaterial = new THREE.MeshStandardMaterial({
              color: 0xff6b00,
              emissive: 0xff6b00,
              emissiveIntensity: 0.8,
              metalness: 0.7,
              roughness: 0.3
            });

            const createEdgeStrip = (w, h, d, x, y, z) => {
              const strip = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), edgeStripMaterial);
              strip.position.set(x, y, z);
              return strip;
            };

            platformGroup.add(createEdgeStrip(20.2, 0.06, 0.06, 0, 0.4, 6));   // Front
            platformGroup.add(createEdgeStrip(20.2, 0.06, 0.06, 0, 0.4, -6));  // Back
            platformGroup.add(createEdgeStrip(0.06, 0.06, 12.2, 10, 0.4, 0));  // Right
            platformGroup.add(createEdgeStrip(0.06, 0.06, 12.2, -10, 0.4, 0)); // Left

            scene.add(platformGroup);

            // Orbit Controls for interactive camera
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.screenSpacePanning = false;
            controls.minDistance = 10;
            controls.maxDistance = 60;
            controls.maxPolarAngle = Math.PI / 2.1;
            controls.target.set(0, 3, 0);
            controls.update();

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

            // GST Tank (left) - Realistic industrial pressure vessel
            const gstGroup = new THREE.Group();
            gstGroup.position.set(-7, 0, 0);

            // Main tank body - industrial steel (semi-transparent to see fill)
            const gstBody = new THREE.Mesh(
              new THREE.CylinderGeometry(2, 2, 8, 32),
              new THREE.MeshStandardMaterial({
                color: 0xc0c5ce,
                metalness: 0.85,
                roughness: 0.35,
                envMapIntensity: 1.0,
                transparent: true,
                opacity: 0.3,
                side: THREE.DoubleSide
              })
            );
            gstBody.position.y = 4;
            gstBody.castShadow = true;
            gstBody.receiveShadow = true;
            gstGroup.add(gstBody);

            // GST fill level indicator (visible through transparent tank)
            const gstFillGeometry = new THREE.CylinderGeometry(1.85, 1.85, 8, 32);
            gstFillGeometry.translate(0, 4, 0);
            const gstFill = new THREE.Mesh(
              gstFillGeometry,
              new THREE.MeshStandardMaterial({
                color: 0x2196f3,
                transparent: true,
                opacity: 0.8,
                roughness: 0.2,
                metalness: 0.0,
                emissive: 0x1976d2,
                emissiveIntensity: 0.3
              })
            );
            gstFill.position.y = 0;
            gstFill.scale.y = 0.01;
            gstGroup.add(gstFill);

            // Add support legs to tank
            const legMaterial = new THREE.MeshStandardMaterial({
              color: 0x6b7280,
              metalness: 0.8,
              roughness: 0.4
            });

            for(let i = 0; i < 4; i++) {
              const angle = (Math.PI / 2) * i;
              const x = Math.cos(angle) * 1.8;
              const z = Math.sin(angle) * 1.8;

              const leg = new THREE.Mesh(
                new THREE.CylinderGeometry(0.08, 0.1, 0.8, 8),
                legMaterial
              );
              leg.position.set(x, 0.4, z);
              leg.castShadow = true;
              gstGroup.add(leg);

              // Add mounting plate
              const plate = new THREE.Mesh(
                new THREE.CylinderGeometry(0.15, 0.15, 0.05, 8),
                legMaterial
              );
              plate.position.set(x, 0.8, z);
              plate.castShadow = true;
              gstGroup.add(plate);
            }

            // GST reinforcement bands (realistic industrial detail)
            const bandMaterial = new THREE.MeshStandardMaterial({
              color: 0x8b9099,
              metalness: 0.9,
              roughness: 0.25
            });

            for(let i = 0; i < 3; i++) {
              const band = new THREE.Mesh(
                new THREE.TorusGeometry(2.05, 0.06, 8, 32),
                bandMaterial
              );
              band.position.y = 1.5 + i * 2.5;
              band.rotation.x = Math.PI / 2;
              band.castShadow = true;
              band.receiveShadow = true;
              gstGroup.add(band);
            }

            // Add pressure gauge on tank
            const gaugeMaterial = new THREE.MeshStandardMaterial({
              color: 0x2c3e50,
              metalness: 0.7,
              roughness: 0.3
            });

            const gaugeBody = new THREE.Mesh(
              new THREE.CylinderGeometry(0.15, 0.15, 0.1, 16),
              gaugeMaterial
            );
            gaugeBody.rotation.z = Math.PI / 2;
            gaugeBody.position.set(2.15, 5, 0);
            gaugeBody.castShadow = true;
            gstGroup.add(gaugeBody);

            // Gauge face
            const gaugeFace = new THREE.Mesh(
              new THREE.CircleGeometry(0.14, 16),
              new THREE.MeshStandardMaterial({
                color: 0xf0f0f0,
                metalness: 0.0,
                roughness: 0.8
              })
            );
            gaugeFace.rotation.y = Math.PI / 2;
            gaugeFace.position.set(2.2, 5, 0);
            gstGroup.add(gaugeFace);

            // Add top manhole cover
            const manholeMaterial = new THREE.MeshStandardMaterial({
              color: 0x7a8288,
              metalness: 0.85,
              roughness: 0.3
            });

            const manhole = new THREE.Mesh(
              new THREE.CylinderGeometry(0.4, 0.4, 0.15, 16),
              manholeMaterial
            );
            manhole.position.y = 8.15;
            manhole.castShadow = true;
            gstGroup.add(manhole);

            // Add bolts around manhole
            for(let i = 0; i < 8; i++) {
              const angle = (Math.PI * 2 / 8) * i;
              const bolt = new THREE.Mesh(
                new THREE.CylinderGeometry(0.04, 0.04, 0.08, 6),
                new THREE.MeshStandardMaterial({
                  color: 0x505050,
                  metalness: 0.9,
                  roughness: 0.2
                })
              );
              bolt.position.set(
                Math.cos(angle) * 0.35,
                8.15,
                Math.sin(angle) * 0.35
              );
              bolt.castShadow = true;
              gstGroup.add(bolt);
            }

            // GST dished end caps (realistic pressure vessel heads)
            const capMaterial = new THREE.MeshStandardMaterial({
              color: 0xb0b5bc,
              metalness: 0.85,
              roughness: 0.3
            });

            const gstTopCap = new THREE.Mesh(
              new THREE.SphereGeometry(2.1, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2),
              capMaterial
            );
            gstTopCap.position.y = 8;
            gstTopCap.castShadow = true;
            gstTopCap.receiveShadow = true;
            gstGroup.add(gstTopCap);

            const gstBottomCap = new THREE.Mesh(
              new THREE.SphereGeometry(2.1, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2),
              capMaterial
            );
            gstBottomCap.position.y = 0;
            gstBottomCap.castShadow = true;
            gstBottomCap.receiveShadow = true;
            gstGroup.add(gstBottomCap);

            // Add access ladder to tank
            const ladderMaterial = new THREE.MeshStandardMaterial({
              color: 0xffa500,
              metalness: 0.6,
              roughness: 0.5
            });

            // Ladder rails
            for(let side = 0; side < 2; side++) {
              const rail = new THREE.Mesh(
                new THREE.CylinderGeometry(0.03, 0.03, 8, 8),
                ladderMaterial
              );
              rail.position.set(-2.2, 4, side === 0 ? -0.25 : 0.25);
              rail.castShadow = true;
              gstGroup.add(rail);
            }

            // Ladder rungs
            for(let i = 0; i < 10; i++) {
              const rung = new THREE.Mesh(
                new THREE.CylinderGeometry(0.025, 0.025, 0.5, 8),
                ladderMaterial
              );
              rung.rotation.z = Math.PI / 2;
              rung.position.set(-2.2, 0.5 + i * 0.8, 0);
              rung.castShadow = true;
              gstGroup.add(rung);
            }

            // GST status indicator light (subtle orange glow)
            const gstGlowRing = new THREE.Mesh(
              new THREE.TorusGeometry(2.3, 0.04, 8, 32),
              new THREE.MeshStandardMaterial({
                color: 0xff6b00,
                emissive: 0xff6b00,
                emissiveIntensity: 1.0,
                transparent: true,
                opacity: 0.7,
                metalness: 0.8,
                roughness: 0.2
              })
            );
            gstGlowRing.position.y = 7;
            gstGlowRing.rotation.x = Math.PI / 2;
            gstGroup.add(gstGlowRing);

            // GST Label with text
            const gstLabel = createTextSprite('GST');
            gstLabel.position.set(0, 10.5, 0);
            gstGroup.add(gstLabel);

            scene.add(gstGroup);

            // HPT Tank (right) - Realistic industrial pressure vessel
            const hptGroup = new THREE.Group();
            hptGroup.position.set(7, 0, 0);

            // Main tank body - industrial steel (semi-transparent to see fill)
            const hptBody = new THREE.Mesh(
              new THREE.CylinderGeometry(2, 2, 8, 32),
              new THREE.MeshStandardMaterial({
                color: 0xc0c5ce,
                metalness: 0.85,
                roughness: 0.35,
                envMapIntensity: 1.0,
                transparent: true,
                opacity: 0.3,
                side: THREE.DoubleSide
              })
            );
            hptBody.position.y = 4;
            hptBody.castShadow = true;
            hptBody.receiveShadow = true;
            hptGroup.add(hptBody);

            // HPT fill level indicator (visible through transparent tank)
            const hptFillGeometry = new THREE.CylinderGeometry(1.85, 1.85, 8, 32);
            hptFillGeometry.translate(0, 4, 0);
            const hptFill = new THREE.Mesh(
              hptFillGeometry,
              new THREE.MeshStandardMaterial({
                color: 0xf44336,
                transparent: true,
                opacity: 0.8,
                roughness: 0.2,
                metalness: 0.0,
                emissive: 0xd32f2f,
                emissiveIntensity: 0.3
              })
            );
            hptFill.position.y = 0;
            hptFill.scale.y = 0.01;
            hptGroup.add(hptFill);

            // Add support legs to HPT tank
            for(let i = 0; i < 4; i++) {
              const angle = (Math.PI / 2) * i;
              const x = Math.cos(angle) * 1.8;
              const z = Math.sin(angle) * 1.8;

              const leg = new THREE.Mesh(
                new THREE.CylinderGeometry(0.08, 0.1, 0.8, 8),
                legMaterial
              );
              leg.position.set(x, 0.4, z);
              leg.castShadow = true;
              hptGroup.add(leg);

              const plate = new THREE.Mesh(
                new THREE.CylinderGeometry(0.15, 0.15, 0.05, 8),
                legMaterial
              );
              plate.position.set(x, 0.8, z);
              plate.castShadow = true;
              hptGroup.add(plate);
            }

            // HPT reinforcement bands (matching GST)
            for(let i = 0; i < 3; i++) {
              const band = new THREE.Mesh(
                new THREE.TorusGeometry(2.05, 0.06, 8, 32),
                bandMaterial
              );
              band.position.y = 1.5 + i * 2.5;
              band.rotation.x = Math.PI / 2;
              band.castShadow = true;
              band.receiveShadow = true;
              hptGroup.add(band);
            }

            // Add pressure gauge and safety valve on HPT
            const hptGaugeBody = new THREE.Mesh(
              new THREE.CylinderGeometry(0.15, 0.15, 0.1, 16),
              gaugeMaterial
            );
            hptGaugeBody.rotation.z = Math.PI / 2;
            hptGaugeBody.position.set(2.15, 5, 0);
            hptGaugeBody.castShadow = true;
            hptGroup.add(hptGaugeBody);

            const hptGaugeFace = new THREE.Mesh(
              new THREE.CircleGeometry(0.14, 16),
              new THREE.MeshStandardMaterial({
                color: 0xf0f0f0,
                metalness: 0.0,
                roughness: 0.8
              })
            );
            hptGaugeFace.rotation.y = Math.PI / 2;
            hptGaugeFace.position.set(2.2, 5, 0);
            hptGroup.add(hptGaugeFace);

            // HPT dished end caps
            const hptTopCap = new THREE.Mesh(
              new THREE.SphereGeometry(2.1, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2),
              capMaterial
            );
            hptTopCap.position.y = 8;
            hptTopCap.castShadow = true;
            hptTopCap.receiveShadow = true;
            hptGroup.add(hptTopCap);

            const hptBottomCap = new THREE.Mesh(
              new THREE.SphereGeometry(2.1, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2),
              capMaterial
            );
            hptBottomCap.position.y = 0;
            hptBottomCap.castShadow = true;
            hptBottomCap.receiveShadow = true;
            hptGroup.add(hptBottomCap);

            // HPT status indicator (subtle)
            const hptGlowRing = new THREE.Mesh(
              new THREE.TorusGeometry(2.3, 0.04, 8, 32),
              new THREE.MeshStandardMaterial({
                color: 0xff8c42,
                emissive: 0xff8c42,
                emissiveIntensity: 1.0,
                transparent: true,
                opacity: 0.7,
                metalness: 0.8,
                roughness: 0.2
              })
            );
            hptGlowRing.position.y = 7;
            hptGlowRing.rotation.x = Math.PI / 2;
            hptGroup.add(hptGlowRing);

            // HPT Label with text
            const hptLabel = createTextSprite('HPT');
            hptLabel.position.set(0, 10.5, 0);
            hptGroup.add(hptLabel);

            scene.add(hptGroup);

            // Realistic industrial compressor
            const compressorGroup = new THREE.Group();
            compressorGroup.position.set(0, 0, 0);

            // Compressor base/skid
            const compressorBase = new THREE.Mesh(
              new THREE.BoxGeometry(3.5, 0.2, 2.5),
              new THREE.MeshStandardMaterial({
                color: 0x6b7280,
                metalness: 0.8,
                roughness: 0.4
              })
            );
            compressorBase.position.y = 0.1;
            compressorBase.castShadow = true;
            compressorBase.receiveShadow = true;
            compressorGroup.add(compressorBase);

            // Main compressor body (painted industrial gray)
            const compressorBody = new THREE.Mesh(
              new THREE.BoxGeometry(2.5, 1.5, 1.8),
              new THREE.MeshStandardMaterial({
                color: 0x8a8f96,
                metalness: 0.7,
                roughness: 0.5,
                emissive: 0x00ff00,
                emissiveIntensity: 0
              })
            );
            compressorBody.position.y = 1;
            compressorBody.castShadow = true;
            compressorBody.receiveShadow = true;
            compressorGroup.add(compressorBody);

            // Motor housing (cylindrical)
            const motor = new THREE.Mesh(
              new THREE.CylinderGeometry(0.4, 0.4, 1.2, 16),
              new THREE.MeshStandardMaterial({
                color: 0x3a3f47,
                metalness: 0.8,
                roughness: 0.3
              })
            );
            motor.rotation.x = Math.PI / 2;
            motor.position.set(-0.8, 1, 0);
            motor.castShadow = true;
            compressorGroup.add(motor);

            // Motor cooling fins
            for(let i = 0; i < 8; i++) {
              const fin = new THREE.Mesh(
                new THREE.BoxGeometry(0.02, 0.85, 0.05),
                new THREE.MeshStandardMaterial({
                  color: 0x3a3f47,
                  metalness: 0.8,
                  roughness: 0.3
                })
              );
              const angle = (Math.PI * 2 / 8) * i;
              fin.position.set(
                -0.8 + Math.cos(angle) * 0.42,
                1,
                Math.sin(angle) * 0.42
              );
              fin.lookAt(-0.8, 1, 0);
              compressorGroup.add(fin);
            }

            // Status indicator light
            const indicator = new THREE.Mesh(
              new THREE.SphereGeometry(0.08, 16, 16),
              new THREE.MeshStandardMaterial({
                color: 0x00ff00,
                emissive: 0x00ff00,
                emissiveIntensity: 0,
                metalness: 0.5,
                roughness: 0.3
              })
            );
            indicator.position.set(0, 1.8, 0.95);
            compressorGroup.add(indicator);

            // Point light for status
            const compressorLight = new THREE.PointLight(0x00ff00, 0, 4);
            compressorLight.position.set(0, 1.8, 0.95);
            compressorGroup.add(compressorLight);

            // Control panel on front
            const controlPanel = new THREE.Mesh(
              new THREE.BoxGeometry(0.6, 0.8, 0.1),
              new THREE.MeshStandardMaterial({
                color: 0x2c3e50,
                metalness: 0.6,
                roughness: 0.4
              })
            );
            controlPanel.position.set(0.5, 1.3, 0.95);
            controlPanel.castShadow = true;
            compressorGroup.add(controlPanel);

            // Rotating fan on front
            const fanGroup = new THREE.Group();
            fanGroup.position.set(0, 1, 1.05);

            // Fan housing/guard
            const fanGuard = new THREE.Mesh(
              new THREE.TorusGeometry(0.45, 0.02, 8, 16),
              new THREE.MeshStandardMaterial({
                color: 0x505050,
                metalness: 0.9,
                roughness: 0.2
              })
            );
            fanGuard.castShadow = true;
            fanGroup.add(fanGuard);

            // Fan blades
            for(let i = 0; i < 4; i++) {
              const blade = new THREE.Mesh(
                new THREE.BoxGeometry(0.08, 0.7, 0.03),
                new THREE.MeshStandardMaterial({
                  color: 0x3a3f47,
                  metalness: 0.8,
                  roughness: 0.3
                })
              );
              blade.rotation.z = (Math.PI / 2) * i;
              blade.castShadow = true;
              fanGroup.add(blade);
            }

            compressorGroup.add(fanGroup);
            scene.add(compressorGroup);

            // Pipes with flanges - realistic industrial piping
            const pipeMaterial = new THREE.MeshStandardMaterial({
              color: 0x9095a0,
              metalness: 0.85,
              roughness: 0.4
            });

            const flangeMaterial = new THREE.MeshStandardMaterial({
              color: 0x7a7f8a,
              metalness: 0.9,
              roughness: 0.3
            });

            // Helper function to create flange
            function createFlange(x, y, z, rotation) {
              const flangeGroup = new THREE.Group();

              // Flange ring
              const flange = new THREE.Mesh(
                new THREE.CylinderGeometry(0.25, 0.25, 0.08, 16),
                flangeMaterial
              );
              flange.castShadow = true;
              flangeGroup.add(flange);

              // Bolts around flange
              for(let i = 0; i < 6; i++) {
                const angle = (Math.PI * 2 / 6) * i;
                const bolt = new THREE.Mesh(
                  new THREE.CylinderGeometry(0.02, 0.02, 0.1, 6),
                  new THREE.MeshStandardMaterial({
                    color: 0x505050,
                    metalness: 0.9,
                    roughness: 0.2
                  })
                );
                bolt.position.set(Math.cos(angle) * 0.2, 0, Math.sin(angle) * 0.2);
                bolt.castShadow = true;
                flangeGroup.add(bolt);
              }

              flangeGroup.position.set(x, y, z);
              if(rotation) flangeGroup.rotation.z = rotation;
              return flangeGroup;
            }

            // INLET PIPE: GST to Compressor
            const inletPipe = new THREE.Mesh(
              new THREE.CylinderGeometry(0.12, 0.12, 3.5, 16),
              pipeMaterial
            );
            inletPipe.position.set(-3.25, 1.5, -0.5);
            inletPipe.rotation.z = Math.PI / 2;
            inletPipe.castShadow = true;
            inletPipe.receiveShadow = true;
            scene.add(inletPipe);

            // Flanges on inlet pipe
            scene.add(createFlange(-5, 1.5, -0.5, Math.PI / 2));
            scene.add(createFlange(-1.5, 1.5, -0.5, Math.PI / 2));

            // OUTLET PIPE: Compressor to HPT
            const outletPipe = new THREE.Mesh(
              new THREE.CylinderGeometry(0.12, 0.12, 3.5, 16),
              pipeMaterial
            );
            outletPipe.position.set(3.25, 2.5, 0.5);
            outletPipe.rotation.z = Math.PI / 2;
            outletPipe.castShadow = true;
            outletPipe.receiveShadow = true;
            scene.add(outletPipe);

            // Flanges on outlet pipe
            scene.add(createFlange(1.5, 2.5, 0.5, Math.PI / 2));
            scene.add(createFlange(5, 2.5, 0.5, Math.PI / 2));

            // Elbow joints at pipe connections
            const elbowMaterial = new THREE.MeshStandardMaterial({
              color: 0x666666,
              metalness: 0.8
            });

            // Elbow at GST outlet (tank wall)
            const elbowGST = new THREE.Mesh(
              new THREE.SphereGeometry(0.2, 16, 16),
              elbowMaterial
            );
            elbowGST.position.set(-5, 1.5, -0.5);
            elbowGST.castShadow = true;
            scene.add(elbowGST);

            // Elbow at Compressor inlet (left side)
            const elbowCompIn = new THREE.Mesh(
              new THREE.SphereGeometry(0.2, 16, 16),
              elbowMaterial
            );
            elbowCompIn.position.set(-1.5, 1.5, -0.5);
            elbowCompIn.castShadow = true;
            scene.add(elbowCompIn);

            // Elbow at Compressor outlet (right side)
            const elbowCompOut = new THREE.Mesh(
              new THREE.SphereGeometry(0.2, 16, 16),
              elbowMaterial
            );
            elbowCompOut.position.set(1.5, 2.5, 0.5);
            elbowCompOut.castShadow = true;
            scene.add(elbowCompOut);

            // Elbow at HPT inlet (tank wall)
            const elbowHPT = new THREE.Mesh(
              new THREE.SphereGeometry(0.2, 16, 16),
              elbowMaterial
            );
            elbowHPT.position.set(5, 2.5, 0.5);
            elbowHPT.castShadow = true;
            scene.add(elbowHPT);

            // Industrial Chimney Stack (beside HPT)
            const chimneyGroup = new THREE.Group();
            chimneyGroup.position.set(11, 0, 0);

            // Chimney base (concrete/brick)
            const chimneyBase = new THREE.Mesh(
              new THREE.CylinderGeometry(1.0, 1.2, 2, 16),
              new THREE.MeshStandardMaterial({
                color: 0x4a4a52,
                roughness: 0.9,
                metalness: 0.1
              })
            );
            chimneyBase.position.y = 1;
            chimneyBase.castShadow = true;
            chimneyBase.receiveShadow = true;
            chimneyGroup.add(chimneyBase);

            // Main stack (brick/concrete with texture)
            const chimneyStack = new THREE.Mesh(
              new THREE.CylinderGeometry(0.7, 0.9, 8, 16),
              new THREE.MeshStandardMaterial({
                color: 0x5a4a42,
                roughness: 0.85,
                metalness: 0.05
              })
            );
            chimneyStack.position.y = 6;
            chimneyStack.castShadow = true;
            chimneyStack.receiveShadow = true;
            chimneyGroup.add(chimneyStack);

            // Metallic bands (3 reinforcement rings)
            const bandMat = new THREE.MeshStandardMaterial({
              color: 0x666677,
              metalness: 0.9,
              roughness: 0.2
            });

            for(let i = 0; i < 3; i++) {
              const band = new THREE.Mesh(
                new THREE.TorusGeometry(0.75, 0.06, 8, 16),
                bandMat
              );
              band.position.y = 3.5 + i * 2;
              band.rotation.x = Math.PI / 2;
              band.castShadow = true;
              chimneyGroup.add(band);
            }

            // Metallic top cap
            const chimneyTop = new THREE.Mesh(
              new THREE.CylinderGeometry(0.8, 0.7, 0.5, 16),
              new THREE.MeshStandardMaterial({
                color: 0x777788,
                metalness: 0.9,
                roughness: 0.3,
                emissive: 0x442200,
                emissiveIntensity: 0.3
              })
            );
            chimneyTop.position.y = 10.25;
            chimneyTop.castShadow = true;
            chimneyGroup.add(chimneyTop);

            // Heat glow ring at top
            const heatGlow = new THREE.Mesh(
              new THREE.TorusGeometry(0.75, 0.05, 8, 16),
              new THREE.MeshStandardMaterial({
                color: 0xff4400,
                emissive: 0xff4400,
                emissiveIntensity: 1.0,
                transparent: true,
                opacity: 0.7
              })
            );
            heatGlow.position.y = 10;
            heatGlow.rotation.x = Math.PI / 2;
            chimneyGroup.add(heatGlow);

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

            // LED Panel (right side)
            const ledPanel = new THREE.Group();
            ledPanel.position.set(15, 3, 0);

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

            // Particle system for gas flow (from compressor outlet pipe to HPT)
            const particleCount = 100;
            const particles = new Float32Array(particleCount * 3);
            const particleVelocities = [];

            for(let i = 0; i < particleCount; i++) {
              // Start particles along the outlet pipe path (compressor to HPT)
              particles[i * 3] = Math.random() * 7; // X: 0 to 7 (compressor to HPT)
              particles[i * 3 + 1] = 2.5; // Y: at outlet pipe height
              particles[i * 3 + 2] = 0.5 + (Math.random() - 0.5) * 0.3; // Z: near outlet pipe
              particleVelocities.push({
                x: 0.03 + Math.random() * 0.02, // Moving right toward HPT
                y: (Math.random() - 0.5) * 0.01, // Slight vertical variance
                z: (Math.random() - 0.5) * 0.01
              });
            }

            const particleGeometry = new THREE.BufferGeometry();
            particleGeometry.setAttribute('position', new THREE.BufferAttribute(particles, 3));

            const particleMaterial = new THREE.PointsMaterial({
              color: 0x00ffaa,
              size: 0.2,
              transparent: true,
              opacity: 0.8,
              sizeAttenuation: true,
              blending: THREE.AdditiveBlending,
              depthWrite: false
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
              size: 0.4,
              vertexColors: true,
              transparent: true,
              opacity: 0.9,
              blending: THREE.AdditiveBlending,
              depthWrite: false,
              sizeAttenuation: true
            });

            const flameSystem = new THREE.Points(flameGeometry, flameMaterial);
            flameSystem.visible = false;
            scene.add(flameSystem);

            // Flame light
            const flameLight = new THREE.PointLight(0xff6600, 0, 10);
            flameLight.position.set(11, 10, 0);
            scene.add(flameLight);

            // Status overlay with glassmorphism design
            const statusOverlay = document.createElement('div');
            statusOverlay.style.cssText = `
              position: absolute;
              bottom: 30px;
              left: 30px;
              background: linear-gradient(135deg, rgba(20, 20, 40, 0.9), rgba(30, 20, 50, 0.8));
              backdrop-filter: blur(10px);
              border: 2px solid rgba(100, 150, 255, 0.3);
              padding: 25px;
              border-radius: 20px;
              color: white;
              font-family: 'Courier New', monospace;
              z-index: 10;
              font-size: 15px;
              box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(100, 150, 255, 0.1);
              animation: statusGlow 3s ease-in-out infinite;
            `;
            statusOverlay.innerHTML = `
              <style>
                @keyframes statusGlow {
                  0%, 100% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(100, 150, 255, 0.1); }
                  50% { box-shadow: 0 8px 32px rgba(100, 150, 255, 0.3), inset 0 0 30px rgba(100, 150, 255, 0.2); }
                }
                .status-value {
                  font-weight: bold;
                  text-shadow: 0 0 10px currentColor;
                  transition: all 0.3s ease;
                }
              </style>
              <h3 style="
                margin: 0 0 20px 0;
                color: #ff8c42;
                font-size: 22px;
                text-transform: uppercase;
                letter-spacing: 3px;
                border-bottom: 2px solid #ff8c42;
                padding-bottom: 12px;
                text-shadow: 0 0 20px rgba(255, 140, 66, 0.6);
                font-weight: bold;
              ">⚡ System Status</h3>
              <div style="display: grid; grid-template-columns: 1fr auto; gap: 12px 20px; line-height: 1.8;">
                <div style="color: #6ab0ff;">● GST Pressure:</div><div class="status-value" style="color: #6ab0ff;"><span id="gst-value">0</span></div>
                <div style="color: #ff6b6b;">● HPT Pressure:</div><div class="status-value" style="color: #ff6b6b;"><span id="hpt-value">0</span></div>
                <div style="color: #ffdd57;">● System Sensor:</div><div class="status-value" style="color: #ffdd57;"><span id="syssen-value">0</span></div>
                <div style="color: #ff8844;">● Blowout:</div><div class="status-value" style="color: #ff8844;"><span id="bosen-value">0</span></div>
                <div style="color: #00ff88;">● Compressor:</div><div class="status-value" style="color: #00ff88;"><span id="compressor-value">OFF</span></div>
                <div style="color: #88ccff;">● System Valve:</div><div class="status-value" style="color: #88ccff;"><span id="systemvalve-value">CLOSED</span></div>
                <div style="color: #cc88ff;">● GST Signal:</div><div class="status-value" style="color: #cc88ff;"><span id="gstsig-value">0</span></div>
                <div style="color: #ff88cc;">● Heartbeat:</div><div class="status-value" style="color: #ff88cc;"><span id="heartbeat-value">0</span></div>
              </div>
            `;
            container.appendChild(statusOverlay);

            // Variables for smooth animations
            let fanRotationSpeed = 0;
            let targetFanSpeed = 0;

            // Fetch live data from server
            async function fetchData() {
              try {
                const response = await fetch('/api/state');
                const data = await response.json();

                // Update tank fill levels (pressure values range 0-255)
                const gstPercent = data.gst / 255;
                const hptPercent = data.hpt / 255;

                // Scale fill (geometry is anchored at bottom, so just scale)
                gstFill.scale.y = Math.max(0.01, gstPercent);
                hptFill.scale.y = Math.max(0.01, hptPercent);

                // Update compressor fan speed and lighting
                targetFanSpeed = data.compressor ? 0.15 : 0;

                // Update compressor status light (realistic)
                const compressorActive = data.compressor > 0;
                compressorBody.material.emissiveIntensity = compressorActive ? 0.3 : 0;
                indicator.material.emissiveIntensity = compressorActive ? 1.5 : 0;
                compressorLight.intensity = compressorActive ? 3 : 0;

                // Update particle visibility
                particleSystem.visible = compressorActive;

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

                // Update status overlay with all values
                document.getElementById('gst-value').textContent = data.gst;
                document.getElementById('hpt-value').textContent = data.hpt;
                document.getElementById('syssen-value').textContent = data.sysSen ? 'OK' : 'ALARM';
                document.getElementById('bosen-value').textContent = data.boSen > 0 ? 'ACTIVE' : 'INACTIVE';
                document.getElementById('compressor-value').textContent = data.compressor > 0 ? 'ON' : 'OFF';
                document.getElementById('systemvalve-value').textContent = data.systemValve ? 'OPEN' : 'CLOSED';
                document.getElementById('gstsig-value').textContent = data.gstSig ? 'HIGH' : 'LOW';
                document.getElementById('heartbeat-value').textContent = data.heartbeat;
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

              // Animate gas particles (flowing along outlet pipe from compressor to HPT)
              if(particleSystem.visible) {
                const positions = particleGeometry.attributes.position.array;
                for(let i = 0; i < particleCount; i++) {
                  positions[i * 3] += particleVelocities[i].x;
                  positions[i * 3 + 1] += particleVelocities[i].y;
                  positions[i * 3 + 2] += particleVelocities[i].z;

                  // Reset particles that reach HPT back to compressor
                  if(positions[i * 3] > 7.5) {
                    positions[i * 3] = 0; // Back to compressor
                    positions[i * 3 + 1] = 2.5; // At outlet pipe height
                    positions[i * 3 + 2] = 0.5 + (Math.random() - 0.5) * 0.3;
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

              // Animate status indicators (subtle realistic pulsing)
              const time = Date.now() * 0.001;
              gstGlowRing.rotation.z = time * 0.3;
              gstGlowRing.material.emissiveIntensity = 1.0 + Math.sin(time * 1.5) * 0.3;

              hptGlowRing.rotation.z = -time * 0.3;
              hptGlowRing.material.emissiveIntensity = 1.0 + Math.cos(time * 1.5) * 0.3;

              // Animate platform edge strips (subtle)
              const stripIntensity = 1.2 + Math.sin(time * 2) * 0.3;
              edgeStripMaterial.emissiveIntensity = stripIntensity;

              // Update orbit controls
              controls.update();

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

  # Mount static files for offline access
  from nicegui import app
  import os
  static_dir = os.path.join(os.path.dirname(__file__), 'static')
  app.add_static_files('/static', static_dir)

  ui.run(port=8090,reload=False,show=False,dark=True,favicon="pics/favicon.ico",title="CybICS VIRT")
