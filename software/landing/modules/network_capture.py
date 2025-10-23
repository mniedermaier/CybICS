"""
Network packet capture module with memory management for Raspberry Pi Zero 2
"""
import threading
import time
import sys
import psutil
from datetime import datetime
from collections import deque

from utils.logger import logger
from utils.config import MAX_PACKETS_IN_MEMORY

class NetworkCapture:
    """Network packet capture with memory limits for low-resource devices"""

    def __init__(self):
        self.active = False
        self.packets = deque(maxlen=MAX_PACKETS_IN_MEMORY)
        self.lock = threading.Lock()
        self.capture_thread = None
        self.packet_id = 0
        self.dropped_packets = 0
        # Fixed average packet size estimate in KB (includes raw packet bytes + metadata)
        self.avg_packet_size_kb = 2.0  # ~2KB per packet on average (raw bytes + fields)

        # Memory monitoring
        self.last_memory_log = time.time()
        self.process = psutil.Process()

        logger.info(f"NetworkCapture initialized with max {MAX_PACKETS_IN_MEMORY} packets (~{MAX_PACKETS_IN_MEMORY * self.avg_packet_size_kb / 1024:.1f}MB max)")
        self._log_memory_stats("Initialization")

    def _log_memory_stats(self, context=""):
        """Log detailed memory statistics"""
        try:
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()
            system_mem = psutil.virtual_memory()

            logger.info(
                f"Memory Stats [{context}] - "
                f"Process RSS: {mem_info.rss / 1024 / 1024:.1f}MB, "
                f"Process VMS: {mem_info.vms / 1024 / 1024:.1f}MB, "
                f"Process %: {mem_percent:.1f}%, "
                f"System Available: {system_mem.available / 1024 / 1024:.1f}MB, "
                f"System %: {system_mem.percent:.1f}%, "
                f"Packets in buffer: {len(self.packets)}"
            )
        except Exception as e:
            logger.error(f"Error logging memory stats: {e}")

    def add_packet(self, packet_data):
        """Add a packet with automatic overflow handling via deque maxlen"""
        with self.lock:
            # deque with maxlen automatically drops oldest when full
            old_len = len(self.packets)
            self.packets.append(packet_data)

            # Track if packet was dropped due to maxlen
            if old_len == MAX_PACKETS_IN_MEMORY:
                self.dropped_packets += 1

                if self.dropped_packets % 1000 == 0:
                    logger.warning(f"Packet buffer full. Dropped {self.dropped_packets} packets (keeping newest {MAX_PACKETS_IN_MEMORY})")
                    self._log_memory_stats("Buffer Full")
            elif len(self.packets) % 500 == 0:
                # Log memory every 500 packets when growing
                estimated_mb = len(self.packets) * self.avg_packet_size_kb / 1024
                logger.debug(f"Captured {len(self.packets)} packets (~{estimated_mb:.1f}MB)")

                # Detailed memory log every 1000 packets or every 30 seconds
                current_time = time.time()
                if len(self.packets) % 1000 == 0 or (current_time - self.last_memory_log) > 30:
                    self._log_memory_stats(f"Packet #{len(self.packets)}")
                    self.last_memory_log = current_time

    def get_packets(self):
        """Get all captured packets"""
        with self.lock:
            packet_list = list(self.packets)

        # Log memory stats periodically when packets are retrieved
        current_time = time.time()
        if (current_time - self.last_memory_log) > 60:  # Every 60 seconds during active retrieval
            self._log_memory_stats(f"Retrieving {len(packet_list)} packets")
            self.last_memory_log = current_time

        return packet_list

    def clear(self):
        """Clear all captured packets"""
        with self.lock:
            packet_count = len(self.packets)
            self.packets.clear()
            self.dropped_packets = 0

        logger.info(f"Cleared {packet_count} captured packets")
        self._log_memory_stats("After Clear")

    def start(self, interface='all', filter_str=''):
        """Start packet capture"""
        if self.active:
            logger.warning("Capture already active")
            return False

        self.clear()
        self.active = True
        self.packet_id = 1

        self.capture_thread = threading.Thread(
            target=self._capture_packets,
            args=(interface, filter_str),
            daemon=True
        )
        self.capture_thread.start()

        logger.info(f"Started network capture on interface: {interface}, filter: '{filter_str}'")
        self._log_memory_stats("Capture Start")
        return True

    def stop(self):
        """Stop packet capture"""
        self.active = False
        logger.info(f"Stopped network capture. Captured {len(self.packets)} packets, Dropped {self.dropped_packets} packets")
        self._log_memory_stats("Capture Stop")
        return True

    def _capture_packets(self, interface='all', filter_str=''):
        """Background thread to capture network packets"""
        try:
            # Try to import scapy
            try:
                from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP, DNS, Raw
                has_scapy = True
                logger.info("Using Scapy for packet capture")
            except ImportError:
                logger.warning("Scapy not available, using simulated packet capture")
                has_scapy = False

            if has_scapy:
                self._capture_with_scapy(interface, filter_str)
            else:
                self._capture_simulated()

        except Exception as e:
            logger.error(f"Error in packet capture: {e}", exc_info=True)
            self.active = False

    def _capture_with_scapy(self, interface, filter_str):
        """Capture packets using Scapy"""
        from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP, DNS, Raw
        from modules.protocol_parsers import parse_modbus_tcp, parse_s7comm, parse_opcua, parse_enip

        def packet_handler(packet):
            if not self.active:
                return True  # Stop sniffing

            try:
                ts = datetime.now()
                packet_data = {
                    'id': self.packet_id,
                    'time': ts.strftime('%H:%M:%S.%f')[:-3],
                    'timestamp': ts.isoformat(),
                    'length': len(packet),
                    'raw': bytes(packet)  # Store raw packet bytes for PCAP export
                }

                # Store only essential parsed fields for display

                # Extract IP layer
                if packet.haslayer(IP):
                    ip_layer = packet[IP]
                    packet_data['source'] = ip_layer.src
                    packet_data['destination'] = ip_layer.dst

                    # Handle TCP packets
                    if packet.haslayer(TCP):
                        tcp_layer = packet[TCP]
                        packet_data['protocol'] = 'TCP'
                        packet_data['source_port'] = tcp_layer.sport
                        packet_data['dest_port'] = tcp_layer.dport
                        packet_data['info'] = f"{tcp_layer.sport} → {tcp_layer.dport} [{tcp_layer.flags}]"

                        # Check for industrial protocols on TCP
                        if packet.haslayer(Raw):
                            payload = bytes(packet[Raw].load)

                            # Modbus TCP (port 502)
                            if tcp_layer.sport == 502 or tcp_layer.dport == 502:
                                modbus_data = parse_modbus_tcp(payload)
                                if modbus_data:
                                    packet_data['protocol'] = 'MODBUS'
                                    packet_data['info'] = f"Modbus: {modbus_data['function_name']} (Unit {modbus_data['unit_id']})"

                            # S7comm (port 102)
                            elif tcp_layer.sport == 102 or tcp_layer.dport == 102:
                                s7_data = parse_s7comm(payload)
                                if s7_data:
                                    packet_data['protocol'] = 'S7COMM'
                                    packet_data['info'] = f"S7comm: {s7_data.get('message_type_name', 'Unknown')}"

                            # OPC-UA (port 4840)
                            elif tcp_layer.sport == 4840 or tcp_layer.dport == 4840:
                                opcua_data = parse_opcua(payload)
                                if opcua_data:
                                    packet_data['protocol'] = 'OPCUA'
                                    packet_data['info'] = f"OPC-UA: {opcua_data['message_type_name']} ({opcua_data['chunk_type_name']})"

                            # EtherNet/IP (port 44818)
                            elif tcp_layer.sport == 44818 or tcp_layer.dport == 44818:
                                enip_data = parse_enip(payload)
                                if enip_data:
                                    packet_data['protocol'] = 'ENIP'
                                    packet_data['info'] = f"EtherNet/IP: {enip_data['command_name']}"

                    # Handle UDP packets
                    elif packet.haslayer(UDP):
                        udp_layer = packet[UDP]
                        packet_data['protocol'] = 'UDP'
                        packet_data['source_port'] = udp_layer.sport
                        packet_data['dest_port'] = udp_layer.dport
                        packet_data['info'] = f"{udp_layer.sport} → {udp_layer.dport}"

                        # Check for DNS
                        if packet.haslayer(DNS):
                            packet_data['protocol'] = 'DNS'
                            packet_data['info'] = "DNS Query/Response"

                    # Handle ICMP packets
                    elif packet.haslayer(ICMP):
                        packet_data['protocol'] = 'ICMP'
                        packet_data['info'] = f"Type {packet[ICMP].type}"
                    else:
                        packet_data['protocol'] = 'IP'
                        packet_data['info'] = f"Protocol {ip_layer.proto}"

                # Handle ARP packets
                elif packet.haslayer(ARP):
                    arp_layer = packet[ARP]
                    packet_data['protocol'] = 'ARP'
                    packet_data['source'] = arp_layer.psrc
                    packet_data['destination'] = arp_layer.pdst
                    packet_data['info'] = f"Who has {arp_layer.pdst}? Tell {arp_layer.psrc}"
                else:
                    packet_data['protocol'] = 'OTHER'
                    packet_data['source'] = 'N/A'
                    packet_data['destination'] = 'N/A'
                    packet_data['info'] = 'Unknown protocol'

                # Add packet with memory management
                self.add_packet(packet_data)
                self.packet_id += 1

            except Exception as e:
                logger.error(f"Error processing packet: {e}", exc_info=True)

        # Start sniffing
        iface = None if interface == 'all' else interface

        # Build BPF filter (Berkeley Packet Filter for performance)
        # Always filter to Docker subnet 172.18.0.0/24 to avoid capturing host traffic
        subnet_filter = "net 172.18.0.0/24"

        if filter_str:
            bpf_filter = f"({subnet_filter}) and ({filter_str})"
        else:
            bpf_filter = subnet_filter

        logger.info(f"Starting Scapy sniff on interface: {iface}, BPF filter: {bpf_filter}")
        sniff(prn=packet_handler, store=False, iface=iface, filter=bpf_filter, stop_filter=lambda x: not self.active)

    def _capture_simulated(self):
        """Simulated packet capture for demonstration"""
        import random

        protocols = ['TCP', 'UDP', 'ICMP', 'DNS', 'HTTP', 'ARP']

        while self.active:
            # Generate simulated packet
            protocol = random.choice(protocols)
            ts = datetime.now()
            packet_data = {
                'id': self.packet_id,
                'time': ts.strftime('%H:%M:%S.%f')[:-3],
                'timestamp': ts.isoformat(),
                'source': f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                'destination': f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                'protocol': protocol,
                'length': random.randint(64, 1500),
                'info': f"Simulated {protocol} packet"
            }

            if protocol in ['TCP', 'UDP', 'HTTP', 'DNS']:
                sport = random.randint(1024, 65535)
                dport = 80 if protocol == 'HTTP' else (53 if protocol == 'DNS' else random.randint(1024, 65535))
                packet_data['source_port'] = sport
                packet_data['dest_port'] = dport
                packet_data['info'] = f"{sport} → {dport}"

            self.add_packet(packet_data)
            self.packet_id += 1
            time.sleep(random.uniform(0.1, 1.0))  # Random interval between packets

    def get_stats(self):
        """Get capture statistics"""
        with self.lock:
            estimated_mb = len(self.packets) * self.avg_packet_size_kb / 1024
            return {
                'total_packets': len(self.packets),
                'dropped_packets': self.dropped_packets,
                'memory_mb': round(estimated_mb, 2),
                'max_packets': MAX_PACKETS_IN_MEMORY
            }
