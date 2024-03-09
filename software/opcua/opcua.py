#!/usr/bin/env python3

import asyncio
import logging

from asyncua import Server, ua
from pymodbus.client import ModbusTcpClient

async def main():
    _logger = logging.getLogger(__name__)

    # Connect to OpenPLC
    client = ModbusTcpClient(host="openplc",port=502)  # Create client object
    client.connect() # connect to device, reconnect automatically

    # setup the cybics opcua our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # set up the namespace
    uri = "http://opcua.cybics.github.io"
    idx = await server.register_namespace(uri)
    server.set_server_name("CybICS")

    # populating the cybics address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    gstvar = await myobj.add_variable(idx, "GST", ua.UInt16(0))
    hptvar = await myobj.add_variable(idx, "HPT", ua.UInt16(0))
    systemSenvar = await myobj.add_variable(idx, "systemSen", ua.UInt16(0))
    boSenvar = await myobj.add_variable(idx, "boSen", ua.UInt16(0))
    stopvar = await myobj.add_variable(idx, "stop", ua.UInt16(0))
    manualvar = await myobj.add_variable(idx, "manual", ua.UInt16(0))
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),
        ua.QualifiedName("ServerMethod", idx),
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )
    _logger.info("Starting server!")
    async with server:
        while True:
            # read GST and HPT to the OpenPLC
            _logger.info("Reading from modbus")
            gst = client.read_holding_registers(1124)
            hpt = client.read_holding_registers(1126)
            systemSen = client.read_holding_registers(2)
            boSen = client.read_holding_registers(3)
            stop = client.read_holding_registers(1129)
            manual = client.read_holding_registers(1131)
            await gstvar.write_value(ua.UInt16(gst.registers[0]))
            await hptvar.write_value(ua.UInt16(hpt.registers[0]))
            await systemSenvar.write_value(ua.UInt16(systemSen.registers[0]))
            await boSenvar.write_value(ua.UInt16(boSen.registers[0]))
            await stopvar.write_value(ua.UInt16(stop.registers[0]))
            await manualvar.write_value(ua.UInt16(manual.registers[0]))
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)