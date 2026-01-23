# OPC UA Server

## Overview
The OPC UA server provides an OPC Unified Architecture interface for industrial communication. It enables secure and reliable data exchange between clients and the CybICS platform.

## Configuration

Generate user hmac sha256:
```sh
echo -n "test" | openssl dgst -sha256 -hmac "678"
```

Create certificate for admin user:
```sh
openssl req -x509 -newkey rsa:2048 -keyout key_admin.pem -out cert_admin.pem -sha256 -days 36500 -nodes -subj "/C=XX/ST=CybICSstate/L=CybICScity/O=CybICS/OU=CybICS/CN=CybICS"
```

Convert pem to der format:
```sh
openssl x509 -in cert_admin.pem -out cert_admin.der -outform DER
```

## Related Documentation
- [OpenPLC Integration](../OpenPLC/README.md)
- [OPC UA Training Module](../../training/opcua/README.md)
- [Getting Started Guide](../../doc/README.md)