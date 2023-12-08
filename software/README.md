


```sh
sudo openocd -f ./openocd_rpi.cfg -c "program build/CybICS.bin verify reset exit 0x08000000"
```
