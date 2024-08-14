### Install dependencies

```sh
sudo apt install python3-netifaces python3-pymodbus
```

### Service for autostart


```sh
sudo nano /lib/systemd/system/readI2Cpi.service
```


```sh
[Unit]
Description=readI2Cpi Service
After=network.target

[Service]
Type=simple
Restart=always
StartLimitInterval=0
RestartSec=10
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/gits/CybICS/software/scripts/readI2Cpi.py

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl daemon-reload
```

```sh
sudo systemctl start readI2Cpi.service
```

```sh
sudo systemctl enable readI2Cpi.service
```

