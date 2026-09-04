# Tuning the IDS

Detection only helps if it is running and its rules actually fire on real attacks. This
module has you confirm the IDS is healthy, active, and catching the techniques the lab
throws at it.

<figure>
<svg viewBox="0 0 520 110" role="img" aria-label="IDS health and active rules">
  <g font-size="10" text-anchor="middle">
    <rect x="20" y="35" width="130" height="40" rx="6" fill="#ff6b00" opacity="0.6"/>
    <text x="85" y="52" fill="#1a1a1a">engine: active</text><text x="85" y="67" fill="#1a1a1a" font-size="9">/health OK</text>
    <rect x="175" y="35" width="150" height="40" rx="6" fill="currentColor" opacity="0.18" stroke="currentColor"/>
    <text x="250" y="52">rules with hits &ge; 3</text><text x="250" y="67" font-size="9">scan, flood, unauth&hellip;</text>
    <rect x="350" y="35" width="150" height="40" rx="6" fill="#ff6b00" opacity="0.35"/>
    <text x="425" y="58">detection effective</text>
  </g>
</svg>
<figcaption>A healthy IDS: the engine is up and several rules have real hits, so the pipeline is proven end to end.</figcaption>
</figure>

## The skill

Ensure the IDS service is up and its rules have fired on the attacks you have run. The check
confirms the engine is active and multiple rules have non-zero hits.

> **NIST SP 800-82 / 800-53** SI-4 System Monitoring. Detection is only a control if it is
> maintained.
