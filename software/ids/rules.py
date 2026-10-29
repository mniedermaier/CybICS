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
DNP3_RESPONSE = 0x81
# The outstation's reply is credited to a request only within this many
# seconds of it.  Connection state (DNP3_MAX_CONNECTIONS at most, each with
# DNP3_MAX_WAITING requests) lives until the connection has been silent in
# both directions for DNP3_CONNECTION_IDLE seconds.
DNP3_REPLY_TIMEOUT = 10
DNP3_MAX_CONNECTIONS = 256
DNP3_MAX_WAITING = 8
DNP3_CONNECTION_IDLE = 600
# Servers (destination address and port) whose last S7 write, S7 control
# request and DNP3 request are remembered for the exact-repeat folding.  The
# plant has a handful; the cap only matters when a flood sprays requests at
# many addresses, which would otherwise grow these maps by one entry per
# packet until the next cleanup -- about 0.5 KB (S7) to 2 KB (DNP3, which
# keeps the alert) each, beyond the IDS's 32 MB on the board within a minute.
# Forgetting a server only means its next repeat is alerted again.
MAX_TRACKED_SERVERS = 64

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
# TCP only, appended by the detector.  Hand-built tuples in the unit tests
# may lack them; the DNP3 rule then cannot follow the stream and judges each
# segment on its own.
_TCP_SEQ = 10
_TCP_ACK = 11
_PAYLOAD_LEN = 12
_SEQ_MASK = 0xFFFFFFFF


def _remember(table, key, value):
    """table[key] = value, dropping the least recently stored key beyond MAX_TRACKED_SERVERS."""
    table.pop(key, None)
    if len(table) >= MAX_TRACKED_SERVERS:
        del table[next(iter(table))]
    table[key] = value


