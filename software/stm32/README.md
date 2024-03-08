## Using openOCD on the Raspberry Pi
openOCD is already installed in a container, if the installation script was executed.
For remote debugging start it with:
```bash
ssh "$DEVICE_USER@$DEVICE_IP" sudo docker compose -f /home/pi/CybICS/docker-compose.yaml exec stm32 openocd -f /CybICS/openocd_rpi.cfg
```

```sh
sudo openocd -f ./openocd_rpi.cfg -c "program build/CybICS.bin verify reset exit 0x08000000"
```

## Build and flash STM32 software
1. Execute "code ." in the GIT main folder
1. `Ctrl+Shift+P` `Dev Containers: Rebuild and Reopen in Container`
1. Select Debug target `Debug with External RPi`
1. Hit F5