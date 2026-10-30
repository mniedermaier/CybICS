# Stop means stop?

In this challenge you send the CybICS controller one command: STOP. The controller answers that it has obeyed and even reports that it is stopped. Your job is to find out whether that is true, and the answer teaches a rule every defender needs: a device's report about itself is not proof of what the process is doing.

## The idea

A Programmable Logic Controller (PLC) has an **operating mode**. In **RUN** it repeats its *scan cycle* over and over: read the inputs, run the program, write the outputs. In **STOP** the program halts. A real Siemens S7 controller then switches its outputs to a safe state; on a gas plant that means compressor off and valves closed.

Engineers use STOP to load a new program. Attackers use it to halt a process, or to clear the way for their own code. MITRE ATT&CK for ICS calls this *Change Operating Mode* (T0858). On a classic S7 controller the STOP command needs no password: anyone who can reach port 102 can send it.

<div class="callout analogy" markdown="1">
**Analogy:** you call a train driver and say "stop the train". The driver answers "stopped". The only way to be sure is to look out of the window and see whether the fields are still passing by.
</div>

So there are three different things you can check after a STOP:

| What you check | What it tells you |
|---|---|
| The **acknowledgement** of the command | the controller received it |
| The controller's **reported mode** | what the controller says about itself |
| The **process** (outputs, sensors, a heartbeat) | what is actually happening |

Only the last one is about the plant.

## How it looks on CybICS

OpenPLC at `172.18.0.3` runs the plant program every 50 milliseconds. Next to Modbus it runs an S7comm server on port 102, built from the Snap7 library, a software model of an S7 controller.

S7 controllers publish their state in **system status lists** (SZL, from the German *System-Zustandsliste*): small read-only records that any S7 client may request. The [S7comm enumeration](/theory/scanning2) challenge read the identity list, `0x0011`. The operating mode lives in list **`0x0424`**, where one byte says RUN (`0x08`) or STOP (`0x04`).

The program also blinks a **heartbeat**: the output `%QX0.0` changes about once a second, and only a running program can change it. Watch it here:

<div data-widget="plant-live" data-fields="heartbeat,hpt,compressor"></div>

<div data-widget="checkpoint" data-id="evidence"></div>

## How to approach it

1. **Read the mode before you change anything.** Request the status list `0x0424` and find the mode byte. Your client library may also offer a ready-made "get CPU state" function; compare the two answers, and when they differ, find out which one actually asked the PLC.
2. **Send the STOP.** python-snap7 in the attack shell has a function for it. Note what the PLC answers.
3. **Read the mode again.** Does the PLC now say it is stopped?
4. **Ask the plant.** Watch the heartbeat and the pressures for a few seconds, over Modbus or on the HMI. A stopped program cannot blink.
5. **Verify** while the PLC still reports STOP, then **restart** it. The plant is shared, and the next player should find the controller in RUN.

<details class="deep-dive" markdown="1">
<summary>Deep dive: STOP and START on the wire</summary>

Both are S7comm *jobs* (ROSCTR `01`). PLC STOP is function `0x29`, followed by the name of a service inside the controller, normally `P_PROGRAM`. A restart is function `0x28`, *PLC Control*, with the same name; an argument `C` turns a warm restart into a cold one. Reading a status list is not a job but a *userdata* request (ROSCTR `07`) in the CPU-functions group, carrying the list number `04 24`. A capture with tcpdump in the attack shell shows all three.

</details>

## Detect and defend

The CybICS IDS decodes S7comm and raises `s7_cpu_control` for every request that changes the controller's mode: critical for a STOP, high for a restart. Nothing in the plant changes the PLC's mode over the network, so in CybICS every such alert is an incident. On a real plant the rule is the same with one exception: the engineering workstation during planned maintenance.

The PLC itself is a weak witness. OpenPLC's runtime log lists S7 connections, but not your STOP.

Defences:

- **Lock the mode.** Some controllers have a physical key switch; locked in RUN, it refuses program changes from the network.
- **Require a password.** S7 controllers have protection levels that demand a password before a client may change memory, the program or the mode.
- **Close port 102** to everything but the engineering workstation, or turn the S7 server off if nothing uses it.
- **Watch the process, not only the controller.** An independent signal, like a heartbeat or a pressure trend, shows what the plant does whatever the controller reports.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

Snap7 sets its CPU status to STOP on function 0x29 and back to RUN on a warm or cold restart (`s7_server.cpp`, `PerformFunctionControl`), but OpenPLC's scan loop never reads that status, so the plant keeps running. A real S7 CPU would stop. OpenPLC's event mask (`SetEventsMask(0x3ff)` in `oplc_snap7.cpp`) covers only connection events, which is why the runtime log never shows the STOP. python-snap7 3.3.0's `get_cpu_state()` sends a Read Var job with no items and returns `S7CpuStatusRun` without parsing the answer; Snap7 answers that malformed request with leftover bytes, so the call sometimes raises `Data item is truncated`.

The verify module needs, at the moment of Verify, the newest `s7_cpu_control` alert to 172.18.0.3:102 to be a STOP from the last five minutes by the IDS clock, SZL 0x0424 to read STOP (read by the board over S7comm, so an `s7_enumeration` alert from 172.18.0.1 appears), and the heartbeat coil to change within three seconds. A restart after the STOP cancels it; a STOP left behind expires after five minutes. Because the plant is shared, a student who clicks Verify within five minutes of somebody else's STOP passes without sending one. `python3 s7_cpu_stop.py start` in the attack shell puts the CPU back in RUN.

</details>

## Before you start

- [PLCs and the scan cycle](/theory/plc-fundamentals).
- [S7comm](/theory/s7comm) for TPKT, COTP and the S7 header.
- [S7comm enumeration](/theory/scanning2) for system status lists.

Later on the path:

- [TRITON/TRISIS (2017)](/theory/trisis): an attack on a safety controller whose mode key had been left in PROGRAM.
