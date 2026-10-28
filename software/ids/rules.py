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
# Unauthorized Message: Command Message.  The catalogue folded the older T0855
# into this sub-technique; the Modbus rules above still carry T0855.
MITRE_COMMAND_MESSAGE = "T1692.001"

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
    "172.18.0.12": "nginx-proxy",
    "172.18.0.100": "attack-machine",
}

# Modbus function codes considered dangerous (write operations).
# Note that the flood and unauthorised-write rules below only ever look at
# these codes, so a *read* flood raises nothing regardless of its rate.  That
# is deliberate -- reads are normal polling traffic here -- but it means the
# detection modules must not be described as catching Modbus flooding in
# general.
MODBUS_WRITE_FUNCTIONS = {0x05, 0x06, 0x0F, 0x10}
MODBUS_DIAGNOSTIC = {0x08, 0x2B}

# S7comm memory areas, as they appear in a read/write item's area byte.
S7_AREAS = {0x81: "PE", 0x82: "PA", 0x83: "MK", 0x84: "DB", 0x1C: "CT", 0x1D: "TM"}
# At most this many items of one WriteVar request are reported in an alert,
# and at most this many data bytes of each item.
S7_MAX_ITEMS = 8
S7_MAX_DATA = 16

# Services that legitimately write to Modbus at high rates
_MODBUS_WRITERS = frozenset(("hwio", "fuxa", "openplc"))
# Services allowed to do Modbus writes without triggering unauth rule
_MODBUS_AUTH_WRITERS = frozenset(("hwio", "fuxa"))
# Services that legitimately originate OPC-UA sessions.  Deliberately narrower
# than KNOWN_SERVICES: the bundled attack machine is a known service too, and
# exempting all of KNOWN_SERVICES meant OPC-UA activity from the attack box
# never raised an alert -- the one host the exercise expects to be detected.
_OPCUA_CLIENTS = frozenset(("hwio", "fuxa", "openplc", "opcua"))

# Packet tuple indices (matches _parse_raw_packet output)
_SRC_IP = 0
_DST_IP = 1
_SPORT = 2
_DPORT = 3
_FLAGS = 4
_PROTO = 5   # 6=TCP, 17=UDP, 0=ARP, -1=OTHER
_PAYLOAD = 6
_ARP_OP = 7
_ARP_SRC_MAC = 8
_ARP_SRC_IP = 9


