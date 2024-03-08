## Using openOCD on the Raspberry Pi
openOCD is already installed in a container, if the installation script was executed.  
This container ensures the stm32 is flashed on startup.

For debugging, the remote openocd is automatically started once the debug or attach launch config is executed.

## Build and flash STM32 software
1. Execute "code ." in the GIT main folder
1. `Ctrl+Shift+P` `Dev Containers: Rebuild and Reopen in Container`
1. Select the devcontainer `stm32`
1. Select Debug target `Debug with External RPi`
1. Hit F5