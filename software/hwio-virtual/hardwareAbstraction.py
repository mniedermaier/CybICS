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
  ui.add_body_html('''
    <style>
      html.light-mode body, html.light-mode .nicegui-content { background: #f3f5f8 !important; color: #172033 !important; }
      html.light-mode .q-page, html.light-mode .q-card, html.light-mode .q-tab-panels, html.light-mode .q-panel { background: #ffffff !important; color: #172033 !important; }
      html.light-mode .q-card[style*="background-color: red"] { background-color: red !important; }
      html.light-mode .q-card[style*="background-color: green"] { background-color: green !important; }
      html.light-mode .q-card[style*="background-color: blue"] { background-color: blue !important; }
      html.light-mode .q-card[style*="background-color: white"] { background-color: white !important; }
      html.light-mode .q-card[style*="background-color: orange"] { background-color: orange !important; }
      html.light-mode .q-card[style*="background-color: grey"] { background-color: #9ca3af !important; }
      html.light-mode .q-tabs { background: #ffffff !important; }
      html.light-mode .q-tab { color: #596273 !important; }
      html.light-mode .q-tab--active, html.light-mode .q-tab:hover { color: #b34700 !important; }
      html.light-mode .q-card .q-label, html.light-mode .q-card span, html.light-mode .q-card div { color: #172033; }
      html.light-mode .q-table, html.light-mode .q-table thead, html.light-mode .q-table tbody { background: #ffffff !important; color: #172033 !important; }
      html.light-mode .q-table th, html.light-mode .q-table td, html.light-mode .q-table tbody, html.light-mode .q-table tr, html.light-mode .q-td, html.light-mode .q-th { color: #172033 !important; background: #ffffff !important; }
      html.light-mode .q-table__middle, html.light-mode .q-table__container { background: #ffffff !important; color: #172033 !important; }
      html.light-mode .q-table th { color: #596273 !important; }
      html.light-mode #container3d { background: #eef1f5 !important; }
    </style>
    <script>
      window.addEventListener('message', function (event) {
        if (!event.data || event.data.type !== 'theme') return;
        document.documentElement.classList.toggle('light-mode', event.data.theme === 'light');
      });
    </script>
        <script src="/static/js/three.min.js"></script>
        <script src="/static/js/OrbitControls.js"></script>
        <script>
          window.CYBICS_3D_VERSION = "7.0.0-CLEAN";
          document.title = "CybICS 3D Visualization";

          // Let the browser breathe.
          //
          // Building this scene is a few seconds of straight-line work on a
          // machine without GPU acceleration: 56 meshes, 39 physically based
          // materials and the shader compiles that go with them.  Done in one
          // block it holds the main thread long enough that NiceGUI's client
          // cannot answer its own handshake, and NiceGUI responds by reloading
          // the page -- so the 3D tab used to take the session down with it,
          // measured as a reload roughly six seconds after opening the tab
          // while the same page left alone ran for forty without one.
          //
          // Yielding between sections costs a few milliseconds and lets the
          // socket be serviced while the scene assembles.
          const yieldToBrowser = () => new Promise(r => setTimeout(r, 0));

          async function init3DScene() {
            const container = document.getElementById('container3d');
            if (!container) {
              setTimeout(init3DScene, 100);
              return;
            }

            if (typeof THREE === 'undefined') {
              setTimeout(init3DScene, 100);
              return;
            }

            // Is there a GPU behind this page?
            //
            // A browser with no hardware acceleration falls back to a software
            // rasteriser -- SwiftShader in Chrome, llvmpipe on Mesa -- and this
            // scene is far outside what that can sustain: 56 meshes, 39
            // physically based materials and nine lights, with every shader
            // compiled on the CPU.
            //
            // That is not a slow scene, it is a broken page.  Measured in
            // headless Chrome on SwiftShader, opening this tab held the main
            // thread long enough that NiceGUI's client could not answer its own
            // handshake and reloaded the page, every time, taking the session
            // with it -- while the same page left on the other tab ran for as
            // long as it was watched without a single reload.  Turning shadows
            // off, dropping to twelve frames a second and building the scene in
            // chunks all helped and none of it was enough.
            //
            // So on a machine without acceleration the honest thing is to say
            // so rather than to take the page down.  A training platform gets
            // run in classroom VMs without GPU passthrough, and everything the
            // 3D tab shows is on the classic view as well.
            const gpuName = (function () {
              try {
                const probe = document.createElement('canvas');
                const gl = probe.getContext('webgl2') || probe.getContext('webgl');
                if (!gl) { return 'none'; }
                const dbg = gl.getExtension('WEBGL_debug_renderer_info');
                return dbg ? String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) : 'unknown';
              } catch (e) { return 'unknown'; }
            })();
            // ?force3d=1 builds the scene anyway.  Someone on a weak machine
            // may want to look at it regardless, and it is the only way to
            // inspect the scene from a browser without hardware acceleration.
            const forced = /[?&]force3d=1/.test(window.location.search);
            const softwareRenderer = !forced &&
              /swiftshader|llvmpipe|software|microsoft basic|^none$/i.test(gpuName);

            if (softwareRenderer) {
              console.log('CybICS 3D: no hardware acceleration (' + gpuName + '), not building the scene');
              container.innerHTML =
                '<div style="display:flex;align-items:center;justify-content:center;' +
                'height:100%;min-height:320px;padding:32px;text-align:center;' +
                'font-family:sans-serif;color:#8fa4bb;line-height:1.6">' +
                '<div><div style="font-size:18px;color:#dfe9f5;margin-bottom:8px">' +
                '3D view needs hardware acceleration</div>' +
                'This browser is rendering WebGL in software, where the scene runs ' +
                'slowly enough to stall the page.<br>Everything it shows is on the ' +
                '<b>Classic View</b> tab as well.' +
                '<div style="font-size:12px;margin-top:12px;opacity:.7">renderer: ' +
                gpuName + '</div></div></div>';
              return;
            }

            // Clear container
            container.innerHTML = '';

            // Alarm treatment for the viewport as a whole.
            //
            // The review was blunt about this: during a blowout the only
            // blowout-specific token in frame was a flare about one and a half
            // per cent of the picture high, in the far corner, and the vessel
            // colour that changed most was salmon -- which is HPT's product
            // colour, so "big and red" also means "HPT is full". An operator
            // reads the wrong thing, or nothing.
            //
            // A pulsing rim on the viewport is caught peripherally, uses a
            // colour nothing else in the scene wears, and says "state change"
            // rather than "quantity". It costs nothing to draw.
            // The rim is its own layer on top of the canvas, not a shadow on
            // the container. An inset box-shadow paints behind the container's
            // children, so the canvas sat straight over it and the first
            // attempt was invisible in the screenshot.
            if (!document.getElementById('cybics-alarm-style')) {
              const style = document.createElement('style');
              style.id = 'cybics-alarm-style';
              style.textContent =
                '@keyframes cybics-alarm-pulse {' +
                '  0%, 100% { opacity: 1; }' +
                '  50%      { opacity: 0.35; }' +
                '}' +
                '#cybics-alarm-rim {' +
                '  position: absolute; inset: 0; pointer-events: none;' +
                '  z-index: 5; display: none; border: 3px solid #ff3b30;' +
                '  box-shadow: inset 0 0 44px 10px rgba(255,59,48,0.22);' +
                '  animation: cybics-alarm-pulse 1.1s ease-in-out infinite; }' +
                '#container3d.cybics-alarm #cybics-alarm-rim { display: block; }';
              document.head.appendChild(style);
            }
            if (getComputedStyle(container).position === 'static') {
              container.style.position = 'relative';
            }
            const alarmRim = document.createElement('div');
            alarmRim.id = 'cybics-alarm-rim';
            container.appendChild(alarmRim);
            container.classList.remove('cybics-alarm');

            // Create scene with stunning gradient background
            const scene = new THREE.Scene();
            const lightTheme = document.documentElement.classList.contains('light-mode');

            // ---- Procedural surfaces -------------------------------------
            //
            // Everything below is drawn into a canvas at build time.  The
            // container has no network at runtime and gets pulled onto
            // classroom machines, so a few kilobytes of JavaScript that draws
            // its own concrete beats any amount of downloaded PBR material.
            // These are the textures the whole scene is judged through: with
            // no variation in a surface, no amount of lighting makes it look
            // like anything but a solid colour.

            // Fine grain plus large soft blotches plus a few stains.  The
            // grain alone reads as video noise; it is the blotches at the
            // scale of a metre or two that make a floor look poured rather
            // than filled.
            function concreteCanvas(size) {
              const c = document.createElement('canvas');
              c.width = c.height = size;
              const g = c.getContext('2d');
              g.fillStyle = '#4b5058';
              g.fillRect(0, 0, size, size);

              for (let i = 0; i < 60; i++) {
                const r = size * (0.04 + Math.random() * 0.14);
                const x = Math.random() * size, y = Math.random() * size;
                const shade = 60 + Math.random() * 40;
                const blot = g.createRadialGradient(x, y, 0, x, y, r);
                blot.addColorStop(0, 'rgba(' + shade + ',' + shade + ',' +
                                  (shade + 6) + ',0.35)');
                blot.addColorStop(1, 'rgba(0,0,0,0)');
                g.fillStyle = blot;
                g.fillRect(x - r, y - r, r * 2, r * 2);
              }

              // A handful of oil stains.  Real plant floors are never clean,
              // and the eye reads "used" long before it reads "detailed".
              for (let i = 0; i < 7; i++) {
                const r = size * (0.02 + Math.random() * 0.05);
                const x = Math.random() * size, y = Math.random() * size;
                const stain = g.createRadialGradient(x, y, 0, x, y, r);
                stain.addColorStop(0, 'rgba(24,22,20,0.45)');
                stain.addColorStop(1, 'rgba(24,22,20,0)');
                g.fillStyle = stain;
                g.fillRect(x - r, y - r, r * 2, r * 2);
              }

              const img = g.getImageData(0, 0, size, size);
              const d = img.data;
              for (let i = 0; i < d.length; i += 4) {
                const n = (Math.random() - 0.5) * 26;
                d[i] += n; d[i + 1] += n; d[i + 2] += n;
              }
              g.putImageData(img, 0, 0);
              return c;
            }

            // Brushed steel: vertical streaks of varying roughness.  Used as a
            // roughness map rather than a colour map, so the metal keeps its
            // colour and only the sharpness of its reflection varies -- which
            // is what actually distinguishes rolled steel from plastic.
            function brushedCanvas(w, h) {
              const c = document.createElement('canvas');
              c.width = w; c.height = h;
              const g = c.getContext('2d');
              g.fillStyle = '#8a8a8a';
              g.fillRect(0, 0, w, h);
              for (let i = 0; i < w * 3; i++) {
                const x = Math.random() * w;
                const v = 118 + Math.random() * 74;
                g.strokeStyle = 'rgba(' + v + ',' + v + ',' + v + ',' +
                                (0.05 + Math.random() * 0.18) + ')';
                g.lineWidth = 0.5 + Math.random() * 1.8;
                g.beginPath();
                g.moveTo(x, 0); g.lineTo(x + (Math.random() - 0.5) * 3, h);
                g.stroke();
              }
              // Horizontal weld seams, where a real vessel's courses meet.
              for (let i = 1; i < 4; i++) {
                const y = h * i / 4;
                g.strokeStyle = 'rgba(210,210,210,0.55)';
                g.lineWidth = Math.max(1, h * 0.012);
                g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke();
              }
              return c;
            }

            // Fold many identical parts into one buffer.
            //
            // r128 ships BufferGeometryUtils only in examples/, which is not
            // vendored here, so this is the small part of it this scene needs.
            // It matters because the scene is draw-call bound rather than
            // triangle bound: the platform grating alone was sixty-five
            // separate meshes drawing sixty-five times for one flat surface.
            function mergeGeometries(geometries) {
              const parts = geometries.map(g => (g.index ? g.toNonIndexed() : g));
              let total = 0;
              parts.forEach(g => { total += g.attributes.position.count; });
              const pos = new Float32Array(total * 3);
              const nor = new Float32Array(total * 3);
              const uv = new Float32Array(total * 2);
              let o = 0, uo = 0;
              parts.forEach(g => {
                pos.set(g.attributes.position.array, o);
                if (g.attributes.normal) { nor.set(g.attributes.normal.array, o); }
                if (g.attributes.uv) { uv.set(g.attributes.uv.array, uo); }
                o += g.attributes.position.count * 3;
                uo += g.attributes.position.count * 2;
              });
              const out = new THREE.BufferGeometry();
              out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
              out.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
              out.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
              return out;
            }

            // Detail costs texture memory and bandwidth, which is exactly what
            // a machine without acceleration has none of.  The software path
            // keeps the flat materials it already had.
            const detail = !softwareRenderer;

            function texture(canvas, repeatX, repeatY) {
              const t = new THREE.CanvasTexture(canvas);
              t.wrapS = t.wrapT = THREE.RepeatWrapping;
              t.repeat.set(repeatX, repeatY);
              t.anisotropy = 4;
              return t;
            }

            // Repeats chosen to keep one tile at ten world units across the
            // larger ground plane, so the concrete does not stretch.
            const concreteMap = detail ? texture(concreteCanvas(512), 30, 30) : null;
            if (concreteMap) { concreteMap.encoding = THREE.sRGBEncoding; }
            const concreteRough = detail ? texture(concreteCanvas(512), 30, 30) : null;
            const steelRough = detail ? texture(brushedCanvas(128, 256), 4, 1) : null;

            // ---- Backdrop ------------------------------------------------
            //
            // A flat colour, and the fog is the same colour.
            //
            // A painted horizon cannot be made to line up: the background
            // texture is stretched across the screen, so its horizon sits at a
            // fixed fraction of the canvas while the real one moves with the
            // camera. Every framing showed a step where the ground met the
            // sky. With one colour for both, the ground simply dissolves into
            // the distance and there is nothing to align -- and it is one less
            // texture, which on a machine with no GPU is the whole point.
            const BACKDROP = 0x1b2836;
            scene.background = new THREE.Color(lightTheme ? 0xf3f5f8 : 0x0a0f16);
            scene.fog = new THREE.FogExp2(lightTheme ? 0xf3f5f8 : BACKDROP, 0.014);

            // A sky dome, so the horizon is in the world rather than on the
            // screen.
            //
            // The first attempt painted a horizon into a background image.
            // That image is stretched across the canvas, so its horizon sits
            // at a fixed fraction of the screen while the real one moves with
            // the camera, and every framing showed a step where the ground met
            // the sky. Replacing it with a flat colour removed the step but
            // took the depth with it -- the plant ended up floating in a void
            // with no far distance.
            //
            // A dome fixes both: the gradient is a real thing at a real place,
            // it lines up from any angle, and the fog is given the same colour
            // as its horizon band so the ground dissolves into it. One mesh,
            // one draw call, no lighting, no fog of its own.
            const skyDome = (function () {
              const c = document.createElement('canvas');
              c.width = 4; c.height = 256;
              const g = c.getContext('2d');
              // Canvas top is the zenith: three.js flips images, so v = 1 --
              // the top of the sphere -- samples row zero.
              const grad = g.createLinearGradient(0, 0, 0, 256);
              grad.addColorStop(0.00, '#0a0f16');
              grad.addColorStop(0.38, '#141d28');
              grad.addColorStop(0.48, '#22303d');
              grad.addColorStop(0.50, '#2b3a49');
              grad.addColorStop(0.54, '#1a232e');
              grad.addColorStop(1.00, '#0a0d12');
              g.fillStyle = grad;
              g.fillRect(0, 0, 4, 256);

              const tex = new THREE.CanvasTexture(c);
              tex.encoding = THREE.sRGBEncoding;
              const dome = new THREE.Mesh(
                new THREE.SphereGeometry(180, 24, 16),
                new THREE.MeshBasicMaterial({
                  map: tex,
                  side: THREE.BackSide,
                  fog: false,
                  depthWrite: false
                }));
              dome.userData.noOutline = true;
              dome.userData.noFrame = true;
              dome.renderOrder = -1;
              return dome;
            })();
            scene.add(skyDome);
            window.addEventListener('message', function (event) {
              if (!event.data || event.data.type !== 'theme') return;
              const isLight = event.data.theme === 'light';
              scene.background = new THREE.Color(isLight ? 0xf3f5f8 : 0x0a0f16);
              scene.fog = new THREE.FogExp2(isLight ? 0xf3f5f8 : BACKDROP, 0.014);
              skyDome.visible = !isLight;
            });

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
            // Render at the display's own resolution, but never beyond 2x: the
            // difference above that is invisible and the cost is quadratic.
            renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
            renderer.sortObjects = true;
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            // Nothing that casts a shadow here ever moves -- the tanks, pipes,
            // platform and floor are fixed, and the only animated things are
            // the fan and the particles.  So the shadow maps are rendered once
            // instead of four more full scene passes on every single frame.
            renderer.shadowMap.autoUpdate = false;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            // Exposure and the light intensities below were tuned against the
            // broken linear output, which swallowed most of what they emitted.
            // Correcting the encoding handed all of that back at once and the
            // scene came out washed out -- the same lighting, now actually
            // arriving.  A mid grey lit to 0.5 in linear space reads as 0.5
            // when written straight to the canvas and as 0.74 once encoded, so
            // roughly everything got brighter by half.
            //
            // Rebalanced rather than simply dimmed: the key light keeps its
            // full strength, because that is what gives the vessels their shape
            // and their shadows, and the ambient and fill terms come down
            // hardest, because those are what flatten a scene when they are too
            // strong.
            renderer.toneMappingExposure = 0.75;
            // The liquid in each vessel is a full-size body cut off at the
            // surface by a clipping plane, which is what lets the level run
            // into the dished heads instead of stopping at the cylinder.
            renderer.localClippingEnabled = true;
            renderer.physicallyCorrectLights = true;
            // Without this the image is written to the canvas in linear space
            // while the tone mapper assumes it will be encoded, which is what
            // made every surface look washed out and flat.
            renderer.outputEncoding = THREE.sRGBEncoding;
            // setSize(..., false) leaves the CSS size alone, so the canvas is
            // told here to fill its box and the observer above only has to
            // keep the drawing buffer in step with it.
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.display = 'block';
            container.appendChild(canvas);

            // An environment for the metals to reflect.
            //
            // MeshStandardMaterial is a physically based material: its
            // metalness and roughness describe how a surface reflects its
            // surroundings, and with no surroundings to reflect, every metal
            // part resolves to flat grey no matter what those values say.  A
            // small gradient -- bright sky, dark floor, warm horizon -- run
            // through PMREM gives the tanks, pipes and frames something to
            // pick up, which is the single biggest step towards looking like
            // metal rather than plastic.  It is generated once.
            (function buildEnvironment() {
              if (softwareRenderer) { return; }
              const c = document.createElement('canvas');
              c.width = 64; c.height = 32;
              const g = c.getContext('2d');
              const grad = g.createLinearGradient(0, 0, 0, 32);
              grad.addColorStop(0.00, '#dfe9f5');
              grad.addColorStop(0.45, '#8fa4bb');
              grad.addColorStop(0.55, '#6b5a4a');
              grad.addColorStop(1.00, '#20242a');
              g.fillStyle = grad; g.fillRect(0, 0, 64, 32);
              const tex = new THREE.CanvasTexture(c);
              tex.mapping = THREE.EquirectangularReflectionMapping;
              const pmrem = new THREE.PMREMGenerator(renderer);
              pmrem.compileEquirectangularShader();
              scene.environment = pmrem.fromEquirectangular(tex).texture;
              tex.dispose();
              pmrem.dispose();
            })();

            // Realistic industrial lighting setup
            // ambient lifts every surface equally, so it is the first thing to cut
            const ambientLight = new THREE.AmbientLight(0x5a6a7a, 0.26);
            scene.add(ambientLight);

            // Main overhead directional light (soft daylight)
            // Carries more of the scene now that the accent spots are gone.
            const directionalLight = new THREE.DirectionalLight(0xfff8f0, 1.25);
            // Lower and further round than it was.
            //
            // At (12, 20, 8) the key stood about 55 degrees up, which threw
            // shadows so short that every one of them landed off the platform
            // -- two separate reviews read the plant as having no contact with
            // its own floor, and the one shadow that was visible, GST's, sat
            // out on the ground detached from anything and read as a bug.
            // Dropping the light puts the vessels' and the stack's shadows
            // back into the picture. Verified by moving it at runtime and
            // photographing the result before committing to it.
            directionalLight.position.set(16, 11, 13);
            directionalLight.castShadow = true;
            // 2048 over a 50-unit shadow camera is 41 texels per world unit,
            // far finer than the screen resolves these objects at any sane
            // camera distance.  4096 cost four times the memory and bandwidth
            // for a difference nobody can see.
            directionalLight.shadow.mapSize.width = 2048;
            directionalLight.shadow.mapSize.height = 2048;
            directionalLight.shadow.camera.left = -25;
            directionalLight.shadow.camera.right = 25;
            directionalLight.shadow.camera.top = 25;
            directionalLight.shadow.camera.bottom = -25;
            directionalLight.shadow.bias = -0.0001;
            directionalLight.shadow.radius = 2;
            scene.add(directionalLight);

            // Soft fill light from side (subtle blue)
            const fillLight = new THREE.DirectionalLight(0xa8c5dd, 0.22);
            fillLight.position.set(-15, 12, -8);
            scene.add(fillLight);

            // Warm accent light from opposite side (CybICS orange)
            const accentLight = new THREE.DirectionalLight(0xff9955, 0.18);
            accentLight.position.set(8, 10, -15);
            scene.add(accentLight);

            // The three accent spotlights that used to stand here are gone.
            //
            // They were a photographic device -- a warm pool on each vessel --
            // and in a scene lit as a stage they did two things wrong: the HPT
            // cone spilled past the platform and put a bright warm patch on the
            // ground with no visible source, which reads as a rendering fault
            // rather than as lighting, and together they washed the whole floor
            // pale and undid the darkness the equipment is meant to stand
            // against. Three fewer lights, and every remaining one is
            // explainable by something in the picture.

            // Industrial concrete floor
            //
            // A flat grey plane is the one surface that cannot be rescued by
            // lighting: it is large, it is lit evenly, and with no variation
            // across it the eye reads it as a backdrop rather than as ground.
            // The texture is the same canvas used twice, once for colour and
            // once for roughness, so the darker patches are also the duller
            // ones -- which is how a damp or oiled patch of concrete behaves.
            //
            // The plane is far larger than the plant it carries.  At 60 units
            // its edge fell inside the fog's reach and cut a hard horizontal
            // line across the middle of the picture; the fog only saturates
            // past about 120 units, so the ground has to outrun it.  This
            // costs nothing: it is still two triangles.
            const groundGeometry = new THREE.PlaneGeometry(300, 300);
            // Dark and close to plain.  The photographic concrete that was
            // here tiled visibly at this size and, more to the point, a
            // detailed floor pulls attention downwards; in this language the
            // ground is a stage for the equipment and the grid does the work
            // of telling you it is a surface at all.
            // Fully matte, and no roughness map.
            //
            // The map was multiplying roughness down to near zero in its
            // darker patches, and the key light answered with a specular lobe:
            // a bright warm pool on the floor with no visible source, which
            // reads as a rendering fault rather than as lighting. It was in
            // the very first screenshot of this scene and survived three
            // rounds of being blamed on the spotlights. Confirmed by clearing
            // the map at runtime and photographing the result.
            const groundMaterial = new THREE.MeshStandardMaterial({
              color: 0x1a2028,
              roughness: 1.0,
              metalness: 0.0
            });
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.userData.noFrame = true;
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

            // Expansion joints.  Dimmer than before: at full strength this
            // read as a debug grid laid over the plant rather than as lines
            // scored in a floor, and it was competing with the grating.
            const gridHelper = new THREE.GridHelper(60, 20, 0x3f5568, 0x2b3a47);
            gridHelper.position.y = 0.01;
            gridHelper.material.opacity = 0.55;
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

            // Grating bars, folded into one mesh.
            //
            // These were sixty-five separate meshes: sixty-five draw calls and
            // seven hundred and eighty outline segments for a surface the eye
            // reads as one texture. Merged, the deck is a single draw call and
            // contributes nothing to the outline pass, which is where the
            // frame time was going.
            const gratingParts = [];
            const numBars = 40;
            for (let i = 0; i < numBars; i++) {
              const g = new THREE.BoxGeometry(20, 0.08, 0.15);
              g.translate(0, 0.3, -6 + (i * 12 / numBars));
              gratingParts.push(g);
            }
            const numCrossBars = 25;
            for (let i = 0; i < numCrossBars; i++) {
              const g = new THREE.BoxGeometry(0.15, 0.08, 12);
              g.translate(-10 + (i * 20 / numCrossBars), 0.3, 0);
              gratingParts.push(g);
            }
            const gratingMesh = new THREE.Mesh(
              mergeGeometries(gratingParts), gratingMaterial);
            gratingMesh.castShadow = true;
            gratingMesh.receiveShadow = true;
            // A repeating pattern outlined edge by edge is visual noise, and
            // there is a great deal of it.
            gratingMesh.userData.noOutline = true;
            platformGroup.add(gratingMesh);

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

            await yieldToBrowser();   // built lighting, floor and platform

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
            // Plant signage, drawn to match the status panel rather than to
            // fight it. These were saturated yellow plates with black Arial on
            // them, which is the one thing in frame that looked printed rather
            // than built, and they were the brightest objects in a dark scene.
            // Dark plate, orange rule, orange text: the same vocabulary as the
            // HUD, so the eye reads them as one system.
            function createTextSprite(text, color = '#ffb070', backgroundColor = 'rgba(14, 20, 28, 0.88)') {
              const canvas = document.createElement('canvas');
              const context = canvas.getContext('2d');
              canvas.width = 512;
              canvas.height = 128;

              // Background
              context.fillStyle = backgroundColor;
              context.fillRect(0, 0, canvas.width, canvas.height);
              context.strokeStyle = 'rgba(255, 140, 66, 0.75)';
              context.lineWidth = 6;
              context.strokeRect(3, 3, canvas.width - 6, canvas.height - 6);

              // Text
              context.font = 'bold 74px ui-monospace, Menlo, Consolas, monospace';
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

            await yieldToBrowser();   // built controls and helpers

            // Vessel plates carry the number, not just the tag
            //
            // The scene and the numbers used to read as two unrelated
            // products: the plant said "GST" and "HPT" and nothing else, while
            // every actual value lived in an HTML card floating over the deck.
            // A plant view that has to be read alongside a separate list is
            // not doing its job.
            //
            // The bands and their wording are not invented here. update_ui()
            // further down this same file already classifies both vessels for
            // the classic view -- HPT as Empty, Low, Normal, High or Critical
            // and GST as Low, Normal or Full -- and HPT's Normal band is the
            // same 50 to 100 window that physical_process_thread uses for
            // sysSen. If those thresholds move, they have to move in both
            // places.
            function makeValuePlate(tag) {
              const canvas = document.createElement('canvas');
              canvas.width = 512;
              canvas.height = 176;
              const ctx = canvas.getContext('2d');
              const texture = new THREE.CanvasTexture(canvas);
              texture.encoding = THREE.sRGBEncoding;
              const sprite = new THREE.Sprite(
                new THREE.SpriteMaterial({ map: texture }));
              sprite.scale.set(4.4, 1.5, 1);

              let last = null;
              sprite.userData.set = function (value, word, accent) {
                const key = value + '|' + word + '|' + accent;
                // Redrawing a canvas and re-uploading its texture every frame
                // for a number that changes twice a second is pure waste.
                if (key === last) { return; }
                last = key;

                ctx.clearRect(0, 0, 512, 176);
                ctx.fillStyle = 'rgba(14, 20, 28, 0.9)';
                ctx.fillRect(0, 0, 512, 176);
                ctx.strokeStyle = accent;
                ctx.lineWidth = 6;
                ctx.strokeRect(3, 3, 506, 170);

                ctx.textBaseline = 'middle';
                ctx.textAlign = 'left';
                ctx.font = 'bold 54px ui-monospace, Menlo, Consolas, monospace';
                ctx.fillStyle = '#cfdcea';
                ctx.fillText(tag, 24, 52);

                ctx.textAlign = 'right';
                ctx.font = 'bold 66px ui-monospace, Menlo, Consolas, monospace';
                ctx.fillStyle = accent;
                ctx.fillText(String(value), 488, 52);

                ctx.textAlign = 'left';
                ctx.font = '500 40px ui-monospace, Menlo, Consolas, monospace';
                ctx.fillStyle = accent;
                ctx.fillText(word, 24, 128);

                texture.needsUpdate = true;
              };
              return sprite;
            }

            const BAND_LOW    = { word: 'LOW',      accent: '#ffb74d',
                                  face: 0xffa726, glow: 0xb56a00 };
            const BAND_HIGH   = { word: 'HIGH',     accent: '#ffb74d',
                                  face: 0xffa726, glow: 0xb56a00 };
            const BAND_NORMAL = { word: 'NORMAL',   accent: '#5fe39a',
                                  face: 0x2ecc71, glow: 0x0b7a3f };
            const BAND_CRIT   = { word: 'CRITICAL', accent: '#ff6b6b',
                                  face: 0xff3b30, glow: 0xb3120a };
            const BAND_EMPTY  = { word: 'EMPTY',    accent: '#8fa0b3',
                                  face: 0x6b7787, glow: 0x2b3340 };
            const BAND_FULL   = { word: 'FULL',     accent: '#6fc5ff',
                                  face: 0x2196f3, glow: 0x0d47a1 };
            const BAND_GST_OK = { word: 'NORMAL',   accent: '#6fc5ff',
                                  face: 0x2196f3, glow: 0x0d47a1 };

            function hptBand(v, blowout) {
              if (blowout || v >= 150) { return BAND_CRIT; }
              if (v === 0) { return BAND_EMPTY; }
              if (v < 50) { return BAND_LOW; }
              if (v < 100) { return BAND_NORMAL; }
              return BAND_HIGH;
            }

            function gstBand(v) {
              if (v < 50) { return BAND_LOW; }
              if (v < 150) { return BAND_GST_OK; }
              return BAND_FULL;
            }

            // Level, shown on the vessel rather than inside it
            //
            // This used to be a body of liquid modelled inside the shell and
            // clipped at the surface, seen through a transparent wall. It was
            // volumetrically exact and it did not communicate. At a low level
            // the contents became a coloured puck standing on the deck with
            // its own lit outer wall, while the shell above it faded into the
            // dark background -- so the picture said "a tall grey tower, and
            // separately a red tub", and the one comparison that has to be
            // instant, two identical vessels at different levels, was not
            // available at all.
            //
            // The vessel is opaque now and the level is a filled band on its
            // outside, rising from the base the way a bar gauge fills. One
            // silhouette, one object, and the band is the brightest thing on
            // it. The band's height is the fraction of the vessel's volume
            // that is full, so half the pressure is still half the tank --
            // the same promise as before, made in a way that reads across a
            // room.
            const BAND_R = 2.03;      // just clear of the 2.0 shell
            const BAND_H = 8.0;       // the barrel, which spans y = 0 to 8

            function makeLevelBand(colour, emissive) {
              const geometry = new THREE.CylinderGeometry(
                BAND_R, BAND_R, BAND_H, 32, 1, true);
              // Origin at the foot of the band, so scaling y fills upwards
              // instead of growing in both directions from the middle.
              geometry.translate(0, BAND_H / 2, 0);

              const band = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
                color: colour,
                emissive: emissive,
                emissiveIntensity: 0.45,
                metalness: 0.0,
                roughness: 0.55,
                // An open cylinder seen from outside and from inside its own
                // far wall.
                side: THREE.DoubleSide
              }));
              // Its silhouette is the vessel's, which is already drawn.
              band.userData.noOutline = true;

              const group = new THREE.Group();
              group.add(band);
              group.userData.setLevel = function (frac) {
                const f = Math.max(0, Math.min(1, frac));
                // A zero-height cylinder is a degenerate mesh, not an empty
                // tank.
                band.visible = f > 0.002;
                band.scale.y = Math.max(f, 0.0001);
              };
              group.userData.setLevel(0);
              group.userData.setColour = function (face, glow) {
                if (band.material.color.getHex() === face) { return; }
                band.material.color.setHex(face);
                band.material.emissive.setHex(glow);
              };
              return group;
            }

            // GST Tank (left) - Realistic industrial pressure vessel
            const gstGroup = new THREE.Group();
            gstGroup.position.set(-7, 0, 0);

            // Main tank body - painted steel, opaque; the level is a band on it
            const gstBody = new THREE.Mesh(
              new THREE.CylinderGeometry(2, 2, 8, 32),
              new THREE.MeshStandardMaterial({
                // Opaque. A see-through vessel was tried and it cost more
                // than it gave: the wall vanished against a dark backdrop,
                // transparency sorted differently from one camera to the next,
                // and the contents detached from the container. Painted steel
                // reads as one mass, takes the level band cleanly, and sorts
                // like everything else.
                color: 0x8f9bab,
                metalness: 0.15,
                roughness: 0.6,
                envMapIntensity: 0.6
                // No depthWrite: false and no DoubleSide here any more. Both
                // were needed while the shell was a window onto the liquid
                // inside it; on an opaque wall they are the bug that made this
                // vessel keep looking transparent -- a surface that does not
                // write depth cannot hide anything behind it, whatever its
                // opacity says.
              })
            );
            gstBody.position.y = 4;
            gstBody.castShadow = true;
            gstBody.receiveShadow = true;
            gstGroup.add(gstBody);

            // GST liquid
            const gstFill = makeLevelBand(0x2196f3, 0x0d47a1);
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
              color: 0x7c8894,
              metalness: 0.25,
              roughness: 0.55
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
            // Opaque heads over a see-through barrel is what makes the
            // vessel read as a cutaway rather than as a jar: the cut is
            // clearly a cut, because it stops. Matte, because the chrome
            // finish they had was the loudest plastic note in the picture.
            const capMaterial = new THREE.MeshStandardMaterial({
              color: 0x98a3b0,
              metalness: 0.2,
              roughness: 0.55
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
              // Radius 2.06 against a wall of 2.0, so it sits on the vessel
              // like a lit collar. At 2.3 it orbited a third of a metre
              // clear of the steel and read as a hoop thrown over the tank.
              new THREE.TorusGeometry(2.06, 0.1, 8, 32),
              new THREE.MeshStandardMaterial({
                color: 0xff6b00,
                emissive: 0xff6b00,
                emissiveIntensity: 1.0,
                transparent: true,
                opacity: 0.92,
                metalness: 0.2,
                roughness: 0.5
              })
            );
            gstGlowRing.position.y = 7;
            gstGlowRing.rotation.x = Math.PI / 2;
            gstGroup.add(gstGlowRing);

            // GST Label with text
            const gstLabel = makeValuePlate('GST');
            gstLabel.position.set(0, 11.0, 0);
            gstGroup.add(gstLabel);

            scene.add(gstGroup);

            await yieldToBrowser();   // built the GST

            // HPT Tank (right) - Realistic industrial pressure vessel
            const hptGroup = new THREE.Group();
            hptGroup.position.set(7, 0, 0);

            // Main tank body - painted steel, opaque; the level is a band on it
            const hptBody = new THREE.Mesh(
              new THREE.CylinderGeometry(2, 2, 8, 32),
              new THREE.MeshStandardMaterial({
                // Opaque. A see-through vessel was tried and it cost more
                // than it gave: the wall vanished against a dark backdrop,
                // transparency sorted differently from one camera to the next,
                // and the contents detached from the container. Painted steel
                // reads as one mass, takes the level band cleanly, and sorts
                // like everything else.
                color: 0x8f9bab,
                metalness: 0.15,
                roughness: 0.6,
                envMapIntensity: 0.6
                // No depthWrite: false and no DoubleSide here any more. Both
                // were needed while the shell was a window onto the liquid
                // inside it; on an opaque wall they are the bug that made this
                // vessel keep looking transparent -- a surface that does not
                // write depth cannot hide anything behind it, whatever its
                // opacity says.
              })
            );
            hptBody.position.y = 4;
            hptBody.castShadow = true;
            hptBody.receiveShadow = true;
            hptGroup.add(hptBody);

            // HPT liquid
            // HPT's band is a state channel rather than a tag colour, and it
            // is driven from the shared bands above so that the vessel, its
            // plate and the classic view cannot disagree with one another.
            const hptFill = makeLevelBand(BAND_NORMAL.face, BAND_NORMAL.glow);
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
              // Radius 2.06 against a wall of 2.0, so it sits on the vessel
              // like a lit collar. At 2.3 it orbited a third of a metre
              // clear of the steel and read as a hoop thrown over the tank.
              new THREE.TorusGeometry(2.06, 0.1, 8, 32),
              new THREE.MeshStandardMaterial({
                color: 0xff8c42,
                emissive: 0xff8c42,
                emissiveIntensity: 1.0,
                transparent: true,
                opacity: 0.92,
                metalness: 0.2,
                roughness: 0.5
              })
            );
            hptGlowRing.position.y = 7;
            hptGlowRing.rotation.x = Math.PI / 2;
            hptGroup.add(hptGlowRing);

            // HPT Label with text
            const hptLabel = makeValuePlate('HPT');
            hptLabel.position.set(0, 11.0, 0);
            hptGroup.add(hptLabel);

            scene.add(hptGroup);

            await yieldToBrowser();   // built the HPT

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
                color: 0x79838f,
                metalness: 0.3,
                roughness: 0.6,
                // The casing does carry the running state after all.
                //
                // It was taken away last round on the grounds that a lime box
                // is crude, and that was the wrong trade: "is the compressor
                // running" is the one fact a viewer has to catch at overview
                // distance, and a three-pixel lamp cannot say it. A restrained
                // green lift over the whole housing can, and it goes dark the
                // moment the machine stops.
                emissive: 0x2bd46a,
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

            // Point light for status.
            //
            // Saturated green over a four-unit radius threw a hard-edged green
            // patch across the grating that reads as light leaking rather than
            // as a machine indicator. A running compressor gets a lamp, not a
            // floodlight: a softer green, and a reach short enough that the
            // glow stays on the casing around it.
            const compressorLight = new THREE.PointLight(0x66ff99, 0, 1.6);
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

            // Compressor Label with text (custom wider canvas for long text)
            // Create custom sprite with wider canvas
            const compressorCanvas = document.createElement('canvas');
            const compressorContext = compressorCanvas.getContext('2d');
            compressorCanvas.width = 1024; // Wider canvas for longer text
            compressorCanvas.height = 128;

            // Background -- the same treatment as createTextSprite above, which
            // this block predates and has to keep in step with by hand.
            compressorContext.fillStyle = 'rgba(14, 20, 28, 0.88)';
            compressorContext.fillRect(0, 0, compressorCanvas.width, compressorCanvas.height);
            compressorContext.strokeStyle = 'rgba(255, 140, 66, 0.75)';
            compressorContext.lineWidth = 6;
            compressorContext.strokeRect(3, 3, compressorCanvas.width - 6,
                                         compressorCanvas.height - 6);

            // Text
            compressorContext.font = 'bold 74px ui-monospace, Menlo, Consolas, monospace';
            compressorContext.fillStyle = '#ffb070';
            compressorContext.textAlign = 'center';
            compressorContext.textBaseline = 'middle';
            compressorContext.fillText('COMPRESSOR', compressorCanvas.width / 2, compressorCanvas.height / 2);

            const compressorTexture = new THREE.CanvasTexture(compressorCanvas);
            const compressorSpriteMaterial = new THREE.SpriteMaterial({ map: compressorTexture });
            const compressorLabel = new THREE.Sprite(compressorSpriteMaterial);
            compressorLabel.scale.set(5, 1, 1); // Adjusted scale for proper size
            compressorLabel.position.set(0, 3, 0);
            compressorGroup.add(compressorLabel);

            scene.add(compressorGroup);

            await yieldToBrowser();   // built the compressor

            // Pipes with flanges - realistic industrial piping
            const pipeMaterial = new THREE.MeshStandardMaterial({
              color: 0x9095a0,
              metalness: 0.85,
              roughness: 0.4
            });

            // Flow, shown on the pipe that carries it
            //
            // The gas used to be a hundred loose particles drifting in the air
            // beside the pipe. They appeared from nothing along the whole run,
            // sat at one height, and read -- in review -- as confetti rather
            // than as gas. Worse, they said nothing at overview distance,
            // which is the distance this view is normally read from.
            //
            // A band of light travelling along the pipe says the same thing
            // better: it has a direction, it is attached to the thing that is
            // actually flowing, it is legible at any zoom because it is
            // emissive, and it costs one texture and no per-particle work at
            // all. Stopped, the pipe simply goes dark.
            function flowCanvas() {
              const c = document.createElement('canvas');
              // u wraps around the pipe and v runs along it, so anything drawn
              // here is a ring, not an arrow. Chevrons were tried first and
              // came out as corrugation -- the pipe looked like a ribbed hose.
              //
              // A ring can still carry a direction if it is shaped like one: a
              // hard bright leading edge with a tail fading out behind it. Two
              // of them on the run, so they read as discrete pulses travelling
              // rather than as a texture on the pipe.
              c.width = 8; c.height = 128;
              const g = c.getContext('2d');
              g.fillStyle = '#000000';
              g.fillRect(0, 0, 8, 128);
              for (let i = 0; i < 2; i++) {
                const head = i * 64 + 40;      // the sharp edge, leading
                const tail = head - 42;
                const grad = g.createLinearGradient(0, tail, 0, head);
                // Teal, and never white. In review the band peaked brighter
                // than the pipe's own lit edge, which flattened the cylinder
                // and made the run look like a corrugated hose from close up
                // and like a pipe with gaps in it from the overview camera.
                // A hue no metal in this scene wears, at a brightness that
                // stays under the pipe's highlight, reads as something moving
                // through the pipe instead of as part of it.
                grad.addColorStop(0.0, 'rgba(0, 140, 150, 0)');
                grad.addColorStop(0.8, 'rgba(60, 214, 224, 0.62)');
                grad.addColorStop(1.0, 'rgba(130, 240, 245, 1.0)');
                g.fillStyle = grad;
                g.fillRect(0, tail, 8, head - tail);
              }
              return c;
            }

            const flowTexture = new THREE.CanvasTexture(flowCanvas());
            flowTexture.wrapS = flowTexture.wrapT = THREE.RepeatWrapping;
            // One tile over the whole run: two pulses on the pipe at a time.
            flowTexture.repeat.set(1, 1);

            const flowMaterial = new THREE.MeshStandardMaterial({
              color: 0x9095a0,
              metalness: 0.85,
              roughness: 0.4,
              emissive: 0xffffff,
              emissiveMap: flowTexture,
              emissiveIntensity: 0
            });

            const flangeMaterial = new THREE.MeshStandardMaterial({
              color: 0x7a7f8a,
              metalness: 0.9,
              roughness: 0.3
            });

            // Helper function to create flange
            //
            // Ring and bolts are one geometry. Each flange used to be seven
            // meshes -- a ring plus six bolts, each with its own material --
            // and there are eight flanges, so this was fifty-six draw calls
            // spent on bolt heads that are two pixels across at the overview
            // camera. Merged, a flange costs one, and the bolts are still
            // there when you come close.
            const flangeGeometry = (function () {
              const parts = [new THREE.CylinderGeometry(0.25, 0.25, 0.08, 16)];
              for (let i = 0; i < 6; i++) {
                const angle = (Math.PI * 2 / 6) * i;
                const bolt = new THREE.CylinderGeometry(0.02, 0.02, 0.1, 6);
                bolt.translate(Math.cos(angle) * 0.2, 0, Math.sin(angle) * 0.2);
                parts.push(bolt);
              }
              return mergeGeometries(parts);
            })();

            function createFlange(x, y, z, rotation) {
              const flange = new THREE.Mesh(flangeGeometry, flangeMaterial);
              flange.castShadow = true;
              flange.position.set(x, y, z);
              if (rotation) { flange.rotation.z = rotation; }
              return flange;
            }

            // INLET PIPE: GST to Compressor
            const inletPipe = new THREE.Mesh(
              // A little thicker than the other runs: this is the pipe the
              // flow is read off, and at 0.12 the chevrons on it were too few
              // pixels to see from the overview camera.
              new THREE.CylinderGeometry(0.16, 0.16, 3.5, 16),
              flowMaterial
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
              new THREE.CylinderGeometry(0.16, 0.16, 3.5, 16),
              flowMaterial
            );
            outletPipe.position.set(3.25, 1.2, 0.5);
            outletPipe.rotation.z = Math.PI / 2;
            outletPipe.castShadow = true;
            outletPipe.receiveShadow = true;
            scene.add(outletPipe);

            // Flanges on outlet pipe
            scene.add(createFlange(1.5, 1.2, 0.5, Math.PI / 2));
            scene.add(createFlange(5, 1.2, 0.5, Math.PI / 2));

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
            elbowCompOut.position.set(1.5, 1.2, 0.5);
            elbowCompOut.castShadow = true;
            scene.add(elbowCompOut);

            // Elbow at HPT inlet (tank wall)
            const elbowHPT = new THREE.Mesh(
              new THREE.SphereGeometry(0.2, 16, 16),
              elbowMaterial
            );
            elbowHPT.position.set(5, 1.2, 0.5);
            elbowHPT.castShadow = true;
            scene.add(elbowHPT);

            await yieldToBrowser();   // built the pipework

            // Industrial Chimney Stack (beside HPT)
            const chimneyGroup = new THREE.Group();
            chimneyGroup.position.set(11, 0, 0);

            // Chimney base (concrete/brick)
            const chimneyBase = new THREE.Mesh(
              new THREE.CylinderGeometry(1.0, 1.2, 2, 16),
              new THREE.MeshStandardMaterial({
                color: 0x333b44,
                roughness: 0.9,
                metalness: 0.1
              })
            );
            chimneyBase.position.y = 1;
            chimneyBase.castShadow = true;
            chimneyBase.receiveShadow = true;
            chimneyGroup.add(chimneyBase);

            // Main stack (brick/concrete with texture) - Taller
            const chimneyStack = new THREE.Mesh(
              new THREE.CylinderGeometry(0.7, 0.9, 12, 16),
              new THREE.MeshStandardMaterial({
                // Warm enough to separate from the vessels, cool enough to
                // stay in the palette. Brown made it the loudest thing in a
                // cool scene; the grey that replaced it merged with HPT into
                // one mass at overview distance, which was no better.
                color: 0x7a6a5f,
                roughness: 0.75,
                metalness: 0.15
              })
            );
            chimneyStack.position.y = 8;
            chimneyStack.castShadow = true;
            chimneyStack.receiveShadow = true;
            chimneyGroup.add(chimneyStack);

            // Metallic bands (4 reinforcement rings)
            const bandMat = new THREE.MeshStandardMaterial({
              color: 0x666677,
              metalness: 0.9,
              roughness: 0.2
            });

            for(let i = 0; i < 4; i++) {
              const band = new THREE.Mesh(
                new THREE.TorusGeometry(0.75, 0.06, 8, 16),
                bandMat
              );
              band.position.y = 3.5 + i * 2.5;
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
            chimneyTop.position.y = 14.25;
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
            heatGlow.position.y = 14;
            heatGlow.rotation.x = Math.PI / 2;
            chimneyGroup.add(heatGlow);

            scene.add(chimneyGroup);

            // Blowout Pipe: HPT to Chimney
            // The vent run carries the flow band too. During a blowout the
            // gas is going somewhere, and with this line standing still while
            // the flare burned, the picture never drew the cause and effect.
            const ventTexture = new THREE.CanvasTexture(flowCanvas());
            ventTexture.wrapS = ventTexture.wrapT = THREE.RepeatWrapping;
            ventTexture.repeat.set(1, 1);
            const ventMaterial = new THREE.MeshStandardMaterial({
              color: 0x9095a0,
              metalness: 0.85,
              roughness: 0.4,
              emissive: 0xff7a3d,
              emissiveMap: ventTexture,
              emissiveIntensity: 0
            });

            const blowoutPipe = new THREE.Mesh(
              new THREE.CylinderGeometry(0.16, 0.16, 4, 16),
              ventMaterial
            );
            blowoutPipe.position.set(9, 7, 0);
            blowoutPipe.rotation.z = Math.PI / 2;
            blowoutPipe.castShadow = true;
            blowoutPipe.receiveShadow = true;
            scene.add(blowoutPipe);

            // Flanges on blowout pipe
            scene.add(createFlange(7, 7, 0, Math.PI / 2));
            scene.add(createFlange(11, 7, 0, Math.PI / 2));

            // Elbow at HPT blowout (top of tank)
            const elbowHPTBlowout = new THREE.Mesh(
              new THREE.SphereGeometry(0.2, 16, 16),
              elbowMaterial
            );
            elbowHPTBlowout.position.set(7, 7, 0);
            elbowHPTBlowout.castShadow = true;
            scene.add(elbowHPTBlowout);

            // Elbow at Chimney inlet
            const elbowChimneyInlet = new THREE.Mesh(
              new THREE.SphereGeometry(0.2, 16, 16),
              elbowMaterial
            );
            elbowChimneyInlet.position.set(11, 7, 0);
            elbowChimneyInlet.castShadow = true;
            scene.add(elbowChimneyInlet);

            await yieldToBrowser();   // built the chimney

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

            // Add labels for LED panel
            const ledLabel1 = createTextSprite('GST', '#ffffff', '#333333');
            ledLabel1.scale.set(1.25, 0.4, 1);
            ledLabel1.position.set(13.3, 4.2, 0);
            scene.add(ledLabel1);

            const ledLabel2 = createTextSprite('COMP', '#ffffff', '#333333');
            ledLabel2.scale.set(1.25, 0.4, 1);
            ledLabel2.position.set(13.3, 3.6, 0);
            scene.add(ledLabel2);

            const ledLabel3 = createTextSprite('SYSTEM', '#ffffff', '#333333');
            ledLabel3.scale.set(1.25, 0.4, 1);
            ledLabel3.position.set(13.3, 3.0, 0);
            scene.add(ledLabel3);

            const ledLabel4 = createTextSprite('BLOWOUT', '#ffffff', '#333333');
            ledLabel4.scale.set(1.25, 0.4, 1);
            ledLabel4.position.set(13.3, 2.4, 0);
            scene.add(ledLabel4);

            scene.add(ledPanel);

            await yieldToBrowser();   // built the cabinet

            // The gas particle system that stood here is gone. A hundred
            // points drifting beside the pipe were a hundred position updates
            // every frame and, in review, read as confetti; the emissive band
            // travelling along the pipe itself says the same thing at any
            // zoom for one texture and no per-frame work.

            // A point sprite is a square unless it is given a shape, which is
            // why the gas flow rendered as a cloud of hard white cubes. One
            // 32-pixel radial gradient turns every particle in the scene into
            // a soft dot, for one texture.
            const dotCanvas = document.createElement('canvas');
            dotCanvas.width = dotCanvas.height = 32;
            const dotCtx = dotCanvas.getContext('2d');
            const dotGrad = dotCtx.createRadialGradient(16, 16, 0, 16, 16, 16);
            dotGrad.addColorStop(0.0, 'rgba(255,255,255,1)');
            dotGrad.addColorStop(0.4, 'rgba(255,255,255,0.55)');
            dotGrad.addColorStop(1.0, 'rgba(255,255,255,0)');
            dotCtx.fillStyle = dotGrad;
            dotCtx.fillRect(0, 0, 32, 32);
            const dotTexture = new THREE.CanvasTexture(dotCanvas);

            // Flame particle system (from chimney)
            const flameCount = 150;
            const flameParticles = new Float32Array(flameCount * 3);
            const flameColors = new Float32Array(flameCount * 3);
            const flameVelocities = [];

            for(let i = 0; i < flameCount; i++) {
              flameParticles[i * 3] = 11 + (Math.random() - 0.5) * 0.4;
              flameParticles[i * 3 + 1] = 14 + Math.random() * 0.5;
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
              map: dotTexture,
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
            flameLight.position.set(11, 14, 0);
            scene.add(flameLight);

            // Status overlay with glassmorphism design
            const statusOverlay = document.createElement('div');
            statusOverlay.style.cssText = `
              position: absolute;
              bottom: 20px;
              left: 20px;
              background: linear-gradient(135deg, rgba(20, 20, 40, 0.9), rgba(30, 20, 50, 0.8));
              backdrop-filter: blur(10px);
              border: 2px solid rgba(100, 150, 255, 0.3);
              padding: 15px 18px;
              border-radius: 12px;
              color: white;
              font-family: 'Courier New', monospace;
              z-index: 10;
              font-size: 13px;
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
                margin: 0 0 12px 0;
                color: #ff8c42;
                font-size: 18px;
                text-transform: uppercase;
                letter-spacing: 2px;
                border-bottom: 2px solid #ff8c42;
                padding-bottom: 8px;
                text-shadow: 0 0 20px rgba(255, 140, 66, 0.6);
                font-weight: bold;
              ">⚡ System Status</h3>
              <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 15px; line-height: 1.6; text-align: left;">
                <div style="color: #6ab0ff;">● GST Pressure:</div><div class="status-value" style="color: #6ab0ff;"><span id="gst-value">0</span></div>
                <div style="color: #ff6b6b;">● HPT Pressure:</div><div class="status-value" style="color: #ff6b6b;"><span id="hpt-value">0</span></div>
                <div style="color: #aabbcc;">● System Sensor:</div><div class="status-value" style="color: #aabbcc;"><span id="syssen-value">0</span></div>
                <div style="color: #aabbcc;">● Blowout:</div><div class="status-value" style="color: #aabbcc;"><span id="bosen-value">0</span></div>
                <div style="color: #aabbcc;">● Compressor:</div><div class="status-value" style="color: #aabbcc;"><span id="compressor-value">OFF</span></div>
                <div style="color: #aabbcc;">● System Valve:</div><div class="status-value" style="color: #aabbcc;"><span id="systemvalve-value">CLOSED</span></div>
                <div style="color: #aabbcc;">● GST Signal:</div><div class="status-value" style="color: #aabbcc;"><span id="gstsig-value">0</span></div>
                <div style="color: #aabbcc;">● Heartbeat:</div><div class="status-value" style="color: #aabbcc;"><span id="heartbeat-value">0</span></div>
              </div>
            `;
            container.appendChild(statusOverlay);

            // Variables for smooth animations
            let fanRotationSpeed = 0;
            let targetFanSpeed = 0;
            let flameFlicker = 0;
            let flowGlow = 0;
            let ventGlow = 0;
            let compressorRunning = false;
            // Set from /api/state; drives the collars as well as the flame.
            let blowoutActive = false;

            // Fetch live data from server
            async function fetchData() {
              try {
                const response = await fetch('/api/state');
                const data = await response.json();

                // Tank levels.  The sensors report 0-255, and the surface is
                // placed so the volume below it is that fraction of the whole
                // vessel -- heads included.  Half the pressure is half the
                // tank, which is what anyone reading the picture assumes.
                gstFill.userData.setLevel(data.gst / 255);
                hptFill.userData.setLevel(data.hpt / 255);
                const hptState = hptBand(data.hpt, data.boSen > 0);
                const gstState = gstBand(data.gst);
                hptFill.userData.setColour(hptState.face, hptState.glow);
                gstFill.userData.setColour(gstState.face, gstState.glow);
                hptLabel.userData.set(data.hpt, hptState.word, hptState.accent);
                gstLabel.userData.set(data.gst, gstState.word, gstState.accent);

                // Update compressor fan speed and lighting
                targetFanSpeed = data.compressor ? 0.15 : 0;

                // Update compressor status light (realistic)
                const compressorActive = data.compressor > 0;
                compressorBody.material.emissiveIntensity = compressorActive ? 0.55 : 0;
                indicator.material.emissiveIntensity = compressorActive ? 1.5 : 0;
                compressorLight.intensity = compressorActive ? 0.9 : 0;

                // Update particle visibility
                compressorRunning = compressorActive;

                // Update flame system
                blowoutActive = data.boSen > 0;
                flameSystem.visible = blowoutActive;
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
                // An alarm has to be a change of state, not a change of
                // word. ACTIVE and INACTIVE were rendered in the same colour,
                // so the one row that matters looked exactly like the seven
                // that do not.
                const boCell = document.getElementById('bosen-value');
                boCell.textContent = data.boSen > 0 ? 'ACTIVE' : 'INACTIVE';
                boCell.style.color = data.boSen > 0 ? '#ff4d4d' : '#aabbcc';
                boCell.style.fontWeight = data.boSen > 0 ? '700' : '';
                container.classList.toggle('cybics-alarm', data.boSen > 0);
                document.getElementById('compressor-value').textContent = data.compressor > 0 ? 'ON' : 'OFF';
                document.getElementById('systemvalve-value').textContent = data.systemValve ? 'OPEN' : 'CLOSED';
                document.getElementById('gstsig-value').textContent = data.gstSig ? 'HIGH' : 'LOW';
                document.getElementById('heartbeat-value').textContent = data.heartbeat;
              } catch (e) {
                // Silent fail - will retry on next frame
              }
            }

            // A handle for tuning the look without a rebuild.
            //
            // These numbers are a judgement about how a scene should appear and
            // whoever is looking at it is better placed to make it than whoever
            // wrote the defaults.  In the browser console:
            //
            //   CybICS3D.exposure(0.9)      brighter or darker overall
            //   CybICS3D.ambient(0.3)       flatter or more contrasty
            //   CybICS3D.report()           the current values, to paste back
            window.CybICS3D = {
              // The objects themselves, for poking at from the console.  Note
              // that three.js puts render() on the instance rather than on
              // WebGLRenderer.prototype, so patching the prototype to observe
              // frames silently does nothing -- reach them through here.
              scene: scene,
              renderer: renderer,
              camera: camera,
              exposure: v => { renderer.toneMappingExposure = v; },
              ambient: v => { ambientLight.intensity = v; },
              fill: v => { fillLight.intensity = v; },
              accent: v => { accentLight.intensity = v; },
              report: () => ({
                exposure: renderer.toneMappingExposure,
                ambient: ambientLight.intensity,
                fill: fillLight.intensity,
                accent: accentLight.intensity,
              }),

              // Instrumentation for tools/3d/motion.py.
              //
              // Motion cannot be judged from a screenshot, and it cannot be
              // judged from the source either: whether the fan turns at the
              // same rate on a fast machine and a slow one is a question about
              // two numbers taken a known time apart. Nothing below changes
              // what the scene does; it only makes what the scene does
              // measurable from outside.
              motion: () => ({
                t: performance.now(),
                frame: renderer.info.render.frame,
                fan: fanGroup.rotation.z,
                fanSpeed: fanRotationSpeed,
                // gstRing used to be reported here. The rotation it measured
                // was removed on purpose -- it spun a ring about its own axis
                // of symmetry and changed no pixel -- and leaving the probe in
                // place made a deliberate removal look like an animation that
                // had stopped working.
                collarPulse: gstGlowRing.material.emissiveIntensity,
                ventGlow: ventMaterial.emissiveIntensity,
                gstLevel: gstFill.children[0].scale.y,
                hptLevel: hptFill.children[0].scale.y,
                flowOffset: flowTexture.offset.y,
                flowGlow: flowMaterial.emissiveIntensity,
                flame0: flameGeometry.attributes.position.array[1],
                strip: edgeStripMaterial.emissiveIntensity,
                frameCapMs: FRAME_MS
              }),

              // Re-cap the loop, so the same scene can be measured at the rate
              // a weak machine would run it at without needing a weak machine.
              frameCap: ms => { FRAME_MS = ms; },
            };

            await yieldToBrowser();   // built everything that gets an outline

            // ---- Technical outlines --------------------------------------
            //
            // This is what carries the whole look.  Shaded primitives with no
            // edges read as soft lumps at any distance; the same primitives
            // with their silhouettes drawn read as equipment, and they stay
            // readable at the overview camera where a texture never would.
            //
            // Every edge in the scene ends up in one buffer and one
            // LineSegments, so the entire outline pass is a single draw call
            // no matter how many objects it covers.  One LineSegments per mesh
            // would have been two hundred more draw calls for the same image,
            // and this scene is already draw-call bound rather than triangle
            // bound.
            const outlineGroup = (function buildOutlines() {
              scene.updateMatrixWorld(true);
              const points = [];
              const v = new THREE.Vector3();
              const sphere = new THREE.Sphere();

              scene.traverse(node => {
                if (!node.isMesh || node.userData.noOutline) { return; }
                const g = node.geometry;
                if (!g || !g.attributes || !g.attributes.position) { return; }
                // Transparent things are see-through on purpose; drawing their
                // silhouette puts a hard line around something the eye is
                // meant to look past.
                const m = node.material;
                if (m && (m.transparent || m.opacity < 1) &&
                    !node.userData.forceOutline) { return; }
                // Bolts, LED dots and flange studs.  At the scale they occupy
                // on screen their outlines are noise, and there are hundreds.
                if (!g.boundingSphere) { g.computeBoundingSphere(); }
                sphere.copy(g.boundingSphere).applyMatrix4(node.matrixWorld);
                if (sphere.radius < 0.45) { return; }

                // 32 degrees keeps the rim of a cylinder and the horizon of a
                // dome while dropping the latitude rings inside them.
                const edges = new THREE.EdgesGeometry(g, 32);
                const pos = edges.attributes.position;
                for (let i = 0; i < pos.count; i++) {
                  v.fromBufferAttribute(pos, i).applyMatrix4(node.matrixWorld);
                  points.push(v.x, v.y, v.z);
                }
                edges.dispose();
              });

              const geom = new THREE.BufferGeometry();
              geom.setAttribute('position',
                new THREE.Float32BufferAttribute(points, 3));
              const lines = new THREE.LineSegments(geom,
                new THREE.LineBasicMaterial({
                  color: 0xd2e2f2,
                  transparent: true,
                  // At 0.55 the outlines cost frame time and carried none of
                  // the look, which is the worst of both. They either do the
                  // work or they come out.
                  opacity: 0.85,
                  // Outlines have to fade with distance like everything else,
                  // or the far side of the plant comes forward.
                  fog: true,
                  depthWrite: false
                }));
              lines.userData.noOutline = true;
              lines.frustumCulled = false;
              scene.add(lines);
              return lines;
            })();

            // Draw the shadow maps once, now that everything is in the scene.
            renderer.shadowMap.needsUpdate = true;

            // Animation loop
            //
            // Two gates, both of which matter more than any single drawing
            // trick in here.
            //
            // The scene lives in a tab.  Without a visibility check it kept
            // rendering the whole thing at the display's refresh rate while
            // the user was looking at the board photograph on the other tab --
            // all of that work thrown away every frame.
            //
            // And it is capped to 30 fps.  Nothing here moves fast enough to
            // need more: the fan eases, the particles drift, the data behind
            // it arrives twice a second.  Uncapped, this pegged a core hard
            // enough that NiceGUI's client could not answer its own handshake
            // in time and reloaded the page out from under the scene, which is
            // how the 3D tab managed to kill the session it was running in.
            // let, not const: tools/3d/motion.py re-caps this to measure the
            // scene at a slow machine's frame rate.
            let FRAME_MS = 1000 / (softwareRenderer ? 12 : 30);
            let lastFrame = 0;

            function visible() {
              return document.visibilityState === 'visible' && canvas.offsetParent !== null;
            }

            function animate(now) {
              requestAnimationFrame(animate);

              // The first call comes from start-up rather than from rAF, so it
              // arrives without a timestamp; leaving it undefined would poison
              // every later comparison with NaN and the cap would never apply.
              if (now === undefined) { now = performance.now(); }

              if (!visible()) { return; }
              if (now - lastFrame < FRAME_MS) { return; }

              // How much time this frame covers, in seconds.
              //
              // Every moving thing in here used to advance by a fixed amount
              // per frame, which quietly made the whole plant a function of
              // the machine it was running on: measured with tools/3d/motion.py,
              // the fan turned at 3.54 rad/s at the 30 fps cap and 1.50 rad/s
              // at the 12 fps cap the software path uses -- the same plant
              // running at 42 per cent speed on a slower computer.
              //
              // Clamped, because a tab that has been in the background comes
              // back with a gap of however long it was hidden, and without the
              // clamp the first frame after that teleports every particle to
              // the far end of its run.
              // 0.25 s, not 0.1: a frame at the software path's 12 fps cap
              // already covers 83 ms, and a machine struggling below 10 fps
              // would have had time clipped off every single frame -- which
              // showed up as the plant still running 6 per cent slow after the
              // per-frame arithmetic was fixed. A quarter of a second is still
              // far short of a backgrounded tab.
              const dt = Math.min((now - lastFrame) / 1000, 0.25);
              lastFrame = now;

              // The per-frame increments below were written against a loop
              // pinned at 30 fps, so they are quantities per thirtieth of a
              // second. This restates them per second without restating every
              // literal, and it is the one place that old assumption is
              // written down.
              const ticks = dt * 30;

              // Fan.
              //
              // The easing was also per frame -- ten per cent of the remaining
              // difference each time -- so the fan spun up more slowly on a
              // slow machine as well as turning more slowly. An exponential
              // with a time constant settles at the same rate either way; 0.32 s
              // is what the old ten-per-cent-per-frame worked out to at 30 fps.
              fanRotationSpeed += (targetFanSpeed - fanRotationSpeed) *
                                  (1 - Math.exp(-dt / 0.32));
              fanGroup.rotation.z += fanRotationSpeed * ticks;

              // Flow band. Speed is in texture repeats per second, so it is
              // the same on any machine; stopped, the pipe goes dark rather
              // than freezing mid-chevron, which would read as a stalled
              // animation instead of as a stopped compressor.
              // Between the two extremes that have been tried: white enough to
              // blow out the pipe's own shading, and faint enough to vanish at
              // the overview camera, which is the view this is actually read
              // from. Measured peak-to-trough along the pipe was 62 levels when
              // it was too bright and 41 when it was too faint.
              flowGlow += ((compressorRunning ? 1.0 : 0) - flowGlow) *
                          (1 - Math.exp(-dt / 0.25));
              flowMaterial.emissiveIntensity = flowGlow;
              if (compressorRunning) {
                flowTexture.offset.y = (flowTexture.offset.y - dt * 0.55) % 1;
              }

              // The vent. Faster than the process flow, because a relief line
              // is not moving gas at the same leisurely rate as the duty
              // pipework, and the difference is worth seeing.
              ventGlow += ((blowoutActive ? 1.3 : 0) - ventGlow) *
                          (1 - Math.exp(-dt / 0.18));
              ventMaterial.emissiveIntensity = ventGlow;
              if (blowoutActive) {
                ventTexture.offset.y = (ventTexture.offset.y - dt * 1.4) % 1;
              }

              // Animate flames
              if(flameSystem.visible) {
                const flamePos = flameGeometry.attributes.position.array;
                const flameCol = flameGeometry.attributes.color.array;

                for(let i = 0; i < flameCount; i++) {
                  flamePos[i * 3] += flameVelocities[i].x * ticks;
                  flamePos[i * 3 + 1] += flameVelocities[i].y * ticks;
                  flamePos[i * 3 + 2] += flameVelocities[i].z * ticks;

                  flameVelocities[i].life -= 0.015 * ticks;

                  // 16.2, not 17: at the default camera the stack tip leaves only
                  // about forty pixels of headroom, so the plume ran off the top
                  // of the frame -- the most important event in the scene cut off
                  // by the edge of the picture announcing it.
                  if(flameVelocities[i].life <= 0 || flamePos[i * 3 + 1] > 16.2) {
                    flamePos[i * 3] = 11 + (Math.random() - 0.5) * 0.4;
                    flamePos[i * 3 + 1] = 14 + Math.random() * 0.5;
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

                // Flicker on a clock rather than on the frame counter, and with
                // one smoothed random rather than a fresh one every frame --
                // a per-frame random flickers faster on faster machines and
                // reads as noise rather than as fire.
                flameFlicker += (Math.random() - flameFlicker) * (1 - Math.exp(-dt / 0.06));
                flameLight.intensity = 5 + Math.sin(now * 0.012) * 2 + flameFlicker;
              }

              // Status collars.
              //
              // These used to rotate about their own axis of symmetry, which
              // is an animation that cannot be seen: a circle spun about its
              // centre looks exactly like a circle standing still. It cost
              // work every frame and changed no pixel.
              //
              // They also pulsed continuously, which is worse than useless --
              // something blinking all the time teaches the eye to ignore it,
              // so when there is finally something to report the blinking says
              // nothing. They are steady now, and pulse only while the blowout
              // sensor is actually reporting, which is a real signal from the
              // plant rather than decoration.
              const alarmPulse = blowoutActive
                ? 1.6 + Math.sin(now * 0.008) * 0.9
                : 0.85;
              gstGlowRing.material.emissiveIntensity = alarmPulse;
              hptGlowRing.material.emissiveIntensity = alarmPulse;
              const collar = blowoutActive ? 0xff3b30 : 0xff6b00;
              if (gstGlowRing.material.emissive.getHex() !== collar) {
                gstGlowRing.material.emissive.setHex(collar);
                gstGlowRing.material.color.setHex(collar);
                hptGlowRing.material.emissive.setHex(collar);
                hptGlowRing.material.color.setHex(collar);
              }

              // The platform edge strips are steady. A painted safety line
              // does not breathe, and this one was pulsing in the corner of
              // every frame for no reason at all.
              edgeStripMaterial.emissiveIntensity = 1.2;

              // Update orbit controls
              controls.update();

              renderer.render(scene, camera);
            }

            // Fetch data every 500ms
            setInterval(fetchData, 500);
            fetchData();

            // Handle resize
            //
            // Watching the container rather than the window: it also changes
            // when the tab is switched to, when the browser chrome grows or
            // shrinks, and when the page is zoomed, none of which fire a
            // window resize.  Without this the canvas kept whatever size it
            // had when the scene was built and left a dead band around itself.
            // Frame the plant, rather than hoping a hand-set camera fits it.
            //
            // The camera used to sit at a fixed point chosen by eye, and the
            // plant filled about a third of the canvas with the right-hand
            // third empty. Every attempt to move it in by hand clipped the top
            // of the stack instead, because the scene is both wide and tall and
            // the trade between the two depends on the window's aspect ratio --
            // which is not knowable when the number is typed into the source.
            //
            // So the scene measures itself. The bounding box of the equipment
            // is fitted to whichever of width or height is the binding
            // constraint, from a fixed three-quarter direction, and it is
            // recomputed whenever the container changes size. The plant fills
            // the frame at any window shape, and the stack stops being cut off.
            const FRAME_DIRECTION = new THREE.Vector3(0.02, 0.36, 1).normalize();
            const FRAME_MARGIN = 1.12;
            const plantBox = new THREE.Box3();
            const plantCentre = new THREE.Vector3();
            const plantSize = new THREE.Vector3();

            function measurePlant() {
              plantBox.makeEmpty();
              scene.traverse(node => {
                // The sky dome is 180 units across and the ground is 300; both
                // would swallow the box and put the camera in the next county.
                if (!node.isMesh || node.userData.noFrame) { return; }
                plantBox.expandByObject(node);
              });
              plantBox.getCenter(plantCentre);
              plantBox.getSize(plantSize);
            }

            // Where the corners of the plant land on screen, in normalised
            // device coordinates: 1 means exactly at the edge of the frame.
            const frameCorner = new THREE.Vector3();
            function worstCorner() {
              let worst = 0;
              for (let i = 0; i < 8; i++) {
                frameCorner.set(
                  (i & 1) ? plantBox.max.x : plantBox.min.x,
                  (i & 2) ? plantBox.max.y : plantBox.min.y,
                  (i & 4) ? plantBox.max.z : plantBox.min.z);
                frameCorner.project(camera);
                worst = Math.max(worst, Math.abs(frameCorner.x),
                                        Math.abs(frameCorner.y));
              }
              return worst;
            }

            function frameCamera() {
              if (plantBox.isEmpty()) { return; }
              // The analytic distance is only a starting point. It measures to
              // the centre of the box, while the near face stands several units
              // closer, and the camera looks down rather than straight on -- so
              // on its own it framed the plant far too tight and cut the stack
              // off at the top. Project the eight corners and pull back until
              // they all fit, which is exact and does not care about the shape
              // of the box or the angle it is seen from.
              const halfFov = THREE.MathUtils.degToRad(camera.fov) / 2;
              let dist = Math.max(
                (plantSize.y / 2) / Math.tan(halfFov),
                (plantSize.x / 2) / (Math.tan(halfFov) * camera.aspect));

              for (let pass = 0; pass < 6; pass++) {
                camera.position.copy(plantCentre)
                      .addScaledVector(FRAME_DIRECTION, dist);
                camera.lookAt(plantCentre);
                camera.updateMatrixWorld(true);
                camera.updateProjectionMatrix();
                const worst = worstCorner();
                if (!isFinite(worst) || worst <= 0) { break; }
                const wanted = dist * worst * FRAME_MARGIN;
                if (Math.abs(wanted - dist) < 0.05) { break; }
                dist = wanted;
              }
              controls.target.copy(plantCentre);
              controls.update();
            }

            function fitToContainer() {
              const w = container.clientWidth, h = container.clientHeight;
              if (!w || !h) { return; }
              camera.aspect = w / h;
              camera.updateProjectionMatrix();
              renderer.setSize(w, h, false);
              frameCamera();
              renderer.shadowMap.needsUpdate = true;
            }

            if (window.ResizeObserver) {
              new ResizeObserver(fitToContainer).observe(container);
            }
            window.addEventListener('resize', fitToContainer);
            measurePlant();
            fitToContainer();

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
