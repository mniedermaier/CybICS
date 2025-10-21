"""
Network capture API routes
"""
import netifaces
from flask import jsonify, request, send_file
from datetime import datetime
import io
import struct

from utils.logger import logger

def register_network_routes(app, network_capture):
    """Register network-related API routes"""

    @app.route('/api/network/interfaces')
    def get_network_interfaces():
        """Get available network interfaces"""
        try:
            interfaces_list = []
            for interface in netifaces.interfaces():
                # Skip loopback only
                if interface.startswith('lo'):
                    continue

                addrs = netifaces.ifaddresses(interface)
                ip = None
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0].get('addr')

                # Determine interface type
                if interface.startswith('docker'):
                    iface_type = 'docker'
                elif interface.startswith('br-'):
                    iface_type = 'bridge'
                elif interface.startswith('veth'):
                    iface_type = 'veth'
                else:
                    iface_type = 'physical'

                interfaces_list.append({
                    'name': interface,
                    'ip': ip,
                    'type': iface_type
                })

            logger.debug(f"Retrieved {len(interfaces_list)} network interfaces")
            return jsonify(interfaces_list)
        except Exception as e:
            logger.error(f"Error getting network interfaces: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/network/start', methods=['POST'])
    def start_network_capture():
        """Start network packet capture"""
        try:
            data = request.get_json() or {}
            interface = data.get('interface', 'all')
            filter_str = data.get('filter', '')

            if network_capture.active:
                logger.warning("Capture start requested but already active")
                return jsonify({'error': 'Capture already active'}), 400

            success = network_capture.start(interface, filter_str)

            if success:
                return jsonify({'success': True, 'message': 'Capture started'})
            else:
                return jsonify({'error': 'Failed to start capture'}), 500

        except Exception as e:
            logger.error(f"Error starting network capture: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/network/stop', methods=['POST'])
    def stop_network_capture():
        """Stop network packet capture"""
        try:
            network_capture.stop()
            stats = network_capture.get_stats()
            logger.info(f"Capture stopped: {stats}")
            return jsonify({'success': True, 'message': 'Capture stopped', 'stats': stats})
        except Exception as e:
            logger.error(f"Error stopping network capture: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/network/packets')
    def get_network_packets():
        """Get captured network packets"""
        try:
            packets = network_capture.get_packets()
            logger.debug(f"Retrieving {len(packets)} packets")
            return jsonify({'packets': packets})
        except Exception as e:
            logger.error(f"Error getting network packets: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/network/clear', methods=['POST'])
    def clear_network_capture():
        """Clear captured packets"""
        try:
            network_capture.clear()
            return jsonify({'success': True, 'message': 'Packets cleared'})
        except Exception as e:
            logger.error(f"Error clearing network packets: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/network/stats')
    def get_network_stats():
        """Get network capture statistics"""
        try:
            stats = network_capture.get_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Error getting network stats: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/network/export')
    def export_network_capture():
        """Export captured packets as PCAP file"""
        try:
            packets = network_capture.get_packets()
            logger.info(f"Exporting {len(packets)} packets to PCAP")

            # Create PCAP file in memory
            pcap_buffer = io.BytesIO()

            # PCAP Global Header
            pcap_buffer.write(struct.pack('I', 0xa1b2c3d4))  # Magic number
            pcap_buffer.write(struct.pack('HH', 2, 4))  # Version
            pcap_buffer.write(struct.pack('I', 0))  # Timezone
            pcap_buffer.write(struct.pack('I', 0))  # Timestamp accuracy
            pcap_buffer.write(struct.pack('I', 65535))  # Snapshot length
            pcap_buffer.write(struct.pack('I', 1))  # Data link type (Ethernet)

            # Write packet data
            for packet in packets:
                # Parse timestamp
                try:
                    from dateutil import parser as date_parser
                    ts = date_parser.parse(packet.get('timestamp', datetime.now().isoformat()))
                    ts_sec = int(ts.timestamp())
                    ts_usec = ts.microsecond
                except:
                    ts_sec = int(datetime.now().timestamp())
                    ts_usec = 0

                # Use raw packet data if available, otherwise create minimal packet
                packet_data = _reconstruct_packet_data(packet)
                packet_length = len(packet_data)

                # PCAP Packet Header
                pcap_buffer.write(struct.pack('I', ts_sec))
                pcap_buffer.write(struct.pack('I', ts_usec))
                pcap_buffer.write(struct.pack('I', packet_length))
                pcap_buffer.write(struct.pack('I', packet_length))
                pcap_buffer.write(packet_data)

            pcap_buffer.seek(0)
            filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap"

            logger.info(f"PCAP export successful: {filename}")
            return send_file(
                pcap_buffer,
                mimetype='application/vnd.tcpdump.pcap',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            logger.error(f"Error exporting network capture: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

def _reconstruct_packet_data(packet):
    """Reconstruct minimal packet data from parsed information"""
    packet_bytes = bytearray()

    # Ethernet header (14 bytes)
    if 'layers' in packet and 'ethernet' in packet['layers']:
        eth = packet['layers']['ethernet']
        dst_mac = bytes.fromhex(eth.get('dst', 'ff:ff:ff:ff:ff:ff').replace(':', ''))
        src_mac = bytes.fromhex(eth.get('src', '00:00:00:00:00:00').replace(':', ''))
        packet_bytes.extend(dst_mac)
        packet_bytes.extend(src_mac)
        packet_bytes.extend(struct.pack('!H', 0x0800))  # IPv4
    else:
        packet_bytes.extend(b'\xff\xff\xff\xff\xff\xff')
        packet_bytes.extend(b'\x00\x00\x00\x00\x00\x00')
        packet_bytes.extend(struct.pack('!H', 0x0800))

    # IPv4 header (20 bytes minimum)
    if 'layers' in packet and 'ip' in packet['layers']:
        ip = packet['layers']['ip']
        src_ip = packet.get('source', '0.0.0.0')
        dst_ip = packet.get('destination', '0.0.0.0')

        packet_bytes.append(0x45)
        packet_bytes.append(0x00)
        total_length = max(packet.get('length', 60), 60)
        packet_bytes.extend(struct.pack('!H', total_length))
        packet_bytes.extend(struct.pack('!H', packet.get('id', 0)))
        packet_bytes.extend(struct.pack('!H', 0x4000))
        packet_bytes.append(ip.get('ttl', 64))

        # Protocol
        proto = 6  # TCP default
        if packet.get('protocol') == 'UDP':
            proto = 17
        elif packet.get('protocol') == 'ICMP':
            proto = 1
        packet_bytes.append(proto)

        packet_bytes.extend(struct.pack('!H', 0x0000))  # Checksum

        # Source and Destination IP
        for octet in src_ip.split('.'):
            packet_bytes.append(int(octet))
        for octet in dst_ip.split('.'):
            packet_bytes.append(int(octet))
    else:
        packet_bytes.extend(b'\x45\x00\x00\x3c\x00\x00\x40\x00\x40\x06\x00\x00')
        packet_bytes.extend(b'\x00\x00\x00\x00\x00\x00\x00\x00')

    # TCP/UDP header
    if 'layers' in packet and 'tcp' in packet['layers']:
        tcp = packet['layers']['tcp']
        packet_bytes.extend(struct.pack('!H', tcp.get('sport', 0)))
        packet_bytes.extend(struct.pack('!H', tcp.get('dport', 0)))
        packet_bytes.extend(struct.pack('!I', tcp.get('seq', 0)))
        packet_bytes.extend(struct.pack('!I', 0))
        packet_bytes.extend(struct.pack('!H', 0x5000))
        packet_bytes.extend(struct.pack('!H', 8192))
        packet_bytes.extend(struct.pack('!H', 0))
        packet_bytes.extend(struct.pack('!H', 0))
    elif 'layers' in packet and 'udp' in packet['layers']:
        udp = packet['layers']['udp']
        packet_bytes.extend(struct.pack('!H', udp.get('sport', 0)))
        packet_bytes.extend(struct.pack('!H', udp.get('dport', 0)))
        packet_bytes.extend(struct.pack('!H', udp.get('len', 8)))
        packet_bytes.extend(struct.pack('!H', 0))

    # Pad to minimum size
    while len(packet_bytes) < 60:
        packet_bytes.append(0)

    return bytes(packet_bytes)
