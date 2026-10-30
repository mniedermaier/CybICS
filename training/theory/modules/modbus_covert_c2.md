# Covert channels in plant traffic

In this challenge nothing is attacked and nothing is written. You get a recording of ordinary Modbus reads at the PLC, and one of the readers is not what it seems: it uses the reads to send a message out of the plant. You find it, decode it and work out which allowlist would have caught it. This is how defenders learn that "read-only" traffic is not the same as harmless traffic.

## The idea

Imagine a library where a visitor borrows one book every evening. Nobody minds; borrowing books is what visitors do. But the visitor picks each book only for the first letter of its title, and a friend outside notes the letters. Over a month, the titles spell a message, and the librarian never saw anything but borrowing.

A **covert channel** works the same way: information hides inside traffic whose official purpose is something else. In a Modbus read request the client chooses the **start address** and the **quantity** freely. A program that wants to send data can choose them to match its data, one character per request, and the PLC answers each request like any other read.

<figure>
<svg viewBox="0 0 520 150" role="img" aria-label="Two Modbus read requests side by side. The poller reads the same start address every time. The implant reads a different start address each time; the low byte of each address is an ASCII letter, here H then i.">
  <g fill="none" stroke="currentColor" stroke-opacity="0.6">
    <rect x="10" y="20" width="240" height="110" rx="6"/>
    <rect x="270" y="20" width="240" height="110" rx="6"/>
  </g>
  <g fill="currentColor" font-size="12" text-anchor="middle">
    <text x="130" y="42" font-weight="bold">Poller</text>
    <text x="130" y="68">read 0x0064, qty 2</text>
    <text x="130" y="88">read 0x0064, qty 2</text>
    <text x="130" y="108">read 0x0064, qty 2</text>
    <text x="390" y="42" font-weight="bold">Implant</text>
    <text x="390" y="68">read 0x05<tspan font-weight="bold">48</tspan>, qty 1  → H</text>
    <text x="390" y="88">read 0x05<tspan font-weight="bold">69</tspan>, qty 1  → i</text>
    <text x="390" y="108">read 0x05<tspan font-weight="bold">21</tspan>, qty 1  → !</text>
  </g>
</svg>
<figcaption>A poller asks for the same registers again and again. The implant's addresses change with its data.</figcaption>
</figure>

## How it looks on CybICS

On the CybICS network two programs read the PLC (OpenPLC, `172.18.0.3`) all day: the HMI (FUXA) for its screens and the OPC-UA gateway, which copies values for the office network. The I/O service mostly writes. All of them use port 502, which the plant cannot close.

That is why the channel is attractive. An implant on the OPC-UA gateway can open a second Modbus connection and blend in: same host, same port, same function code as the gateway's own polling. The CybICS IDS only inspects writes and diagnostic requests, so a reader never raises an alert. OpenPLC also answers reads of unused memory words with 0 instead of an error, so nothing fails.

Try it: the decoder turns register values into bytes and text. A start address works the same way.

<div data-widget="register-decoder" data-values="1352,1385"></div>

<div data-widget="checkpoint" data-id="channel"></div>

## How to approach it

1. **Count conversations, not hosts.** A TCP connection is one program talking. One host with two Modbus connections to the same PLC deserves a question.
2. **Describe each connection's normal.** A poller reads the same few registers forever. Note the function code, start address and quantity of each.
3. **Measure the rhythm, carefully.** In an office network a perfectly regular connection is a classic beacon. In a plant, *every* poller is regular, because it runs on a timer. Rhythm helps you confirm a suspect, not find one.
4. **Look for data where there should be none.** Addresses that keep changing, that no screen uses, often decode when you write them in hexadecimal.
5. **Turn your finding into a rule.** Ask what the smallest allowlist is that passes every legitimate request and flags the odd one.

Sort these observations from a plant capture:

<div data-widget="sequence" data-id="normal"></div>

## Detect and defend

- **Allowlist by client, function code and address range.** A host-only list passes an implant on an allowed host; a list by function code passes it too when it only reads. The address range is what separates it.
- **Learn the baseline, then check it.** Monitoring products learn this table automatically. If the implant was already there during the learning phase, it becomes "normal", so review what was learned.
- **Watch for new sessions from known hosts.** A gateway that suddenly holds two connections has changed.
- **Enforce the list.** A Modbus-aware firewall can drop reads outside the allowlist, and segmentation limits who could ever see the hidden data.

<div class="callout cybics" markdown="1">
**In CybICS:** the IDS rules count writes. A read allowlist is the missing piece for traffic like this; in the challenge you design one and test it against the capture.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: how much a read can carry</summary>

A read request has two free 16-bit fields, so up to four bytes per request if the implant varies both, and the transaction ID adds two more. Using only the low byte of the start address, as here, is slow but keeps the quantity at 1, so the PLC's answer stays tiny. Real implants trade speed for stealth in the same way. The answer direction can carry data as well, if the attacker can write the registers the implant reads, which turns an exfiltration channel into command and control.

</details>

## Before you start

- [Modbus TCP](/theory/modbus)
- [Capturing Modbus traffic](/theory/wireshark_capture)
- [Reading an incident capture](/theory/incident_pcap)

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The capture is generated by `software/scripts/generate_covert_c2_pcap.py`
and is deterministic; the answers are graded on the board. The polling
patterns of FUXA and the OPC-UA gateway were measured on the virtual stack;
the I/O service is filtered out as in Incident PCAP. There is no live
beacon and no live read-allowlist rule in the IDS on purpose: both would
add continuous load on the Raspberry Pi and change the baselines of the
other IDS challenges. `read_allowlist.py` lets students test a rule set
offline.

</details>
