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

```sh
python3 flooding_hpt.py
```