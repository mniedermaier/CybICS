"""
CybICS IDS - Lightweight Intrusion Detection System for Industrial Control Systems
Optimized for Raspberry Pi Zero 2 W (24-32 MB memory)
"""

import os
import logging
from flask import Flask, jsonify, request, render_template

from detector import Detector

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("cybics-ids")

app = Flask(__name__)
detector = Detector()

# Auto-start detection on boot
BPF_FILTER = os.environ.get("IDS_BPF_FILTER", "net 172.18.0.0/24")
IDS_INTERFACE = os.environ.get("IDS_INTERFACE", None)
AUTO_START = os.environ.get("IDS_AUTO_START", "true").lower() == "true"

# CTF flags
CTF_FLAG_DETECTION = "CybICS(1ntrusi0n_d3tect3d)"
CTF_FLAG_FORENSICS = "CybICS(f0r3ns1c_4n4lyst)"
CTF_FLAG_EVASION = "CybICS(st34lth_0p3r4t0r)"

CTF_ALERT_THRESHOLD = 3  # minimum alerts needed for detection challenge
FORENSICS_MIN_ALERTS = 5  # minimum alerts for forensics challenge
FORENSICS_MIN_RULES = 3  # minimum distinct rule types for forensics


# ========== API ROUTES ==========

@app.route("/")
def index():
    """IDS dashboard"""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "cybics-ids"})


@app.route("/api/status")
def status():
    """Get IDS status and statistics"""
    return jsonify(detector.get_status())


@app.route("/api/alerts")
def get_alerts():
    """Get alerts, optionally filtered by since_id"""
    since_id = request.args.get("since_id", 0, type=int)
    alerts = detector.get_alerts(since_id=since_id)
    return jsonify({"alerts": alerts, "total": len(alerts)})


@app.route("/api/alerts/clear", methods=["POST"])
def clear_alerts():
    """Clear all alerts"""
    detector.clear_alerts()
    return jsonify({"success": True})


@app.route("/api/start", methods=["POST"])
def start():
    """Start the IDS detector"""
    data = request.get_json(silent=True) or {}
    interface = data.get("interface", IDS_INTERFACE)
    bpf_filter = data.get("filter", BPF_FILTER)
    ok = detector.start(interface=interface, bpf_filter=bpf_filter)
    return jsonify({"success": ok})


@app.route("/api/stop", methods=["POST"])
def stop():
    """Stop the IDS detector"""
    ok = detector.stop()
    return jsonify({"success": ok})


