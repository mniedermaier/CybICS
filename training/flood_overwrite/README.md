# Flood & overwrite
The provided script "flooding_hpt.py" floods via modbus the high pressure tank (HPT) values to 10.
With this flooding, the OpenPLC does not get the correct values and enables the compressor (C) all the time.
This is leading to a critical pressure value in the HPT.

The script uses the ".dev.env" file in the root folder of the git.
Check if these settings are correct, before executing the flooding script.

```sh
python3 flooding_hpt.py
```