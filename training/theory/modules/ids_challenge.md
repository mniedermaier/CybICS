# Intrusion detection

This module is about the IDS as a whole: generate enough malicious activity that the system
recognises it is under attack, and collect the reward for a working detection pipeline.

<figure>
<svg viewBox="0 0 520 120" role="img" aria-label="Alerts accumulating to a threshold">
  <g fill="#ff6b00" opacity="0.8">
    <rect x="30" y="70" width="24" height="20"/><rect x="64" y="60" width="24" height="30"/>
    <rect x="98" y="52" width="24" height="38"/><rect x="132" y="40" width="24" height="50"/>
  </g>
  <line x1="20" y1="50" x2="300" y2="50" stroke="currentColor" stroke-dasharray="5 4" opacity="0.5"/>
  <text x="304" y="53" font-size="10">alert threshold</text>
  <text x="20" y="108" font-size="10" opacity="0.7">alerts accumulating in the buffer</text>
  <rect x="360" y="45" width="150" height="30" rx="4" fill="#ff6b00" opacity="0.6"/>
  <text x="435" y="64" text-anchor="middle" font-size="10" fill="#1a1a1a">flag unlocked</text>
</svg>
<figcaption>Once enough alerts accumulate, the IDS confirms an intrusion and releases the flag.</figcaption>
</figure>

## The skill

Combine the attacks you have learned &mdash; scan, flood, unauthorised writes &mdash; until
the IDS has logged enough alerts to declare an intrusion. It ties the offensive modules to
their detections.

> **MITRE D3FEND:** the detection side of the whole attack lifecycle.