class RuleEngine:
    """Lightweight ICS-focused rule engine with sliding window counters.

    Packet format: tuple (src_ip, dst_ip, sport, dport, flags, proto_id,
                          payload, arp_op, arp_src_mac, arp_src_ip)
    """

    def __init__(self):
        # Sliding window trackers (key -> deque of timestamps)
        self.port_scan_tracker = {}
        self.modbus_write_tracker = {}
        self.modbus_flood_tracker = {}
        self.http_login_tracker = {}
        self.syn_tracker = {}
        self.arp_tracker = {}  # ip -> set of MAC addresses

        # Thresholds
        self.PORT_SCAN_THRESHOLD = 5
        self.PORT_SCAN_WINDOW = 10
        self.MODBUS_FLOOD_THRESHOLD = 50
        self.MODBUS_FLOOD_WINDOW = 5
        self.MODBUS_WRITE_THRESHOLD = 10
        self.MODBUS_WRITE_WINDOW = 30
        self.HTTP_BRUTE_THRESHOLD = 5
        self.HTTP_BRUTE_WINDOW = 30
        self.SYN_FLOOD_THRESHOLD = 100
        self.SYN_FLOOD_WINDOW = 10

        # Deduplication: avoid repeating same alert
        self.recent_alerts = {}  # (rule, src) -> last_alert_time
        self.s7_last_write = {}  # (dst, port) -> ((src, items), time) of the last write
        self.ALERT_COOLDOWN = 30

    def _should_alert(self, rule_name, source_ip, now):
        """Rate-limit alerts: one per rule+source per cooldown period"""
        key = (rule_name, source_ip)
        last = self.recent_alerts.get(key, 0)
        if now - last < self.ALERT_COOLDOWN:
            return False
        self.recent_alerts[key] = now
        return True

    def _track_event(self, tracker, key, window, now):
        """Add timestamp to sliding window tracker, prune old entries"""
        if key not in tracker:
            tracker[key] = deque(maxlen=200)
        dq = tracker[key]
        dq.append(now)
        cutoff = now - window
        while dq[0] < cutoff:
            dq.popleft()
        return len(dq)

    def check_packet(self, pkt):
        """Analyze a parsed packet tuple and return a list of alerts (may be empty).

        Dispatches by protocol/port for early exit on irrelevant packets.
        """
        proto = pkt[_PROTO]

        # ARP packets -> rule 8 only
        if proto == 0:
            return self._check_arp(pkt)

        # Non-TCP packets: only UDP to specific ports could matter,
        # but our rules only check TCP. Skip.
        if proto != 6:
            return []

        # TCP packets — dispatch by port
        src_ip = pkt[_SRC_IP]
        dport = pkt[_DPORT]
        sport = pkt[_SPORT]
        flags = pkt[_FLAGS]

        # Check if SYN-only (S set, A not set)
        is_syn = "S" in flags and "A" not in flags

        alerts = []

        # SYN packets: port scan + SYN flood (rules 1, 2)
        if is_syn:
            now = time.time()
            self._check_syn(pkt, src_ip, dport, now, alerts)

        # Port-specific rules
        if dport == 502:
            # Modbus rules 3, 4, 5 (merged)
            self._check_modbus(pkt, src_ip, alerts)
        elif dport == 102 or dport == 1102:
            # S7comm rule 6
            self._check_s7(pkt, src_ip, dport, alerts)
        elif dport == 8080 or dport == 1881:
            # HTTP brute force rule 7
            self._check_http_brute(pkt, src_ip, dport, alerts)
        elif dport == 4840:
            # OPC-UA rule 9
            self._check_opcua(pkt, src_ip, alerts)

        return alerts

    # ---- Rule 1 + 2: Port scan + SYN flood ----

    def _check_syn(self, pkt, src_ip, dport, now, alerts):
        dst_ip = pkt[_DST_IP]

        # Rule 1: Port scan — track unique dst ports per src->dst pair
        port_key = (src_ip, dst_ip)
        tracker = self.port_scan_tracker
        if port_key not in tracker:
            tracker[port_key] = {}
        ports = tracker[port_key]
        ports[dport] = now
        # Prune expired entries before checking threshold
        cutoff = now - self.PORT_SCAN_WINDOW
        tracker[port_key] = {p: t for p, t in ports.items() if t >= cutoff}
        ports = tracker[port_key]
        unique_ports = len(ports)
        if unique_ports >= self.PORT_SCAN_THRESHOLD:
            if self._should_alert("port_scan", src_ip, now):
                alerts.append({
                    "rule": "port_scan",
                    "severity": SEVERITY_MEDIUM,
                    "mitre": MITRE_DISCOVERY,
                    "src": src_ip,
                    "dst": dst_ip,
                    "message": f"Port scan detected: {unique_ports} ports probed on {dst_ip}",
                    "details": f"Ports: {sorted(ports.keys())}"
                })

        # Rule 2: SYN flood
        count = self._track_event(self.syn_tracker, src_ip, self.SYN_FLOOD_WINDOW, now)
        if count >= self.SYN_FLOOD_THRESHOLD:
            if self._should_alert("syn_flood", src_ip, now):
                alerts.append({
                    "rule": "syn_flood",
                    "severity": SEVERITY_HIGH,
                    "mitre": MITRE_FLOODING,
                    "src": src_ip,
                    "dst": dst_ip,
                    "message": f"SYN flood detected: {count} SYN packets in {self.SYN_FLOOD_WINDOW}s",
                })

    # ---- Rules 3, 4, 5: Modbus (merged, single func_code parse) ----

    def _check_modbus(self, pkt, src_ip, alerts):
        payload = pkt[_PAYLOAD]
        if len(payload) < 8:
            return

        func_code = payload[7] & 0x7F
        dst_ip = pkt[_DST_IP]
        service = KNOWN_SERVICES.get(src_ip)

        if func_code in MODBUS_WRITE_FUNCTIONS:
            now = time.time()

            # Rule 3: Modbus write flood (skip known Modbus writers)
            if service not in _MODBUS_WRITERS:
                count = self._track_event(
                    self.modbus_flood_tracker, src_ip, self.MODBUS_FLOOD_WINDOW, now
                )
                if count >= self.MODBUS_FLOOD_THRESHOLD:
                    if self._should_alert("modbus_flood", src_ip, now):
                        alerts.append({
                            "rule": "modbus_flood",
                            "severity": SEVERITY_CRITICAL,
                            "mitre": MITRE_FLOODING,
                            "src": src_ip,
                            "dst": dst_ip,
                            "message": f"Modbus write flood: {count} writes in {self.MODBUS_FLOOD_WINDOW}s",
                        })

            # Rule 4: Modbus unauthorized write
            if service not in _MODBUS_AUTH_WRITERS:
                count = self._track_event(
                    self.modbus_write_tracker, src_ip, self.MODBUS_WRITE_WINDOW, now
                )
                if count >= self.MODBUS_WRITE_THRESHOLD:
                    if self._should_alert("modbus_unauth_write", src_ip, now):
                        alerts.append({
                            "rule": "modbus_unauth_write",
                            "severity": SEVERITY_HIGH,
                            "mitre": MITRE_UNAUTHORIZED_CMD,
                            "src": src_ip,
                            "dst": dst_ip,
                            "message": f"Unauthorized Modbus writes from {src_ip} ({count} in {self.MODBUS_WRITE_WINDOW}s)",
                        })

        # Rule 5: Modbus diagnostic functions
        elif func_code in MODBUS_DIAGNOSTIC:
            now = time.time()
            if self._should_alert("modbus_diagnostic", src_ip, now):
                alerts.append({
                    "rule": "modbus_diagnostic",
                    "severity": SEVERITY_MEDIUM,
                    "mitre": MITRE_DISCOVERY,
                    "src": src_ip,
                    "dst": dst_ip,
                    "message": f"Modbus diagnostic function 0x{func_code:02X} from {src_ip}",
                })

    # ---- Rules 6 + 10: S7comm access and S7comm writes ----

    def _check_s7(self, pkt, src_ip, dport, alerts):
        payload = pkt[_PAYLOAD]
        if len(payload) < 4:
            return
        now = time.time()
        if self._should_alert("s7_enumeration", src_ip, now):
            alerts.append({
                "rule": "s7_enumeration",
                "severity": SEVERITY_MEDIUM,
                "mitre": MITRE_DISCOVERY,
                "src": src_ip,
                "dst": pkt[_DST_IP],
                "message": f"S7comm access from {src_ip} to port {dport}",
            })

        # Rule 10: a WriteVar job changes controller memory.  No plant
        # service speaks S7comm, so every write is worth an alert of its own.
        # Only an exact repeat of the previous write to this server -- same
        # host, same addresses, same value -- within the cooldown is
        # suppressed: a script looping one write is one alert per cooldown,
        # but every change -- set, restore, set again -- is an alert, so the
        # newest alert that covers an address carries the value last written
        # there.  The verify check of the S7 Side Door challenge relies on it.
        items = parse_s7_write(payload)
        if not items:
            return
        dst_ip = pkt[_DST_IP]
        written = (src_ip, tuple((i["area"], i["db"], i["start"], i["bit"], i["data"])
                                 for i in items))
        last = self.s7_last_write.get((dst_ip, dport))
        if last is None or last[0] != written or now - last[1] >= self.ALERT_COOLDOWN:
            self.s7_last_write[(dst_ip, dport)] = (written, now)
            where = ", ".join(_describe_s7_item(i) for i in items)
            alerts.append({
                "rule": "s7_write",
                "severity": SEVERITY_HIGH,
                "mitre": MITRE_COMMAND_MESSAGE,
                "src": src_ip,
                "dst": dst_ip,
                "dport": dport,
                "message": f"S7comm write from {src_ip} to {dst_ip}:{dport}: {where}",
                "s7_items": items,
            })

    # ---- Rule 7: HTTP brute force ----

    def _check_http_brute(self, pkt, src_ip, dport, alerts):
        payload = pkt[_PAYLOAD]
        if len(payload) == 0:
            return
        # Fast bytes check before decode
        if b"POST" not in payload[:200]:
            return
        payload_lower = payload[:200].lower()
        if b"login" not in payload_lower and b"auth" not in payload_lower:
            return
        now = time.time()
        count = self._track_event(
            self.http_login_tracker, (src_ip, dport), self.HTTP_BRUTE_WINDOW, now
        )
        if count >= self.HTTP_BRUTE_THRESHOLD:
            target = "OpenPLC" if dport == 8080 else "FUXA"
            if self._should_alert("http_brute_force", src_ip, now):
                alerts.append({
                    "rule": "http_brute_force",
                    "severity": SEVERITY_HIGH,
                    "mitre": MITRE_BRUTE_FORCE,
                    "src": src_ip,
                    "dst": pkt[_DST_IP],
                    "message": f"Brute force on {target}: {count} login attempts in {self.HTTP_BRUTE_WINDOW}s",
                })

    # ---- Rule 8: ARP spoofing ----

    def _check_arp(self, pkt):
        arp_op = pkt[_ARP_OP]
        if not arp_op:
            return []
        arp_src_ip = pkt[_ARP_SRC_IP]
        arp_src_mac = pkt[_ARP_SRC_MAC]
        if not arp_src_ip or not arp_src_mac:
            return []

        if arp_src_ip not in self.arp_tracker:
            self.arp_tracker[arp_src_ip] = set()
        macs = self.arp_tracker[arp_src_ip]
        macs.add(arp_src_mac)
        if len(macs) > 1:
            now = time.time()
            if self._should_alert("arp_spoof", arp_src_ip, now):
                return [{
                    "rule": "arp_spoof",
                    "severity": SEVERITY_CRITICAL,
                    "mitre": MITRE_SPOOF_REPORTING,
                    "src": arp_src_ip,
                    "dst": "",
                    "message": f"ARP spoofing: IP {arp_src_ip} seen with multiple MACs: {macs}",
                }]
        return []

    # ---- Rule 9: OPC-UA ----

    def _check_opcua(self, pkt, src_ip, alerts):
        if len(pkt[_PAYLOAD]) < 8:
            return
        if KNOWN_SERVICES.get(src_ip) not in _OPCUA_CLIENTS:
            now = time.time()
            if self._should_alert("opcua_access", src_ip, now):
                alerts.append({
                    "rule": "opcua_access",
                    "severity": SEVERITY_LOW,
                    "mitre": MITRE_DISCOVERY,
                    "src": src_ip,
                    "dst": pkt[_DST_IP],
                    "message": f"OPC-UA access from non-service host {src_ip}",
                })

    # ---- Stats & cleanup ----

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
        self.recent_alerts = {
            k: v for k, v in self.recent_alerts.items()
            if now - v < self.ALERT_COOLDOWN * 2
        }
        self.s7_last_write = {
            k: v for k, v in self.s7_last_write.items()
            if now - v[1] < self.ALERT_COOLDOWN * 2
        }
        for key in list(self.port_scan_tracker.keys()):
            cutoff = now - self.PORT_SCAN_WINDOW * 2
            self.port_scan_tracker[key] = {
                p: t for p, t in self.port_scan_tracker[key].items()
                if t >= cutoff
            }
            if not self.port_scan_tracker[key]:
                del self.port_scan_tracker[key]


