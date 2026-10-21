#!/usr/bin/env python3

import asyncio
import logging
import socket
import user_manager

from datetime import datetime, timezone

from pathlib import Path
from asyncua import Server, ua
from asyncua.common.utils import ServiceError
from asyncua.crypto.permission_rules import SimpleRoleRuleset
from asyncua.crypto.cert_gen import setup_self_signed_certificate
from asyncua.crypto.validator import CertificateValidator, CertificateValidatorOptions
from cryptography.x509.oid import ExtendedKeyUsageOID
from asyncua.crypto.truststore import TrustStore
from pymodbus.client import ModbusTcpClient

#Trust Store is feature for GDS-Certificate support
USE_TRUST_STORE = False

# Built by the Dockerfile; asyncua creates it on first start if it is missing.
ADDRESS_SPACE_SHELF = Path(__file__).parent / "address_space.shelf"


async def validate_client_certificate(cert, app_description):
    """Accept any client certificate that is within its validity period.

    asyncua's CertificateValidator reads the SubjectAlternativeName extension
    even when none of the selected options uses it, and answers
    BadCertificateInvalid when it is missing.  The admin certificate the opcua
    challenge leaks has no SAN, so the server rejected the very certificate the
    challenge is about, over every security policy.  Which certificate gets
    admin rights is decided by the user manager, by comparing it with the
    registered one; this only keeps the time check.
    """
    now = datetime.now(timezone.utc)
    if not cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
        raise ServiceError(ua.StatusCodes.BadCertificateTimeInvalid)

async def main():
    # Wait for OpenPLC to start
    await asyncio.sleep(5)

    # Define Path for self-signed server certificate used by secure channel
    cert_base = Path(__file__).parent
    server_cert = Path(cert_base / "certificates/server-certificate-example.der")
    server_private_key = Path(cert_base / "certificates/server-private-key-example.pem")

    # Define Hostname and URI of OPC UA Server
    host_name = socket.gethostname()
    server_app_uri = f"urn:opcua:python:server"

    # Define user manager and register certificate with user role admin
    cert_user_manager = user_manager.Pw_Cert_UserManager()
    await cert_user_manager.add_admin("certificates/trusted/cert_admin.der", name='test_admin')

    # Connect to OpenPLC
    client = ModbusTcpClient(host="openplc",port=502)  # Create client object
    client.connect() # connect to device, reconnect automatically

    # setup the cybics opcua our server
    server = Server(user_manager=cert_user_manager)
    # The standard address space comes from a shelf built into the image, so
    # nodes are only unpickled when a client touches them. Filling it from code
    # held ~45 MB more RSS, most of it swapped out on a 512 MB board.
    await server.init(ADDRESS_SPACE_SHELF)
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    await server.set_application_uri(server_app_uri)

    # set up the namespace
    uri = "http://opcua.cybics.github.io"
    idx = await server.register_namespace(uri)
    server.set_server_name("CybICS")

    # Set authentication modes and security modes/policies
    # Reduced security policies to save memory on constrained devices
    server.set_security_IDs(["Anonymous", "Basic256Sha256", "Username"])
    server.set_security_policy(
        [
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
        ],
        permission_ruleset=SimpleRoleRuleset()
    )

    # Generate its own self-signed certificate,
    # It will renew also when the valid datetime range is out of range (on startup, no on runtime)
    await setup_self_signed_certificate(server_private_key,
                                        server_cert,
                                        server_app_uri,
                                        host_name,
                                        [ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH],
                                        {
                                            'countryName': 'CN',
                                            'stateOrProvinceName': 'AState',
                                            'localityName': 'Foo',
                                            'organizationName': "Bar Ltd",
                                        })

    # load server certificate and private key for secure channel communication. 
    await server.load_certificate(str(server_cert))
    await server.load_private_key(str(server_private_key))

    # validate used certificate
    if USE_TRUST_STORE:
        trust_store = TrustStore([Path(cert_base / "certificates/trusted/")], [])
        await trust_store.load()
        validator = CertificateValidator(options=CertificateValidatorOptions.TRUSTED_VALIDATION | CertificateValidatorOptions.PEER_CLIENT,
                                         trust_store = trust_store)
    else:
        validator = validate_client_certificate
    server.set_certificate_validator(validator)

    # populating the cybics address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, "CybICS Variables")
    gstvar = await myobj.add_variable(idx, "GST", ua.UInt16(0))
    hptvar = await myobj.add_variable(idx, "HPT", ua.UInt16(0))
    systemSenvar = await myobj.add_variable(idx, "systemSen", ua.UInt16(0))
    boSenvar = await myobj.add_variable(idx, "boSen", ua.UInt16(0))
    stopvar = await myobj.add_variable(idx, "STOP", ua.UInt16(0))
    manualvar = await myobj.add_variable(idx, "manual", ua.UInt16(0))
    userflag = await myobj.add_variable(idx, "userFLAG", "CybICS(OPC-UA)")
    obtain_flag = await myobj.add_variable(idx, "Set > 0 to obtain flag!", ua.UInt16(0))
    adminflag = await myobj.add_variable(idx, "adminFLAG", "")
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),
        ua.QualifiedName("ServerMethod", idx),
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )
    async with server:
        while True:
            # read GST and HPT from OpenPLC via Modbus
            try:
                gst = client.read_holding_registers(1124)
                hpt = client.read_holding_registers(1126)
                systemSen = client.read_holding_registers(1132)
                boSen = client.read_holding_registers(1134)
                stop = client.read_holding_registers(1128)
                manual = client.read_holding_registers(1130)
            except Exception as e:
              logging.error("Read from OpenPLC failed - " + str(e))
              # Keep serving the last values until OpenPLC answers again;
              # falling through crashed on the unbound registers and put the
              # container in a restart loop whenever Modbus was not up yet.
              await asyncio.sleep(2)
              continue
            await gstvar.write_value(ua.UInt16(gst.registers[0]))
            await hptvar.write_value(ua.UInt16(hpt.registers[0]))
            await systemSenvar.write_value(ua.UInt16(systemSen.registers[0]))
            await boSenvar.write_value(ua.UInt16(boSen.registers[0]))
            await stopvar.write_value(ua.UInt16(stop.registers[0]))
            await manualvar.write_value(ua.UInt16(manual.registers[0]))
            if await obtain_flag.get_value() >  0:
                await adminflag.write_value("CybICS(OPC-UA-$ADMIN)")
            else: 
                await adminflag.write_value("set the correct variable > 0")
            await asyncio.sleep(2)  # Reduced polling frequency to lower I/O


if __name__ == "__main__":
    # Suppress verbose logging from asyncua and dependencies to reduce I/O
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("pymodbus").setLevel(logging.WARNING)
    asyncio.run(main())
