#!/usr/bin/env python3

import asyncio
import logging
import socket
import user_manager

from pathlib import Path
from asyncua import Server, ua
from asyncua.crypto.permission_rules import SimpleRoleRuleset
from asyncua.crypto.cert_gen import setup_self_signed_certificate
from asyncua.crypto.validator import CertificateValidator, CertificateValidatorOptions
from cryptography.x509.oid import ExtendedKeyUsageOID
from asyncua.crypto.truststore import TrustStore
from pymodbus.client import ModbusTcpClient

#Trust Store is feature for GDS-Certificate support
USE_TRUST_STORE = False

async def main():
    _logger = logging.getLogger(__name__)
    _logger.info("Wait 5s that openplc can start")
    await asyncio.sleep(5) # wait that openplc is up and running

    # Define Path for self-signed server certificate used by secure channel
    cert_base = Path(__file__).parent
    server_cert = Path(cert_base / "certificates/server-certificate-example.der")
    server_private_key = Path(cert_base / "certificates/server-private-key-example.pem")

    # Define Hostname and URI of OPC UA Server
    host_name = socket.gethostname()
    server_app_uri = f"urn:opcua:python:server"

    # Define user manager and register certificate with user role admin
    cert_user_manager = user_manager.Pw_Cert_UserManager()
    try:
        await cert_user_manager.add_admin("certificates/trusted/cert_admin.der", name='test_admin')
        _logger.info("Successfully loaded admin certificate: test_admin from certificates/trusted/cert_admin.der")
    except Exception as e:
        _logger.error(f"Failed to load admin certificate: {e}")
        raise

    # Connect to OpenPLC
    client = ModbusTcpClient(host="openplc",port=502)  # Create client object
    client.connect() # connect to device, reconnect automatically

    # setup the cybics opcua our server
    server = Server(user_manager=cert_user_manager)
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    await server.set_application_uri(server_app_uri)

    # set up the namespace
    uri = "http://opcua.cybics.github.io"
    idx = await server.register_namespace(uri)
    server.set_server_name("CybICS")

    # Set authentication modes and security modes/policies
    server.set_security_IDs(["Anonymous", "Basic256Sha256", "Username"])
    server.set_security_policy(
        [
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic128Rsa15_Sign,
            ua.SecurityPolicyType.Basic128Rsa15_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256_Sign,
            ua.SecurityPolicyType.Basic256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Aes128Sha256RsaOaep_Sign,
            ua.SecurityPolicyType.Aes128Sha256RsaOaep_SignAndEncrypt,
            ua.SecurityPolicyType.Aes256Sha256RsaPss_Sign,
            ua.SecurityPolicyType.Aes256Sha256RsaPss_SignAndEncrypt,
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
        # Use PEER_CLIENT only (removed EXT_VALIDATION to support certificates without Extended Key Usage)
        # This allows certificate-based user authentication to work in various environments
        validator = CertificateValidator(options=CertificateValidatorOptions.PEER_CLIENT)
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
    userflag = await myobj.add_variable(idx, "userFLAG", "CybICS(0PC-UA)")
    obtain_flag = await myobj.add_variable(idx, "Set > 0 to obtain flag!", ua.UInt16(0))
    adminflag = await myobj.add_variable(idx, "adminFLAG", "")
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),
        ua.QualifiedName("ServerMethod", idx),
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )
    _logger.info("Starting server!")
    async with server:
        _logger.info("Starting while True")
        while True:
            # read GST and HPT to the OpenPLC
            # Check if flag var is set and display flag
            _logger.info("Reading from modbus")
            try:
                gst = client.read_holding_registers(1124)
                hpt = client.read_holding_registers(1126)
                systemSen = client.read_holding_registers(2)
                boSen = client.read_holding_registers(3)
                stop = client.read_holding_registers(1129)
                manual = client.read_holding_registers(1131)
            except Exception as e:
              logging.error("Read from OpenPLC failed - " + str(e))
            await gstvar.write_value(ua.UInt16(gst.registers[0]))
            await hptvar.write_value(ua.UInt16(hpt.registers[0]))
            await systemSenvar.write_value(ua.UInt16(systemSen.registers[0]))
            await boSenvar.write_value(ua.UInt16(boSen.registers[0]))
            await stopvar.write_value(ua.UInt16(stop.registers[0]))
            await manualvar.write_value(ua.UInt16(manual.registers[0]))
            if await obtain_flag.get_value() >  0:
                await adminflag.write_value("CybICS(0PC-UA-$ADMIN)")
            else: 
                await adminflag.write_value("set the correct variable > 0")
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Suppress verbose INFO messages from asyncua about missing optional parent nodes
    logging.getLogger('asyncua.server.address_space').setLevel(logging.WARNING)
    asyncio.run(main())
