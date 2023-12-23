import sqlite3
import time
import os
from pymodbus.client import ModbusTcpClient

path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
db_path = os.path.join(path, "historian.sqlite")
conn = None

def get_db():
    conn = sqlite3.connect(db_path)
    return conn

def close_db():
    conn.close()

def reset_db():
    db = get_db()
    db.execute('DROP TABLE IF EXISTS readings')
    db.commit()

    db.execute("CREATE TABLE IF NOT EXISTS readings(time DATETIME, type TEXT, value REAL)")

    db.commit()

db = get_db()
reset_db()

# Main loop to read each sensor and save the readings in the database.
print('Saving sensor data every two seconds (press Ctrl-C to quit)...')
while True:
    # Save the current unix time for this measurement.
    reading_time = int(time.time())
    client = ModbusTcpClient(host="192.168.178.141",port=502)   # Create client object
    client.connect()                           # connect to device, reconnect automatically
    request = client.read_holding_registers(1124,1)
    gst = request.registers
    print("GST: " + str(gst[0]))
    request = client.read_holding_registers(1125,1)
    hpt = request.registers
    print("HPT: " + str(hpt[0]))

    # Save the reading in the readings table.
    db.execute('INSERT INTO readings VALUES (?, ?, ?)',
             (reading_time, "GST", int(gst[0])))
    db.execute('INSERT INTO readings VALUES (?, ?, ?)',
             (reading_time, "HPT", int(hpt[0])))
    db.commit()
    time.sleep(2.0)
