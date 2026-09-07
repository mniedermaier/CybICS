#!/usr/bin/env bash
# Firmware analysis for the UART console lesson (cybics-22).
# The flag lives on the STM32's serial console, behind a login password.
F=/CybICS/software/stm32/src/main.c
echo "[*] target: the STM32 microcontroller's UART debug console (physical device)"
echo "[*] UART / JTAG / SWD debug ports often have weak or no authentication - and"
echo "    physical access to them bypasses every network control on the plant."
echo
echo "[*] the firmware prints the flag on the serial console, behind a login password:"
echo
echo "    --- login gate  (software/stm32/src/main.c) ---"
sed -n '916,924p' "$F" | sed 's/\t/    /g; s/^/    /'
echo
echo "    --- the flag, behind menu option 2 ---"
sed -n '966,969p' "$F" | sed 's/\t/    /g; s/^/    /'
echo
echo "[*] the login password (LOGIN_PASSWORD) is just 3 lowercase letters:"
echo "    26 ^ 3  =  17,576 combinations  ->  trivially brute-forceable over serial"
