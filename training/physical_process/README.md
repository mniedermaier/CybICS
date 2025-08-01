# 🏭 Understanding the Physical Process

## 📋 Overview
In an industrial environment, the physical process refers to the actual operations and mechanisms involved in manufacturing, processing, or producing goods.
This includes activities such as the movement of raw materials through conveyor belts, the operation of machinery to shape or assemble components, and the monitoring of variables like temperature, pressure, and flow rates to ensure optimal performance.
These processes are often controlled and monitored by industrial control systems (ICS) and Supervisory Control and Data Acquisition (SCADA) systems, which provide real-time data and automation capabilities to enhance efficiency and safety.

The physical process is critical to the overall productivity and quality of an industrial operation.
Ensuring that all components work harmoniously and efficiently is essential to maintain high standards of output and to avoid downtime or accidents.
Regular maintenance, calibration, and monitoring of the equipment are necessary to keep the physical process running smoothly and to detect any potential issues before they escalate into major problems.

Read through the process description in the main [readme](../../README.md) and understand how the control loop works.

## 🎮 Manual Control Exercise
Try to control the process manually as an operator via the FUXA HMI.

### 📝 Steps
1. 🌐 Open a web browser and connect to the FUXA HMI `http://<IP>:1881`
2. 🔑 Login with the credentials `operator:operator`
3. 🔄 Switch to the system view
4. ⚡ Click the red button "Manual / Automatic"
5. 🎛️ Control the different valves and operate the system manually

![FUXA system view](doc/fuxa.png)

## 🎯 Find the Flag
The flag has the format `CybICS(flag)`.
To get the flag, the blowout needs to be triggered.

**💡 Hint**: The flag appears on the FUXA HMI, when the blowout was triggered.

<details>
  <summary><strong><span style="color:orange;font-weight: 900">🔍 Solution</span></strong></summary>
  
  After login on the FUXA dashboard switch to the "System" view.
  By closing the "System Valve" (SV) and enabling the Compressor (C),
  the pressure is rising.
  After a certain time, the pressure in the High Pressure Tank (HTB)
  gets a critical level and the Blowout (BO) will be opened.

  <div style="color:orange;font-weight: 900">
    🚩 Flag: CybICS(Bl0w0ut)
  </div>
  
  ![Flag OpenPLC Password](doc/flag.png)
</details>
