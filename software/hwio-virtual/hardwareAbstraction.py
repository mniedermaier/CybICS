#!/usr/bin/env python3

import logging
import time
import sys
import os

# The 3D plant scene lives next to this file rather than inside it: ~2500 lines
# of HTML, CSS and Three.js that an editor can only treat as one opaque string
# while it sits in a Python literal.  Read once at import, so a missing asset
# fails at startup with a clear path rather than on the first page load.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PLANT_3D_PATH = os.path.join(_HERE, "static", "plant3d.html")
with open(_PLANT_3D_PATH, encoding="utf-8") as _fh:
    _PLANT_3D_HTML = _fh.read()

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

# ---------------------------------------------------------------------------
# The LCD
#
# The panel on the board and the panel in the browser show the same thing.
# These are the same strings the firmware uses, copied out of
# software/stm32/src/main.c, and tests/test_display_parity.py parses both files
# and fails if they drift apart -- the same guard test_plant_model_parity.py
# puts on the physical model.
#
# Values differ, of course: this plant has no STM32 unique ID and no WiFi radio,
# just as two real boards show different uptimes.  The screens, their order and
# their layout are what have to match.
#
# LCD_SCREENS_BEGIN
LCD_SCREEN_COUNT           = 5
# Boot animation geometry and timing.  Shared because this plays the same wave
# at the same speed as the board; the captions are not shared, because the two
# wait for different peers and neither should claim otherwise.
#
# LCD_BOOT_BUMP is the pulse shape: entry i is the height, 0..8, at a distance
# of i eighths of a character from the crest.  A shape that drifted between the
# two files would be a wave in two different speeds.
LCD_BOOT_LEVELS            = 8
LCD_BOOT_SUBSTEPS          = 8
LCD_BOOT_BUMP              = "8888777666554332221110"
LCD_BOOT_SWEEP_MS          = 972
LCD_FMT_OVERVIEW_L0        = "CybICS %-9s"
LCD_FMT_OVERVIEW_L1        = "%16u"
LCD_TXT_NET_STA_L0         = "Wifi STA mode"
LCD_FMT_NET_STA_L1         = "IP: %-12s"
LCD_TXT_NET_AP_L0          = "AP mode: cybics-"
LCD_FMT_NET_AP_L1          = "%-16s"
LCD_TXT_NET_ERR_L0         = "WiFi error"
LCD_TXT_NET_ERR_L1         = ""
LCD_TXT_PROCESS_L0         = "Physical/real:  "
LCD_FMT_PROCESS_L1         = "GST:%03d HPT:%03d "
LCD_TXT_STATUS_L0          = "Status:"
LCD_TXT_STATUS_BLOWOUT     = "Danger! BlowOut"
LCD_TXT_STATUS_OPERATIONAL = "Operational"
LCD_TXT_STATUS_SV_CLOSED   = "SV closed"
LCD_TXT_STATUS_PRESS_HIGH  = "Pressure high"
LCD_TXT_STATUS_PRESS_LOW   = "Pressure low"
LCD_FMT_BUILD_L0           = "Build %s"
LCD_FMT_BUILD_L1           = "%-8s HW %-4s"
# LCD_SCREENS_END

LCD_COLS = 16

# The firmware's screen 0 prints FIRMWARE_VERSION_STRING from
# software/stm32/src/version.h.  That header is the source of truth; this copy
# has to be bumped alongside it.
FIRMWARE_VERSION_STRING = "v1.2.2"

# There is no PCB here, so there is no revision strap to read.  Four characters,
# because that is all the firmware's build screen leaves for it.
HW_VERSION_SHORT = "virt"

BUILD_DATE = time.strftime("%Y.%m.%d")
BUILD_TIME = time.strftime("%H:%M:%S")

displayScreen = 0


