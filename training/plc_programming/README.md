# PLC programming
This module introduces the concept on programming the PLC in the CybICS testbed.

## OpenPLC Editor
OpenPLC Editor is a powerful, open-source tool designed for programming and configuring PLCs (Programmable Logic Controllers) using the IEC 61131-3 standard.
It provides a user-friendly interface for creating and managing control logic in various programming languages, such as Ladder Diagram (LD), Structured Text (ST), and Function Block Diagram (FBD).

With OpenPLC Editor, users can design and simulate control processes, making it easier to develop and test automation systems before deployment.
The editor supports real-time monitoring and debugging, allowing engineers to troubleshoot and refine their control logic efficiently.
Its compatibility with multiple PLC hardware platforms and its open-source nature make it a versatile and accessible option for both professionals and hobbyists in industrial automation.

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