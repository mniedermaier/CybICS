# Flood & overwrite
A flooding attack in an industrial security context can have devastating consequences, disrupting critical operations and compromising safety.
By overwhelming industrial control systems (ICS) or Supervisory Control and Data Acquisition (SCADA) networks with excessive traffic, attackers can cause delays or complete halts in manufacturing processes, energy distribution, or other essential industrial functions.
These disruptions can lead to significant financial losses, damage to equipment, and potential safety hazards for workers and the surrounding community.

Spoofing a Modbus register involves an attacker sending fraudulent data to a Modbus device, tricking it into believing the data is legitimate.
This type of attack can severely disrupt industrial processes by manipulating the readings or settings of critical devices such as sensors, actuators, or controllers.
For instance, an attacker could alter temperature or pressure readings, causing a system to operate outside safe parameters, potentially leading to equipment damage or safety hazards.

The provided script `flooding_hpt.py` floods via modbus the high pressure tank (HPT) values to 10.
With this flooding, the OpenPLC does not get the correct values and enables the compressor (C) all the time.
This is leading to a critical pressure value in the HPT.

The script uses the `.dev.env` file in the root folder of the git.
Check if these settings are correct, before executing the flooding script.


<details>
  <summary><strong><span style="color:orange;font-weight: 900">Solution</span></strong></summary>

  Execute the provided script to flood the sensor values of the high pressure tank (HPT).
  This script is designed to continuously send a specific value to a Modbus TCP device to simulate flooding a high-pressure tank (HPT) in a system controlled by an OpenPLC. 
  The script is intended to flood a high-pressure tank's register in an OpenPLC system by repeatedly writing a specific value (10) to a Modbus register (1126).
  It connects to a Modbus TCP device using the IP address specified in an environment file and performs the flooding operation at a very high frequency.
  This script would be used in scenarios where testing or stress-testing of the PLC's handling of high-frequency updates is required.
  
  ```sh
  python3 flooding_hpt.py
  ```

What can be observed on the FUXA HMI and what happens to the physical process?

* Historical Data and Trends: The interface provides access to historical data and trend analysis. This feature enables operators to review past performance, analyze trends over time, and make data-driven decisions to optimize process efficiency.
* Response to Alerts: When an alert is triggered, it often prompts immediate action. For example, if a temperature sensor detects an anomaly, the HMI might notify the operator to take corrective measures, such as reducing the heat or shutting down a component to prevent damage.

</details>

