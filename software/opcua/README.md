### Configuration


Create certificate for admin user:
```sh
openssl req -x509 -newkey rsa:2048 -keyout key_admin.pem -out cert_admin.pem -sha256 -days 36500 -nodes -subj "/C=XX/ST=CybICSstate/L=CybICScity/O=CybICS/OU=CybICS/CN=CybICS"
```

Convert pem to der format:
```sh
openssl x509 -in cert_admin.pem -out cert_admin.der -outform DER
```