"""
Network capture API routes
"""
import ipaddress
import netifaces
from flask import Response, jsonify, request
from datetime import datetime

from modules.network_capture import CAPTURE_FILTERS, CaptureError, capturable_interfaces, public_message
from utils.config import UPLINK_INTERFACE
from utils.logger import logger

# The lab's Docker network (see .devcontainer/virtual/docker-compose.yml). The
# host's bridge on it is the interface Sharky should offer first.
LAB_NETWORK = ipaddress.ip_network('172.18.0.0/24')


def _on_lab_network(ip):
    try:
        return ip is not None and ipaddress.ip_address(ip) in LAB_NETWORK
    except ValueError:
        return False

def register_network_routes(app, network_capture):
    """Register network-related API routes"""

    @app.route('/api/network/interfaces')
    def get_network_interfaces():
        """The interfaces Sharky can capture on.

        The uplink to the CTF server is never among them, and neither is an
        interface that is not Ethernet: the export declares Ethernet frames.
        """
        try:
            interfaces_list = []
            for interface in capturable_interfaces():
                addrs = netifaces.ifaddresses(interface)
                ip = None
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0].get('addr')

                # Determine interface type
                if interface.startswith('br-') and _on_lab_network(ip):
                    iface_type = 'ics_bridge'
                elif interface.startswith('docker'):
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
            return jsonify({'error': 'An internal error occurred'}), 500

    @app.route('/api/network/filters')
    def get_capture_filters():
        """The capture filters a capture can be started with."""
        return jsonify(sorted(name for name in CAPTURE_FILTERS if name))

    @app.route('/api/network/start', methods=['POST'])
    def start_network_capture():
        """Start a capture, replacing any that is running."""
        data = request.get_json(silent=True) or {}
        interface = data.get('interface', 'all')
        filter_name = data.get('filter', '')
        if interface == UPLINK_INTERFACE:
            return jsonify({'error': 'This interface cannot be captured'}), 403
        try:
            network_capture.start(interface, filter_name)
        except CaptureError as e:
            logger.warning(f"Capture refused: {e}")
            return jsonify({'error': public_message(e)}), 400
        except Exception as e:
            logger.error(f"Error starting network capture: {e}", exc_info=True)
            return jsonify({'error': 'An internal error occurred'}), 500
        return jsonify({'success': True, 'message': 'Capture started'})

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
            return jsonify({'error': 'An internal error occurred'}), 500

    @app.route('/api/network/packets')
    def get_network_packets():
        """Packets newer than ?since=<id>, and the capture's state.

        The page used to fetch the whole buffer twice a second -- about
        240 KB of JSON each time, serialised on the Pi -- although all but a
        few hundred packets were already on screen.
        """
        try:
            since = request.args.get('since', default=0, type=int)
            packets, stats = network_capture.packets_since(since)
            return jsonify({'packets': packets, 'stats': stats})
        except Exception as e:
            logger.error(f"Error getting network packets: {e}", exc_info=True)
            return jsonify({'error': 'An internal error occurred'}), 500

    @app.route('/api/network/packet/<int:packet_id>/raw')
    def get_network_packet_raw(packet_id):
        """One packet's bytes as hex, for the hex dump, read from the capture file."""
        raw = network_capture.packet_raw(packet_id)
        if raw is None:
            return jsonify({'error': 'Packet is not in the capture file'}), 404
        return jsonify({'id': packet_id, 'raw_hex': raw.hex()})

    @app.route('/api/network/clear', methods=['POST'])
    def clear_network_capture():
        """Clear captured packets"""
        try:
            network_capture.clear()
            return jsonify({'success': True, 'message': 'Packets cleared'})
        except Exception as e:
            logger.error(f"Error clearing network packets: {e}", exc_info=True)
            return jsonify({'error': 'An internal error occurred'}), 500

    @app.route('/api/network/stats')
    def get_network_stats():
        """Get network capture statistics"""
        try:
            stats = network_capture.get_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Error getting network stats: {e}", exc_info=True)
            return jsonify({'error': 'An internal error occurred'}), 500

    @app.route('/api/network/export')
    def export_network_capture():
        """The capture so far as a pcap file, the frames as they were received.

        Streamed from the capture file on disk, up to the size it had when
        the request came in, so a capture still running cannot make the body
        longer than its Content-Length.
        """
        snapshot = network_capture.pcap_snapshot()
        if snapshot is None:
            return jsonify({'error': 'Nothing has been captured'}), 404
        path, size = snapshot

        def chunks():
            remaining = size
            with open(path, 'rb') as handle:
                while remaining > 0:
                    chunk = handle.read(min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap"
        logger.info(f"Exporting {size} bytes of capture as {filename}")
        return Response(chunks(), mimetype='application/vnd.tcpdump.pcap', headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Length': str(size),
        })
