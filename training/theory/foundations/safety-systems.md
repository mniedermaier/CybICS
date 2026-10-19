# Safety systems

A control system keeps the plant running well. A safety system has one job only: stop the plant from hurting anyone when everything else has gone wrong. This article explains how plants are protected in layers, where CybICS keeps its last line of defence, and why attackers who want real damage go after the safety layer first.

## Safety is not security

The two words sound alike, and in German they are even the same word: *Sicherheit*. In engineering they mean different things.

- **Safety** protects people and the environment *from the plant*. It deals with things that go wrong by accident: a sensor that drifts, a pump that wears out, an operator who presses the wrong button.
- **Security** protects the plant *from people*. It deals with someone who wants things to go wrong and chooses how and when.

<div class="callout analogy" markdown="1">
**Analogy:** a car's airbag is safety. It fires in a crash, whatever caused it. The car's door lock is security. It keeps out a person who wants in. A thief who can disable the airbag before the crash is a problem neither system was built for on its own.
</div>

Safety engineering has a long tradition and its own standards: **IEC 61508** for safety-related electronics in general and **IEC 61511** for the process industry (chemical plants, refineries, gas). These standards assume that failures are *random*: two independent parts are unlikely to break at the same moment. An attacker breaks that assumption, because an attacker can make several things fail at once, on purpose.

## Layers of protection

No single device is trusted to prevent a disaster. Plants stack several independent layers, and each one only has to catch what the layer above it missed. Engineers often draw this as an onion; the analysis method behind it is called **Layer of Protection Analysis (LOPA)**.

<figure>
<svg viewBox="0 0 520 300" role="img" aria-label="Five nested layers of protection drawn as concentric rings around the process. From the inside out: the process design itself, the basic process control system, alarms and operator response, the safety instrumented system, and physical relief devices such as a relief valve. Arrows show that each outer layer acts only when the inner one has failed.">
  <g fill="none" stroke="currentColor" stroke-width="1.5">
    <ellipse cx="260" cy="150" rx="250" ry="140" opacity="0.5"/>
    <ellipse cx="260" cy="150" rx="200" ry="112" opacity="0.6"/>
    <ellipse cx="260" cy="150" rx="150" ry="84" opacity="0.7"/>
    <ellipse cx="260" cy="150" rx="100" ry="56" opacity="0.85"/>
    <ellipse cx="260" cy="150" rx="50" ry="28" fill="#ff6b00" fill-opacity="0.2"/>
  </g>
  <g font-size="12" text-anchor="middle" fill="currentColor">
    <text x="260" y="154" font-weight="bold">Process</text>
    <text x="260" y="114">Control (BPCS / PLC)</text>
    <text x="260" y="86">Alarms + operator</text>
    <text x="260" y="58">Safety instrumented system</text>
    <text x="260" y="30">Physical relief (relief valve)</text>
  </g>
</svg>
<figcaption>Layers of protection. The control system keeps the process normal; if it fails, alarms call the operator; if the operator cannot fix it, the SIS shuts the process down; if even that fails, a mechanical relief device limits the damage.</figcaption>
</figure>

From the inside out, a typical stack looks like this:

1. **Process design.** Pipes and tanks rated for more than the normal pressure.
2. **Basic Process Control System (BPCS).** The PLC and its program, which keep the process at its set points. This is a *control* layer, not a safety layer.
3. **Alarms and the operator.** The Human-Machine Interface (HMI) warns, a person reacts.
4. **Safety Instrumented System (SIS).** A separate controller with its own sensors and its own outputs. It watches for a dangerous condition and forces the plant into a safe state, for example by cutting power to a compressor.
5. **Physical relief.** A spring-loaded relief valve or a burst disc that opens by physics alone, with no software at all.

Outside these sit containment (walls, catch basins) and emergency response. The point of the stack is **independence**: a fault in one layer should not take out another.

## What makes an SIS different

An SIS looks a lot like a PLC from the outside, but it is built and run differently.

- **Its own sensor, logic and final element.** The three parts of a safety function are a sensor (a pressure transmitter), a logic solver (the safety controller) and a final element (a valve or a contactor that cuts power). None of them should be shared with the BPCS.
- **Fail-safe by design.** Safety outputs are usually *de-energise to trip*: when a wire breaks or power fails, the output drops and the plant goes to its safe state.
- **Rated reliability.** Each safety function gets a **Safety Integrity Level (SIL)** from 1 to 4. A higher SIL means a lower allowed chance that the function fails when it is needed.
- **Rarely changed.** The safety logic is reviewed, tested and then locked. Many safety controllers have a physical key switch that must be turned before new logic can be loaded.

