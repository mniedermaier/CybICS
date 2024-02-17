<p align="center">
  <img alt="CybICS Logo" src="CybICS.png" height="120" />
  <p align="center">Understanding industrial Cybersecurity.</p>
</p>

---

<div align="center">

[![License](https://img.shields.io/badge/license-MIT%20License-32c955)](/LICENSE)
[![KiBot](https://github.com/mniedermaier/CybICS/actions/workflows/kibotVerify.yml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/kibotVerify.yml)
[![C/C++ CI](https://github.com/mniedermaier/CybICS/actions/workflows/buildTest.yml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/buildTest.yml)
[![flawFinder C](https://github.com/mniedermaier/CybICS/actions/workflows/flawfinder.yml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/flawfinder.yml)
[![TruffleHog](https://github.com/mniedermaier/CybICS/actions/workflows/trufflehog.yaml/badge.svg)](https://github.com/mniedermaier/CybICS/actions/workflows/trufflehog.yaml)

</div>

---

The CybICS project is interesting for anyone who wants to delve into the world of industrial cybersecurity or deepen their knowledge.

## Getting Started

First, read through this page to get a better understanding of the testbed setup.

 - [Physical Process](#physical)
 - [Hardware](#hardware)
 - [Software](#software)
 - [Abbreviations](#abbreviations)



## Physical Process  <a id="physical"></a>
For educational purpose, a very simple process has been chosen.
The process represents a control loop, where the system needs a specific gas pressure.
This pressure is achieved by a compressor from a gas storage tank (GST) compressing the gas in the high pressure tank (HPT) buffer.
The gas is toxic and flammable.
It will be released and burned via a mechanical blow-out valve, if there is a critical overpressure in the HPT.

All pressure values are in bar above normal atmospheric pressure.

### Gas Storage Tank (GST)
The gas storage is used to buffer gas from the external gas supply.
The pressure from the external gas supply can not be regulated.
Only the fill level of the GST will be controlled by the PLC.

| Pressure    | Description | Range       |
| ----------- | ----------- | ----------- |
| <50         | Low         | 0-49        | 
| <150        | Normal      | 50-99       |
| 150+        | Full        | 150-255     |

**Controll Loop:**
The GST is kept between 60 and 240 with a simple control (Filling GST to GST < 240 when GST < 60).
The compressor to fill up the HPT can only run if the GST is at least filled up to a normal filling level.

### High Pressure Tank (HPT)
The high pressure tank is the tank that serves as a buffer for the system pressure.
The measurement unit of the sensor is in bar.

| Pressure    | Description | Range       |
| ----------- | ----------- | ----------- |
| <1          | Empty       | 0-0         |
| <50         | Low         | 1-49        |
| <100        | Normal      | 50-99       |
| <150        | High        | 100-149     |
| 150+        | Critical    | 150-255     |

**Controll Loop:**
The HPT is kept between 60 and 90 with a simple control.
(Running compressor when HPT < 60 up to HPT < 90)

### System
The system can be operated in the normal pressure range between 50 to 100 bar (HPT > 50 & HPT < 100).
If the pressure is too low, the system can not operate.
If the pressure if too high, the system can be damaged.

### Blowout (BO)
The blowout valve is a mechanical valve.
This is not operated by the PLC.
It will open and release toxic gas if the HPT pressure is above 220 bar to prevent bursting of the HPT.
The blowout will release the toxic gas, until it is again in a range below 200 bar (BO open when HPT > 220 until HPT > 200).


## Hardware  <a id="hardware"></a>
The hardware was kept simple and cost-efficient.
All you need is the CybICS baseboard, a Raspberry Pi 2 Zero and a 1602 display.
For the physical process visualization on the PCB a few LEDs are used.

<table align="center"><tr><td align="center" width="9999">
<img src="hardware/PCB/pcb/CybICS_top.png" width=90%></img>
</td></tr></table>

The PCB can be ordered completly assembled at [JLCPCB](https://jlcpcb.com/).
The total cost for a testbed is around 50 euros.
However, the minimum purchase of PCBs is 5 pieces when ordered from [JLCPCB](https://jlcpcb.com/).

| Component        | Description                             |
| ---------------- | --------------------------------------- |
| Base Board       | Simulating the physical process         |
| Raspberry Pi     | Controlling the physical process        |
| Display          | HD44780 1602 LCD showing physical state |


## Software  <a id="software"></a>

| Component        | Description                   | Running on   |
| ---------------- | ----------------------------- | ------------ |
| OpenPLC          | Programmable Logic Controller | Raspberry Pi |
| FUXA             | Historian and HMI             | Raspberry Pi |
| Physical Process |                               | STM32        |


## Abbreviations  <a id="abbreviations"></a>
| Abbreviation | Long                            | Description |
| ------------ | ------------------------------- | ----------- |
| GST          | Gas Storage Tank                |             |
| HPT          | High Pressure Tank              |             |
| LED          | Light-emitting Diode            |             |
| PCB          | Printed Circuit Board           |             |
| PLC          | Programmable Logic Controller   |             |
