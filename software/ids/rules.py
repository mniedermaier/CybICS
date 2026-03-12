"""
CybICS IDS - Detection Rules for Industrial Control Systems
Lightweight rule engine optimized for Raspberry Pi Zero 2 W
"""

from collections import deque
import time
import logging

logger = logging.getLogger("cybics-ids")

# Severity levels
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

# MITRE ATT&CK for ICS technique references
MITRE_DISCOVERY = "T0846"
MITRE_NETWORK_SNIFFING = "T0842"
MITRE_UNAUTHORIZED_CMD = "T0855"
MITRE_FLOODING = "T0836"
MITRE_MANIPULATION = "T0831"
MITRE_SPOOF_REPORTING = "T0856"
MITRE_BRUTE_FORCE = "T0812"

# CybICS network constants
CYBICS_SUBNET = "172.18.0."
KNOWN_SERVICES = {
    "172.18.0.2": "hwio",
    "172.18.0.3": "openplc",
    "172.18.0.4": "fuxa",
    "172.18.0.5": "opcua",
    "172.18.0.6": "s7com",
    "172.18.0.7": "stm32",
    "172.18.0.10": "engineeringws",
    "172.18.0.11": "cybicsagent",
    "172.18.0.100": "attack-machine",
}

# Modbus function codes considered dangerous (write operations)
MODBUS_WRITE_FUNCTIONS = {0x05, 0x06, 0x0F, 0x10}
MODBUS_DIAGNOSTIC = {0x08, 0x2B}


