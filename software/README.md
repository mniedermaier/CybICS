


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

Wireshark Network capture
```sh
sshpass -p raspberry ssh pi@192.168.178.141 -p 22 sudo tcpdump -U -s0 'not port 22' -i lo -w - | sudo wireshark -k -i -
```
