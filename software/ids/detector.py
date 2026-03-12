"""
CybICS IDS - Packet Capture and Detection Engine
Lightweight sniffer using tcpdump + raw packet parsing for minimal CPU usage.
Optimized for Raspberry Pi Zero 2 W.
"""

import struct
import subprocess
import threading
import time
from collections import deque
from datetime import datetime
import logging

from rules import RuleEngine, KNOWN_SERVICES, MODBUS_WRITE_FUNCTIONS

logger = logging.getLogger("cybics-ids")

MAX_ALERTS = 500
CLEANUP_INTERVAL = 60  # seconds


class Detector:
    """Packet capture and ICS intrusion detection engine"""

    def __init__(self):
        self.active = False
        self.alerts = deque(maxlen=MAX_ALERTS)
        self.lock = threading.Lock()
        self.capture_thread = None
        self.rule_engine = RuleEngine()
        self.stats = {
            "packets_analyzed": 0,
            "alerts_total": 0,
            "started_at": None,
            "last_packet_at": None,
        }
        self._alert_id = 0
        self._tcpdump_proc = None

        # Evasion challenge state
        self.evasion_active = False
        self.evasion_start_time = 0
        self.evasion_start_alert_count = 0
        self.evasion_modbus_writes = 0
        self.evasion_timeout = 120  # 2 minute window

        logger.info(f"Detector initialized (max {MAX_ALERTS} alerts in memory)")

    def start(self, interface=None, bpf_filter="net 172.18.0.0/24"):
        """Start packet capture and analysis"""
        if self.active:
            return False

        self.active = True
        self.stats["started_at"] = datetime.now().isoformat()
        self.stats["packets_analyzed"] = 0

        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(interface, bpf_filter),
            daemon=True,
        )
        self.capture_thread.start()

        logger.info(f"Detector started (interface={interface}, filter={bpf_filter})")
        return True

    def stop(self):
        """Stop packet capture"""
        self.active = False
        self._cleanup_tcpdump()
        logger.info(
            f"Detector stopped. Analyzed {self.stats['packets_analyzed']} packets, "
            f"generated {self.stats['alerts_total']} alerts"
        )
        return True

    # ========== CAPTURE LOOP ==========

    def _capture_loop(self, interface, bpf_filter):
        """Main capture loop using tcpdump subprocess"""
        iface = interface
        if iface is None or iface == "all":
            iface = self._find_bridge_interface(bpf_filter)

        cmd = ["tcpdump", "-l", "-xx", "-n", "--immediate-mode", "-s", "300"]
        if iface:
            cmd += ["-i", iface]
        if bpf_filter:
            cmd += bpf_filter.split()

        try:
            self._tcpdump_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            logger.error("tcpdump not found - detector cannot start")
            self.active = False
            return

        logger.info(f"tcpdump started: {' '.join(cmd)} (pid={self._tcpdump_proc.pid})")
        self._read_tcpdump_output()

    def _read_tcpdump_output(self):
        """Read tcpdump -xx output and parse packets from hex dump lines"""
        proc = self._tcpdump_proc
        if proc is None:
            return

        last_cleanup = time.time()
        hex_parts = []

        for raw_line in iter(proc.stdout.readline, b""):
            if not self.active:
                break

            line = raw_line.decode("utf-8", errors="ignore").rstrip()
            if not line:
                continue

            if line.startswith("\t0x"):
                # Hex data line: "\t0x0000:  aabb ccdd eeff ..."
                hex_part = line.split(":", 1)[1].strip()
                hex_parts.append(hex_part.replace(" ", ""))
            else:
                # Header line for a new packet — process previous
                if hex_parts:
                    self._process_hex_packet(hex_parts)
                    hex_parts = []

                now = time.time()
                if now - last_cleanup > CLEANUP_INTERVAL:
                    self.rule_engine.cleanup()
                    last_cleanup = now

        # Process last buffered packet
        if hex_parts:
            self._process_hex_packet(hex_parts)

        self._cleanup_tcpdump()

    def _process_hex_packet(self, hex_parts):
        """Convert accumulated hex lines to bytes and analyze"""
        try:
            raw = bytes.fromhex("".join(hex_parts))
            pkt_info = _parse_raw_packet(raw)
            if pkt_info:
                self.stats["packets_analyzed"] += 1
                self.stats["last_packet_at"] = datetime.now().isoformat()

                alerts = self.rule_engine.check_packet(pkt_info)
                for alert in alerts:
                    self._add_alert(alert)

                if self.evasion_active:
                    self._track_evasion_packet(pkt_info)
        except Exception as e:
            logger.debug(f"Packet processing error: {e}")

    def _cleanup_tcpdump(self):
        """Terminate tcpdump subprocess cleanly"""
        proc = self._tcpdump_proc
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            logger.info(f"tcpdump process terminated (pid={proc.pid})")
        self._tcpdump_proc = None

    def _find_bridge_interface(self, bpf_filter):
        """Auto-detect the Docker bridge interface for the CybICS subnet"""
        try:
            subnet_prefix = "172.18.0."
            if "net " in bpf_filter:
                net_part = bpf_filter.split("net ")[1].split("/")[0].split(")")[0].strip()
                parts = net_part.split(".")
                if len(parts) >= 3:
                    subnet_prefix = ".".join(parts[:3]) + "."

            result = subprocess.run(
                ["ip", "-o", "addr", "show"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if subnet_prefix in line:
                    iface = line.split(":")[1].strip().split()[0]
                    logger.info(f"Auto-detected bridge interface: {iface} (subnet {subnet_prefix}*)")
                    return iface

            logger.warning(f"No bridge interface found for {subnet_prefix}*, falling back to 'any'")
        except Exception as e:
            logger.warning(f"Bridge detection failed: {e}, falling back to 'any'")
        return None

    # ========== ALERTS ==========

    def _add_alert(self, alert):
        """Add alert to buffer"""
        self._alert_id += 1
        alert["id"] = self._alert_id
        alert["timestamp"] = datetime.now().isoformat()
        with self.lock:
            self.alerts.append(alert)
        self.stats["alerts_total"] += 1
        logger.warning(
            f"ALERT [{alert['severity'].upper()}] {alert['rule']}: {alert['message']}"
        )

    def get_alerts(self, since_id=0):
        """Get alerts, optionally filtered by ID"""
        with self.lock:
            if since_id:
                return [a for a in self.alerts if a["id"] > since_id]
            return list(self.alerts)

    def clear_alerts(self):
        """Clear all alerts"""
        with self.lock:
            self.alerts.clear()
        self._alert_id = 0
        self.stats["alerts_total"] = 0
        logger.info("Alerts cleared")

    # ========== EVASION CHALLENGE ==========

    def _track_evasion_packet(self, pkt_info):
        """Track Modbus write packets from non-service hosts during evasion challenge"""
        if pkt_info.get("dport") != 502:
            return
        payload = pkt_info.get("payload", b"")
        if len(payload) < 8:
            return
        try:
            func_code = payload[7] & 0x7F
            if func_code in MODBUS_WRITE_FUNCTIONS:
                src_ip = pkt_info.get("src_ip", "")
                if KNOWN_SERVICES.get(src_ip) not in ("hwio", "fuxa", "openplc"):
                    self.evasion_modbus_writes += 1
                    logger.info(
                        f"Evasion: Modbus write #{self.evasion_modbus_writes} "
                        f"from {src_ip} (func=0x{func_code:02X})"
                    )
        except (IndexError, TypeError):
            pass

    def start_evasion(self):
        """Start an evasion challenge window"""
        if not self.active:
            return {
                "success": False,
                "message": "IDS must be running to start evasion challenge.",
            }
        self.evasion_active = True
        self.evasion_start_time = time.time()
        self.evasion_start_alert_count = self.stats["alerts_total"]
        self.evasion_modbus_writes = 0
        logger.info("Evasion challenge started")
        return {
            "success": True,
            "message": "Evasion window started. Send Modbus writes without triggering alerts.",
            "timeout": self.evasion_timeout,
        }

    def check_evasion(self):
        """Check evasion challenge status"""
        if not self.evasion_active:
            return {
                "active": False,
                "message": "No evasion challenge in progress. Start one first.",
            }

        elapsed = time.time() - self.evasion_start_time
        new_alerts = self.stats["alerts_total"] - self.evasion_start_alert_count

        if elapsed > self.evasion_timeout:
            self.evasion_active = False
            return {
                "active": False,
                "expired": True,
                "message": "Evasion window expired. Start a new attempt.",
                "modbus_writes_detected": self.evasion_modbus_writes,
                "writes_required": 3,
                "new_alerts": new_alerts,
                "success": False,
            }

        success = self.evasion_modbus_writes >= 3 and new_alerts == 0

        return {
            "active": True,
            "elapsed": round(elapsed),
            "remaining": round(self.evasion_timeout - elapsed),
            "timeout": self.evasion_timeout,
            "modbus_writes_detected": self.evasion_modbus_writes,
            "writes_required": 3,
            "new_alerts": new_alerts,
            "success": success,
        }

    def get_status(self):
        """Get detector status"""
        return {
            "active": self.active,
            "stats": {
                **self.stats,
                "alerts_in_buffer": len(self.alerts),
                "max_alerts": MAX_ALERTS,
            },
            "rule_engine": self.rule_engine.get_stats(),
            "evasion": {
                "active": self.evasion_active,
                "modbus_writes": self.evasion_modbus_writes if self.evasion_active else 0,
                "new_alerts": (
                    self.stats["alerts_total"] - self.evasion_start_alert_count
                ) if self.evasion_active else 0,
            },
        }


# ========== RAW PACKET PARSER (module-level for performance) ==========

_UNPACK_H = struct.Struct("!H").unpack
_UNPACK_HH = struct.Struct("!HH").unpack


def _parse_raw_packet(raw):
    """Parse raw Ethernet frame bytes into pkt_info dict.

    Returns None for packets we don't care about.
    Handles: ARP, IPv4/TCP, IPv4/UDP.
    """
    if len(raw) < 14:
        return None

    eth_type = _UNPACK_H(raw[12:14])[0]

    # Handle 802.1Q VLAN tag
    if eth_type == 0x8100:
        if len(raw) < 18:
            return None
        eth_type = _UNPACK_H(raw[16:18])[0]
        eth_hdr_len = 18
    else:
        eth_hdr_len = 14

    # ARP (0x0806)
    if eth_type == 0x0806:
        arp_start = eth_hdr_len
        if len(raw) < arp_start + 28:
            return None
        arp = raw[arp_start:]
        op = _UNPACK_H(arp[6:8])[0]
        src_mac = "%02x:%02x:%02x:%02x:%02x:%02x" % tuple(arp[8:14])
        src_ip = "%d.%d.%d.%d" % tuple(arp[14:18])
        dst_ip = "%d.%d.%d.%d" % tuple(arp[24:28])
        return {
            "proto": "ARP",
            "arp_op": op,
            "arp_src_mac": src_mac,
            "arp_src_ip": src_ip,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
        }

    # Only handle IPv4
    if eth_type != 0x0800:
        return None

    ip_start = eth_hdr_len
    if len(raw) < ip_start + 20:
        return None

    ip_hdr = raw[ip_start:]
    ihl = (ip_hdr[0] & 0x0F) * 4
    protocol = ip_hdr[9]
    src_ip = "%d.%d.%d.%d" % tuple(ip_hdr[12:16])
    dst_ip = "%d.%d.%d.%d" % tuple(ip_hdr[16:20])

    transport = ip_hdr[ihl:]

    # TCP (protocol 6)
    if protocol == 6:
        if len(transport) < 20:
            return None
        sport, dport = _UNPACK_HH(transport[0:4])
        flags_byte = transport[13]
        # Build flags string matching Scapy convention (used by rules)
        flags_chars = []
        if flags_byte & 0x02:
            flags_chars.append("S")
        if flags_byte & 0x10:
            flags_chars.append("A")
        if flags_byte & 0x01:
            flags_chars.append("F")
        if flags_byte & 0x04:
            flags_chars.append("R")
        if flags_byte & 0x08:
            flags_chars.append("P")
        tcp_hdr_len = ((transport[12] >> 4) & 0x0F) * 4
        payload = bytes(transport[tcp_hdr_len:tcp_hdr_len + 256])
        return {
            "src_ip": src_ip, "dst_ip": dst_ip,
            "proto": "TCP", "sport": sport, "dport": dport,
            "flags": "".join(flags_chars), "payload": payload,
        }

    # UDP (protocol 17)
    if protocol == 17:
        if len(transport) < 8:
            return None
        sport, dport = _UNPACK_HH(transport[0:4])
        payload = bytes(transport[8:8 + 256])
        return {
            "src_ip": src_ip, "dst_ip": dst_ip,
            "proto": "UDP", "sport": sport, "dport": dport,
            "flags": "", "payload": payload,
        }

    # Other protocols — still report for completeness
    return {
        "src_ip": src_ip, "dst_ip": dst_ip,
        "proto": "OTHER", "sport": 0, "dport": 0,
        "flags": "", "payload": b"",
    }
