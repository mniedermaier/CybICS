"""CybICS AI Agent - Network scanning tools"""
import logging
import subprocess

logger = logging.getLogger(__name__)


VALID_SCAN_TYPES = ('basic', 'port', 'service', 'vuln')


def execute_network_scan(target, scan_type='basic'):
    """
    Execute a network scan using nmap on the CybICS network.

    Args:
        target: Target IP address or network range (e.g., '172.18.0.0/24').
        scan_type: Type of scan - 'basic' (ping), 'port' (all ports),
            'service' (version detection), or 'vuln' (vulnerability scan).
    """
    # Validate scan_type against allowlist
    if scan_type not in VALID_SCAN_TYPES:
        return {'error': f'Invalid scan type: {scan_type}. Must be one of: {", ".join(VALID_SCAN_TYPES)}'}

    # Validate target is an IP address or CIDR range (no shell metacharacters)
    import re
    if not re.match(r'^[\d./]+$', target):
        return {'error': f'Invalid target: {target}. Must be an IP address or CIDR range.'}

    try:
        if scan_type == 'basic':
            cmd = ['nmap', '-sn', target]
        elif scan_type == 'port':
            cmd = ['nmap', '-p-', target]
        elif scan_type == 'service':
            cmd = ['nmap', '-sV', target]
        elif scan_type == 'vuln':
            cmd = ['nmap', '--script', 'vuln', target]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        return {
            'success': True,
            'scan_type': scan_type,
            'target': target,
            'results': result.stdout
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Scan timed out (exceeded 5 minutes)'}
    except FileNotFoundError:
        return {'error': 'nmap not found - network scanning not available'}
    except Exception as e:
        logger.error(f"Error executing network scan: {e}")
        return {'error': 'Failed to execute network scan'}