@app.route("/api/summary")
def summary():
    """Get alert summary statistics for dashboard charts"""
    alerts = detector.get_alerts()
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    rule_counts = {}
    source_counts = {}
    timeline = []

    for a in alerts:
        sev = a.get("severity", "low")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        rule = a.get("rule", "unknown")
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
        src = a.get("src", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1
        timeline.append({
            "timestamp": a.get("timestamp", ""),
            "severity": sev,
            "rule": rule,
        })

    # Sort sources by count descending
    top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return jsonify({
        "severity": severity_counts,
        "rules": rule_counts,
        "top_sources": [{"ip": ip, "count": c} for ip, c in top_sources],
        "timeline": timeline[-100:],  # last 100 alerts for chart
        "total": len(alerts),
    })


ALL_RULE_IDS = [
    "port_scan", "syn_flood", "modbus_flood", "modbus_unauth_write",
    "modbus_diagnostic", "s7_enumeration", "http_brute_force",
    "arp_spoof", "opcua_access",
]


@app.route("/api/rules/stats")
def rules_stats():
    """Get per-rule statistics derived from the alert buffer"""
    alerts = detector.get_alerts()

    # Initialize all rules so zero-count rules still appear
    stats = {r: {"count": 0, "last_seen": None, "sources": {}} for r in ALL_RULE_IDS}

    for a in alerts:
        rule = a.get("rule", "")
        if rule not in stats:
            stats[rule] = {"count": 0, "last_seen": None, "sources": {}}
        s = stats[rule]
        s["count"] += 1
        ts = a.get("timestamp")
        if ts and (s["last_seen"] is None or ts > s["last_seen"]):
            s["last_seen"] = ts
        src = a.get("src", "")
        if src:
            s["sources"][src] = s["sources"].get(src, 0) + 1

    # Build response with top sources per rule
    result = {}
    for rule, s in stats.items():
        top = sorted(s["sources"].items(), key=lambda x: x[1], reverse=True)[:5]
        result[rule] = {
            "count": s["count"],
            "last_seen": s["last_seen"],
            "top_sources": [{"ip": ip, "count": c} for ip, c in top],
        }

    return jsonify(result)


# ========== CTF: DETECTION CHALLENGE ==========

@app.route("/api/flag")
def get_flag():
    """CTF flag endpoint - only returns flag when IDS has detected enough alerts"""
    alert_count = detector.stats["alerts_total"]
    if alert_count >= CTF_ALERT_THRESHOLD:
        return jsonify({
            "flag": CTF_FLAG_DETECTION,
            "message": f"IDS detected {alert_count} intrusion alerts. Flag unlocked!"
        })
    else:
        return jsonify({
            "flag": None,
            "message": f"IDS has detected {alert_count}/{CTF_ALERT_THRESHOLD} alerts. "
                       "Trigger more attacks to unlock the flag."
        })


# ========== CTF: FORENSICS CHALLENGE ==========

@app.route("/api/forensics")
def forensics_briefing():
    """Get forensics challenge briefing and current investigation data"""
    alerts = detector.get_alerts()
    rules = set(a.get("rule") for a in alerts)

    if len(alerts) < FORENSICS_MIN_ALERTS:
        return jsonify({
            "ready": False,
            "message": (
                f"Insufficient alert data for investigation. "
                f"Need at least {FORENSICS_MIN_ALERTS} alerts, "
                f"currently have {len(alerts)}. "
                f"Trigger more attacks first."
            ),
            "alert_count": len(alerts),
            "required_alerts": FORENSICS_MIN_ALERTS,
            "unique_rules": len(rules),
            "required_rules": FORENSICS_MIN_RULES,
        })

    if len(rules) < FORENSICS_MIN_RULES:
        return jsonify({
            "ready": False,
            "message": (
                f"Need alerts from at least {FORENSICS_MIN_RULES} different rule types. "
                f"Currently have {len(rules)}: {', '.join(sorted(rules))}. "
                f"Try different attack techniques."
            ),
            "alert_count": len(alerts),
            "required_alerts": FORENSICS_MIN_ALERTS,
            "unique_rules": len(rules),
            "required_rules": FORENSICS_MIN_RULES,
        })

    return jsonify({
        "ready": True,
        "briefing": (
            "INCIDENT REPORT: Multiple intrusion attempts have been detected "
            "on the CybICS industrial control network (172.18.0.0/24). "
            "As the incident responder, analyze the IDS alert data using the "
            "/api/alerts and /api/summary endpoints. Answer the investigation "
            "questions to demonstrate your forensic analysis skills."
        ),
        "questions": [
            {
                "id": "top_attacker",
                "question": (
                    "What is the IP address of the top attacker "
                    "(source IP with the most alerts)?"
                ),
                "type": "string",
                "example": "172.18.0.x",
            },
            {
                "id": "unique_rules",
                "question": "How many unique detection rules have been triggered?",
                "type": "integer",
            },
            {
                "id": "critical_count",
                "question": "How many critical-severity alerts have been recorded?",
                "type": "integer",
            },
        ],
        "hint": "Use GET /api/summary for aggregated statistics and GET /api/alerts for raw alert data.",
        "submit_to": "POST /api/forensics/submit",
        "alert_count": len(alerts),
        "unique_rules": len(rules),
    })


@app.route("/api/forensics/submit", methods=["POST"])
def forensics_submit():
    """Submit forensics investigation answers"""
    data = request.get_json(silent=True) or {}
    alerts = detector.get_alerts()

    if len(alerts) < FORENSICS_MIN_ALERTS:
        return jsonify({
            "success": False,
            "message": f"Insufficient alert data. Need at least {FORENSICS_MIN_ALERTS} alerts.",
        })

    # Calculate correct answers from current alert data
    source_counts = {}
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    rules = set()

    for a in alerts:
        src = a.get("src", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1
        sev = a.get("severity", "low")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        rules.add(a.get("rule", "unknown"))

    correct_top_attacker = max(source_counts, key=source_counts.get) if source_counts else ""
    correct_unique_rules = len(rules)
    correct_critical_count = severity_counts.get("critical", 0)

    # Validate submitted answers
    errors = []

    given_top = str(data.get("top_attacker", "")).strip()
    if given_top != correct_top_attacker:
        errors.append("top_attacker: Incorrect. Check /api/summary top_sources.")

    try:
        given_rules = int(data.get("unique_rules", -1))
        if given_rules != correct_unique_rules:
            errors.append("unique_rules: Incorrect. Count distinct rule names in /api/alerts.")
    except (ValueError, TypeError):
        errors.append("unique_rules: Must be an integer.")

    try:
        given_critical = int(data.get("critical_count", -1))
        if given_critical != correct_critical_count:
            errors.append("critical_count: Incorrect. Check /api/summary severity counts.")
    except (ValueError, TypeError):
        errors.append("critical_count: Must be an integer.")

    if errors:
        return jsonify({
            "success": False,
            "message": "Investigation incomplete. Some answers are incorrect.",
            "errors": errors,
        })

    return jsonify({
        "success": True,
        "flag": CTF_FLAG_FORENSICS,
        "message": "Excellent forensic analysis! All answers correct. Flag unlocked.",
    })


# ========== CTF: EVASION CHALLENGE ==========

@app.route("/api/evasion/start", methods=["POST"])
def evasion_start():
    """Start an evasion challenge attempt"""
    result = detector.start_evasion()
    return jsonify(result)


@app.route("/api/evasion/check")
def evasion_check():
    """Check evasion challenge status and award flag on success"""
    result = detector.check_evasion()
    if result.get("success"):
        result["flag"] = CTF_FLAG_EVASION
        result["message"] = (
            "Stealth operation successful! You wrote to Modbus registers "
            "without triggering any IDS alerts. Flag unlocked."
        )
    return jsonify(result)


# ========== ENTRY POINT ==========

if __name__ == "__main__":
    port = int(os.environ.get("IDS_PORT", 8443))

    if AUTO_START:
        logger.info(f"Auto-starting detector (filter={BPF_FILTER}, interface={IDS_INTERFACE})")
        detector.start(interface=IDS_INTERFACE, bpf_filter=BPF_FILTER)

    logger.info(f"CybICS IDS starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
