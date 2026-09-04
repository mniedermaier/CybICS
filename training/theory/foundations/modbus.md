# Modbus TCP

**Modbus** is the lingua franca of industrial automation. It was designed in 1979 for
serial links and later wrapped in TCP/IP as **Modbus TCP** on port **502**. It is simple,
open, and everywhere &mdash; and it has no authentication, no encryption, and no integrity
checking. Whoever can reach port 502 can read and write the controller.

## The data model

Modbus exposes four tables of values. Two are bits, two are 16-bit words:

| Table | Access | Typical use |
|---|---|---|
| Coils | read/write | digital outputs (a valve, a motor) |
| Discrete inputs | read only | digital inputs (a limit switch) |
| Holding registers | read/write | analogue setpoints, counters |
| Input registers | read only | sensor readings |

In CybICS the plant's variables live in holding registers: gas storage tank at 1124, high
pressure tank at 1126, and so on.

## Request and response

A client (the "master") sends a request naming a **function code** and an address; the
server (the PLC) answers. There is no session and no login.

<figure>
<svg viewBox="0 0 520 180" role="img" aria-label="Modbus request and response">
  <rect x="20" y="30" width="120" height="50" rx="6" fill="#ff6b00" opacity="0.85"/>
  <text x="80" y="52" text-anchor="middle" font-size="12" fill="#1a1a1a" font-weight="bold">Client</text>
  <text x="80" y="68" text-anchor="middle" font-size="10" fill="#1a1a1a">HMI / attacker</text>
  <rect x="380" y="30" width="120" height="50" rx="6" fill="currentColor" opacity="0.2" stroke="currentColor"/>
  <text x="440" y="52" text-anchor="middle" font-size="12" font-weight="bold">Server</text>
  <text x="440" y="68" text-anchor="middle" font-size="10">PLC : 502</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <line x1="140" y1="48" x2="378" y2="48" stroke="#ff6b00" stroke-width="2" marker-end="url(#a)"/>
  <text x="260" y="42" text-anchor="middle" font-size="11">FC 06: write reg 1126 = 90</text>
  <line x1="380" y1="72" x2="142" y2="72" stroke="currentColor" stroke-width="2" opacity="0.6" marker-end="url(#a)"/>
  <text x="260" y="90" text-anchor="middle" font-size="11" opacity="0.8">echo: reg 1126 = 90 (OK)</text>
  <text x="20" y="130" font-size="11" opacity="0.8">No handshake, no credentials. The server trusts the request because it</text>
  <text x="20" y="146" font-size="11" opacity="0.8">arrived. This single fact underlies the flood, overwrite and MITM attacks.</text>
</svg>
<figcaption>A Modbus write. Function code 6 writes one register; the server applies it and echoes it back. Nothing proves the client is allowed to write.</figcaption>
</figure>

## The frame

A Modbus TCP message is a 7-byte **MBAP header** followed by the function code and its data.

<figure>
<svg viewBox="0 0 520 110" role="img" aria-label="Modbus TCP frame layout">
  <g font-size="10" text-anchor="middle">
    <rect x="10" y="30" width="70" height="40" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="45" y="20" font-size="10">2 B</text><text x="45" y="54">Transaction</text>
    <rect x="80" y="30" width="70" height="40" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="115" y="20">2 B</text><text x="115" y="54">Protocol</text>
    <rect x="150" y="30" width="70" height="40" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="185" y="20">2 B</text><text x="185" y="54">Length</text>
    <rect x="220" y="30" width="50" height="40" fill="currentColor" opacity="0.15" stroke="currentColor"/>
    <text x="245" y="20">1 B</text><text x="245" y="54">Unit</text>
    <rect x="270" y="30" width="60" height="40" fill="#ff6b00" opacity="0.7"/>
    <text x="300" y="20">1 B</text><text x="300" y="54" fill="#1a1a1a">Func</text>
    <rect x="330" y="30" width="180" height="40" fill="#ff6b00" opacity="0.35"/>
    <text x="420" y="20">n B</text><text x="420" y="54">Data (address, values)</text>
  </g>
  <text x="10" y="95" font-size="10" opacity="0.7">MBAP header (7 bytes)</text>
  <text x="420" y="95" font-size="10" opacity="0.7" text-anchor="middle">PDU</text>
</svg>
<figcaption>The frame is easy to read and to forge. In the Wireshark challenge you find a flag written byte-by-byte into holding registers.</figcaption>
</figure>

## Common function codes

- **1/2** read coils / discrete inputs
- **3/4** read holding / input registers
- **5/6** write single coil / register
- **15/16** write multiple coils / registers
- **8** diagnostics (used by the fuzzing challenge)

## Security relevance

Because Modbus authenticates nothing, the CybICS IDS cannot rely on identity. Instead it
watches **behaviour**: a burst of writes (flood), writes from an unexpected host
(unauthorised write), or odd function codes (diagnostics/fuzzing). That is the seam every
Modbus attack &mdash; and every Modbus detection &mdash; runs through.
