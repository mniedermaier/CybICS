# OPC UA

In this example we try to attack OPA UA.
For this install opcua-client.

```sh
pip3 install opcua-client
```

Remove configuration file for the OpcUaClient:
```sh
rm -rf .config/FreeOpcUa/OpcUaClient.conf
```

## Find the flag
The flag has the format "CybICS(flag)".

**Hint**: The flag is written to a OPC UA variable
<details>
  <summary>Solution</summary>
  
  ##
  
  ![Flag opcua](doc/opcua.png)
</details>