def _tcp_stream(pkt):
    """(sequence number, acknowledgement number, payload length) or None."""
    if len(pkt) > _PAYLOAD_LEN:
        return pkt[_TCP_SEQ], pkt[_TCP_ACK], pkt[_PAYLOAD_LEN]
    return None


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
        self.dnp3_last_request = {}  # (dst, port) -> ((src, requests), time, alert), as for S7
        # (master, master port, outstation) -> {"waiting": [(alert, time)],
        # "opaque": bool, "seen": time, "next": next master sequence number}
        self.dnp3_connections = {}
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
        elif sport == DNP3_PORT:
            # The outstation's reply to a rule-11 request; raises nothing
            self._check_dnp3_reply(pkt, src_ip)

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
            _remember(self.s7_last_write, (dst_ip, dport), (written, now))
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
            _remember(self.s7_last_control, key, (sent, now))
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
        # number is logged again.  The alert records what was sent; whether
        # the outstation acted on it is only known from its reply, which
        # _check_dnp3_reply files under each request as "reply".
        now = time.time()
        dst_ip = pkt[_DST_IP]
        connection = self._follow_dnp3_master(pkt, (src_ip, pkt[_SPORT], dst_ip), now)
        if connection is None:
            return
        if pkt[_PAYLOAD] and dnp3_opaque(pkt[_PAYLOAD]):
            # Something the IDS cannot read in full -- part of a frame, a
            # message in several transport segments or application fragments,
            # objects it does not decode, frames past the ones the rule reads:
            # the outstation may act on a request the IDS never logs, so no
            # reply on this connection is trusted to answer a logged one.
            connection["opaque"] = True
        requests = parse_dnp3_requests(pkt[_PAYLOAD])
        if not requests:
            return
        signature = (src_ip, tuple(
            (r["function"], r["link_dst"], r["link_src"], r["seq"], r["objects_crc"],
             tuple(tuple(sorted(o.items())) for o in r["objects"]))
            for r in requests))
        last = self.dnp3_last_request.get((dst_ip, dport))
        if last is not None and last[0] == signature and now - last[1] < self.ALERT_COOLDOWN:
            # The repeat's reply belongs to the alert that logged it first.
            self._await_dnp3_reply(connection, last[2], now)
            return
        for request in requests:
            # Created here, filled in later: the key set of a stored alert
            # never changes while the API may be serialising it.
            request["reply"] = None
        what = "; ".join(_describe_dnp3_request(r) for r in requests)
        alert = {
            "rule": "dnp3_operate",
            "severity": SEVERITY_HIGH,
            "mitre": MITRE_COMMAND_MESSAGE,
            "src": src_ip,
            "dst": dst_ip,
            "dport": dport,
            "message": f"DNP3 control from {src_ip} to {dst_ip}:{dport}: {what}",
            "dnp3": requests,
        }
        _remember(self.dnp3_last_request, (dst_ip, dport), (signature, now, alert))
        self._await_dnp3_reply(connection, alert, now)
        alerts.append(alert)

    def _follow_dnp3_master(self, pkt, key, now):
        """The connection's state after this master-to-outstation packet, or None.

        Clean state starts only at a SYN the IDS sees. The byte stream is
        followed by sequence number: a segment that does not start where the
        last one ended (one the capture lost, a retransmission, a connection
        the IDS joined midway or forgot) means the outstation may have
        received a request the IDS never read, so the connection is opaque.
        """
        stream = _tcp_stream(pkt)
        flags = pkt[_FLAGS]
        if stream is not None and "S" in flags and "A" not in flags:
            # A SYN on a connection the IDS already follows with requests on
            # it may be crafted to make it forget them while the outstation
            # keeps the connection, so that state does not start clean.
            old = self.dnp3_connections.get(key)
            self._store_dnp3_connection(key, {
                "waiting": [], "seen": now,
                "opaque": old is not None and (old["opaque"] or bool(old["waiting"])),
                "next": (stream[0] + 1) & _SEQ_MASK, "last": None})
            return None
        length = stream[2] if stream is not None else len(pkt[_PAYLOAD])
        connection = self.dnp3_connections.pop(key, None)
        if connection is None:
            if not length:
                return None   # a bare ACK or FIN: nothing to follow
            connection = {"waiting": [], "opaque": stream is not None, "seen": now,
                          "next": None, "last": None}
            self._store_dnp3_connection(key, connection)
        else:
            self.dnp3_connections[key] = connection   # most recently used
        connection["seen"] = now
        if stream is not None and length:
            segment = (stream[0], length, pkt[_PAYLOAD])
            if segment == connection.get("last"):
                return connection   # the same segment seen twice (capture on "any")
            if (stream[0] != connection["next"] or length > len(pkt[_PAYLOAD])
                    or "U" in flags):
                # A gap, a retransmission with other bytes, bytes the capture
                # cut off (tcpdump runs with a short snap length), or urgent
                # data, which the outstation's TCP stack takes out of the
                # stream while the IDS would read it in place.
                connection["opaque"] = True
            connection["next"] = (stream[0] + length) & _SEQ_MASK
            connection["last"] = segment
        return connection

    def _store_dnp3_connection(self, key, connection):
        self.dnp3_connections.pop(key, None)
        if len(self.dnp3_connections) >= DNP3_MAX_CONNECTIONS:
            # Forget a connection without requests first.  Forgetting one
            # forgets its requests too, and a later segment on it starts
            # opaque, so nothing on it can be credited afterwards.
            idle = next((k for k, v in self.dnp3_connections.items() if not v["waiting"]),
                        next(iter(self.dnp3_connections)))
            del self.dnp3_connections[idle]
        self.dnp3_connections[key] = connection

    def _await_dnp3_reply(self, connection, alert, now):
        # Every request on a connection stays on its list for as long as the
        # connection lives, answered or not: a reply is only credited when it
        # fits exactly one of them.  A request pushed off a full list could
        # have been the one a reply answers, so that makes the connection
        # opaque.
        waiting = [w for w in connection["waiting"] if w[0] is not alert]
        waiting.append((alert, now))
        if len(waiting) > DNP3_MAX_WAITING:
            connection["opaque"] = True
            waiting = waiting[-DNP3_MAX_WAITING:]
        connection["waiting"] = waiting

    def _check_dnp3_reply(self, pkt, src_ip):
        # An outstation answers every request it accepts at the link layer
        # with a response (function 0x81) carrying the request's sequence
        # number and echoing each control point with its status, 0 for
        # success.  A frame it drops -- wrong addresses, wrong direction,
        # a transport or application header it does not take -- gets no
        # response at all, and a refused one gets a non-zero status.
        #
        # A response does not name the request it answers: a SELECT is
        # answered with status 00 and writes nothing, and a frame the IDS
        # could not read whole may be one the outstation acted on.  So a
        # reply is filed only when the IDS followed the connection from its
        # SYN without a gap, it carried nothing opaque, the reply acknowledges
        # exactly the bytes the IDS read, it
        # fits exactly one request seen on the connection (sequence number,
        # swapped link addresses, the same points), and that request is
        # unanswered and recent.  Otherwise the requests it fits are marked
        # "unattributed" and are never credited.  None of this depends on
        # when the reply arrives, which the master can delay by closing its
        # TCP window.  What is left needs hand-crafted raw TCP: forging the
        # outstation's reply, insertion packets the outstation discards but
        # the IDS reads (bad checksum, PAWS) timed with a capture loss, or a
        # forged SYN on a connection the IDS forgot -- each more work than
        # the real DNP3 command.
        key = (pkt[_DST_IP], pkt[_DPORT], src_ip)
        connection = self.dnp3_connections.pop(key, None)
        if connection is None:
            return
        self.dnp3_connections[key] = connection   # most recently used
        now = time.time()
        connection["seen"] = now
        stream = _tcp_stream(pkt)
        # The reply's acknowledgement number says how far the outstation has
        # read the master's stream; anything beyond what the IDS followed is
        # a request it never saw.
        complete = stream is None or (connection["next"] is not None
                                      and stream[1] == connection["next"])
        for response in parse_dnp3_responses(pkt[_PAYLOAD]):
            echoed = _dnp3_points(response["objects"])
            matches = [(r, since) for alert, since in connection["waiting"]
                       for r in alert["dnp3"]
                       if r["seq"] == response["seq"]
                       and r["link_dst"] == response["link_src"]
                       and r["link_src"] == response["link_dst"]
                       and _dnp3_points(r["objects"]) == echoed]
            if (not connection["opaque"] and complete and len(matches) == 1
                    and matches[0][0]["reply"] is None
                    and now - matches[0][1] <= DNP3_REPLY_TIMEOUT):
                matches[0][0]["reply"] = {"iin": response["iin"],
                                          "objects": response["objects"]}
                continue
            for request, _ in matches:
                if request["reply"] is None:
                    request["reply"] = {"unattributed": True}

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
        self.dnp3_last_request = {
            k: v for k, v in self.dnp3_last_request.items()
            if now - v[1] < self.ALERT_COOLDOWN * 2
        }
        self.s7_last_control = {
            k: v for k, v in self.s7_last_control.items()
            if now - v[1] < self.ALERT_COOLDOWN * 2
        }
        self.dnp3_connections = {
            k: v for k, v in self.dnp3_connections.items()
            if now - v["seen"] <= DNP3_CONNECTION_IDLE
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


def _dnp3_objects(data, status=False):
    return _dnp3_decode(data, status)[0]


def _dnp3_decode(data, status=False):
    """(control points, True if every byte was decoded) of a request's objects.

    Decodes g12v1 (CROB) and g41v1-4 (analog output) with qualifier 0x17 or
    0x28, the forms a control request uses.  Parsing stops at the first header
    it cannot size, and a header whose points do not fit in the data yields
    none of them: an outstation rejects such a request, so it must not look
    like a write here either.
    """
    objects = []
    pos = 0
    complete = True
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
            if status:
                obj["status"] = point[-1]   # control status, 0 = success
            if len(objects) < DNP3_MAX_POINTS:
                objects.append(obj)
            else:
                complete = False
    return objects, complete and pos == len(data)


def _dnp3_frames(payload, limit=DNP3_MAX_FRAMES):
    """(position, link control, destination, source, user data) of each intact frame.

    The payload is one or more link-layer frames: 05 64, length, control,
    destination and source address (little-endian), a CRC over those eight
    bytes, then the user data in blocks of up to 16 bytes, each followed by its
    own CRC.  Only frames carrying user data (function 3 confirmed, 4
    unconfirmed) with every CRC correct are returned: a station drops anything
    else, so the IDS must not read a command or an answer out of it either.
    Position counts every frame, intact or not; only the first `limit` frames
    are read (None for all).
    """
    pos = 0
    index = -1
    while limit is None or index + 1 < limit:
        index += 1
        if pos + 10 > len(payload) or payload[pos:pos + 2] != b"\x05\x64":
            return
        length, control = payload[pos + 2], payload[pos + 3]
        if length < 5:
            return
        data_len = length - 5
        frame_len = 10 + data_len + 2 * ((data_len + 15) // 16)
        frame = payload[pos:pos + frame_len]
        pos += frame_len
        if len(frame) < frame_len or not control & 0x40 or control & 0x0F not in (3, 4):
            continue
        if dnp3_crc(frame[0:8]) != int.from_bytes(frame[8:10], "little"):
            continue
        user = bytearray()
        for start in range(10, frame_len, 18):
            block = frame[start:min(start + 16, frame_len - 2)]
            crc = frame[start + len(block):start + len(block) + 2]
            if dnp3_crc(block) != int.from_bytes(crc, "little"):
                break
            user += block
        else:
            yield (index, control, int.from_bytes(frame[4:6], "little"),
                   int.from_bytes(frame[6:8], "little"), bytes(user))


def dnp3_intact_frames(payload):
    """True if a TCP payload is a run of complete link frames with every CRC correct.

    A station cannot trust the length in a header that fails its CRC; it
    searches for the next 05 64 instead, and so finds frames inside the bytes
    the IDS would have skipped by that length.  A master never needs to send
    a broken frame, so one makes the stream unreadable for the IDS.
    """
    pos = 0
    while pos < len(payload):
        if pos + 10 > len(payload) or payload[pos:pos + 2] != b"\x05\x64" or payload[pos + 2] < 5:
            return False
        data_len = payload[pos + 2] - 5
        frame_len = 10 + data_len + 2 * ((data_len + 15) // 16)
        frame = payload[pos:pos + frame_len]
        if len(frame) < frame_len or dnp3_crc(frame[0:8]) != int.from_bytes(frame[8:10], "little"):
            return False
        for start in range(10, frame_len, 18):
            block = frame[start:min(start + 16, frame_len - 2)]
            crc = frame[start + len(block):start + len(block) + 2]
            if dnp3_crc(block) != int.from_bytes(crc, "little"):
                return False
        pos += frame_len
    return True


def dnp3_opaque(payload):
    """True if a TCP payload to an outstation holds anything the IDS cannot read in full.

    That is a payload that is not a run of whole link frames with correct
    CRCs, a frame from a
    master with user data past the first DNP3_MAX_FRAMES, or one whose transport or application header is not a
    single segment and fragment (FIR and FIN both set), or a control request
    whose object headers do not decode to the last byte.  The outstation
    reassembles messages the IDS reads frame by frame, so for any of these it
    may act on a request the IDS never sees whole.
    """
    if not dnp3_intact_frames(payload):
        return True
    try:
        for index, control, _, _, user in _dnp3_frames(payload, limit=None):
            if control & 0xC0 != 0xC0:
                continue
            if index >= DNP3_MAX_FRAMES:
                return True   # a request past the frames the rules read
            if len(user) < 3 or user[0] & 0xC0 != 0xC0 or user[1] & 0xC0 != 0xC0:
                return True
            if user[2] in DNP3_CONTROL_FUNCTIONS and not _dnp3_decode(user[3:])[1]:
                return True
    except (IndexError, ValueError, struct.error):
        return True
    return False


def parse_dnp3_requests(payload):
    """Control requests in a TCP payload to a DNP3 outstation, or [] if none.

    Reads frames from a master (DIR and PRM set in the link control byte).
    The user data starts with the transport header; the first segment of a
    message (FIR) carries the application control byte and the function code,
    then the object headers.  The rule logs what was sent, including requests
    the outstation goes on to drop or refuse; its reply tells which.
    """
    requests = []
    try:
        for _, control, link_dst, link_src, user in _dnp3_frames(payload):
            if control & 0xC0 != 0xC0 or len(user) < 3 or not user[0] & 0x40:
                continue
            function = user[2]
            if function not in DNP3_CONTROL_FUNCTIONS:
                continue
            requests.append({
                "function": function,
                "function_name": DNP3_CONTROL_FUNCTIONS[function],
                "link_dst": link_dst,
                "link_src": link_src,
                # Application sequence number and a CRC-16/DNP of the raw
                # object headers: the outstation's response repeats the
                # sequence number, and an OPERATE (0x04) is paired with its
                # SELECT by both.
                "seq": user[1] & 0x0F,
                "objects_crc": dnp3_crc(user[3:]),
                "objects": _dnp3_objects(user[3:]),
            })
    except (IndexError, ValueError, struct.error):
        return []
    return requests


def parse_dnp3_responses(payload):
    """Solicited responses in a TCP payload from a DNP3 outstation, or [].

    Reads single-fragment responses (function 0x81) from an outstation (DIR
    clear, PRM set): the sequence number, the internal indications and the
    echoed control points, each with its control status (0 = success).
    """
    responses = []
    try:
        for _, control, link_dst, link_src, user in _dnp3_frames(payload):
            if (control & 0xC0 != 0x40 or len(user) < 5 or user[0] & 0xC0 != 0xC0
                    or user[1] & 0xC0 != 0xC0 or user[2] != DNP3_RESPONSE):
                continue
            responses.append({
                "link_dst": link_dst,
                "link_src": link_src,
                "seq": user[1] & 0x0F,
                "iin": int.from_bytes(user[3:5], "little"),
                "objects": _dnp3_objects(user[5:], status=True),
            })
    except (IndexError, ValueError, struct.error):
        return []
    return responses


def _dnp3_points(objects):
    """The points of decoded objects without their status, for comparing an echo."""
    return [tuple(sorted((k, v) for k, v in o.items() if k != "status")) for o in objects]


def _describe_dnp3_request(request):
    points = ", ".join(
        f"g{o['group']}v{o['variation']} index {o['index']} = "
        + (f"code 0x{o['code']:02X}" if "code" in o else f"{o['value']:g}")
        for o in request["objects"]) or "no decoded points"
    return (f"{request['function_name']} link {request['link_src']} -> "
            f"{request['link_dst']}: {points}")
