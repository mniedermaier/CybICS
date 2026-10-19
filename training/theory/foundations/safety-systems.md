# Safety systems

A control system keeps the plant running well. A safety system has one job: stop the plant from hurting anyone when everything else has gone wrong. Attackers who want real damage go after this layer first.

## Safety is not security

The two words sound alike (in German both are *Sicherheit*), but in engineering they mean different things.

- **Safety** protects people and the environment *from the plant*. It handles accidents: a sensor that drifts, a pump that wears out, an operator who presses the wrong button.
- **Security** protects the plant *from people*: someone who wants things to go wrong and chooses how and when.

<div class="callout analogy" markdown="1">
**Analogy:** a car's airbag is safety: it fires in a crash, whatever caused it. The door lock is security: it keeps out a person who wants in. A thief who disables the airbag before the crash is a problem neither was built for on its own.
</div>

Safety standards assume that failures are *random*: two independent parts are unlikely to break at the same moment. An attacker breaks that assumption, because an attacker can make several things fail at once, on purpose.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the safety standards</summary>

Safety engineering has a long tradition and its own standards: **IEC 61508** for safety-related electronics in general and **IEC 61511** for the process industry (chemical plants, refineries, gas). The method engineers use to decide how many layers of protection a hazard needs is called **Layer of Protection Analysis (LOPA)**.

</details>

## Layers of protection

No single device is trusted to prevent a disaster. Plants stack independent layers, drawn as an onion; each catches what the one before it missed.

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
<figcaption>Layers of protection around the process. Each outer layer acts only when the layers inside it have failed.</figcaption>
</figure>

From the inside out:

1. **Process design.** Pipes and tanks rated above the normal pressure.
2. **Basic Process Control System (BPCS).** The PLC and its program keep the process at its set points. This is a *control* layer, not a safety layer.
3. **Alarms and the operator.** The Human-Machine Interface (HMI) warns, a person reacts.
4. **Safety Instrumented System (SIS).** A separate controller with its own sensors and outputs that forces the plant into a safe state, for example by cutting a compressor's power.
5. **Physical relief.** A spring-loaded relief valve or a burst disc that opens by physics alone, with no software.

The point of the stack is **independence**: a fault in one layer should not take out another.

## What makes an SIS different

An SIS looks like a PLC from the outside, but it is built and run differently.

- **Its own sensor, logic and final element.** A safety function has a sensor (a pressure transmitter), a logic solver (the safety controller) and a final element (a valve or a contactor that cuts power). None of them should be shared with the BPCS.
- **Fail-safe by design.** When a wire breaks or power fails, the output drops and the plant goes to its safe state.
- **Rated reliability.** Each safety function gets a **Safety Integrity Level (SIL)** from 1 to 4. A higher SIL means a lower allowed chance that it fails when needed.
- **Rarely changed.** The safety logic is reviewed, tested and then locked.

<div class="callout warning" markdown="1">
**Watch out:** an SIS on the plant network is convenient, and it is also a path in. Independence means little if the safety controller and the PLC share one flat network and one programming workstation.
</div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: de-energise to trip and the key switch</summary>

Safety outputs are usually *de-energise to trip*: the output is powered in normal operation, so any loss of power or a broken wire drops it and trips the plant. Many safety controllers also have a physical key switch that must be turned before new logic can be loaded.

</details>

## Why attackers target safety

An attacker who only manipulates the control system will usually be stopped by the safety layer. The plant trips, but nobody is hurt. To cause harm, the attacker must defeat the safety layer *and* push the process into danger at the same time.

That is what the TRITON (also called TRISIS) malware was built for. Found in 2017 at a petrochemical facility, it targeted Schneider Electric Triconex safety controllers. A mistake in its code tripped the controllers and shut the process down safely, which gave it away. Read the full story in [the TRITON/TRISIS case study](/theory/trisis).

MITRE ATT&CK for ICS names the outcomes **Loss of Safety (T0880)** and **Loss of Protection (T0837)**: the moment a plant can no longer protect itself.

<div data-widget="checkpoint" data-id="independence"></div>

## In CybICS: the blow-out valve

The CybICS plant pumps gas from the gas storage tank (GST) into the high-pressure tank (HPT). The onion maps onto it like this:

| Layer | In CybICS |
|---|---|
| Control (BPCS) | The OpenPLC program at `172.18.0.3`. In automatic mode it runs the compressor to keep the HPT between 60 and 90 bar. |
| Alarms and operator | The FUXA HMI and, on the board, the LCD status line, which reads `Pressure high` and finally `Danger! BlowOut`. |
| SIS | **None.** CybICS has no separate safety controller. |
| Physical relief | The **blow-out valve**: it opens when the HPT goes above 220 bar and stays open until the pressure has fallen back to 200. |

The blow-out valve is not part of the PLC program. It lives in the plant model itself, the simulated physics in the firmware and in `hwio`, so it behaves like a real spring-loaded valve: nothing you write to the PLC can switch it off. Only its *status* travels over the network, so the HMI can show it.

Normally the HPT sits between 60 and 90, the compressor cycles and the blow-out sensor (`boSen`) stays at 0:

<div data-widget="plant-live" data-fields="hpt,compressor,systemValve,boSen"></div>

The relief valve has a limit, and that limit is the lesson. While open it vents at most one bar per step, and on about half of the steps none at all, while a running compressor adds one bar per step. A valve sized for an occasional overshoot cannot win against a compressor that is forced on. In the *Physical process* challenge you create that situation yourself from the HMI.

<details class="deep-dive" markdown="1">
<summary>Deep dive: the PLC set points, where the valve lives, and the attacker's version</summary>

The PLC starts the compressor when the HPT drops below 60 bar, stops it at 90, and opens the system valve only between 50 and 100 bar.

The blow-out logic is in `thread_physical` in the STM32 firmware and in its mirror in `hwio`. `hwio` writes the valve's status into holding register 1134 (`boSen`).

The *Physical process* challenge is an operator mistake, not a hack, but an attacker who keeps forcing coil 1 (the compressor) on over Modbus, faster than the PLC program switches it back, would reach the same state.

</details>

<div class="callout cybics" markdown="1">
**Design exercise:** where would you add an SIS to CybICS? Give it its own HPT pressure sensor, logic solver and a final element that cuts the compressor's power well below 220 bar, on a network segment that a Modbus write to the PLC cannot reach.
</div>

<div data-widget="checkpoint" data-id="relief-limit"></div>

<details class="deep-dive" markdown="1">
<summary>Deep dive: SIL, demand and the safety-security overlap</summary>

A SIL is defined by the *probability of failure on demand* (PFD) of a safety function that is used rarely. SIL 1 allows an average PFD between 1 in 10 and 1 in 100, and each step up is ten times stricter, so SIL 4 allows between 1 in 10,000 and 1 in 100,000. These numbers come from IEC 61508 and assume random hardware faults. They say nothing about a deliberate attacker.

The standards have started to close that gap. The 2016 edition of IEC 61511 requires a security risk assessment of the SIS, and it points to the IEC 62443 series for how to do it (see [Asset inventory, risk and IEC 62443](/theory/risk-assessment)). The usual architecture advice is to keep the SIS network physically separate from the BPCS, to allow only read-only data to flow out of it, and to keep the program key switch in the run position except during supervised changes.

</details>
