## Using openOCD on the Raspberry Pi
openOCD is already running in a container, if the installation script was executed.
```sh
sudo openocd -f ./openocd_rpi.cfg -c "program build/CybICS.bin verify reset exit 0x08000000"
```

## Build and flash STM32 software
1. Execute "code ." in the GIT main folder
1. `Ctrl+Shift+P` `Dev Containers: Rebuild and Reopen in Container`
1. Select Debug target `Debug with External RPi`
1. Hit F5