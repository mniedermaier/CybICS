import time 
from pymodbus.client import ModbusTcpClient

hpt = 10

client = ModbusTcpClient(host="192.168.178.141",port=502)   # Create client object
client.connect()                 # connect to device, reconnect automatically
    
while True:
    print("Setting HPT to " + str(hpt))


    client.write_registers(1126,hpt) #(register, value, unit)  
  
    time.sleep(0.01)
    
client.close()                             # Disconnect device