def lcd_render(screen):
  """Return the two 16-column lines the panel shows for `screen`.

  Mirrors the switch in thread_display() in software/stm32/src/main.c,
  including the order the status conditions are tested in -- that order is
  what decides which message wins when several apply at once.
  """
  if screen == 0:
    line0 = LCD_FMT_OVERVIEW_L0 % FIRMWARE_VERSION_STRING
    line1 = LCD_FMT_OVERVIEW_L1 % timer

  elif screen == 1:
    # The virtual plant has no radio.  It reports the STA layout with the
    # address it is actually reachable on, and never the AP or error branch.
    line0 = "%-16s" % LCD_TXT_NET_STA_L0
    line1 = LCD_FMT_NET_STA_L1 % virtual_ip()

  elif screen == 2:
    line0 = "%-16s" % LCD_TXT_PROCESS_L0
    line1 = LCD_FMT_PROCESS_L1 % (gst, hpt)

  elif screen == 3:
    line0 = "%-16s" % LCD_TXT_STATUS_L0
    # BO_red, then S_green, then SV_red, then HPT_high/critical.
    if boSen:
      line1 = "%-16s" % LCD_TXT_STATUS_BLOWOUT
    elif sysSen:
      line1 = "%-16s" % LCD_TXT_STATUS_OPERATIONAL
    elif systemValve <= 0:
      line1 = "%-16s" % LCD_TXT_STATUS_SV_CLOSED
    elif hpt >= 100:
      line1 = "%-16s" % LCD_TXT_STATUS_PRESS_HIGH
    else:
      line1 = "%-16s" % LCD_TXT_STATUS_PRESS_LOW

  else:
    line0 = LCD_FMT_BUILD_L0 % BUILD_DATE
    line1 = LCD_FMT_BUILD_L1 % (BUILD_TIME, HW_VERSION_SHORT)

  # The HD44780 has sixteen columns and no more; snprintf() truncates on the
  # board and so does this.
  return line0[:LCD_COLS].ljust(LCD_COLS), line1[:LCD_COLS].ljust(LCD_COLS)


def virtual_ip():
  """Address this plant is reachable on, for the network screen."""
  return os.environ.get("HWIO_ADDRESS", "172.18.0.4")


# ---------------------------------------------------------------------------
# Boot animation
#
# The same one the firmware plays: the name, then a bar sweeping across the
# bottom row, and that same bar is what says the plant is waiting for its
# controller.  Same 972 ms sweep, same five sub-pixel steps per character.
#
# The one thing that cannot be identical is the caption: the board waits for the
# Raspberry Pi over I2C and this waits for OpenPLC over Modbus, so each names
# the peer it actually has.  The wave itself is exact -- an HD44780 cell is
# eight pixel rows tall and Unicode has eight block heights, so every glyph the
# firmware draws has a character here that is the same shape.
WAVE_LEVELS = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"

boot_started_at = None
boot_finished = False


def boot_animation_start():
  """Replay the animation, from a reset or at start-up."""
  global boot_started_at, boot_finished
  boot_started_at = time.monotonic()
  boot_finished = False


def wave_height(col, pos, base, floor_to):
  """Height of one cell with the crest at `pos`, over a floor of `base` that
  has been laid as far as `floor_to`.

  Those are two different positions on purpose: while the pulse is crossing for
  the first time the floor follows it, and while it patrols the floor is
  already down across the whole row.
  """
  dx = abs(col * LCD_BOOT_SUBSTEPS - pos)
  h = int(LCD_BOOT_BUMP[dx]) if dx < len(LCD_BOOT_BUMP) else 0
  if col * LCD_BOOT_SUBSTEPS <= floor_to:
    h = max(h, base)
  return h


def wave_row(pos, base, floor_to):
  """The bottom row for one frame of the pulse."""
  return "".join(WAVE_LEVELS[wave_height(c, pos, base, floor_to)] for c in range(LCD_COLS))


