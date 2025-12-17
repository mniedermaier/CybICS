#!/usr/bin/env python3

# hardwareIO.py
#
# This script reads i2c sensor values from the STM32
# and writes these values to the OpenPLC registers.
# Additionally, the IP address of wlan0 will be transferred
# to the STM32, to show it in the display

try:
    import smbus
except ImportError:
    import smbus2 as smbus
import time 
from pymodbus.client import ModbusTcpClient
import nmcli
import RPi.GPIO as GPIO
import logging
import threading

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

listIp = [] # IP of the raspberry pi

id = "unknown" # ID of the STM32
data = [] # Data received over i2c from the STM32
dataID = [] # dataID received over i2c from the STM32

# thread for openplc communication
def thread_openplc():
  attempts = 0
  consecutive_failures = 0
  MAX_FAILURES = 10

  # Connect to OpenPLC
  client = ModbusTcpClient(host="openplc",port=502)  # Create client object

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

  logging.info("Entering while true in OpenPLC thread")
  while True:
    global gst
    global hpt
    global flag

    # Ensure connection to OpenPLC
    if not client.connected:
      try:
        client.connect()
        if client.connected:
          logging.info("Successfully reconnected to OpenPLC")
          consecutive_failures = 0
      except Exception as e:
        consecutive_failures += 1
        if consecutive_failures % 50 == 0:  # Log every 50 failures to avoid spam
          logging.warning(f"Cannot connect to OpenPLC - {str(e)} (Attempt {consecutive_failures})")
        time.sleep(0.1)
        continue  # Skip this cycle

    try:
      # write GST and HPT to the OpenPLC
      client.write_register(1124,gst) #
      client.write_register(1126,hpt) #
      flag = [17273, 25161, 17235, 10349, 12388, 25205, 9257]
      client.write_registers(1200,flag) #
      # Reset failure counter on successful write
      consecutive_failures = 0
    except Exception as e:
      consecutive_failures += 1
      logging.error(f"Write to OpenPLC (GST|HPT|FLAG) failed - {str(e)} (Failure {consecutive_failures}/{MAX_FAILURES})")
      
      if consecutive_failures >= MAX_FAILURES:
        logging.warning("Maximum consecutive failures reached. Attempting to reconnect to OpenPLC...")
        try:
          client.close()
          client.connect()
          consecutive_failures = 0
          logging.info("Successfully reconnected to OpenPLC")
        except Exception as reconnect_error:
          logging.error(f"Failed to reconnect to OpenPLC - {str(reconnect_error)}")

    # read coils from OpenPLC
    try:
      plcCoils=client.read_coils(0,count=4, device_id=1)
      GPIO.output(4, plcCoils.bits[0])   # heartbeat
      GPIO.output(8, plcCoils.bits[1])   # compressor
      GPIO.output(7, plcCoils.bits[2])   # systemValve
      GPIO.output(20, plcCoils.bits[3])  # gstSig
      # Reset failure counter on successful read
      consecutive_failures = 0
    except Exception as e:
      consecutive_failures += 1
      logging.error(f"Read from OpenPLC failed - {str(e)} (Failure {consecutive_failures}/{MAX_FAILURES})")
      
      if consecutive_failures >= MAX_FAILURES:
        logging.warning("Maximum consecutive failures reached. Attempting to reconnect to OpenPLC...")
        try:
          client.close()
          client.connect()
          consecutive_failures = 0
          logging.info("Successfully reconnected to OpenPLC")
        except Exception as reconnect_error:
          logging.error(f"Failed to reconnect to OpenPLC - {str(reconnect_error)}")

    # write input register to OpenPLC
    try:
      client.write_register(1132,GPIO.input(1))  # System sensor
      client.write_register(1134,GPIO.input(12)) # BO sensor
      # Reset failure counter on successful write
      consecutive_failures = 0
    except Exception as e:
      consecutive_failures += 1
      logging.error(f"Write to OpenPLC failed - {str(e)} (Failure {consecutive_failures}/{MAX_FAILURES})")
      
      if consecutive_failures >= MAX_FAILURES:
        logging.warning("Maximum consecutive failures reached. Attempting to reconnect to OpenPLC...")
        try:
          client.close()
          client.connect()
          consecutive_failures = 0
          logging.info("Successfully reconnected to OpenPLC")
        except Exception as reconnect_error:
          logging.error(f"Failed to reconnect to OpenPLC - {str(reconnect_error)}")

    time.sleep(0.02) # OpenPLC has a Cycle time of 50ms

  # Should never be reached
  client.close() # Disconnect device

