


```sh
sudo openocd -f ./openocd_rpi.cfg -c "program build/CybICS.bin verify reset exit 0x08000000"
```

## Build and flash STM32 software
1. Open this folder in vscode
1. Install `@recommended` extensions (ms-vscode-remote.remote-containers)
1. `Ctrl+Shift+P` `Dev Containers: Rebuild and Reopen in Container`
1. Select Debug target `Debug with External RPi`
1. Hit F5

## Enable UART on the Raspberry Pi
```sh
sudo nano /boot/config.txt
```
Change/add in config "enable_uart=1"

```sh
ln -s /lib/systemd/system/getty@.service /mnt/root/etc/systemd/system/getty.target.wants/getty@ttyGS0.service
```



Wireshark Network capture
```sh
sshpass -p raspberry ssh pi@192.168.178.141 -p 22 sudo tcpdump -U -s0 'not port 22' -i lo -w - | sudo wireshark -k -i -
```


# Setting-up the Raspberry Pi Zero
## Install Raspberry Pi OS using Raspberry Pi Imager
With the help of the Raspberry Pi Imager, the basic linux installation on the SD card can be done.
The software can b e download for Windows, macOS, and Linux from the Raspberry Pi homepage (https://www.raspberrypi.com/software/).
After installation start the rpi-imager software.

<table align="center"><tr><td align="center" width="9999">
<img src="pictures/01_rpi-imager.png" width=70%></img>
</td></tr></table>

Click on "CHOOSE DEVICE" and select "No filtering".


<table align="center"><tr><td align="center" width="9999">
<img src="pictures/02_rpi-imager_device.png" width=70%></img>
</td></tr></table>

Click on "CHOOSE OS" &rarr; "Raspberry Pi OS (other)" and select "Raspberry Pi OS Lite (64-bit)".

<table align="center"><tr><td align="center" width="9999">
<img src="pictures/03_rpi-imager_OS.png" width=70%></img>
</td></tr></table>

Click on "CHOOSE STORAGE" and select the SD card, where the image should be installed.

<table align="center"><tr><td align="center" width="9999">
<img src="pictures/04_rpi-imager.png" width=70%></img>
</td></tr></table>

Click NEXT and select "EDIT SETTINGS":
<table align="center"><tr><td align="center" width="9999">
<img src="pictures/05_rpi-imager_custom.png" width=70%></img>
</td></tr></table>

Edit the options for image customization:
- Set hostname to "CybICS".
- Set username and password
  - Username: pi
  - Password: raspberry
- Configure wireless LAN
  - SSID: "your SSID"
  - Password: "your password"
- Configure local settings

<table align="center"><tr><td align="center" width="9999">
<img src="pictures/06_rpi-imager_options.png" width=45%></img>
<img src="pictures/07_rpi-imager_services.png" width=45%></img>
</td></tr></table>


Write the changes to the SD card.

