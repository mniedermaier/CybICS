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


def _resolve_cybics_container(name):
    """
    Map a requested name onto a real CybICS container.

    Compose does not pin container_name, so the running containers are called
    e.g. "software-openplc-1" while CYBICS_CONTAINERS holds the bare service
    names. Matching on the compose service label rather than on substrings of
    the container name keeps an unrelated container from passing the check by
    merely embedding an allowed name.

    Returns the real container name, or None if it is not a CybICS container.
    """
    from config import CYBICS_CONTAINERS

    result = subprocess.run(
        ['docker', 'ps', '--all', '--format',
         '{{.Names}}\t{{.Label "com.docker.compose.service"}}'],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        real_name, _, service = line.partition('\t')
        if service in CYBICS_CONTAINERS and name in (real_name, service):
            return real_name
    return None


def restart_containers(container_names=None):
    """
    Restart CybICS Docker containers.

    Args:
        container_names: Name or list of names of containers to restart.
            Must specify which container(s) to restart.
    """
    from config import CYBICS_CONTAINERS

    try:
        if not container_names:
            return {
                'error': 'Must specify which container to restart. '
                         f'Available: {", ".join(CYBICS_CONTAINERS)}'
            }

        requested = container_names if isinstance(container_names, list) else [container_names]

        # Only allow restarting known CybICS containers
        resolved = {c: _resolve_cybics_container(c) for c in requested}
        invalid = [c for c, real in resolved.items() if real is None]
        if invalid:
            return {
                'error': f'Unknown container(s): {", ".join(invalid)}. '
                         f'Allowed: {", ".join(CYBICS_CONTAINERS)}'
            }

        containers = list(resolved.values())
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
    from config import CYBICS_CONTAINERS

    try:
        real_name = _resolve_cybics_container(container_name)
        if real_name is None:
            return {
                'error': f'Unknown container: {container_name}. '
                         f'Allowed: {", ".join(CYBICS_CONTAINERS)}'
            }

        result = subprocess.run(
            ['docker', 'logs', '--tail', str(lines), '--timestamps', real_name],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {'error': f'Failed to get logs: {result.stderr}'}

        return {
            'success': True,
            'container': real_name,
            'logs': result.stdout
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        logger.error(f"Error getting container logs: {e}")
        return {'error': 'Failed to get container logs'}