# ---- S7comm WriteVar parsing (rule 10) ----

def _describe_s7_item(item):
    """Human-readable address of one write item, e.g. DB1002.DBB208 (2 bytes)."""
    if item["area"] == "DB":
        where = f"DB{item['db']}.DBB{item['start']}"
    elif item["area"] == "PA":
        # The process image of outputs: on OpenPLC the %QX coils that drive
        # the compressor and the valves, written directly past the program.
        where = f"PA (process outputs) byte {item['start']}.{item['bit']}"
    else:
        where = f"{item['area']} byte {item['start']}"
    return f"{where} ({item['length']} bytes) = {item['data'] or '-'}"


def _s7_write_items(pdu):
    """Items of one S7comm PDU if it is a WriteVar job, else None.

    pdu starts at the S7comm protocol id (0x32).  Layout of a job: header
    (10 bytes: id, ROSCTR, reserved, PDU reference, parameter length, data
    length), parameters (function 0x05, item count, 12 bytes per item) and
    data (return code, transport size, length, value, padded to even length
    between items).
    """
    if len(pdu) < 12 or pdu[0] != 0x32 or pdu[1] != 0x01:
        return None
    par_len = int.from_bytes(pdu[6:8], "big")
    data_len = int.from_bytes(pdu[8:10], "big")
    params = pdu[10:10 + par_len]
    data = pdu[10 + par_len:10 + par_len + data_len]
    if len(params) < 2 or params[0] != 0x05:
        return None
    count = params[1]
    items = []
    pos = 0
    for n in range(count):
        spec = params[2 + 12 * n:14 + 12 * n]
        # Only the common "S7ANY" addressing (0x12 0x0A 0x10) is decoded.
        if len(spec) < 12 or spec[0] != 0x12 or spec[2] != 0x10:
            return items or None
        area = spec[8]
        bit_address = int.from_bytes(spec[9:12], "big")
        value = b""
        if len(data) >= pos + 4:
            tsize = data[pos + 1]
            length = int.from_bytes(data[pos + 2:pos + 4], "big")
            # Transport sizes 3 (bit), 4 (byte/word/dword) count in bits.
            nbytes = (length + 7) // 8 if tsize in (0x03, 0x04, 0x05) else length
            value = data[pos + 4:pos + 4 + nbytes]
            pos += 4 + nbytes + (nbytes % 2)
        if len(items) < S7_MAX_ITEMS:
            items.append({
                "area": S7_AREAS.get(area, f"0x{area:02X}"),
                "db": int.from_bytes(spec[6:8], "big") if area == 0x84 else 0,
                "start": bit_address >> 3,
                "bit": bit_address & 7,
                "length": len(value),
                "data": value[:S7_MAX_DATA].hex(),
            })
    return items or None


def parse_s7_write(payload):
    """WriteVar items in a TCP payload to an S7comm port, or [] if there are none.

    The payload is one or more TPKT frames (RFC 1006: version 3, reserved,
    16-bit length), each carrying a COTP data unit (length indicator, PDU type
    0xF0) followed by the S7comm PDU.  Anything that does not parse is not a
    write and yields [], so a malformed packet can never raise in the sniffer.
    """
    items = []
    pos = 0
    try:
        while pos + 7 <= len(payload) and payload[pos] == 0x03:
            frame_len = int.from_bytes(payload[pos + 2:pos + 4], "big")
            if frame_len < 7:
                break
            frame = payload[pos:pos + frame_len]
            cotp_len = frame[4]
            if len(frame) > 5 and frame[5] == 0xF0:
                found = _s7_write_items(frame[5 + cotp_len:])
                if found:
                    items.extend(found)
            pos += frame_len
    except (IndexError, ValueError):
        return []
    return items[:S7_MAX_ITEMS]
