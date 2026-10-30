# Physics as a witness

In this challenge someone fed the PLC a false sensor value, and every screen in the control room showed a calm plant. You get the historian's record of that night. There is no network capture and no alarm, only numbers. You find the lie the way an engineer would: by asking whether the plant could physically have done what the numbers say. Attackers can forge a value; forging physics is much harder.

## The idea

Think of a bank account. The statement says your balance stayed the same all month, but your card was charged every day and no money came in. You do not need to see the bank's computers to know the statement is wrong: money that leaves one place has to arrive somewhere.

A process plant keeps the same kind of books. Gas, water and energy do not appear from nowhere. When a pump or compressor runs, the pressures must change in a way that matches. Such a rule, which must hold every time, is called a **process invariant**. A forged sensor value has to obey every invariant at once to stay hidden, and that is hard to fake.

There are three kinds of witnesses:

- **Conservation laws:** what leaves one tank must show up in another.
- **Rates:** a value can only change as fast as the machine can change it.
- **Redundant signals:** a second sensor, or a value computed from the real process, that must agree with the first.

## How it looks on CybICS

The I/O service (`hwio`) simulates the plant in steps of about one second, called ticks. It writes the pressures of the gas storage tank (GST) and the high-pressure tank (HPT) to the PLC, and the PLC switches the compressor, the system valve and the refill from them. The historian records what the PLC holds, once per tick.

The plant's books are simple:

| When | HPT | GST |
|------|-----|-----|
| Compressor on | rises by exactly 1 | falls by 2 |
| Compressor off, valve open | falls by 0 to 2 | unchanged |
| Compressor off, valve closed | unchanged | unchanged |
| Refill on | | adds 0 to 3 on top |

The I/O service also computes the system sensor (`sysSen`) from the **real** HPT, and the PLC opens the valve in the same pressure band of the HPT **it sees**. So the two must agree. If someone forges the HPT on its way to the PLC, the PLC and the screens believe the lie, but the GST and `sysSen` keep telling the truth.

<figure>
<svg viewBox="0 0 520 210" role="img" aria-label="A chart over time. The recorded HPT line stays almost flat around 70. The GST line falls steadily from 200 to 120 while the compressor runs. A dashed line, the HPT reconstructed from the GST, rises from 70 to 110. The gap between the recorded and the reconstructed HPT grows with every tick.">
  <g fill="none" stroke="currentColor" stroke-opacity="0.35">
    <path d="M50 20 V180 H500"/>
  </g>
  <polyline points="50,40 500,120" fill="none" stroke="#2a7ab0" stroke-width="2.5"/>
  <polyline points="50,140 140,140 230,136 320,134 410,132 500,130" fill="none" stroke="#ff6b00" stroke-width="2.5"/>
  <polyline points="50,140 500,60" fill="none" stroke="#ff6b00" stroke-width="2.5" stroke-dasharray="7 5"/>
  <g fill="currentColor" font-size="12">
    <text x="58" y="32">GST 200</text>
    <text x="440" y="114">GST 120</text>
    <text x="360" y="150">HPT as recorded: about 72</text>
    <text x="330" y="52">HPT from the gas balance: 110</text>
    <text x="50" y="200" opacity="0.7">40 ticks with the compressor on and the refill off</text>
  </g>
</svg>
<figcaption>An example: 80 bar left the GST in 40 compressor ticks, so 40 bar must have arrived in the HPT. The recorded HPT barely moved; the gas balance shows where the real pressure went.</figcaption>
</figure>

<div data-widget="checkpoint" data-id="balance"></div>

## How to approach it

1. **Learn what normal looks like.** Skim a stretch of healthy operation: how far the HPT moves, how long the compressor runs, what happens during a refill.
2. **Write the books down as rules.** Turn each row of the table above into a check from one row of the historian to the next, and add the `sysSen` check within a row.
3. **Separate odd from impossible.** A plant that was stopped looks frozen; a refill can make the GST rise while the compressor runs. Both look strange and both obey the rules. Only a rule that breaks is evidence.
4. **Find the first broken rule.** Different rules break at different moments. The earliest one marks the start; the row before it is the last one you can trust.
5. **Reconstruct.** From the last trusted row, use the rules that still hold, such as the gas balance, to calculate what the forged value really was.

Practise step 3 here. Decide for each observation whether the plant can do it:

<div data-widget="sequence" data-id="verdict"></div>

## Detect and defend

- **Run the invariants live.** The checks you write are cheap enough to run on every tick. An alarm on "the compressor runs but the tank does not fill" catches forged values that look perfectly normal on their own.
- **Add an independent witness.** A second pressure transmitter on a separate path, or a mechanical gauge read on the operator's rounds, cannot be forged through the same network.
- **Limit what one value can do.** A run-time limit for the compressor, or an interlock wired to the real tank pressure, keeps a single false number from driving the plant into danger.
- **Protect the measurement path.** Sensor values travel to the PLC over Modbus, which has no integrity protection. Segmenting that network and locking down who can reach it makes the forgery much harder in the first place.

<div class="callout cybics" markdown="1">
**In CybICS:** the Man in the middle lesson shows how a value is changed on its way between two hosts, and the Flood & Overwrite challenge shows the same lie on the HMI. This challenge is the defender's side of both: catching the lie with nothing but the plant's own physics.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: why the attacker could not just forge everything</summary>

To stay hidden, the attacker would have to forge the GST so that it matches the fake HPT, and `sysSen` as well. But the GST is what the PLC uses to decide the refill and to allow the compressor, so faking it changes the plant's behaviour in other visible ways. Every extra forged value adds new invariants that must also hold. This is why real plants combine several independent signals: an attacker who controls one of them is caught by the others. Stuxnet avoided this by replaying a whole recording of normal values, which only works while nobody compares them with an independent measurement.

</details>

## Before you start

- [The gas pressure process](/theory/physical_process)
- [Man in the middle](/theory/mitm)
- [Detection and monitoring](/theory/detection-monitoring)

Later on the path:

- [Stuxnet (2010)](/theory/stuxnet)

<details class="instructor" markdown="1">
<summary>Instructor notes</summary>

The historian export is generated by
`software/scripts/generate_physics_historian.py` with a copy of the hwio tick
and the PLC's automatic mode; `tests/test_physics_forensics.py` executes the
real hwio code against that copy. Real historians sample on their own clock,
so a live export of CybICS would show occasional repeated or skipped ticks
(the tick is about 1.09 s) and torn reads between the GST and HPT writes.
The challenge file has exactly one row per tick so the invariants hold
exactly; mention this if students try the rules on live data. The answers
are graded on the board and appear nowhere in the challenge page.

</details>
