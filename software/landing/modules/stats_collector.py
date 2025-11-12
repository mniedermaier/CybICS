"""
System and Docker statistics collection module
"""
import threading
import time
import psutil
from datetime import datetime
from collections import deque

from utils.logger import logger
from utils.config import HISTORY_MAX_LENGTH, STATS_COLLECTION_INTERVAL, DOCKER_STATS_INTERVAL

class StatsCollector:
    """Collect and store system and Docker container statistics"""

    def __init__(self):
        self.history = {
            'timestamps': deque(maxlen=HISTORY_MAX_LENGTH),
            'cpu': deque(maxlen=HISTORY_MAX_LENGTH),
            'memory': deque(maxlen=HISTORY_MAX_LENGTH),
            'swap': deque(maxlen=HISTORY_MAX_LENGTH),
            'disk': deque(maxlen=HISTORY_MAX_LENGTH),
            'network_rx': deque(maxlen=HISTORY_MAX_LENGTH),
            'network_tx': deque(maxlen=HISTORY_MAX_LENGTH),
            'network_total': deque(maxlen=HISTORY_MAX_LENGTH)
        }
        self.history_lock = threading.Lock()
        self.prev_network_counters = {'bytes_sent': 0, 'bytes_recv': 0, 'timestamp': time.time()}

        self.docker_container_cache = []
        self.docker_cache_lock = threading.Lock()

        self.stats_thread = None
        self.docker_thread = None
        self.running = False

        logger.info("StatsCollector initialized")

    def start(self):
        """Start background collection threads"""
        if self.running:
            logger.warning("StatsCollector already running")
            return

        self.running = True

        # Initialize network counters
        net_stats = self._get_host_network_stats()
        self.prev_network_counters = {
            'bytes_sent': net_stats['bytes_sent'],
            'bytes_recv': net_stats['bytes_recv'],
            'timestamp': time.time()
        }

        self.stats_thread = threading.Thread(target=self._collect_stats_history, daemon=True)
        self.stats_thread.start()
        logger.info("Started system stats collection thread")

        self.docker_thread = threading.Thread(target=self._collect_docker_stats, daemon=True)
        self.docker_thread.start()
        logger.info("Started Docker stats collection thread")

    def stop(self):
        """Stop collection threads"""
        self.running = False
        logger.info("Stopped stats collection")

    def _get_host_network_stats(self):
        """Get network stats from host, excluding Docker-related interfaces"""
        try:
            net_io_per_nic = psutil.net_io_counters(pernic=True)

            bytes_recv = 0
            bytes_sent = 0

            for interface, stats in net_io_per_nic.items():
                # Skip loopback and docker interfaces
                if interface.startswith(('lo', 'docker', 'br-', 'veth')):
                    continue

                bytes_recv += stats.bytes_recv
                bytes_sent += stats.bytes_sent

            return {
                'bytes_recv': bytes_recv,
                'bytes_sent': bytes_sent,
                'source': 'host'
            }
        except Exception as e:
            logger.error(f"Error getting host network stats: {e}")
            # Fallback to all interfaces
            net_io = psutil.net_io_counters()
            return {'bytes_recv': net_io.bytes_recv, 'bytes_sent': net_io.bytes_sent, 'source': 'fallback'}

    def _collect_stats_history(self):
        """Background thread to collect stats every interval"""
        logger.info(f"Stats history collection started (interval: {STATS_COLLECTION_INTERVAL}s)")

        while self.running:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                swap_percent = psutil.swap_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                timestamp = datetime.now().isoformat()

                # Get network stats
                net_stats = self._get_host_network_stats()
                current_time = time.time()
                time_delta = current_time - self.prev_network_counters['timestamp']

                # Calculate rates in MB/s
                if time_delta > 0:
                    rx_rate = (net_stats['bytes_recv'] - self.prev_network_counters['bytes_recv']) / time_delta / (1024 ** 2)
                    tx_rate = (net_stats['bytes_sent'] - self.prev_network_counters['bytes_sent']) / time_delta / (1024 ** 2)
                    total_rate = rx_rate + tx_rate
                else:
                    rx_rate = tx_rate = total_rate = 0

                # Update previous counters
                self.prev_network_counters = {
                    'bytes_sent': net_stats['bytes_sent'],
                    'bytes_recv': net_stats['bytes_recv'],
                    'timestamp': current_time
                }

                with self.history_lock:
                    self.history['timestamps'].append(timestamp)
                    self.history['cpu'].append(round(cpu_percent, 2))
                    self.history['memory'].append(round(memory_percent, 2))
                    self.history['swap'].append(round(swap_percent, 2))
                    self.history['disk'].append(round(disk_percent, 2))
                    self.history['network_rx'].append(round(rx_rate, 2))
                    self.history['network_tx'].append(round(tx_rate, 2))
                    self.history['network_total'].append(round(total_rate, 2))

                logger.debug(f"Stats collected: CPU={cpu_percent:.1f}%, MEM={memory_percent:.1f}%, NET_RX={rx_rate:.2f}MB/s")

            except Exception as e:
                logger.error(f"Error collecting stats history: {e}", exc_info=True)

            time.sleep(STATS_COLLECTION_INTERVAL)

    def _collect_docker_stats(self):
        """Background thread to collect Docker container stats"""
        logger.info(f"Docker stats collection started (interval: {DOCKER_STATS_INTERVAL}s)")

        while self.running:
            try:
                import requests_unixsocket
                session = requests_unixsocket.Session()

                # Get containers list via Docker API (using version-agnostic endpoint)
                response = session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/json')

                # Check response status first
                if response.status_code != 200:
                    logger.warning(f"Docker API returned status {response.status_code}: {response.text}")
                    containers_list = []
                else:
                    containers_list = response.json()

                    # Ensure containers_list is actually a list
                    if not isinstance(containers_list, list):
                        logger.warning(f"Docker API returned non-list containers: {type(containers_list)}")
                        logger.debug(f"Response content: {containers_list}")
                        containers_list = []

                logger.debug(f"Found {len(containers_list)} running containers")

                containers_info = []
                for container in containers_list:
                    # Ensure container is a dictionary
                    if not isinstance(container, dict):
                        logger.debug(f"Skipping non-dict container: {type(container)}")
                        continue

                    container_names = container.get('Names', [])
                    if not container_names:
                        continue
                    container_name = container_names[0].lstrip('/')

                    # Filter for CybICS-related containers
                    container_name_lower = container_name.lower()
                    if not (container_name_lower.startswith('virtual-') or
                            container_name_lower.startswith('raspberry-') or
                            'cybics' in container_name_lower):
                        continue

                    # Skip buildkit and registry containers
                    if 'buildkit' in container_name_lower or container_name_lower.endswith('-registry-1'):
                        continue

                    logger.debug(f"Processing container: {container_name}")

                    try:
                        container_id = container['Id']
                        stats_response = session.get(f'http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/{container_id}/stats?stream=false')
                        stats = stats_response.json()

                        # Calculate CPU usage
                        cpu_percent_container = 0.0
                        try:
                            cpu_stats = stats.get('cpu_stats', {})
                            precpu_stats = stats.get('precpu_stats', {})

                            if isinstance(cpu_stats, dict) and isinstance(precpu_stats, dict):
                                cpu_usage = cpu_stats.get('cpu_usage', {})
                                precpu_usage = precpu_stats.get('cpu_usage', {})

                                if isinstance(cpu_usage, dict) and isinstance(precpu_usage, dict):
                                    cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
                                    system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)

                                    if system_delta > 0:
                                        percpu_usage = cpu_usage.get('percpu_usage', [1]) if isinstance(cpu_usage.get('percpu_usage', [1]), list) else [1]
                                        cpu_percent_container = (cpu_delta / system_delta) * len(percpu_usage) * 100.0
                        except Exception as e:
                            logger.debug(f"Error calculating CPU stats for {container_name}: {e}")

                        # Calculate memory usage
                        memory_stats = stats.get('memory_stats', {})
                        mem_usage = memory_stats.get('usage', 0) / (1024 ** 2) if isinstance(memory_stats, dict) else 0
                        mem_limit = memory_stats.get('limit', 1) / (1024 ** 2) if isinstance(memory_stats, dict) else 1
                        mem_percent_container = (mem_usage / mem_limit * 100) if mem_limit > 0 else 0

                        # Get network stats
                        networks = stats.get('networks', {})
                        rx_bytes = sum(net.get('rx_bytes', 0) for net in networks.values() if isinstance(net, dict)) / (1024 ** 2)  # MB
                        tx_bytes = sum(net.get('tx_bytes', 0) for net in networks.values() if isinstance(net, dict)) / (1024 ** 2)  # MB

                        # Get image name
                        image_name = container.get('Image', 'unknown')

                        # Calculate uptime
                        uptime_str = 'N/A'
                        try:
                            inspect_response = session.get(f'http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/{container_id}/json')
                            inspect_data = inspect_response.json()
                            state = inspect_data.get('State', {})
                            started_at_str = state.get('StartedAt', '') if isinstance(state, dict) else ''

                            if started_at_str:
                                from dateutil import parser
                                started_at = parser.parse(started_at_str)
                                now = datetime.now(started_at.tzinfo)
                                uptime_seconds = (now - started_at).total_seconds()

                                days = int(uptime_seconds // 86400)
                                hours = int((uptime_seconds % 86400) // 3600)
                                minutes = int((uptime_seconds % 3600) // 60)

                                if days > 0:
                                    uptime_str = f"{days}d {hours}h {minutes}m"
                                elif hours > 0:
                                    uptime_str = f"{hours}h {minutes}m"
                                else:
                                    uptime_str = f"{minutes}m"
                        except Exception as e:
                            logger.debug(f"Error calculating uptime for {container_name}: {e}")

                        containers_info.append({
                            'name': container_name,
                            'id': container_id[:12],
                            'status': container.get('State', 'unknown'),
                            'uptime': uptime_str,
                            'cpu_percent': round(cpu_percent_container, 2),
                            'memory_usage_mb': round(mem_usage, 2),
                            'memory_limit_mb': round(mem_limit, 2),
                            'memory_percent': round(mem_percent_container, 2),
                            'network_rx_mb': round(rx_bytes, 2),
                            'network_tx_mb': round(tx_bytes, 2),
                            'image': image_name
                        })
                    except Exception as e:
                        logger.warning(f"Error getting stats for container {container_name}: {e}")
                        continue

                # Update cache
                with self.docker_cache_lock:
                    self.docker_container_cache = containers_info

                logger.debug(f"Updated Docker cache with {len(containers_info)} containers")

            except Exception as e:
                import traceback
                logger.warning(f"Error collecting Docker stats: {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")

            time.sleep(DOCKER_STATS_INTERVAL)

    def get_history(self):
        """Get historical stats data"""
        with self.history_lock:
            return {
                'timestamps': list(self.history['timestamps']),
                'cpu': list(self.history['cpu']),
                'memory': list(self.history['memory']),
                'swap': list(self.history['swap']),
                'disk': list(self.history['disk']),
                'network_rx': list(self.history['network_rx']),
                'network_tx': list(self.history['network_tx']),
                'network_total': list(self.history['network_total'])
            }

    def get_docker_containers(self):
        """Get Docker container stats from cache"""
        with self.docker_cache_lock:
            return self.docker_container_cache.copy()

    def get_current_stats(self):
        """Get current system statistics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 ** 3)  # GB
        memory_used = memory.used / (1024 ** 3)  # GB
        memory_percent = memory.percent

        swap = psutil.swap_memory()
        swap_total = swap.total / (1024 ** 3)  # GB
        swap_used = swap.used / (1024 ** 3)  # GB
        swap_percent = swap.percent

        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024 ** 3)  # GB
        disk_used = disk.used / (1024 ** 3)  # GB
        disk_percent = disk.percent

        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)

        net_stats = self._get_host_network_stats()
        net_io = psutil.net_io_counters()

        return {
            'timestamp': datetime.now().isoformat(),
            'uptime': {
                'days': uptime_days,
                'hours': uptime_hours,
                'minutes': uptime_minutes,
                'total_seconds': int(uptime_seconds)
            },
            'cpu': {
                'percent': round(cpu_percent, 2),
                'count': cpu_count
            },
            'memory': {
                'total_gb': round(memory_total, 2),
                'used_gb': round(memory_used, 2),
                'percent': round(memory_percent, 2)
            },
            'swap': {
                'total_gb': round(swap_total, 2),
                'used_gb': round(swap_used, 2),
                'percent': round(swap_percent, 2)
            },
            'disk': {
                'total_gb': round(disk_total, 2),
                'used_gb': round(disk_used, 2),
                'percent': round(disk_percent, 2)
            },
            'network': {
                'bytes_sent': net_stats['bytes_sent'],
                'bytes_recv': net_stats['bytes_recv'],
                'bytes_sent_gb': round(net_stats['bytes_sent'] / (1024 ** 3), 2),
                'bytes_recv_gb': round(net_stats['bytes_recv'] / (1024 ** 3), 2),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'source': net_stats.get('source', 'unknown')
            },
            'containers': self.get_docker_containers()
        }
