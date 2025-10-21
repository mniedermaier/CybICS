"""
Network packet capture module with memory management for Raspberry Pi Zero 2
"""
import threading
import time
import sys
from datetime import datetime
from collections import deque

from utils.logger import logger
from utils.config import MAX_PACKETS_IN_MEMORY, MAX_PACKET_MEMORY_MB, PACKET_CLEANUP_THRESHOLD

class NetworkCapture:
    """Network packet capture with memory limits for low-resource devices"""

    def __init__(self):
        self.active = False
        self.packets = deque(maxlen=MAX_PACKETS_IN_MEMORY)
        self.lock = threading.Lock()
        self.capture_thread = None
        self.packet_id = 0
        self.total_memory_mb = 0
        self.dropped_packets = 0

        logger.info(f"NetworkCapture initialized with max {MAX_PACKETS_IN_MEMORY} packets, {MAX_PACKET_MEMORY_MB}MB limit")

    def _estimate_packet_size(self, packet_data):
        """Estimate packet size in memory (MB)"""
        size = sys.getsizeof(packet_data)
        for key, value in packet_data.items():
            if isinstance(value, dict):
                size += sys.getsizeof(value)
                for k, v in value.items():
                    size += sys.getsizeof(k) + sys.getsizeof(v)
            else:
                size += sys.getsizeof(value)
        return size / (1024 * 1024)  # Convert to MB

    def _cleanup_old_packets(self):
        """Remove oldest packets if memory limit is reached"""
        with self.lock:
            while self.total_memory_mb > MAX_PACKET_MEMORY_MB * PACKET_CLEANUP_THRESHOLD:
                if len(self.packets) == 0:
                    break
                removed_packet = self.packets.popleft()
                removed_size = self._estimate_packet_size(removed_packet)
                self.total_memory_mb -= removed_size
                self.dropped_packets += 1

                if self.dropped_packets % 100 == 0:
                    logger.warning(f"Memory limit reached. Dropped {self.dropped_packets} packets. Memory: {self.total_memory_mb:.2f}MB")

    def add_packet(self, packet_data):
        """Add a packet with memory management"""
        packet_size = self._estimate_packet_size(packet_data)

        # Check if adding this packet would exceed memory limit
        if self.total_memory_mb + packet_size > MAX_PACKET_MEMORY_MB:
            self._cleanup_old_packets()

        with self.lock:
            self.packets.append(packet_data)
            self.total_memory_mb += packet_size

        if len(self.packets) % 1000 == 0:
            logger.debug(f"Captured {len(self.packets)} packets, Memory: {self.total_memory_mb:.2f}MB")

    def get_packets(self):
        """Get all captured packets"""
        with self.lock:
            return list(self.packets)

    def clear(self):
        """Clear all captured packets"""
        with self.lock:
            self.packets.clear()
            self.total_memory_mb = 0
            self.dropped_packets = 0
            logger.info("Cleared all captured packets")

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
        return True

    def stop(self):
        """Stop packet capture"""
        self.active = False
        logger.info(f"Stopped network capture. Captured {len(self.packets)} packets, Dropped {self.dropped_packets} packets")
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
                packet_data = {
                    'id': self.packet_id,
                    'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    'timestamp': datetime.now().isoformat(),
                    'length': len(packet),
                    'layers': {}
                }

                # Extract Ethernet layer
                if packet.haslayer('Ether'):
                    packet_data['layers']['ethernet'] = {
                        'src': packet['Ether'].src,
                        'dst': packet['Ether'].dst,
                        'type': hex(packet['Ether'].type)
                    }

                # Extract IP layer
                if packet.haslayer(IP):
                    ip_layer = packet[IP]
                    packet_data['source'] = ip_layer.src
                    packet_data['destination'] = ip_layer.dst
                    packet_data['layers']['ip'] = {
                        'version': ip_layer.version,
                        'ttl': ip_layer.ttl,
                        'proto': ip_layer.proto
                    }

                    # Handle TCP packets
                    if packet.haslayer(TCP):
                        tcp_layer = packet[TCP]
                        packet_data['protocol'] = 'TCP'
                        packet_data['source_port'] = tcp_layer.sport
                        packet_data['dest_port'] = tcp_layer.dport
                        packet_data['layers']['tcp'] = {
                            'sport': tcp_layer.sport,
                            'dport': tcp_layer.dport,
                            'flags': str(tcp_layer.flags),
                            'seq': tcp_layer.seq
                        }
                        packet_data['info'] = f"{tcp_layer.sport} → {tcp_layer.dport} [{tcp_layer.flags}]"

                        # Check for industrial protocols on TCP
                        if packet.haslayer(Raw):
                            payload = bytes(packet[Raw].load)

                            # Modbus TCP (port 502)
                            if tcp_layer.sport == 502 or tcp_layer.dport == 502:
                                modbus_data = parse_modbus_tcp(payload)
                                if modbus_data:
                                    packet_data['protocol'] = 'MODBUS'
                                    packet_data['layers']['modbus'] = modbus_data
                                    packet_data['info'] = f"Modbus: {modbus_data['function_name']} (Unit {modbus_data['unit_id']})"

                            # S7comm (port 102)
                            elif tcp_layer.sport == 102 or tcp_layer.dport == 102:
                                s7_data = parse_s7comm(payload)
                                if s7_data:
                                    packet_data['protocol'] = 'S7COMM'
                                    packet_data['layers']['s7comm'] = s7_data
                                    packet_data['info'] = f"S7comm: {s7_data.get('message_type_name', 'Unknown')}"

                            # OPC-UA (port 4840)
                            elif tcp_layer.sport == 4840 or tcp_layer.dport == 4840:
                                opcua_data = parse_opcua(payload)
                                if opcua_data:
                                    packet_data['protocol'] = 'OPCUA'
                                    packet_data['layers']['opcua'] = opcua_data
                                    packet_data['info'] = f"OPC-UA: {opcua_data['message_type_name']} ({opcua_data['chunk_type_name']})"

                            # EtherNet/IP (port 44818)
                            elif tcp_layer.sport == 44818 or tcp_layer.dport == 44818:
                                enip_data = parse_enip(payload)
                                if enip_data:
                                    packet_data['protocol'] = 'ENIP'
                                    packet_data['layers']['enip'] = enip_data
                                    packet_data['info'] = f"EtherNet/IP: {enip_data['command_name']}"

                    # Handle UDP packets
                    elif packet.haslayer(UDP):
                        udp_layer = packet[UDP]
                        packet_data['protocol'] = 'UDP'
                        packet_data['source_port'] = udp_layer.sport
                        packet_data['dest_port'] = udp_layer.dport
                        packet_data['layers']['udp'] = {
                            'sport': udp_layer.sport,
                            'dport': udp_layer.dport,
                            'len': udp_layer.len
                        }
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
            packet_data = {
                'id': self.packet_id,
                'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                'timestamp': datetime.now().isoformat(),
                'source': f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                'destination': f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                'protocol': protocol,
                'length': random.randint(64, 1500),
                'info': f"Simulated {protocol} packet",
                'layers': {
                    'ethernet': {'src': 'aa:bb:cc:dd:ee:ff', 'dst': 'ff:ee:dd:cc:bb:aa', 'type': '0x0800'},
                    'ip': {'version': 4, 'ttl': 64, 'proto': protocol.lower()}
                }
            }

            if protocol in ['TCP', 'UDP', 'HTTP', 'DNS']:
                sport = random.randint(1024, 65535)
                dport = 80 if protocol == 'HTTP' else (53 if protocol == 'DNS' else random.randint(1024, 65535))
                packet_data['source_port'] = sport
                packet_data['dest_port'] = dport
                packet_data['info'] = f"{sport} → {dport}"

                if protocol in ['TCP', 'HTTP']:
                    packet_data['layers']['tcp'] = {
                        'sport': sport,
                        'dport': dport,
                        'flags': random.choice(['S', 'A', 'SA', 'FA', 'PA']),
                        'seq': random.randint(1000000, 9999999)
                    }
                else:
                    packet_data['layers']['udp'] = {
                        'sport': sport,
                        'dport': dport,
                        'len': packet_data['length']
                    }

            self.add_packet(packet_data)
            self.packet_id += 1
            time.sleep(random.uniform(0.1, 1.0))  # Random interval between packets

    def get_stats(self):
        """Get capture statistics"""
        with self.lock:
            return {
                'total_packets': len(self.packets),
                'dropped_packets': self.dropped_packets,
                'memory_mb': round(self.total_memory_mb, 2),
                'max_memory_mb': MAX_PACKET_MEMORY_MB,
                'max_packets': MAX_PACKETS_IN_MEMORY
            }
