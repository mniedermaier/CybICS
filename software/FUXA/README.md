

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