# thread for network connection
def thread_network():
  global dataID
  global ssid
  global id
  global listIp

  # Getting current connection
  try:
    current_connection = ""
    nmcli.disable_use_sudo()
    for conn in nmcli.connection():
      if conn.device == 'wlan0':
        current_connection = conn.name
        break
  except Exception as e:
    logging.error("Error getting current connection... " + str(e))

  # Detect the Station mode connection (any WiFi connection that isn't 'cybics')
  # This handles different naming conventions (e.g., 'preconfigured', 'netplan-*', etc.)
  station_connection = None
  try:
    for conn in nmcli.connection():
      # Find a WiFi connection that isn't the 'cybics' AP
      if conn.conn_type == 'wifi' and conn.name != 'cybics':
        station_connection = conn.name
        logging.info(f"Detected Station mode connection: {station_connection}")
        break
    if station_connection is None:
      logging.warning("No Station mode WiFi connection found (only 'cybics' AP exists)")
  except Exception as e:
    logging.error(f"Error detecting Station mode connection: {str(e)}")

  try:
    current_ssid = nmcli.connection.show('cybics')["802-11-wireless.ssid"]
    logging.info(f"Current connection: {current_connection}, ap ssid: {current_ssid}")
  except Exception as e:
    logging.error("No current connection " + str(e))

  logging.info("Entering while true in network thread")
  while True:
    try:
      # Get IP address of wlan0
      ip = nmcli.device.show('wlan0').get('IP4.ADDRESS[1]', "unknown")
      ip = ip.split('/')[0] # remove the network CIDR suffix
      listIp = list(ip) + ['\0']  # Add null terminator for STM32 strlen()

      

    except Exception as e:
      logging.error("Error in getting IP of wlan0 - " + str(e))

    # Simple check, if correct dataID was received
    if dataID[12] in ['0', '1']:
      ssid = f"cybics-{id}"
      if current_ssid != ssid:
        try:
          logging.info(f"Configure ssid {ssid}")
          nmcli.connection.modify('cybics', {'wifi.ssid': ssid})
          current_ssid = ssid
        except Exception as e:
          logging.error("Configure ssid failed - " + str(e))
          time.sleep(1)

    connection = 'cybics' if dataID[12] == '1' else station_connection
    if connection and current_connection != connection:
      try:
        logging.info(f"Enable connection {connection}")
        nmcli.connection.up(connection, 0) # do not wait for connection
        logging.info(f"Enable connection - " + str(nmcli.connection.show(connection)))
        current_connection = connection
      except Exception as e:
        logging.error("Enable connection failed - " + str(e))
        time.sleep(1)
    elif not connection and dataID[12] != '1':
      logging.warning("Cannot switch to Station mode: no Station connection detected")
    
    logging.debug("End of while true thread_network")
    time.sleep(1)

# thread for i2c communication
def thread_i2c():
  global gst
  global hpt
  global flag
  global id
  global data
  global dataID
  global listIp
  global bus

  logging.info("Entering while true in i2c thread")
  while True:
    try:
      # Read the values for GST and HPT
      data = bus.read_i2c_block_data(address, 0x00, 20)
      # print(data)
      for row in range(len(data)):
        data[row] = chr(data[row])
      logging.debug("Read over i2c: " + str(data))

      # Format the IP and send it via i2c to the RPI
      sendIP = ['I', 'P',':'] + listIp
      for row in range(len(sendIP)):
        sendIP[row] = ord(sendIP[row])
      bus.write_i2c_block_data(address, 0x00, sendIP)

      # Simple check, if correct data was received
      if(str(data[0]) == "G" and str(data[1]) == "S" and str(data[2]) == "T"):
        gst = int(str(data[5] + data[6] + data[7]))
        hpt = int(str(data[14] + data[15] + data[16]))

      logging.debug(f"Setting GST to {str(gst)} and HPT to {str(hpt)}")

      # Read STM32 ID Code
      data = bus.read_i2c_block_data(address, 0x01, 13)
      for c in range(len(data)):
        data[c] = chr(data[c])
      #id=str(c-"a" for c in id)
      data="".join(data)
      dataID=data
      id = data[:12]

      time.sleep(0.02) # OpenPLC has a Cycle time of 50ms

    except Exception as e:
      logging.error("Error in read i2c - retrying in 1 sec: " + str(e))
      time.sleep(1)


# main function
if __name__ == "__main__":
  format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
  logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
  
  try:
    logging.info("Main    : before creating threads")
    openplcX = threading.Thread(target=thread_openplc, args=())
    i2cX = threading.Thread(target=thread_i2c, args=())
    networkX = threading.Thread(target=thread_network, args=())
    logging.info("Main    : before running threads")
    openplcX.start()
    i2cX.start()
    networkX.start()
    logging.info("Main    : after starting threads")

    # Continuously check if threads are active
    while openplcX.is_alive() or i2cX.is_alive() or networkX.is_alive():
      logging.info(f"Main    : openplcX is {'alive' if openplcX.is_alive() else 'not alive'}")
      logging.info(f"Main    : i2cX is {'alive' if i2cX.is_alive() else 'not alive'}")
      logging.info(f"Main    : networkX is {'alive' if networkX.is_alive() else 'not alive'}")
      time.sleep(30)  # Check every 30 second

  except KeyboardInterrupt:
    logging.info("Main    : Received keyboard interrupt, shutting down...")
  except Exception as e:
    logging.error(f"Main    : Unexpected error: {str(e)}")
  finally:
    logging.info("Main    : Cleaning up GPIO...")
    GPIO.cleanup()
    logging.info("Main    : GPIO cleanup complete")