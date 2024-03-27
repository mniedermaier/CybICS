# Understanding the physical process
Read through the process description in the main [readme](../../README.md) and understand how the control loop works.

### Control the process manually
Try to control the process manually as an operator via the FUXA HMI.
1. Open a web browser and connect to the FUXA HMI http://<IP>:1881
1. Login with the credentials operator:operator
1. Switch to the system view
1. click the red button "Manual / Automatic"
1. control the different valves and operate the system manually

![FUXA system view](doc/fuxa.png)

### Find the flag
The flag has the format "CybICS(flag)".
To get the flag, the blowout needs to be triggered.

**Hint**: The flag appears on the FUXA HMI, when the blowout was triggered.
<details>
  <summary>Solution</summary>
  After login on the FUXA dashboard switch to the "System" view.
  By closing the "System Valve" (SV) and enabling the Compressor (C),
  the pressure is rising.
  After a certain time, the pressure in the High Pressure Tank (HTB)
  gets a critical level and the Blowout (BO) will be opened.


  ##
  Flag: CybICS(Bl0w0ut)
  ![Flag OpenPLC Password](doc/flag.png)
</details>
