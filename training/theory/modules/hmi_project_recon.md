# HMI project recon

In this challenge you download the complete configuration of the CybICS operator screen, without logging in, and turn it into a map of the plant: which controller it talks to, which number stands for which tank or motor, and which button writes which value. No packet is sent to the PLC. It shows why the files engineers build a plant with are as valuable to an attacker as the plant itself.

## The idea

A Modbus scan of a PLC gives you numbers: register 1126 holds 76, coil 2 is on. It does not tell you that 76 is the pressure in a tank or that coil 2 opens a valve. To attack a process on purpose, an attacker has to connect the numbers to their meaning. MITRE ATT&CK for ICS calls that step *Point & Tag Identification* (T0861).

The Human-Machine Interface (HMI) already contains that connection. When engineers build the operator screens, they create a **tag** for each process value: a name such as `HPT`, the controller it comes from and its address. Then they draw the screens and bind each indicator and each button to a tag. The result, the **HMI project**, is the plant's I/O map with labels.

<div class="callout analogy" markdown="1">
**Analogy:** a burglar can try every key on a ring, or read the caretaker's key cabinet, where every hook is labelled with the door it opens. The HMI project is the labelled cabinet.
</div>

Taking such engineering data from a server is *Data from Information Repositories* (T0811). Using the same HMI to read live values is *Monitor Process State* (T0801).

## How it looks on CybICS

The CybICS HMI is FUXA at `172.18.0.4`, port 1881. FUXA keeps the project on its server. A browser that opens the HMI starts with an empty page and then asks the server for the project, because it needs the screens and the tags to draw anything. FUXA answers that request for everyone, logged in or not.

| Part of the project | What it holds |
|---|---|
| Devices | The controller FUXA polls, its protocol and its address |
| Tags | Every process value: name, Modbus area, address and an internal **tag ID** |
| Views | The screens, with their buttons and what each click does |

Two details matter when you read it:

- **Counting from one.** FUXA lists Modbus addresses from 1, the protocol counts from 0. FUXA subtracts one before it sends a request, so the number you see in the project is one higher than the number in the packet. The [HMI and SCADA](/theory/hmi-scada) lesson shows this offset for the HPT tag.
- **Tag IDs.** FUXA also offers a request that returns the current value of tags by their ID. It answers without a login too, so anyone with the project can read the plant through the HMI, even from a computer that cannot reach the PLC.

<div data-widget="checkpoint" data-id="offset"></div>

## How to approach it

1. **Watch the HMI load.** Open it in a browser with the developer tools' network view and do not log in. Look for the request that brings in the largest answer.
2. **Repeat the request yourself.** A command-line client such as `curl` can make the same request without a browser and save the answer to a file.
3. **Read the devices and tags.** The file is JSON, text with nested names and values. A few lines of Python list each device and each tag with its address.
4. **Follow the buttons.** Each screen lists its items. A button's click event names the tag it changes. Follow the shutdown button and the compressor button to their tags, and turn FUXA's addresses into addresses on the wire.
5. **Check against the plant, read-only.** A single Modbus read shows whether an address holds what the project says. Do not press buttons or write anything: the plant is shared.

The challenge page asks for four facts from your map and checks them all at once.

<details class="deep-dive" markdown="1">
<summary>Deep dive: why FUXA's permissions do not hide the map</summary>

FUXA can attach permissions to screens and to single items. For a user without the permission, FUXA 1.2.6 marks the item as hidden or disables its button, but it still sends the item, every device and every tag. Permissions decide what the screen shows, not what the browser receives. Anything in the project, including an element that is hidden until some condition is met, is in the file every visitor downloads.

</details>

## Detect and defend

Detection is hard. Every operator's browser downloads the same project each time it opens the HMI, so an attacker's download looks like a page load. The CybICS IDS watches industrial protocols, not this web traffic, and FUXA's own log records the request without the address it came from. A web proxy in front of the HMI that logs addresses can at least show downloads from computers that are not operator stations, or from scripts rather than browsers.

Defences:

- **Limit who reaches the HMI.** Only operator and engineering stations need port 1881. Network segmentation and firewall rules keep everyone else from even asking.
- **Put a login in front of the HMI.** Because FUXA sends the whole project to anonymous visitors, the login has to happen before the request reaches FUXA, for example at an authenticating proxy.
- **Keep secrets out of screens.** A hidden label is still in the file. Passwords, instructions and anything sensitive do not belong in an HMI project.
- **Treat engineering files as sensitive.** HMI projects, PLC programs and their backups describe the plant as completely as a network diagram. Store and share them accordingly.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The check grades four typed answers all or nothing: the PLC endpoint (`openplc:502` or `172.18.0.3:502`), the wire address of the holding register the STOP / SHUTDOWN buttons write, the wire coil the SystemView "Comp." button toggles, and the FUXA tag ID of HPT. The expected values live in `check_hmi_project_recon.py` and mirror `software/FUXA/fuxa-project.json`; `tests/test_hmi_project_recon_check.py` fails if a re-export changes them. The register and coil numbers are also in other lessons; the tag ID is in no document, so it is what proves the project was read.

The anonymous project carries no flag. It used to hold the Password Attack and Physical Process flags as hidden text, so one search of this download solved both; those two challenges now hand out their flags through Verify, and `tests/test_hmi_flags.py` fails if a flag ever lands in `fuxa-project.json` again.

</details>

## Before you start

- [HMI and SCADA](/theory/hmi-scada)
- [Modbus TCP](/theory/modbus)
- [Network scanning](/theory/scanning)
