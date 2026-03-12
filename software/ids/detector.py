"""
CybICS IDS - Packet Capture and Detection Engine
Lightweight sniffer optimized for Raspberry Pi Zero 2 W (~2-4 MB memory)
"""

import threading
import time
import subprocess
from collections import deque
from datetime import datetime
import logging

from rules import RuleEngine

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
        logger.info(
            f"Detector stopped. Analyzed {self.stats['packets_analyzed']} packets, "
            f"generated {self.stats['alerts_total']} alerts"
        )
        return True

    def _capture_loop(self, interface, bpf_filter):
        """Main capture loop using Scapy"""
        try:
            from scapy.all import sniff, IP, TCP, UDP, ARP, Raw
        except ImportError:
            logger.error("Scapy not available - detector cannot start")
            self.active = False
            return

        last_cleanup = time.time()

        def packet_handler(pkt):
            if not self.active:
                return True  # stop sniffing

            try:
                pkt_info = self._parse_packet(pkt, IP, TCP, UDP, ARP, Raw)
                if pkt_info:
                    self.stats["packets_analyzed"] += 1
                    self.stats["last_packet_at"] = datetime.now().isoformat()

                    alerts = self.rule_engine.check_packet(pkt_info)
                    for alert in alerts:
                        self._add_alert(alert)
            except Exception as e:
                logger.debug(f"Packet processing error: {e}")

            # Periodic cleanup
            nonlocal last_cleanup
            now = time.time()
            if now - last_cleanup > CLEANUP_INTERVAL:
                self.rule_engine.cleanup()
                last_cleanup = now

        try:
            iface = interface
            if iface is None or iface == "all":
                iface = self._find_bridge_interface(bpf_filter)
            logger.info(f"Starting Scapy sniff (iface={iface}, filter={bpf_filter})")
            sniff(
                prn=packet_handler,
                store=False,
                iface=iface,
                filter=bpf_filter,
                stop_filter=lambda x: not self.active,
            )
        except Exception as e:
            logger.error(f"Capture error: {e}")
            self.active = False

    def _find_bridge_interface(self, bpf_filter):
        """Auto-detect the Docker bridge interface for the CybICS subnet"""
        try:
            # Extract subnet from BPF filter (e.g., "net 172.18.0.0/24" -> "172.18.0.")
            subnet_prefix = "172.18.0."
            if "net " in bpf_filter:
                net_part = bpf_filter.split("net ")[1].split("/")[0].split(")")[0].strip()
                # Get first 3 octets as prefix
                parts = net_part.split(".")
                if len(parts) >= 3:
                    subnet_prefix = ".".join(parts[:3]) + "."

            # Find bridge interface matching this subnet via ip addr
            result = subprocess.run(
                ["ip", "-o", "addr", "show"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if subnet_prefix in line:
                    # Line format: "26: br-3908d1976c24    inet 172.18.0.1/24 ..."
                    iface = line.split(":")[1].strip().split()[0]
                    logger.info(f"Auto-detected bridge interface: {iface} (subnet {subnet_prefix}*)")
                    return iface

            logger.warning(f"No bridge interface found for {subnet_prefix}*, falling back to 'any'")
        except Exception as e:
            logger.warning(f"Bridge detection failed: {e}, falling back to 'any'")
        return None

    def _parse_packet(self, pkt, IP, TCP, UDP, ARP, Raw):
        """Extract minimal info from packet for rule engine"""
        info = {}

        if pkt.haslayer(ARP):
            arp = pkt[ARP]
            info["arp_op"] = arp.op
            info["arp_src_mac"] = arp.hwsrc
            info["arp_src_ip"] = arp.psrc
            info["src_ip"] = arp.psrc
            info["dst_ip"] = arp.pdst
            info["proto"] = "ARP"
            return info

        if not pkt.haslayer(IP):
            return None

        ip = pkt[IP]
        info["src_ip"] = ip.src
        info["dst_ip"] = ip.dst
        info["payload"] = b""

        if pkt.haslayer(TCP):
            tcp = pkt[TCP]
            info["proto"] = "TCP"
            info["sport"] = tcp.sport
            info["dport"] = tcp.dport
            info["flags"] = str(tcp.flags)
            if pkt.haslayer(Raw):
                info["payload"] = bytes(pkt[Raw].load)[:256]  # limit payload size
        elif pkt.haslayer(UDP):
            udp = pkt[UDP]
            info["proto"] = "UDP"
            info["sport"] = udp.sport
            info["dport"] = udp.dport
            info["flags"] = ""
            if pkt.haslayer(Raw):
                info["payload"] = bytes(pkt[Raw].load)[:256]
        else:
            info["proto"] = "OTHER"
            info["sport"] = 0
            info["dport"] = 0
            info["flags"] = ""

        return info

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
        }
