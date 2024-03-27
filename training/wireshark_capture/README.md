# Getting network traffic

## Installation of Wireshark
Install wireshark
```sh
sudo apt install wireshark
```

Ensure that the ssh key is deployed on the Raspberry Pi.
```sh
ssh-copy-id -i <path to id file> pi@$DEVICE_IP
```

## Wireshark Network capture
Start remote capture.
```sh
ssh pi@$DEVICE_IP -p 22 sudo tcpdump -U -s0 'not port 22' -i br-cybics -w - | sudo wireshark -k -i -
```

![wireshark capture](doc/wireshark.png)

## Find the flag
The flag has the format "CybICS(flag)".

**Hint**: The flag is written to registers over modbus.
<details>
  <summary>Solution</summary>
  
  ##
  
  ![Flag modbus](doc/modbus.png)
</details>