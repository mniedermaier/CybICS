# PLC programming
This module introduces the concept on programming the PLC in the CybICS testbed.

## OpenPLC Editor
Clone the repository of the OpenPLC editor.
```sh
git clone https://github.com/thiagoralves/OpenPLC_Editor
```

Change into the folder of the OpenPLC editor.
```sh
cd OpenPLC_Editor/
```

Start the installation script.
```sh
./install.sh
```

To start the OpenPLC editor run the following.
```sh
./openplc_editor.sh
```

Open the project called "software" in this folder.
After this you can start to make changes.
![Picture of OpenPLC Editor](doc/openplc_editor.png)

### Upload the compiled program on the OpenPLC
Upload the program to the OpenPLC via the web interface on port 8080.
Do not forget to delete the previous CybICS ST code.