# Trusted writer

In this challenge you stop the gas plant without your own computer ever talking to the PLC. You ask the Human-Machine Interface (HMI) to do it, and the HMI sends the command. The Intrusion Detection System (IDS) sees the HMI doing its normal job and stays silent. The lesson is about trust: what a monitoring system trusts, an attacker wants to borrow.

## The idea

Picture an office building where the guard at the door waves through anyone wearing a courier's jacket. The guard is not careless: couriers come and go all day, and checking every parcel would stop the building. But anyone who can get a courier to carry a parcel for them gets it inside without being checked.

Network defences often work the same way. An **allowlist** names the hosts whose traffic is expected, and a rule or a firewall then ignores, or always permits, traffic from them. That saves a lot of false alarms. It also means the decision rests on an **address**, not on a person or an intention. An attacker who cannot pass the guard looks for someone the guard trusts and makes them carry the message. Security people call this "living off the land": using the tools that are already there instead of bringing your own.

<figure>
<svg viewBox="0 0 520 190" role="img" aria-label="Three boxes in a row: the attack machine on the left, the FUXA HMI in the middle and the OpenPLC controller on the right. An arrow labelled 'please write stop' goes from the attack machine to FUXA. A second arrow labelled 'Modbus write, from 172.18.0.4' goes from FUXA to OpenPLC. Below, the IDS looks at the second arrow and shows a tick labelled 'trusted writer, not counted'.">
  <g fill="none" stroke="currentColor" stroke-opacity="0.6">
    <rect x="10" y="30" width="130" height="60" rx="6"/>
    <rect x="195" y="30" width="130" height="60" rx="6"/>
    <rect x="380" y="30" width="130" height="60" rx="6"/>
    <rect x="300" y="130" width="160" height="44" rx="6" stroke-dasharray="4 3"/>
  </g>
  <g fill="currentColor" font-size="13" text-anchor="middle">
    <text x="75" y="57">Attack machine</text>
    <text x="75" y="75" opacity="0.7">172.18.0.100</text>
    <text x="260" y="57">FUXA (HMI)</text>
    <text x="260" y="75" opacity="0.7">172.18.0.4</text>
    <text x="445" y="57">OpenPLC</text>
    <text x="445" y="75" opacity="0.7">172.18.0.3</text>
    <text x="380" y="150">IDS: trusted writer,</text>
    <text x="380" y="166">not counted</text>
    <text x="167" y="22" font-size="12">"please write stop"</text>
    <text x="352" y="22" font-size="12">Modbus write</text>
  </g>
  <g stroke="currentColor" stroke-width="2" fill="none">
    <path d="M140 60 H190"/><path d="M184 54 L190 60 L184 66"/>
    <path d="M325 60 H375"/><path d="M369 54 L375 60 L369 66"/>
    <path d="M350 128 L350 66" stroke-dasharray="3 3" stroke-opacity="0.6"/>
  </g>
</svg>
<figcaption>The attack machine never sends Modbus. It asks the HMI, and the write the PLC receives comes from the HMI's address, which the IDS write rules skip.</figcaption>
</figure>

## How it looks on CybICS

FUXA, the HMI at `172.18.0.4`, port 1881, reads the plant from OpenPLC over Modbus and writes to it when an operator presses a button such as STOP. Because of that, the IDS treats FUXA as a **trusted writer**: its two Modbus write rules count writes per source host and skip FUXA completely.

FUXA itself takes orders from its clients. The HMI page in a browser is one client: it keeps a live connection to FUXA and sends a small message whenever a button is pressed. Scripts are another: FUXA also offers a web API for setting a tag. Whatever the client, the Modbus request that reaches the PLC comes from FUXA.

To make what happens visible, the CybICS IDS keeps a **write journal** next to its alerts. It is not a rule and never raises an alarm. It lists every Modbus write request it sees, with the source address, the register and the value. Your own host appears there whenever it writes; FUXA appears there as `fuxa`.

<div data-widget="checkpoint" data-id="who-writes"></div>

## How to approach it

1. Find out what you want FUXA to write: the stop tag's ID and its device, from the HMI's project (the HMI Project Recon challenge shows how).
2. Find out how FUXA's clients ask it to write. The browser's developer tools show the messages the HMI page exchanges; FUXA is open source, so its code shows what it accepts and what it checks first.
3. Send the same request yourself, without a browser. Then look at the IDS write journal and the alerts: who does the IDS say wrote the stop flag?
4. Stay quiet. Port scans and guessing passwords raise alerts that have nothing to do with Modbus.
5. Restore the plant the same way afterwards.

<details class="deep-dive" markdown="1">
<summary>Deep dive: why "who sent it" is a weak signal</summary>

Network monitoring sees packets, and the most reliable thing about a packet is where it came from and where it goes. That is why allowlists are popular: they are cheap, and they cut false alarms from the hosts that legitimately write all day.

The cost shows up when one of those hosts takes instructions from others. An HMI, an engineering workstation, a historian with write-back, a gateway: each of them relays commands. A rule that trusts the relay trusts everyone who can talk to it. Detection that still works looks at *what* is written (a stop, a setpoint far outside its usual range) and *when* (no operator logged in), not only at the sender.

</details>

## Detect and defend

- **Watch the content, not only the sender.** A write to a safety-critical register, such as the stop flag, deserves an alert whoever sends it. A trusted writer writes rarely, so such a rule is cheap.
- **Correlate with the operator.** Only the HMI knows which person or client asked for a write. Its logs belong in the monitoring, and a command sent while no operator is logged in is suspicious.
- **Limit who can reach the HMI's server.** If only the operator stations can reach port 1881, nobody else can use FUXA as a relay.
- **Require authorization on every write path.** A button that is greyed out in the browser protects nothing if the server accepts the write anyway. That has to be fixed in the HMI software itself.
- **Keep safety in the PLC.** Limits that keep the process safe belong in the controller or a separate safety system, where no HMI command can override them.

<div class="callout cybics" markdown="1">
**In CybICS:** the IDS Evasion challenge stays *below* a threshold. This one goes *around* the rules: the source it uses is never counted at all.
</div>

## Before you start

- [HMI and SCADA](/theory/hmi-scada)
- [HMI project recon](/theory/hmi_project_recon)
- [IDS evasion](/theory/ids_evasion)

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

FUXA 1.2.6 accepts the socket.io `device-values` set message from guests: the
connection handler lets a client without a token connect as a guest, and the
event handler writes without a permission check. Button permissions only
disable the button in the browser. Newer FUXA code (main branch) checks write
authorization in that handler. The REST route `/api/setTagValue` needs an
administrator token (an operator gets 401); a token from the Forged HMI Token
challenge works.

To make the challenge verifiable, the IDS capture filter now keeps FUXA's
Modbus write requests (its reads stay filtered out) and the IDS journals every
write it captures at `/api/modbus/writes`. Verify cannot tell an operator's
click from a script, and neither can the IDS. A student who logs in as
operator and presses STOP passes too; the README says so openly, because that
indistinguishability is the point of the lesson.

</details>
