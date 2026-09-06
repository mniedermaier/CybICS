# Video series naming and ordering

One video per CTF challenge, numbered in learning-path order. The number gives a
stable playlist position; the slug is a human-readable topic, independent of the
internal challenge id (which is sometimes terse, e.g. `scanning2`, `fuzzingMB`).

## File name

```
cybics-NN-<slug>.mp4
```

- `NN` — two-digit sequence (`01`..`22`), zero-padded, fixed per challenge.
- `<slug>` — lower-case kebab-case topic, stable once published.

Examples: `cybics-01-network-scanning.mp4`, `cybics-08-mitm-arp-spoofing.mp4`.

A series intro, if produced, is `cybics-00-intro.mp4`.

## YouTube title

```
CybICS #NN — <Title> · <short hook>
```

e.g. `CybICS #01 — Network Scanning · mapping an ICS from the attack VM`.

## The series order

| NN | slug | Title | challenge id | category |
|----|------|-------|--------------|----------|
| 01 | network-scanning | Network Scanning | scanning | recon |
| 02 | s7comm-enumeration | S7comm Enumeration | scanning2 | recon |
| 03 | modbus-capture | Reading Modbus in Wireshark | wireshark_capture | recon |
| 04 | fuxa-password-attack | Brute-forcing the FUXA HMI | password_attack | credential access |
| 05 | openplc-password-attack | Brute-forcing OpenPLC | password_openplc | credential access |
| 06 | modbus-write-flood | Overwriting Coils by Flood | flood_overwrite | impair process control |
| 07 | modbus-fuzzing | Fuzzing Modbus | fuzzingMB | impair process control |
| 08 | mitm-arp-spoofing | Man-in-the-Middle via ARP | mitm | collection |
| 09 | opcua-abuse | Abusing OPC-UA | opcua | lateral movement |
| 10 | plc-programming | Rewriting PLC Logic | plc_programming | impair process control |
| 11 | physical-process | Forcing a Process Blow-out | physical_process | impact |
| 12 | detect-scan | Detecting a Scan | detect_basic | detection |
| 13 | detect-flood | Detecting a Write Flood | detect_overwrite | detection |
| 14 | ids-intrusion | Catching the Intrusion | ids_challenge | detection |
| 15 | ids-forensics | Reading the Alert Buffer | ids_forensics | detection |
| 16 | ids-evasion | Low-and-Slow Evasion | ids_evasion | evasion |
| 17 | harden-openplc | Hardening the OpenPLC Login | defense_openplc_password | defense |
| 18 | harden-fuxa | Hardening the FUXA Login | defense_fuxa_password | defense |
| 19 | firewall | Firewalling the PLC | defense_firewall | defense |
| 20 | network-segmentation | Network Segmentation | defense_network_segmentation | defense |
| 21 | ids-tuning | Tuning the IDS | defense_ids_tuning | defense |
| 22 | uart-console | The UART Console (hardware) | uart_basic | hardware |

## In the spec

Each spec carries `seq` and `slug`; the renderer names the output
`cybics-<seq:02d>-<slug>.mp4`. `--out` still overrides. Numbers and slugs are
fixed once a video is published so links and playlist order stay stable.
