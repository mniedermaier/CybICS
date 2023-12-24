


```sh
sudo openocd -f ./openocd_rpi.cfg -c "program build/CybICS.bin verify reset exit 0x08000000"
```

## Build and flash STM32 software
1. Open this folder in vscode
1. Install `@recommended` extensions (ms-vscode-remote.remote-containers)
1. `Ctrl+Shift+P` `Dev Containers: Rebuild and Reopen in Container`
1. Select Debug target `Debug with External RPi`
1. Hit F5

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
