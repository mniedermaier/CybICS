
## Install FUXA
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
RestartSec=1
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