class RuleEngine:
    """Lightweight ICS-focused rule engine with sliding window counters"""

    def __init__(self):
        # Sliding window trackers (source_ip -> deque of timestamps)
        self.port_scan_tracker = {}
        self.modbus_write_tracker = {}
        self.modbus_flood_tracker = {}
        self.http_login_tracker = {}
        self.syn_tracker = {}
        self.arp_tracker = {}  # ip -> set of MAC addresses

        # Thresholds
        self.PORT_SCAN_THRESHOLD = 5         # ports in window
        self.PORT_SCAN_WINDOW = 10           # seconds
        self.MODBUS_FLOOD_THRESHOLD = 50     # writes in window
        self.MODBUS_FLOOD_WINDOW = 5         # seconds
        self.MODBUS_WRITE_THRESHOLD = 10     # writes from unknown source in window
        self.MODBUS_WRITE_WINDOW = 30        # seconds
        self.HTTP_BRUTE_THRESHOLD = 5        # login attempts in window
        self.HTTP_BRUTE_WINDOW = 30          # seconds
        self.SYN_FLOOD_THRESHOLD = 100       # SYNs in window
        self.SYN_FLOOD_WINDOW = 10           # seconds

        # Deduplication: avoid repeating same alert
        self.recent_alerts = {}  # (rule, src) -> last_alert_time
        self.ALERT_COOLDOWN = 30  # seconds before re-alerting same rule+source

    def _should_alert(self, rule_name, source_ip):
        """Rate-limit alerts: one per rule+source per cooldown period"""
        key = (rule_name, source_ip)
        now = time.time()
        last = self.recent_alerts.get(key, 0)
        if now - last < self.ALERT_COOLDOWN:
            return False
        self.recent_alerts[key] = now
        return True

    def _track_event(self, tracker, key, window):
        """Add timestamp to sliding window tracker, prune old entries"""
        now = time.time()
        if key not in tracker:
            tracker[key] = deque(maxlen=200)
        tracker[key].append(now)
        # Prune entries outside window
        while tracker[key] and tracker[key][0] < now - window:
            tracker[key].popleft()
        return len(tracker[key])

    def check_packet(self, pkt_info):
        """
        Analyze a parsed packet dict and return a list of alerts (may be empty).

        pkt_info keys: src_ip, dst_ip, proto, sport, dport, flags,
                       payload (bytes), arp_op, arp_src_mac, arp_src_ip
        """
        alerts = []

        src_ip = pkt_info.get("src_ip", "")
        dst_ip = pkt_info.get("dst_ip", "")
        proto = pkt_info.get("proto", "")
        sport = pkt_info.get("sport", 0)
        dport = pkt_info.get("dport", 0)
        flags = pkt_info.get("flags", "")
        payload = pkt_info.get("payload", b"")

        # --- Rule 1: Port Scan Detection ---
        if proto == "TCP" and "S" in flags and "A" not in flags:
            key = (src_ip, dst_ip)
            # Track unique destination ports per source->target pair
            port_key = f"{src_ip}->{dst_ip}"
            if port_key not in self.port_scan_tracker:
                self.port_scan_tracker[port_key] = {}
            now = time.time()
            self.port_scan_tracker[port_key][dport] = now
            # Prune old entries
            self.port_scan_tracker[port_key] = {
                p: t for p, t in self.port_scan_tracker[port_key].items()
                if now - t < self.PORT_SCAN_WINDOW
            }
            unique_ports = len(self.port_scan_tracker[port_key])
            if unique_ports >= self.PORT_SCAN_THRESHOLD:
                if self._should_alert("port_scan", src_ip):
                    alerts.append({
                        "rule": "port_scan",
                        "severity": SEVERITY_MEDIUM,
                        "mitre": MITRE_DISCOVERY,
                        "src": src_ip,
                        "dst": dst_ip,
                        "message": f"Port scan detected: {unique_ports} ports probed on {dst_ip}",
                        "details": f"Ports: {sorted(self.port_scan_tracker[port_key].keys())}"
                    })

        # --- Rule 2: SYN Flood Detection ---
        if proto == "TCP" and "S" in flags and "A" not in flags:
            count = self._track_event(self.syn_tracker, src_ip, self.SYN_FLOOD_WINDOW)
            if count >= self.SYN_FLOOD_THRESHOLD:
                if self._should_alert("syn_flood", src_ip):
                    alerts.append({
                        "rule": "syn_flood",
                        "severity": SEVERITY_HIGH,
                        "mitre": MITRE_FLOODING,
                        "src": src_ip,
                        "dst": dst_ip,
                        "message": f"SYN flood detected: {count} SYN packets in {self.SYN_FLOOD_WINDOW}s",
                    })

        # --- Rule 3: Modbus Write Flood (skip known services like HWIO/FUXA) ---
        if (dport == 502 or sport == 502) and len(payload) >= 8:
            try:
                func_code = payload[7] & 0x7F  # mask error bit
                if func_code in MODBUS_WRITE_FUNCTIONS:
                    # Skip known services that legitimately write at high rates
                    if KNOWN_SERVICES.get(src_ip) not in ("hwio", "fuxa", "openplc"):
                        count = self._track_event(
                            self.modbus_flood_tracker, src_ip, self.MODBUS_FLOOD_WINDOW
                        )
                        if count >= self.MODBUS_FLOOD_THRESHOLD:
                            if self._should_alert("modbus_flood", src_ip):
                                alerts.append({
                                    "rule": "modbus_flood",
                                    "severity": SEVERITY_CRITICAL,
                                    "mitre": MITRE_FLOODING,
                                    "src": src_ip,
                                    "dst": dst_ip,
                                    "message": f"Modbus write flood: {count} writes in {self.MODBUS_FLOOD_WINDOW}s",
                                })
            except (IndexError, TypeError):
                pass

        # --- Rule 4: Modbus Unauthorized Write ---
        if dport == 502 and len(payload) >= 8:
            try:
                func_code = payload[7] & 0x7F
                if func_code in MODBUS_WRITE_FUNCTIONS:
                    # Only known services should write to PLC
                    if src_ip not in KNOWN_SERVICES or KNOWN_SERVICES.get(src_ip) not in (
                        "hwio", "fuxa"
                    ):
                        count = self._track_event(
                            self.modbus_write_tracker, src_ip, self.MODBUS_WRITE_WINDOW
                        )
                        if count >= self.MODBUS_WRITE_THRESHOLD:
                            if self._should_alert("modbus_unauth_write", src_ip):
                                alerts.append({
                                    "rule": "modbus_unauth_write",
                                    "severity": SEVERITY_HIGH,
                                    "mitre": MITRE_UNAUTHORIZED_CMD,
                                    "src": src_ip,
                                    "dst": dst_ip,
                                    "message": f"Unauthorized Modbus writes from {src_ip} ({count} in {self.MODBUS_WRITE_WINDOW}s)",
                                })
            except (IndexError, TypeError):
                pass

        # --- Rule 5: Modbus Diagnostic/Special Functions ---
        if dport == 502 and len(payload) >= 8:
            try:
                func_code = payload[7] & 0x7F
                if func_code in MODBUS_DIAGNOSTIC:
                    if self._should_alert("modbus_diagnostic", src_ip):
                        alerts.append({
                            "rule": "modbus_diagnostic",
                            "severity": SEVERITY_MEDIUM,
                            "mitre": MITRE_DISCOVERY,
                            "src": src_ip,
                            "dst": dst_ip,
                            "message": f"Modbus diagnostic function 0x{func_code:02X} from {src_ip}",
                        })
            except (IndexError, TypeError):
                pass

        # --- Rule 6: S7comm Enumeration ---
        if (dport == 102 or dport == 1102) and len(payload) >= 4:
            # COTP + S7comm: look for SZL read (system info enumeration)
            if self._should_alert("s7_enumeration", src_ip):
                alerts.append({
                    "rule": "s7_enumeration",
                    "severity": SEVERITY_MEDIUM,
                    "mitre": MITRE_DISCOVERY,
                    "src": src_ip,
                    "dst": dst_ip,
                    "message": f"S7comm access from {src_ip} to port {dport}",
                })

        # --- Rule 7: HTTP Brute Force (OpenPLC/FUXA login) ---
        if dport in (8080, 1881) and proto == "TCP" and len(payload) > 0:
            try:
                payload_str = payload[:200].decode("utf-8", errors="ignore")
                if "POST" in payload_str and ("login" in payload_str.lower() or "auth" in payload_str.lower()):
                    count = self._track_event(
                        self.http_login_tracker, f"{src_ip}:{dport}", self.HTTP_BRUTE_WINDOW
                    )
                    if count >= self.HTTP_BRUTE_THRESHOLD:
                        target = "OpenPLC" if dport == 8080 else "FUXA"
                        if self._should_alert("http_brute_force", src_ip):
                            alerts.append({
                                "rule": "http_brute_force",
                                "severity": SEVERITY_HIGH,
                                "mitre": MITRE_BRUTE_FORCE,
                                "src": src_ip,
                                "dst": dst_ip,
                                "message": f"Brute force on {target}: {count} login attempts in {self.HTTP_BRUTE_WINDOW}s",
                            })
            except Exception:
                pass

        # --- Rule 8: ARP Spoofing Detection ---
        if pkt_info.get("arp_op"):
            arp_src_ip = pkt_info.get("arp_src_ip", "")
            arp_src_mac = pkt_info.get("arp_src_mac", "")
            if arp_src_ip and arp_src_mac:
                if arp_src_ip not in self.arp_tracker:
                    self.arp_tracker[arp_src_ip] = set()
                self.arp_tracker[arp_src_ip].add(arp_src_mac)
                if len(self.arp_tracker[arp_src_ip]) > 1:
                    if self._should_alert("arp_spoof", arp_src_ip):
                        alerts.append({
                            "rule": "arp_spoof",
                            "severity": SEVERITY_CRITICAL,
                            "mitre": MITRE_SPOOF_REPORTING,
                            "src": arp_src_ip,
                            "dst": "",
                            "message": f"ARP spoofing: IP {arp_src_ip} seen with multiple MACs: {self.arp_tracker[arp_src_ip]}",
                        })

        # --- Rule 9: OPC-UA Unauthorized Access ---
        if dport == 4840 and len(payload) >= 8:
            if src_ip not in KNOWN_SERVICES:
                if self._should_alert("opcua_access", src_ip):
                    alerts.append({
                        "rule": "opcua_access",
                        "severity": SEVERITY_LOW,
                        "mitre": MITRE_DISCOVERY,
                        "src": src_ip,
                        "dst": dst_ip,
                        "message": f"OPC-UA access from non-service host {src_ip}",
                    })

        return alerts

    def get_stats(self):
        """Return current tracker sizes for monitoring"""
        return {
            "port_scan_tracked": len(self.port_scan_tracker),
            "modbus_flood_tracked": len(self.modbus_flood_tracker),
            "modbus_write_tracked": len(self.modbus_write_tracker),
            "http_login_tracked": len(self.http_login_tracker),
            "syn_tracked": len(self.syn_tracker),
            "arp_tracked": len(self.arp_tracker),
            "alert_cooldowns": len(self.recent_alerts),
        }

    def cleanup(self):
        """Periodic cleanup of stale tracker entries to free memory"""
        now = time.time()
        # Clean up old cooldowns
        self.recent_alerts = {
            k: v for k, v in self.recent_alerts.items()
            if now - v < self.ALERT_COOLDOWN * 2
        }
        # Clean up old port scan entries
        for key in list(self.port_scan_tracker.keys()):
            self.port_scan_tracker[key] = {
                p: t for p, t in self.port_scan_tracker[key].items()
                if now - t < self.PORT_SCAN_WINDOW * 2
            }
            if not self.port_scan_tracker[key]:
                del self.port_scan_tracker[key]
