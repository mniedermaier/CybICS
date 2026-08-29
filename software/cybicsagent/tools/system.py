"""CybICS AI Agent - System monitoring tools"""
import json
import logging
import subprocess

logger = logging.getLogger(__name__)


def get_system_stats():
    """Get real-time resource usage statistics for all Docker containers including CPU, memory, and network I/O"""
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {'error': f'Failed to get stats: {result.stderr}'}

        stats = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    stats.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return {
            'success': True,
            'container_stats': stats
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {'error': 'Failed to get system statistics'}


def list_docker_images():
    """List all Docker images available on the system"""
    try:
        result = subprocess.run(
            ['docker', 'images', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {'error': f'Failed to list images: {result.stderr}'}

        images = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    images.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return {
            'success': True,
            'total_images': len(images),
            'images': images
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        logger.error(f"Error listing Docker images: {e}")
        return {'error': 'Failed to list Docker images'}