def boot_frame():
  """Two lines for the current moment, or None once the animation is over."""
  global boot_finished
  if boot_started_at is None or boot_finished:
    return None

  span = LCD_BOOT_SWEEP_MS / 1000.0
  elapsed = time.monotonic() - boot_started_at
  maxp = LCD_COLS * LCD_BOOT_SUBSTEPS
  # The floor the pulse lays down, and the quieter one it patrols over.
  floor_laid, floor_idle = 3, 2

  if elapsed < span:
    # The pulse crosses, leaving the floor behind it.
    pos = int(maxp * elapsed / span)
    return ("CybICS %s" % FIRMWARE_VERSION_STRING).ljust(LCD_COLS), wave_row(
      pos, floor_laid, pos)

  # It arrives: full, overshoot down, settle.  Same three frames as the board.
  for until, height in ((0.09, LCD_BOOT_LEVELS), (0.15, 4), (0.27, 6)):
    if elapsed < span + until:
      return ("CybICS %s" % FIRMWARE_VERSION_STRING).ljust(LCD_COLS), \
        WAVE_LEVELS[height] * LCD_COLS

  if not client.connected:
    # Keep the pulse running for as long as the controller is missing, which is
    # the only part of this that carries information.  There and back, over a
    # floor that stays where the first pass left it: a pulse that ran only one
    # way had to jump back to the start, and that jump moved fifteen of the
    # sixteen cells in a single frame, once a second, for as long as the wait
    # lasted.
    patrol_max = (LCD_COLS - 1) * LCD_BOOT_SUBSTEPS
    phase = ((elapsed - span - 0.27) % (2 * span)) / span
    pos = int(patrol_max * (phase if phase < 1 else 2 - phase))
    return "Waiting for PLC".ljust(LCD_COLS), wave_row(pos, floor_idle, maxp)

  if elapsed < span + 0.87:
    return "PLC connected".ljust(LCD_COLS), WAVE_LEVELS[LCD_BOOT_LEVELS] * LCD_COLS

  boot_finished = True
  return None


