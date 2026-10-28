"""
CybICS IDS - Detection Rules for Industrial Control Systems
Lightweight rule engine optimized for Raspberry Pi Zero 2 W
"""

from collections import deque
import struct
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
MITRE_CHANGE_OPERATING_MODE = "T0858"

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
# S7comm job functions that change the CPU's operating mode: PLC Control
# (0x28, a PI service call -- "P_PROGRAM" with no argument is a warm restart,
# with argument "C " a cold restart) and PLC Stop (0x29).
S7_FUNC_PLC_CONTROL = 0x28
S7_FUNC_PLC_STOP = 0x29
S7_MAX_PI_NAME = 32

# DNP3 on TCP 20000 (OpenPLC's outstation).  Application function codes that
# act on the outstation; a READ (0x01) does not and is ignored, the same way
# the Modbus rules ignore reads.  Only the three operate codes change memory --
# a SELECT just arms a later OPERATE -- but every one of them is a command a
# plant without a DNP3 master should never see.
DNP3_PORT = 20000
DNP3_CONTROL_FUNCTIONS = {
    0x02: "WRITE",
    0x03: "SELECT",
    0x04: "OPERATE",
    0x05: "DIRECT_OPERATE",
    0x06: "DIRECT_OPERATE_NR",
}
DNP3_OPERATE_FUNCTIONS = frozenset((0x04, 0x05, 0x06))
# Point sizes of the control objects the parser decodes, by (group, variation):
# g12v1 Control Relay Output Block, g41v1-4 Analog Output Int32/Int16/
# Float32/Double64, each with the trailing status byte.
_DNP3_OBJECT_SIZES = {(12, 1): 11, (41, 1): 5, (41, 2): 3, (41, 3): 5, (41, 4): 9}
# Qualifiers used for control requests: index prefix and count, both 1 octet
# (0x17) or both 2 octets (0x28).
_DNP3_QUALIFIERS = {0x17: 1, 0x28: 2}
DNP3_MAX_FRAMES = 16
DNP3_MAX_POINTS = 8

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
        self.dnp3_last_request = {}  # (dst, port) -> ((src, requests), time), as for S7
        self.s7_last_control = {}  # (dst, port) -> ((src, action, service, arg), time)
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
            # S7comm rules 6, 10 and 12
            self._check_s7(pkt, src_ip, dport, alerts)
        elif dport == 8080 or dport == 1881:
            # HTTP brute force rule 7
            self._check_http_brute(pkt, src_ip, dport, alerts)
        elif dport == 4840:
            # OPC-UA rule 9
            self._check_opcua(pkt, src_ip, alerts)
        elif dport == DNP3_PORT:
            # DNP3 rule 11
            self._check_dnp3(pkt, src_ip, dport, alerts)

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

    # ---- Rules 6, 10 + 12: S7comm access, writes and CPU control ----

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

        dst_ip = pkt[_DST_IP]
        # Rule 12: PLC STOP / PLC Control jobs change the CPU's operating mode.
        self._check_s7_control(payload, src_ip, dst_ip, dport, now, alerts)

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

    # ---- Rule 12: S7comm CPU operating mode (s7_cpu_control) ----

    def _check_s7_control(self, payload, src_ip, dst_ip, dport, now, alerts):
        """Alert on every S7comm PLC STOP / PLC Control (start) job.

        A mode change is a command no plant service sends.  As for s7_write,
        only an exact repeat of the previous control request to this server
        (same host, same action) within the cooldown is folded, so stop,
        start and stop again are three alerts and the newest alert always
        names the mode the CPU was last told to take.  The verify check of
        the S7 CPU Stop challenge relies on it.
        """
        for control in parse_s7_control(payload):
            key = (dst_ip, dport)
            sent = (src_ip, control["action"], control["pi_service"], control["argument"])
            last = self.s7_last_control.get(key)
            if last is not None and last[0] == sent and now - last[1] < self.ALERT_COOLDOWN:
                continue
            self.s7_last_control[key] = (sent, now)
            label = S7_CONTROL_LABELS.get(control["action"],
                                          f"PI service {control['pi_service'] or '?'}")
            alerts.append({
                "rule": "s7_cpu_control",
                "severity": SEVERITY_CRITICAL if control["action"] == "stop" else SEVERITY_HIGH,
                "mitre": MITRE_CHANGE_OPERATING_MODE,
                "src": src_ip,
                "dst": dst_ip,
                "dport": dport,
                "message": f"S7comm CPU {label} request from {src_ip} to {dst_ip}:{dport}",
                "s7_control": control["action"],
                "s7_pi_service": control["pi_service"],
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

    # ---- Rule 11: DNP3 control requests (dnp3_operate) ----

    def _check_dnp3(self, pkt, src_ip, dport, alerts):
        # No plant service speaks DNP3, so every control request is an alert.
        # Suppression works exactly as for s7_write: only an exact repeat of
        # the previous request to this outstation (same host, function, link
        # addresses, application sequence number, object bytes) within the
        # cooldown is folded, so the newest alert that covers a point carries
        # the value last sent to it, and a SELECT resent with a new sequence
        # number is logged again.  The rule logs requests, not their outcome:
        # an OPERATE without a matching SELECT is logged although the
        # outstation refuses it.  The DNP3 Side Door verify check relies on
        # both and pairs SELECT and OPERATE itself.
        requests = parse_dnp3_requests(pkt[_PAYLOAD])
        if not requests:
            return
        now = time.time()
        dst_ip = pkt[_DST_IP]
        signature = (src_ip, tuple(
            (r["function"], r["link_dst"], r["link_src"], r["seq"], r["objects_crc"],
             tuple(tuple(sorted(o.items())) for o in r["objects"]))
            for r in requests))
        last = self.dnp3_last_request.get((dst_ip, dport))
        if last is not None and last[0] == signature and now - last[1] < self.ALERT_COOLDOWN:
            return
        self.dnp3_last_request[(dst_ip, dport)] = (signature, now)
        what = "; ".join(_describe_dnp3_request(r) for r in requests)
        alerts.append({
            "rule": "dnp3_operate",
            "severity": SEVERITY_HIGH,
            "mitre": MITRE_COMMAND_MESSAGE,
            "src": src_ip,
            "dst": dst_ip,
            "dport": dport,
            "message": f"DNP3 control from {src_ip} to {dst_ip}:{dport}: {what}",
            "dnp3": requests,
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


# ---- Modbus write journal (no rule) ----

# At most this many Modbus requests of one TCP segment, and this many values
# of one request, are decoded for the write journal.
MODBUS_MAX_ADUS = 8
MODBUS_MAX_VALUES = 16


def parse_modbus_writes(payload):
    """Decode the Modbus TCP write requests in one TCP payload.

    Returns a list of dicts with unit, function, address (0-based, as on the
    wire), count and values (registers as integers, coils as 0/1), one per
    write ADU; reads, responses and anything malformed are skipped.  Used for
    the write journal the detector keeps next to its alerts: it records what
    was written and by whom, including the trusted writers (FUXA) that the
    write rules exempt.  Never raises.
    """
    writes = []
    offset = 0
    try:
        for _ in range(MODBUS_MAX_ADUS):
            if len(payload) - offset < 8:
                break
            proto, length = struct.unpack_from("!HH", payload, offset + 2)
            if proto != 0 or length < 2:
                break
            unit = payload[offset + 6]
            pdu = payload[offset + 7:offset + 6 + length]
            offset += 6 + length
            if len(pdu) < 5:
                continue
            func = pdu[0]
            address, second = struct.unpack_from("!HH", pdu, 1)
            if func == 0x06:
                count, values = 1, [second]
            elif func == 0x05:
                if second not in (0x0000, 0xFF00):
                    continue
                count, values = 1, [1 if second else 0]
            elif func in (0x0F, 0x10) and len(pdu) >= 6:
                count, data = second, pdu[6:6 + pdu[5]]
                if func == 0x10:
                    n = min(count, len(data) // 2, MODBUS_MAX_VALUES)
                    values = list(struct.unpack_from(f"!{n}H", data)) if n else []
                else:
                    n = min(count, len(data) * 8, MODBUS_MAX_VALUES)
                    values = [(data[i // 8] >> (i % 8)) & 1 for i in range(n)]
            else:
                continue
            writes.append({"unit": unit, "function": func,
                           "address": address, "count": count, "values": values})
    except (struct.error, IndexError, TypeError):
        pass
    return writes


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


# ---- S7comm CPU control parsing (rule 12) ----

S7_CONTROL_LABELS = {"stop": "STOP", "warm_start": "warm restart (START)",
                     "cold_start": "cold restart (START)"}


def _s7_control_of(pdu):
    """The CPU control request in one S7comm PDU, or None if it is not one.

    pdu starts at the protocol id (0x32).  PLC Stop (0x29) parameters are the
    function, five unused bytes, then the PI service name (length byte and
    name, normally "P_PROGRAM").  PLC Control (0x28) parameters are the
    function, seven unused bytes (the last 0xFD), a 16-bit argument length
    and the argument, then the PI service name.  Snap7 stops the CPU on any
    0x29 and starts it on a 0x28 of the start form.
    """
    if len(pdu) < 11 or pdu[0] != 0x32 or pdu[1] != 0x01:
        return None
    par_len = int.from_bytes(pdu[6:8], "big")
    params = pdu[10:10 + par_len]
    if not params or params[0] not in (S7_FUNC_PLC_STOP, S7_FUNC_PLC_CONTROL):
        return None

    def name_at(pos):
        if pos >= len(params):
            return ""
        raw = params[pos + 1:pos + 1 + params[pos]][:S7_MAX_PI_NAME]
        return raw.decode("ascii", "replace")

    if params[0] == S7_FUNC_PLC_STOP:
        return {"action": "stop", "pi_service": name_at(6), "argument": ""}
    if len(params) < 10:
        return {"action": "pi_service", "pi_service": "", "argument": ""}
    arg_len = int.from_bytes(params[8:10], "big")
    argument = params[10:10 + arg_len]
    service = name_at(10 + arg_len)
    if service == "P_PROGRAM":
        action = "cold_start" if argument.startswith(b"C") else "warm_start"
    else:
        action = "pi_service"
    return {"action": action, "pi_service": service,
            "argument": argument[:S7_MAX_PI_NAME].decode("ascii", "replace")}


def parse_s7_control(payload):
    """CPU control requests (stop, start, other PI services) in a TCP payload.

    Walks the TPKT/COTP frames like parse_s7_write.  Anything that does not
    parse yields [], so a malformed packet can never raise in the sniffer.
    """
    found = []
    pos = 0
    try:
        while pos + 7 <= len(payload) and payload[pos] == 0x03:
            frame_len = int.from_bytes(payload[pos + 2:pos + 4], "big")
            if frame_len < 7:
                break
            frame = payload[pos:pos + frame_len]
            cotp_len = frame[4]
            if len(frame) > 5 and frame[5] == 0xF0:
                control = _s7_control_of(frame[5 + cotp_len:])
                if control:
                    found.append(control)
            pos += frame_len
    except (IndexError, ValueError):
        return []
    return found[:S7_MAX_ITEMS]


# ---- DNP3 parsing (rule 11) ----

def _dnp3_crc_table():
    table = []
    for byte in range(256):
        crc = byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA6BC if crc & 1 else crc >> 1
        table.append(crc)
    return table


_DNP3_CRC_TABLE = _dnp3_crc_table()


def dnp3_crc(data):
    """CRC-16/DNP of a block, as the integer sent little-endian after it."""
    crc = 0
    for byte in data:
        crc = (crc >> 8) ^ _DNP3_CRC_TABLE[(crc ^ byte) & 0xFF]
    return ~crc & 0xFFFF


def _dnp3_objects(data):
    """Control points in the object headers of a request, best effort.

    Decodes g12v1 (CROB) and g41v1-4 (analog output) with qualifier 0x17 or
    0x28, the forms a control request uses.  Parsing stops at the first header
    it cannot size, and a header whose points do not fit in the data yields
    none of them: an outstation rejects such a request, so it must not look
    like a write here either.
    """
    objects = []
    pos = 0
    while pos + 3 <= len(data) and len(objects) < DNP3_MAX_POINTS:
        group, variation, qualifier = data[pos], data[pos + 1], data[pos + 2]
        size = _DNP3_OBJECT_SIZES.get((group, variation))
        width = _DNP3_QUALIFIERS.get(qualifier)
        if size is None or width is None:
            break
        pos += 3
        if pos + width > len(data):
            break
        count = int.from_bytes(data[pos:pos + width], "little")
        pos += width
        end = pos + count * (width + size)
        if count == 0 or end > len(data):
            break
        for _ in range(count):
            index = int.from_bytes(data[pos:pos + width], "little")
            point = data[pos + width:pos + width + size]
            pos += width + size
            obj = {"group": group, "variation": variation, "index": index}
            if group == 12:
                obj["code"] = point[0]   # control code: latch on 0x03, off 0x04, ...
            elif variation == 1:
                obj["value"] = int.from_bytes(point[0:4], "little", signed=True)
            elif variation == 2:
                obj["value"] = int.from_bytes(point[0:2], "little", signed=True)
            elif variation == 3:
                obj["value"] = struct.unpack("<f", point[0:4])[0]
            else:
                obj["value"] = struct.unpack("<d", point[0:8])[0]
            if len(objects) < DNP3_MAX_POINTS:
                objects.append(obj)
    return objects


def parse_dnp3_requests(payload):
    """Control requests in a TCP payload to a DNP3 outstation, or [] if none.

    The payload is one or more link-layer frames: 05 64, length, control,
    destination and source address (little-endian), a CRC over those eight
    bytes, then the user data in blocks of up to 16 bytes, each followed by its
    own CRC.  Only frames from a master carrying user data, with every CRC
    correct, are read -- the outstation drops anything else, so the IDS must
    not count it as a command either.  The user data starts with the transport
    header; the first segment of a message (FIR) carries the application
    control byte and the function code, then the object headers.
    """
    requests = []
    pos = 0
    try:
        for _ in range(DNP3_MAX_FRAMES):
            if pos + 10 > len(payload) or payload[pos:pos + 2] != b"\x05\x64":
                break
            length, control = payload[pos + 2], payload[pos + 3]
            if length < 5:
                break
            data_len = length - 5
            frame_len = 10 + data_len + 2 * ((data_len + 15) // 16)
            frame = payload[pos:pos + frame_len]
            pos += frame_len
            # PRM set (from the initiating station) and a user-data function
            # (3 confirmed, 4 unconfirmed); link status, resets and replies
            # carry no command.
            if len(frame) < frame_len or not control & 0x40 or control & 0x0F not in (3, 4):
                continue
            if dnp3_crc(frame[0:8]) != int.from_bytes(frame[8:10], "little"):
                continue
            user = bytearray()
            ok = True
            for start in range(10, frame_len, 18):
                block = frame[start:min(start + 16, frame_len - 2)]
                crc = frame[start + len(block):start + len(block) + 2]
                if dnp3_crc(block) != int.from_bytes(crc, "little"):
                    ok = False
                    break
                user += block
            if not ok or len(user) < 3 or not user[0] & 0x40:
                continue
            function = user[2]
            if function not in DNP3_CONTROL_FUNCTIONS:
                continue
            requests.append({
                "function": function,
                "function_name": DNP3_CONTROL_FUNCTIONS[function],
                "link_dst": int.from_bytes(frame[4:6], "little"),
                "link_src": int.from_bytes(frame[6:8], "little"),
                # Application sequence number and a CRC-16/DNP of the raw
                # object headers: an outstation runs an OPERATE (0x04) only
                # when a SELECT with the previous sequence number and the
                # same object bytes came first, and these two fields let a
                # consumer pair them the same way.
                "seq": user[1] & 0x0F,
                "objects_crc": dnp3_crc(bytes(user[3:])),
                "objects": _dnp3_objects(bytes(user[3:])),
            })
    except (IndexError, ValueError, struct.error):
        return []
    return requests


def _describe_dnp3_request(request):
    points = ", ".join(
        f"g{o['group']}v{o['variation']} index {o['index']} = "
        + (f"code 0x{o['code']:02X}" if "code" in o else f"{o['value']:g}")
        for o in request["objects"]) or "no decoded points"
    return (f"{request['function_name']} link {request['link_src']} -> "
            f"{request['link_dst']}: {points}")
