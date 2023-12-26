# i2ctest.py
# A brief demonstration of the Raspberry Pi I2C interface, using the Sparkfun
# Pi Wedge breakout board and a SparkFun MCP4725 breakout board:
# https://www.sparkfun.com/products/8736

import smbus
import time 
import netifaces as ni
from pymodbus.client import ModbusTcpClient

# I2C channel 1 is connected to the GPIO pins
channel = 1

#  MCP4725 defaults to address 0x60
address = 0x20


# Initialize I2C (SMBus)
bus = smbus.SMBus(channel)

gst = 0
hpt = 0

while True:
  ip = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
  print(ip)
  print(list(ip))

  listIp = list(ip)
  listIp = ['I', 'P',':'] + listIp
  for row in range(len(listIp)):
    listIp[row] = ord(listIp[row])
  print(listIp)
  bus.write_i2c_block_data(address, 0x00, listIp)

  # Create a sawtooth wave 16 times
  data = bus.read_i2c_block_data(address, 0x00, 20)
  print(data)
  for row in range(len(data)):
    data[row] = chr(data[row])
  print(data)

  if(str(data[0]) == "G" and str(data[1]) == "S" and str(data[2]) == "T"):
    gst = int(str(data[5] + data[6] + data[7]))
    hpt = int(str(data[14] + data[15] + data[16]))

    print("Setting GST to " + str(gst) + " and HPT to " + str(hpt))
    client = ModbusTcpClient(host="127.0.0.1",port=502)   # Create client object
    client.connect()                           # connect to device, reconnect automatically
    client.write_registers(1124,gst) #(register, value, unit)
    client.write_registers(1126,hpt) #(register, value, unit)

    client.close()                             # Disconnect device
  
  
  time.sleep(0.01)

