#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  historianFlask.py
#  


'''
	Flask Web Server historian Data  
'''
import sqlite3
import random
import logging
import sys
import json
import time
from datetime import datetime
from typing import Iterator
from pymodbus.client import ModbusTcpClient

from flask import Flask, Response, render_template, request, stream_with_context


logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
random.seed()  # Initialize the random number generator



# Retrieve data from database
def getData():
    client = ModbusTcpClient(host="192.168.178.141",port=502)   # Create client object
    client.connect()                           # connect to device, reconnect automatically
    reading_time = datetime.now()

    request = client.read_holding_registers(1124,1)
    gst = request.registers[0]
    logger.info("GST: " + str(gst))
    request = client.read_holding_registers(1125,1)
    hpt = request.registers[0]
    logger.info("HPT: " + str(hpt))

    return reading_time, gst, hpt

# main route 
@app.route("/")
def index():
	return render_template('index.html')

def generate_random_data() -> Iterator[str]:
    """
    Generates random value between 0 and 100

    :return: String containing current timestamp (YYYY-mm-dd HH:MM:SS) and randomly generated data.
    """
    if request.headers.getlist("X-Forwarded-For"):
        client_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        client_ip = request.remote_addr or ""

    try:
        logger.info("Client %s connected", client_ip)
        while True:
            timeEvent, gst, hpt = getData()
            #timeEvent = datetime.strptime(timeEvent,"%Y-%m-%d %H:%M:%S.%f")
            json_data = json.dumps(
                {                    
                    "time": timeEvent.strftime("%Y-%m-%d %H:%M:%S"),
                    "gst": gst,
                    "hpt": hpt,
                }
            )
            yield f"data:{json_data}\n\n"
            logger.info(json_data)
            time.sleep(1)
    except GeneratorExit:
        logger.info("Client %s disconnected", client_ip)


@app.route("/chart-data")
def chart_data() -> Response:
    response = Response(stream_with_context(generate_random_data()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=False)