"""CybICS AI Agent - Container management tools"""
import json
import logging
import subprocess

logger = logging.getLogger(__name__)


def get_container_status():
    """Get status of all CybICS Docker containers"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {'error': f'Failed to get container status: {result.stderr}'}

        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return {
            'success': True,
            'total_containers': len(containers),
            'containers': containers
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        logger.error(f"Error getting container status: {e}")
        return {'error': 'Failed to get container status'}


def restart_containers(container_names=None):
    """
    Restart CybICS Docker containers.

    Args:
        container_names: Name or list of names of containers to restart.
            If not provided, restarts all running containers.
    """
    try:
        if container_names:
            containers = container_names if isinstance(container_names, list) else [container_names]
        else:
            ps_result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if ps_result.returncode != 0:
                return {'error': f'Failed to list containers: {ps_result.stderr}'}
            containers = [c for c in ps_result.stdout.strip().split('\n') if c]

        if not containers:
            return {'error': 'No containers found to restart'}

        failed = []
        succeeded = []
        for container in containers:
            result = subprocess.run(
                ['docker', 'restart', container],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                succeeded.append(container)
            else:
                failed.append(container)

        return {
            'success': len(failed) == 0,
            'restarted': succeeded,
            'failed': failed,
            'message': f'Restarted {len(succeeded)} container(s)'
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Restart operation timed out'}
    except Exception as e:
        logger.error(f"Error restarting containers: {e}")
        return {'error': 'Failed to restart containers'}


def get_container_logs(container_name, lines=50):
    """
    Get logs from a specific container.

    Args:
        container_name: Name of the container.
        lines: Number of log lines to retrieve (default: 50).
    """
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail', str(lines), '--timestamps', container_name],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {'error': f'Failed to get logs: {result.stderr}'}

        return {
            'success': True,
            'container': container_name,
            'logs': result.stdout
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        logger.error(f"Error getting container logs: {e}")
        return {'error': 'Failed to get container logs'}