<div class="callout warning" markdown="1">
**Watch out:** an SIS that is connected to the plant network so engineers can monitor it from their desk is convenient, and it is also a path in. Independence on paper means little if the safety controller and the PLC sit on the same flat network with the same workstation programming both.
</div>

## Why attackers target safety

An attacker who only manipulates the control system will usually be stopped by the safety layer. The plant trips, production stops, an investigation starts, but nobody is hurt. To cause physical harm, the attacker has to defeat the safety layer *and* push the process into danger at the same time.

That is exactly what the TRITON (also called TRISIS) malware was built for. It was found in 2017 at a petrochemical facility, widely reported to be in Saudi Arabia, and targeted Schneider Electric Triconex safety controllers. A mistake in the attackers' code made the safety controllers trip and shut the process down safely, and that shutdown led to the investigation. Read the full story in [the TRITON/TRISIS case study](/theory/trisis).

MITRE ATT&CK for ICS names the outcomes **Loss of Safety (T0880)** and **Loss of Protection (T0837)**. Both describe the moment a plant can no longer protect itself.

<div data-widget="checkpoint" data-id="independence"></div>

## In CybICS: the blow-out valve

The CybICS plant pumps gas from the gas storage tank (GST) into the high-pressure tank (HPT). The roles from the onion map onto it like this:

| Layer | In CybICS |
|---|---|
| Control (BPCS) | The OpenPLC program at `172.18.0.3`. In automatic mode it starts the compressor when the HPT drops below 60 bar and stops it at 90, and it opens the system valve only between 50 and 100 bar. |
| Alarms and operator | The FUXA HMI and, on the board, the LCD status line, which reads `Pressure high` and finally `Danger! BlowOut`. |
| SIS | **None.** CybICS has no separate safety controller. |
| Physical relief | The **blow-out valve**: it opens when the HPT goes above 220 bar and stays open until the pressure has fallen back to 200. |

The blow-out valve is not part of the PLC program. It lives in the plant model itself: in `thread_physical` in the STM32 firmware and in its mirror in `hwio`. That makes it behave like a real spring-loaded valve: nothing you write to the PLC can switch it off. What travels over the network is only its *status*, which `hwio` writes into holding register 1134 (`boSen`) so the HMI can show it.

Watch it here. Normally the HPT sits between 60 and 90, the compressor cycles and the blow-out sensor stays at 0.

<div data-widget="plant-live" data-fields="hpt,compressor,systemValve,boSen"></div>

The relief valve has a limit, and that limit is the lesson. While it is open it vents at most one bar per step, and on about half of the steps none at all, while a running compressor adds one bar per step. A relief valve sized for an occasional overshoot cannot win against a compressor that is forced on. In the *Physical process* challenge you take manual control on the HMI and create that situation yourself. That challenge is an operator mistake, not a hack, but an attacker who keeps forcing coil 1 (the compressor) on over Modbus, faster than the PLC program switches it back, would reach the same state.

<div class="callout cybics" markdown="1">
**Design exercise:** where would you add an SIS to CybICS? A good answer has its own pressure sensor on the HPT, a separate logic solver, and a final element that cuts the compressor's power above a trip point well below 220 bar. It would sit on its own network segment, not on `172.18.0.0/24`, so that a Modbus write to the PLC cannot reach it.
</div>

<div data-widget="checkpoint" data-id="relief-limit"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: SIL, demand and the safety-security overlap</summary>

A SIL is defined by the *probability of failure on demand* (PFD) of a safety function that is used rarely. SIL 1 allows an average PFD between 1 in 10 and 1 in 100, and each step up is ten times stricter, so SIL 4 allows between 1 in 10,000 and 1 in 100,000. These numbers come from IEC 61508 and assume random hardware faults. They say nothing about a deliberate attacker.

The standards have started to close that gap. The 2016 edition of IEC 61511 requires a security risk assessment of the SIS, and it points to the IEC 62443 series for how to do it (see [Asset inventory, risk and IEC 62443](/theory/risk-assessment)). The usual architecture advice is to keep the SIS network physically separate from the BPCS, to allow only read-only data to flow out of it, and to keep the program key switch in the run position except during supervised changes.

</details>