def nav_event(event):
  """One press of the front panel.

  The navigation switch is modelled, not the v1.0 button, because that is the
  hardware being built now.  ui_input.c maps centre, down and right to NEXT and
  up and left to PREV; this does the same, so the browser and the board walk
  the screens in the same order.
  """
  global displayScreen
  if event == "next":
    displayScreen = (displayScreen + 1) % LCD_SCREEN_COUNT
  else:
    displayScreen = (displayScreen - 1) % LCD_SCREEN_COUNT


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

    # Physical simulation logic.
    #
    # This mirrors thread_physical() in software/stm32/src/main.c, which is the
    # reference implementation: it is what runs on the board in the physical
    # deployment.  Keep the two in step -- the rates, the guards and the order
    # of the updates all matter, because an attack that defeats the control
    # logic ends differently if they drift apart.
    if delay > 50:
      delay = 0
      timer = timer + 1

      # Compressor moves gas GST -> HPT.  It only does so while the GST still
      # holds enough pressure to push against, and it cannot fill the HPT past
      # the sensor range.  When the compressor is off, the downstream process
      # consumes from the HPT instead -- but only while the system valve is
      # open, and never below empty.
      if compressor > 0:
        if hpt < 255 and gst >= 50:
          gst = gst - 2
          hpt = hpt + 1
      else:
        use = random.randint(0, 2)
        if systemValve > 0 and (hpt - use) >= 0:
          hpt = hpt - use

      # Refill the GST from the external supply.
      if gstSig > 0 and gst < 251:
        gst = gst + random.randint(0, 3)

      # Mechanical blowout valve: opens above 220 bar and stays open until the
      # tank falls back below 200.  The condition is evaluated here, right
      # before venting, so the order within a tick matches the firmware.  It
      # vents more slowly than the compressor fills, so a compressor stuck on
      # drives the tank to a state the relief valve cannot recover -- which is
      # the point of the exercise.
      if hpt > 220 or (boSen > 0 and hpt > 200):
        boSen = 1
        vent = random.randint(0, 1)
        if (hpt - vent) >= 0:
          hpt = hpt - vent
      else:
        boSen = 0
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
  boot_animation_start()
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

  ui.add_head_html("""<script>(function(){if(new URLSearchParams(location.search).get(\"theme\")==\"light\")document.documentElement.classList.add(\"light-mode\");})();</script>""")

  # Create container for the content
  with ui.element('div').style('text-align: center; min-width: 1024px; width: 1200px; margin: 0 auto;'):

    # NiceGUI setup - Header with tabs on same row
    with ui.row().style('width: 100%; align-items: center; justify-content: space-between; margin-bottom: 20px;'):
      # Left side: Spinner and Logo
      with ui.row().style('align-items: center;'):
        ui.spinner('dots', size='lg', color='red')
        ui.image('pics/CybICS_logo.png').classes('w-64')
        ui.spinner('dots', size='lg', color='red')

      # Right side: Tabs
      with ui.tabs().style('background-color: #1a1a2e;') as tabs:
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

        # Add PCB as a PNG image - centered wrapper
        with ui.element('div').style('display: flex; justify-content: center; width: 100%;'):
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
            #
            # A real 16x2 panel rather than two free-floating labels: the same
            # sixteen columns, monospaced and left-aligned, so a line that is
            # padded or truncated on the board is padded or truncated here too.
            # lcd_render() decides what goes in them.
            # Sized to the panel rather than by eye.  The blue area of the
            # module in pics/pcb.png covers x 424..783 and y 375..462 of the
            # 800 x 500 the image is drawn at, so 360 x 88 px.  Sixteen columns
            # of monospace at 32px advance 0.6022em each, 308 px, which leaves
            # about 26 px of margin on either side -- roughly the proportion a
            # real 1602 has, whose 56 mm character area sits in a 64 mm window.
            # The previous 40px was 385 px wide and spilled over the edge of
            # the display.
            lcd_line_style = (
              'position: absolute; left: 450px; color: black;'
              'background-color: transparent; font-size: 32px; line-height: 34px;'
              'font-family: monospace; white-space: pre; letter-spacing: 0px;'
              'display: block;'
            )
            DISPLAYoverlay1 = ui.label('').style('top: 385px;' + lcd_line_style)
            DISPLAYoverlay2 = ui.label('').style('top: 419px;' + lcd_line_style)

            # The navigation switch, SW3.
            #
            # From board v1.1 the front panel is a 5-way switch, so the virtual
            # plant offers the same five contacts instead of a single button.
            # Placement follows SW3 on the board: (204.5, 103.5) mm on a
            # 160 x 100 mm outline is 96 % across and 53 % down, which lands
            # here on the 800 x 500 photograph.
            nav_button_style = (
              'position: absolute; background-color: #444; color: white;'
              'width: 22px; height: 22px; min-width: 22px; padding: 0;'
              'font-size: 14px; line-height: 22px;'
              'display: block;'
            )
            ui.button('^', on_click=lambda: nav_event('prev')).style(
              'top: 240px; left: 745px;' + nav_button_style).tooltip('Up: previous screen')
            ui.button('<', on_click=lambda: nav_event('prev')).style(
              'top: 264px; left: 721px;' + nav_button_style).tooltip('Left: previous screen')
            ui.button('O', on_click=lambda: nav_event('next')).style(
              'top: 264px; left: 745px;' + nav_button_style).tooltip('Centre: next screen')
            ui.button('>', on_click=lambda: nav_event('next')).style(
              'top: 264px; left: 769px;' + nav_button_style).tooltip('Right: next screen')
            ui.button('v', on_click=lambda: nav_event('next')).style(
              'top: 288px; left: 745px;' + nav_button_style).tooltip('Down: next screen')

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
        with ui.element('div').style('display: flex; justify-content: center; width: 100%;'):
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
        # Sized to the window rather than to a number.  800px was taller than
        # the viewport on a laptop, which pushed the status panel off the
        # bottom, and shorter than it on a desktop, which left a dead band
        # under the scene.
        container_3d = ui.element('div').props('id=container3d').style(
          'width: 100%; height: calc(100vh - 150px); min-height: 380px;'
          'position: relative; background-color: #0a0a0f;')

  # Three.js 3D Visualization - Clean implementation
  # The 3D plant is ~2500 lines of HTML, CSS and Three.js. Kept in
  # static/plant3d.html so an editor can highlight and lint it, and so
  # this file stays about the service rather than about the scene.
  ui.add_body_html(_PLANT_3D_HTML)

  # Update function called periodically (UI updates only)
  async def update():
    global gst, hpt, sysSen, boSen, heartbeat, compressor, systemValve, gstSig, delay, timer, consecutive_failures

    # Update the LCD.  Both lines every tick, from one renderer, so the panel
    # can never show half of one screen and half of another.  The boot
    # animation owns the panel while it runs.
    frame = boot_frame()
    line0, line1 = frame if frame else lcd_render(displayScreen)
    DISPLAYoverlay1.set_text(line0)
    DISPLAYoverlay2.set_text(line1)

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

  # The panel boots the way the board does, for whoever opens the page first.
  if boot_started_at is None:
    boot_animation_start()

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
