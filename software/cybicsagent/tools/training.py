"""CybICS AI Agent - Training, CTF, and learning tools"""
import logging

import requests

from config import LANDING_HOST, LANDING_PORT

logger = logging.getLogger(__name__)


def _landing_url():
    return f'http://{LANDING_HOST}:{LANDING_PORT}'


def get_ctf_progress():
    """
    Get current CTF progress showing solved challenges, total points,
    and completion statistics across all categories.
    """
    try:
        resp = requests.get(f'{_landing_url()}/ctf/progress', timeout=5)
        resp.raise_for_status()
        progress = resp.json()

        return {
            'success': True,
            'progress': progress,
        }
    except requests.ConnectionError:
        return {'error': 'Could not connect to landing page - is it running?'}
    except Exception as e:
        logger.error(f"Error getting CTF progress: {e}")
        return {'error': f'Failed to get CTF progress: {str(e)}'}


def verify_defense_challenge(challenge_id):
    """
    Run automatic verification for a defense challenge to check if the student
    has correctly applied the security hardening measure.

    Args:
        challenge_id: ID of the defense challenge to verify (e.g.,
            'defense_openplc_password', 'defense_fuxa_password',
            'defense_firewall', 'defense_network_segmentation',
            'defense_ids_tuning').
    """
    try:
        resp = requests.post(
            f'{_landing_url()}/ctf/verify/{challenge_id}',
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()

        return {
            'success': True,
            'challenge_id': challenge_id,
            'verification': result,
        }
    except requests.ConnectionError:
        return {'error': 'Could not connect to landing page for verification'}
    except Exception as e:
        logger.error(f"Error verifying defense challenge: {e}")
        return {'error': f'Failed to verify challenge: {str(e)}'}


def get_network_packets(count=50):
    """
    Get recently captured network packets with protocol analysis.
    Shows parsed protocol information including Modbus, S7comm, OPC-UA, and EtherNet/IP.

    Args:
        count: Number of recent packets to retrieve (default: 50).
    """
    try:
        resp = requests.get(
            f'{_landing_url()}/api/network/packets',
            params={'count': count},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        packets = data.get('packets', [])

        # Build protocol summary
        protocols = {}
        for pkt in packets:
            proto = pkt.get('protocol', 'unknown')
            protocols[proto] = protocols.get(proto, 0) + 1

        return {
            'success': True,
            'total_packets': len(packets),
            'protocol_summary': protocols,
            'packets': packets[-count:],
            'capture_active': data.get('capturing', False),
        }
    except requests.ConnectionError:
        return {'error': 'Could not connect to landing page for packet data'}
    except Exception as e:
        logger.error(f"Error getting network packets: {e}")
        return {'error': f'Failed to get network packets: {str(e)}'}


def get_capture_stats():
    """
    Get network capture statistics including packet counts, protocol breakdown,
    and capture status.
    """
    try:
        resp = requests.get(f'{_landing_url()}/api/network/stats', timeout=5)
        resp.raise_for_status()
        return {
            'success': True,
            'stats': resp.json(),
        }
    except requests.ConnectionError:
        return {'error': 'Could not connect to landing page'}
    except Exception as e:
        logger.error(f"Error getting capture stats: {e}")
        return {'error': f'Failed to get capture stats: {str(e)}'}
