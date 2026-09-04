# Network scanning

Reconnaissance comes first. Scanning maps which hosts are alive and which industrial
services they run, so the attacker knows where the PLC, HMI and protocols live. In OT this
must be done carefully &mdash; aggressive scans can disturb fragile devices.

<figure>
<svg viewBox="0 0 520 130" role="img" aria-label="Port scan">
  <defs><marker id="sc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff6b00"/></marker></defs>
  <rect x="20" y="45" width="90" height="40" rx="6" fill="#ff6b00" opacity="0.8"/>
  <text x="65" y="69" text-anchor="middle" font-size="11" fill="#1a1a1a">scanner</text>
  <g font-size="10" text-anchor="middle">
    <line x1="110" y1="55" x2="380" y2="25" stroke="#ff6b00" stroke-width="1.5" marker-end="url(#sc)"/>
    <line x1="110" y1="62" x2="380" y2="55" stroke="#ff6b00" stroke-width="1.5" marker-end="url(#sc)"/>
    <line x1="110" y1="69" x2="380" y2="85" stroke="#ff6b00" stroke-width="1.5" marker-end="url(#sc)"/>
    <line x1="110" y1="76" x2="380" y2="115" stroke="#ff6b00" stroke-width="1.5" marker-end="url(#sc)"/>
    <text x="430" y="28">502 Modbus</text>
    <text x="430" y="58">102 S7</text>
    <text x="430" y="88">4840 OPC-UA</text>
    <text x="430" y="118">8080 web</text>
  </g>
  <text x="20" y="120" font-size="10" opacity="0.7">One host probing many ports is the classic scan signature.</text>
</svg>
<figcaption>A port scan probes many services on the target. It is fast and informative &mdash; and noisy, which is exactly what the detection module later catches.</figcaption>
</figure>

## The skill

Use `nmap -sV` to discover hosts and service versions on the lab network. Service banners
reveal the ICS stack; one of them even carries a flag in its HTTP `Server` header.

> **MITRE ATT&CK for ICS:** T0846 Remote System Discovery. It is loud on purpose here, to
> connect directly to the *detect a scan* module.
