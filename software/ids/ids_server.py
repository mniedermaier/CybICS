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

# CTF flag - revealed via the /flag endpoint when enough alerts are detected
CTF_FLAG = "CybICS(1ntrusi0n_d3tect3d)"
CTF_ALERT_THRESHOLD = 3  # minimum alerts needed to unlock flag


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


@app.route("/api/flag")
def get_flag():
    """CTF flag endpoint - only returns flag when IDS has detected enough alerts"""
    alert_count = detector.stats["alerts_total"]
    if alert_count >= CTF_ALERT_THRESHOLD:
        return jsonify({
            "flag": CTF_FLAG,
            "message": f"IDS detected {alert_count} intrusion alerts. Flag unlocked!"
        })
    else:
        return jsonify({
            "flag": None,
            "message": f"IDS has detected {alert_count}/{CTF_ALERT_THRESHOLD} alerts. "
                       "Trigger more attacks to unlock the flag."
        })


# ========== ENTRY POINT ==========

if __name__ == "__main__":
    port = int(os.environ.get("IDS_PORT", 8443))

    if AUTO_START:
        logger.info(f"Auto-starting detector (filter={BPF_FILTER}, interface={IDS_INTERFACE})")
        detector.start(interface=IDS_INTERFACE, bpf_filter=BPF_FILTER)

    logger.info(f"CybICS IDS starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
