## Hardware  <a id="hardware"></a>
The hardware was kept simple and cost-efficient.
All you need is the CybICS baseboard, a Raspberry Pi 2 Zero and a 1602 display.
For the physical process visualization on the PCB a few LEDs are used.

<table align="center"><tr><td align="center" width="9999">
<img src="pcb/pcb/CybICS_top.png" width=90%></img>
</td></tr></table>

The PCB can be ordered completly assembled at [JLCPCB](https://jlcpcb.com/).
The total cost for a testbed is around 50 euros.
However, the minimum purchase of PCBs is 5 pieces when ordered from [JLCPCB](https://jlcpcb.com/).

### Components
The hardware consists of three core components.
Additionally, there is a 3d printable case,
which makes desk usage easier ([link](case/README.md)).

| Component        | Description                             |
| ---------------- | --------------------------------------- |
| Base Board       | Simulating the physical process         |
| Raspberry Pi     | Controlling the physical process        |
| Display          | HD44780 1602 LCD showing physical state |

