# OPC UA

In this example we try to attack OPA UA.
For this install opcua-client.

```sh
pip3 install opcua-client
```

Remove configuration file for the OpcUaClient if there is any:
```sh
rm -rf .config/FreeOpcUa/OpcUaClient.conf
```

## Get the user flag
The flag has the format "CybICS(flag)".

**Hint**: The flag is written to a OPC UA of a user, which you need to brute force
<details>
  <summary>Solution</summary>
  
  ##
  
  ![Flag opcua](doc/opcua_user.png)
</details>