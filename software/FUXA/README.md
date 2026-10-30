# FUXA HMI

## Overview
FUXA is a web-based SCADA/HMI interface for monitoring and controlling the industrial process.

## Usage
FUXA is running on port 1881.

## Users

| Name        | Password    | Description                           |
| ----------- | ----------- | ------------------------------------- |
| viewer      | viewer      | This user can only view all views     |
| operator    | operator    | This user can operate the system      |
| admin       | 123456      | The admin can make changes on the HMI |


## Install FUXA (optional without docker)
The following steps are not necessary, as the installation script installs FUXA already in a docker container.
### Increase SWAP file size
Temporarily Stop Swap:
```sh
sudo dphys-swapfile swapoff
```

Modify the size of the swap
```sh
sudo nano /etc/dphys-swapfile
```
Change in config "CONF_SWAPSIZE=1024"

Initialize Swap File
```sh
sudo dphys-swapfile setup
```
Start Swap
```sh
sudo dphys-swapfile swapon
```

### Install NPM and Fuxa
Install npm
```sh
sudo apt install npm
```

```sh
sudo npm install -g --unsafe-perm @frangoteam/fuxa
```

Start fuxa
```sh
fuxa
```

## Add FUXA to system.d for autostart

```sh
sudo nano /lib/systemd/system/fuxa.service
```

```
[Unit]
Description=FUXA Service
After=network.target

[Service]
Type=simple
Restart=always
StartLimitInterval=0
RestartSec=10
User=pi
WorkingDirectory=/home/pi
ExecStart=sudo /usr/local/bin/fuxa

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl daemon-reload
```

```sh
sudo systemctl start fuxa.service
```

```sh
sudo systemctl enable fuxa.service
```

## Changing the HMI project
`fuxa-project.json` is exported from FUXA, never edited by hand. Change the
views in the FUXA editor (`http://<DEVICE_IP>:1881/editor`, logged in as
admin), save, then export the project as admin and format it with `jq`:

```sh
TOKEN=$(curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"123456"}' http://localhost:1881/api/signin | jq -r .data.token)
curl -s -H "x-access-token: $TOKEN" http://localhost:1881/api/project | jq . > fuxa-project.json
```

Export as admin: without a token FUXA marks the items a guest may not see
as hidden, and that copy differs from the stored project. An unchanged
project exported this way is byte-identical to the committed file.

**Never put a flag or a secret in the project.** FUXA answers
`GET /api/project` without a login, and the answer holds every view,
including admin-only views and hidden items. `tests/test_hmi_flags.py` fails if a flag ends up in it.

A board keeps its FUXA data in the `fuxa_data` volume and imports the project
only on the first start, so a changed project reaches an existing board only
after that volume is removed.

## Format fuxa-project.json to be pretty

Install jq
```sh
sudo apt install jq
```

Make a pretty version of the FUXA project file:
```sh
jq . fuxa-project.json > fuxa-project-pretty.json
```

## Related Documentation
- [OpenPLC Integration](../OpenPLC/README.md)
- [Virtual Hardware I/O](../hwio-virtual/README.md)
- [Raspberry Pi Hardware I/O](../hwio-raspberry/README.md)
- [Getting Started Guide](../../doc/README.md)