#!/usr/bin/env python3
"""
CybICS IDS Forensics Challenge - Solution Script
Queries IDS alert data, analyzes it, and submits the correct forensic answers.

Usage:
    python3 solve_ids_forensics.py [ids_url]

Default:
    ids_url = http://localhost:8443

Prerequisites:
    The IDS must have at least 5 alerts from at least 3 different rule types.
    Run solve_ids_challenge.py first if you don't have enough alerts.
"""

import sys
import argparse
import requests

parser = argparse.ArgumentParser(description="Solve the IDS Forensics Challenge")
parser.add_argument("ids_url", nargs="?", default="http://localhost:8443",
                    help="IDS base URL (default: http://localhost:8443)")
args = parser.parse_args()

IDS_URL = args.ids_url


def main():
    print("=" * 60)
    print("  CybICS IDS Forensics Challenge - Solution")
    print("  Analyzing IDS alert data for incident investigation")
    print("=" * 60)

    # Step 1: Check if forensics challenge is ready
    print("\n[*] Step 1: Checking forensics readiness...")
    try:
        r = requests.get(f"{IDS_URL}/api/forensics", timeout=5)
        briefing = r.json()
    except Exception as e:
        print(f"[-] Cannot reach IDS at {IDS_URL}: {e}")
        sys.exit(1)

    if not briefing.get("ready"):
        print(f"[-] Not ready: {briefing.get('message')}")
        print("[!] Run solve_ids_challenge.py first to generate alerts.")
        sys.exit(1)

    print(f"[+] Investigation ready ({briefing['alert_count']} alerts, "
          f"{briefing['unique_rules']} rule types)")

    # Step 2: Gather intelligence from /api/summary
    print("\n[*] Step 2: Querying /api/summary for aggregated data...")
    r = requests.get(f"{IDS_URL}/api/summary", timeout=5)
    summary = r.json()

    print(f"    Total alerts: {summary['total']}")
    print(f"    Severity breakdown: {summary['severity']}")
    print(f"    Rules triggered: {summary['rules']}")
    print(f"    Top sources: {summary['top_sources']}")

    # Step 3: Gather raw alert data from /api/alerts
    print("\n[*] Step 3: Querying /api/alerts for raw data...")
    r = requests.get(f"{IDS_URL}/api/alerts", timeout=5)
    alerts_data = r.json()

    alerts = alerts_data["alerts"]
    print(f"    Retrieved {len(alerts)} alerts")

    # Step 4: Analyze the data to answer investigation questions
    print("\n[*] Step 4: Analyzing alert data...")

    # Question 1: Top attacker IP (source with most alerts)
    source_counts = {}
    for a in alerts:
        src = a.get("src", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    top_attacker = max(source_counts, key=source_counts.get)
    print(f"    Q1 - Top attacker: {top_attacker} "
          f"({source_counts[top_attacker]} alerts)")

    # Question 2: Number of unique detection rules
    rules = set(a.get("rule") for a in alerts)
    unique_rules = len(rules)
    print(f"    Q2 - Unique rules: {unique_rules} "
          f"({', '.join(sorted(rules))})")

    # Question 3: Number of critical-severity alerts
    critical_count = sum(1 for a in alerts if a.get("severity") == "critical")
    print(f"    Q3 - Critical alerts: {critical_count}")

    # Alternative: get the same answers from /api/summary directly
    print("\n    -- Cross-validation from /api/summary --")
    alt_top = summary["top_sources"][0]["ip"] if summary["top_sources"] else "N/A"
    alt_rules = len(summary["rules"])
    alt_critical = summary["severity"]["critical"]
    print(f"    Top attacker (summary): {alt_top}")
    print(f"    Unique rules (summary): {alt_rules}")
    print(f"    Critical count (summary): {alt_critical}")

    # Step 5: Submit answers
    print("\n[*] Step 5: Submitting investigation report...")
    submission = {
        "top_attacker": top_attacker,
        "unique_rules": unique_rules,
        "critical_count": critical_count,
    }
    print(f"    Payload: {submission}")

    r = requests.post(
        f"{IDS_URL}/api/forensics/submit",
        json=submission,
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    result = r.json()

    if result.get("success"):
        print(f"\n{'='*60}")
        print(f"  FLAG: {result['flag']}")
        print(f"  {result['message']}")
        print(f"{'='*60}\n")
    else:
        print(f"\n[-] Submission failed: {result.get('message')}")
        if result.get("errors"):
            for err in result["errors"]:
                print(f"    - {err}")


if __name__ == "__main__":
    main()
