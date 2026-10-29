# Register map recon

In this challenge you map the memory of the CybICS PLC without any documentation: no program, no HMI project, only reads. By watching how each number changes while the plant runs, you work out what it means, and you find words the control logic uses that no operator screen ever shows. Then you locate one of them in a second protocol. It shows that anything a controller answers on the network can be mapped by someone patient enough to watch.

## The idea

A Programmable Logic Controller (PLC) keeps more than the values an operator sees. Its program also needs bookkeeping: counters, timers and words that remember what it decided last time. On many controllers all of that sits in one memory, and the network protocols read from that memory directly. Whether a value is on a screen does not decide whether it can be read.

An attacker without a register map can still build one. Reading a block of addresses once gives a list of numbers. Reading it again every half second for a few minutes turns the list into a set of time series, and each address starts to show its character. MITRE ATT&CK for ICS calls the result *Point & Tag Identification* (T0861); watching the values over time is *Monitor Process State* (T0801), and doing it with a script is *Automated Collection* (T0802).

<div class="callout analogy" markdown="1">
**Analogy:** you do not need a building's wiring plan to find out which switch controls which light. Flip nothing, just sit in the hallway for an hour and note which lights go on together with which sounds. A pattern that repeats is a connection.
</div>

## How it looks on CybICS

The PLC is OpenPLC at `172.18.0.3`. Its program keeps its own words in an area called `%MW` (memory words). OpenPLC publishes that area over Modbus TCP as holding registers from 1024 upwards, so `%MW0` is holding register 1024. The same memory is also reachable over S7comm on port 102, where it appears as one data block with two bytes per word.

A sweep of that area mostly returns zeros. The interesting words fall into a few kinds:

<div data-widget="sequence" data-id="kinds"></div>

The kind you are looking for is the **latch**. The [PLCs and the scan cycle](/theory/plc-fundamentals) lesson shows the compressor rule: start below one pressure, keep running until a higher one. To keep running, the program has to remember that it is running. That memory is a word that only ever holds 0 or 1, and it switches at the same pressures every cycle.

<div data-widget="plant-live" data-fields="gst,hpt,compressor,gstSig"></div>

Watch the live values for a while: the compressor and the tank refill signal switch on and off at repeating values. The words that remember those decisions are what the challenge asks you to find.

<div data-widget="checkpoint" data-id="translate"></div>

## How to approach it

1. **Pick the area.** Learn how the controller numbers its memory for each protocol, and choose the range that holds the program's words.
2. **Sample, do not snapshot.** Read the whole range repeatedly and keep every sample. The plant's cycles take minutes, so a short window misses words that only change once in a while.
3. **Classify each address** by the values it took: always zero, constant, analog, or switching between 0 and 1.
4. **Name the analog values.** Compare them with what the HMI shows for the two tanks.
5. **Tie each switching word to the process.** Note the analog values at every switch. A latch switches at the same values each time, and those values are the thresholds the plant was designed around.
6. **Translate.** Work out the same word's address in the other protocol, and check it there with a single read.

Only read. Writing a latch would start or stop real equipment in the lab, and the plant is shared.

<details class="deep-dive" markdown="1">
<summary>Deep dive: one word, four names</summary>

| View | Address of program word n |
|---|---|
| PLC program | `%MWn` |
| Modbus on the wire | holding register 1024 + n |
| HMI tools that count from 1 | holding register 1025 + n |
| S7comm on OpenPLC | data block DB1002, byte offset 2n |

Holding registers 0 to 1023 belong to another area, the analog outputs. Every translation is simple, and every one is a chance to be off by one, by 1024 or by a factor of two. On a real plant a translation error means reading or writing a different variable than intended.

</details>

## Detect and defend

The CybICS Intrusion Detection System (IDS) ignores Modbus reads, at any rate: the HMI, the OPC-UA server and the hardware bridge read the PLC many times a second, so reads are normal traffic. A sweep differs only in *what* it reads and *who* reads it: hundreds of addresses no client normally asks for, from a host that never polled before. Catching that needs a baseline of normal clients and the addresses they use. The S7comm read is different: no plant service speaks S7comm, so the IDS raises an alert for it.

Defences:

- **Limit who can reach the PLC.** Only the plant's own clients need Modbus or S7comm. A firewall keeps everyone else from reading at all.
- **Close unused protocols.** Every protocol that maps the same memory is one more way to read it, and one more to defend.
- **Filter by address where possible.** Some gateways and firewalls inspect Modbus and allow only the address ranges a client really needs.
- **Do not rely on hiding.** A word that answers a read will be found. Protect the writes and the network path, and watch for unusual readers.

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The check grades four typed answers all or nothing: the wire addresses of the two hysteresis latches (`compressorState` and `gstState`), the HPT value at which the compressor latch releases, and the compressor latch's byte offset in DB1002. The expected values live in `check_register_map_recon.py`; `tests/test_register_map_recon_check.py` derives them from `software/OpenPLC/cybICS.st` and fails if the program changes them.

The answers can also be computed from `cybICS.st` or from `training/plc_programming/software/plc.xml` without observing the plant. That is still point and tag identification from engineering files, and the Kali machine has the repository mounted anyway; the challenge rewards the observation by not printing a map anywhere a student would normally look.

The refill latch can stay on for several minutes while the storage tank fills. Students who sample for a minute or two often see it as a constant 1 and miss that it is a latch. Point them at the sampling window, not at the address.

A full sweep of the area also shows a constant block of seven words written by the hardware bridge. That block belongs to the Wireshark Capture challenge; the sweep helper prints it as numbers and does not decode it.

</details>

## Before you start

- [PLCs and the scan cycle](/theory/plc-fundamentals)
- [Modbus TCP](/theory/modbus)
- [S7comm](/theory/s7comm)
- [HMI project recon](/theory/hmi_project_recon)
