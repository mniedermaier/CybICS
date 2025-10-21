from flask import Flask, render_template, jsonify, request, session, send_from_directory
import logging
import sys
import json
import os
import markdown
import psutil
from datetime import datetime
from collections import deque
import threading
import time
import socket
import struct
import netifaces

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger('CybICS')

# Store the current layout state
layout_state = {
    'current_view': 'all',
    'card_order': ['openplc', 'fuxa', 'vhardware'],
    'card_sizes': {}
}

# CTF progress file path
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PROGRESS_FILE = os.path.join(DATA_DIR, 'ctf_progress.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Service configurations (port only, URL built dynamically in template)
services = {
    'openplc': {
        'name': 'OpenPLC',
        'port': 8080
    },
    'fuxa': {
        'name': 'FUXA',
        'port': 1881
    },
    'vhardware': {
        'name': 'Virtual Hardware IO',
        'port': 8090
    }
}

logger.info('Starting application with services: %s', list(services.keys()))

app = Flask(__name__)
app.secret_key = 'cybics_ctf_secret_key_change_in_production'

# Historical data storage (keep 1 hour of data at 5-second intervals = 720 data points)
HISTORY_MAX_LENGTH = 720
stats_history = {
    'timestamps': deque(maxlen=HISTORY_MAX_LENGTH),
    'cpu': deque(maxlen=HISTORY_MAX_LENGTH),
    'memory': deque(maxlen=HISTORY_MAX_LENGTH),
    'swap': deque(maxlen=HISTORY_MAX_LENGTH),
    'disk': deque(maxlen=HISTORY_MAX_LENGTH),
    'network_rx': deque(maxlen=HISTORY_MAX_LENGTH),
    'network_tx': deque(maxlen=HISTORY_MAX_LENGTH),
    'network_total': deque(maxlen=HISTORY_MAX_LENGTH)
}
history_lock = threading.Lock()

# Track previous network counters for rate calculation
prev_network_counters = {'bytes_sent': 0, 'bytes_recv': 0, 'timestamp': time.time()}

# Network capture state
network_capture_active = False
network_capture_packets = []
network_capture_lock = threading.Lock()
network_capture_thread = None

def get_host_network_stats():
    """
    Get network stats from host, excluding Docker-related interfaces.
    Since we're running in host network mode, we can access all interfaces directly.
    """
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

# Cached Docker container stats
docker_container_cache = []
docker_cache_lock = threading.Lock()

def collect_docker_stats():
    """Background thread to collect Docker container stats every 10 seconds"""
    while True:
        try:
            import requests_unixsocket
            session = requests_unixsocket.Session()

            # Get containers list via Docker API
            response = session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/v1.41/containers/json')
            containers_list = response.json()

            logger.debug(f"Found {len(containers_list)} running containers")

            containers_info = []
            for container in containers_list:
                # Get container name from Names field (it's a list with leading /)
                container_names = container.get('Names', [])
                if not container_names:
                    continue
                container_name = container_names[0].lstrip('/')

                # Filter for CybICS-related containers (virtual-*, raspberry-*, or cybics*)
                container_name_lower = container_name.lower()
                if not (container_name_lower.startswith('virtual-') or
                        container_name_lower.startswith('raspberry-') or
                        'cybics' in container_name_lower):
                    continue

                # Skip buildkit and registry containers
                if 'buildkit' in container_name_lower or container_name_lower.endswith('-registry-1'):
                    continue

                logger.debug(f"Processing CybICS container: {container_name}")
                try:
                    container_id = container['Id']
                    # Get stats via direct API call
                    stats_response = session.get(f'http+unix://%2Fvar%2Frun%2Fdocker.sock/v1.41/containers/{container_id}/stats?stream=false')
                    stats = stats_response.json()

                    # Calculate CPU usage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                                stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                   stats['precpu_stats']['system_cpu_usage']
                    cpu_percent_container = 0.0
                    if system_delta > 0:
                        cpu_percent_container = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1])) * 100.0

                    # Calculate memory usage
                    mem_usage = stats['memory_stats'].get('usage', 0) / (1024 ** 2)  # MB
                    mem_limit = stats['memory_stats'].get('limit', 1) / (1024 ** 2)  # MB
                    mem_percent_container = (mem_usage / mem_limit * 100) if mem_limit > 0 else 0

                    # Get network stats
                    networks = stats.get('networks', {})
                    rx_bytes = sum(net.get('rx_bytes', 0) for net in networks.values()) / (1024 ** 2)  # MB
                    tx_bytes = sum(net.get('tx_bytes', 0) for net in networks.values()) / (1024 ** 2)  # MB

                    # Get image name
                    image_name = container.get('Image', 'unknown')

                    # Calculate container uptime from inspect API
                    uptime_str = 'N/A'
                    try:
                        # Get detailed container info to access StartedAt
                        inspect_response = session.get(f'http+unix://%2Fvar%2Frun%2Fdocker.sock/v1.41/containers/{container_id}/json')
                        inspect_data = inspect_response.json()
                        started_at_str = inspect_data.get('State', {}).get('StartedAt', '')

                        if started_at_str:
                            # Parse the timestamp (format: 2024-01-15T10:30:00.123456789Z)
                            from dateutil import parser
                            started_at = parser.parse(started_at_str)
                            now = datetime.now(started_at.tzinfo)
                            uptime_seconds = (now - started_at).total_seconds()

                            # Format uptime as human-readable string
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
                        uptime_str = 'N/A'

                    containers_info.append({
                        'name': container_name,
                        'id': container_id[:12],  # Short ID
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

            # Update the cache
            with docker_cache_lock:
                global docker_container_cache
                docker_container_cache = containers_info

            logger.debug(f"Updated Docker cache with {len(containers_info)} containers")
        except Exception as e:
            logger.warning(f"Error collecting Docker stats: {e}")

        time.sleep(10)  # Update every 10 seconds

def collect_stats_history():
    """Background thread to collect stats every 5 seconds"""
    global prev_network_counters

    # Initialize with current values to avoid initial spike
    net_stats = get_host_network_stats()
    prev_network_counters = {
        'bytes_sent': net_stats['bytes_sent'],
        'bytes_recv': net_stats['bytes_recv'],
        'timestamp': time.time()
    }
    logger.info("Initialized network counters for rate calculation")

    while True:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            swap_percent = psutil.swap_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            timestamp = datetime.now().isoformat()

            # Get network stats from host
            net_stats = get_host_network_stats()
            current_time = time.time()
            time_delta = current_time - prev_network_counters['timestamp']

            # Calculate rates in MB/s
            if time_delta > 0:
                rx_rate = (net_stats['bytes_recv'] - prev_network_counters['bytes_recv']) / time_delta / (1024 ** 2)
                tx_rate = (net_stats['bytes_sent'] - prev_network_counters['bytes_sent']) / time_delta / (1024 ** 2)
                total_rate = rx_rate + tx_rate
            else:
                rx_rate = tx_rate = total_rate = 0

            # Update previous counters
            prev_network_counters = {
                'bytes_sent': net_stats['bytes_sent'],
                'bytes_recv': net_stats['bytes_recv'],
                'timestamp': current_time
            }

            with history_lock:
                stats_history['timestamps'].append(timestamp)
                stats_history['cpu'].append(round(cpu_percent, 2))
                stats_history['memory'].append(round(memory_percent, 2))
                stats_history['swap'].append(round(swap_percent, 2))
                stats_history['disk'].append(round(disk_percent, 2))
                stats_history['network_rx'].append(round(rx_rate, 2))
                stats_history['network_tx'].append(round(tx_rate, 2))
                stats_history['network_total'].append(round(total_rate, 2))

            logger.debug(f"Stats history collected: CPU={cpu_percent}%, MEM={memory_percent}%, SWAP={swap_percent}%, DISK={disk_percent}%, NET_RX={rx_rate:.2f}MB/s, NET_TX={tx_rate:.2f}MB/s")
        except Exception as e:
            logger.error(f"Error collecting stats history: {e}")

        time.sleep(5)

# Start background stats collection threads
stats_thread = threading.Thread(target=collect_stats_history, daemon=True)
stats_thread.start()
logger.info("Started background stats collection thread")

docker_thread = threading.Thread(target=collect_docker_stats, daemon=True)
docker_thread.start()
logger.info("Started background Docker stats collection thread")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'pics'), 'favicon.ico', mimetype='image/x-icon')

@app.route('/')
def main_page():
    logger.info('Rendering main page')
    return render_template('index.html', services=services)

@app.route('/api/services')
def get_services():
    return jsonify(services)

# Load CTF configuration
def load_ctf_config():
    config_path = os.path.join(os.path.dirname(__file__), 'ctf_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"CTF config file not found: {config_path}")
        return {"categories": {}}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing CTF config: {e}")
        return {"categories": {}}

def load_markdown_content(relative_path):
    """Load and convert markdown content to HTML"""
    if not relative_path:
        return ""
    
    # Construct full path relative to the CybICS root directory
    # In container, app.py is at /CybICS/app.py, so we use the current directory as base
    base_path = os.path.dirname(__file__)  # This is /CybICS
    full_path = os.path.join(base_path, relative_path)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            
            # Preprocess to add markdown="1" attribute to HTML tags that should process markdown
            import re
            markdown_content = re.sub(r'<details>', '<details markdown="1">', markdown_content)
            markdown_content = re.sub(r'<summary>', '<summary markdown="1">', markdown_content)
            markdown_content = re.sub(r'<div([^>]*)>', r'<div\1 markdown="1">', markdown_content)
            
            # Convert markdown to HTML with extensions for better formatting
            html = markdown.markdown(markdown_content, extensions=[
                'fenced_code', 
                'codehilite', 
                'tables', 
                'nl2br', 
                'extra',
                'md_in_html'
            ])
            return html
    except FileNotFoundError:
        logger.warning(f"Training content file not found: {full_path}")
        return f"<p><em>Training content not available at: {relative_path}</em></p>"
    except Exception as e:
        logger.error(f"Error loading markdown content from {full_path}: {e}")
        return f"<p><em>Error loading training content: {str(e)}</em></p>"

# Load CTF configuration at startup
ctf_config = load_ctf_config()
ctf_challenges = ctf_config.get('categories', {})

def load_progress():
    """Load CTF progress from file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load progress file: {e}")
    
    return {'solved_challenges': [], 'total_points': 0}

def save_progress(progress):
    """Save CTF progress to file"""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)
        logger.info(f"Progress saved: {len(progress['solved_challenges'])} challenges, {progress['total_points']} points")
    except Exception as e:
        logger.error(f"Failed to save progress: {e}")

def get_current_progress():
    """Get current progress from session or load from file"""
    if 'solved_challenges' not in session:
        progress = load_progress()
        session['solved_challenges'] = progress['solved_challenges']
        session['total_points'] = progress['total_points']
    
    return {
        'solved_challenges': session['solved_challenges'],
        'total_points': session['total_points']
    }

def initialize_session():
    """Initialize session with persistent data"""
    progress = load_progress()
    session['solved_challenges'] = progress['solved_challenges']
    session['total_points'] = progress['total_points']

@app.route('/ctf')
def ctf_page():
    initialize_session()
    logger.info('Rendering CTF page')
    return render_template('ctf.html', 
                         config=ctf_config,
                         challenges=ctf_challenges, 
                         solved=session['solved_challenges'],
                         total_points=session['total_points'])

@app.route('/ctf/challenge/<challenge_id>')
def challenge_detail(challenge_id):
    initialize_session()
    challenge = None
    category = None
    
    for cat_data in ctf_challenges.values():
        for chall in cat_data['challenges']:
            if chall['id'] == challenge_id:
                challenge = chall
                category = cat_data
                break
        if challenge:
            break
    
    if not challenge:
        return "Challenge not found", 404
    
    # Load training content if available
    training_content = ""
    if 'training_content' in challenge:
        training_content = load_markdown_content(challenge['training_content'])
    
    return render_template('challenge.html', 
                         challenge=challenge, 
                         category=category,
                         training_content=training_content,
                         solved=challenge_id in session['solved_challenges'])

@app.route('/ctf/submit', methods=['POST'])
def submit_flag():
    initialize_session()
    data = request.get_json()
    challenge_id = data.get('challenge_id')
    submitted_flag = data.get('flag', '').strip()
    
    if challenge_id in session['solved_challenges']:
        return jsonify({'success': False, 'message': 'Challenge already solved!'})
    
    challenge = None
    for cat_data in ctf_challenges.values():
        for chall in cat_data['challenges']:
            if chall['id'] == challenge_id:
                challenge = chall
                break
        if challenge:
            break
    
    if not challenge:
        return jsonify({'success': False, 'message': 'Challenge not found'})
    
    if submitted_flag == challenge['flag']:
        session['solved_challenges'].append(challenge_id)
        session['total_points'] += challenge['points']
        session.modified = True
        
        # Save progress to file
        progress = {
            'solved_challenges': session['solved_challenges'],
            'total_points': session['total_points']
        }
        save_progress(progress)
        
        return jsonify({'success': True, 'message': f'Correct! You earned {challenge["points"]} points!'})
    else:
        return jsonify({'success': False, 'message': 'Incorrect flag. Try again!'})

@app.route('/ctf/progress')
def ctf_progress():
    initialize_session()
    total_challenges = sum(len(cat['challenges']) for cat in ctf_challenges.values())
    solved_count = len(session['solved_challenges'])
    max_points = sum(chall['points'] for cat in ctf_challenges.values() for chall in cat['challenges'])
    
    return jsonify({
        'solved_challenges': solved_count,
        'total_challenges': total_challenges,
        'total_points': session['total_points'],
        'max_points': max_points,
        'progress_percentage': (solved_count / total_challenges * 100) if total_challenges > 0 else 0
    })

@app.route('/ctf/reset', methods=['POST'])
def reset_progress():
    """Reset CTF progress"""
    try:
        # Clear session
        session['solved_challenges'] = []
        session['total_points'] = 0
        session.modified = True
        
        # Save empty progress to file
        progress = {
            'solved_challenges': [],
            'total_points': 0
        }
        save_progress(progress)
        
        logger.info("CTF progress has been reset")
        return jsonify({'success': True, 'message': 'Progress has been reset successfully!'})
    except Exception as e:
        logger.error(f"Failed to reset progress: {e}")
        return jsonify({'success': False, 'message': 'Failed to reset progress'})

@app.route('/training/<path:filename>')
def serve_training_file(filename):
    """Serve training files including images"""
    training_dir = os.path.join(os.path.dirname(__file__), 'training')
    return send_from_directory(training_dir, filename)

@app.route('/ctf/challenge/<challenge_id>/<path:filename>')
def serve_challenge_asset(challenge_id, filename):
    """Serve challenge assets like images"""
    training_dir = os.path.join(os.path.dirname(__file__), 'training', challenge_id)
    return send_from_directory(training_dir, filename)

@app.route('/ctf/challenge/doc/<path:filename>')
def serve_challenge_doc_asset(filename):
    """Serve challenge doc assets like images from doc/ folder"""
    # Check the referer header to determine which challenge we're in
    referer = request.headers.get('Referer', '')
    if '/ctf/challenge/' in referer:
        challenge_id = referer.split('/ctf/challenge/')[-1].split('/')[0].split('?')[0]
        training_dir = os.path.join(os.path.dirname(__file__), 'training', challenge_id, 'doc')
        try:
            return send_from_directory(training_dir, filename)
        except:
            pass
    
    # Fallback: try to find the file in any training directory's doc folder
    training_base = os.path.join(os.path.dirname(__file__), 'training')
    for challenge_dir in os.listdir(training_base):
        doc_path = os.path.join(training_base, challenge_dir, 'doc')
        if os.path.isdir(doc_path):
            try:
                return send_from_directory(doc_path, filename)
            except:
                continue
    
    return "File not found", 404

@app.route('/stats')
def stats_page():
    logger.info('Rendering stats page')
    return render_template('stats.html')

@app.route('/network')
def network_page():
    logger.info('Rendering network analyzer page')
    return render_template('sharky.html')

@app.route('/api/stats/history')
def get_stats_history():
    """Get historical stats data for the past hour"""
    try:
        with history_lock:
            return jsonify({
                'timestamps': list(stats_history['timestamps']),
                'cpu': list(stats_history['cpu']),
                'memory': list(stats_history['memory']),
                'swap': list(stats_history['swap']),
                'disk': list(stats_history['disk']),
                'network_rx': list(stats_history['network_rx']),
                'network_tx': list(stats_history['network_tx']),
                'network_total': list(stats_history['network_total'])
            })
    except Exception as e:
        logger.error(f"Error getting stats history: {e}")
        return jsonify({'error': str(e)}), 500

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

        return jsonify(interfaces_list)
    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
        return jsonify({'error': str(e)}), 500

def parse_modbus_tcp(payload):
    """Parse Modbus TCP protocol"""
    try:
        if len(payload) < 8:
            return None

        transaction_id = int.from_bytes(payload[0:2], 'big')
        protocol_id = int.from_bytes(payload[2:4], 'big')
        length = int.from_bytes(payload[4:6], 'big')
        unit_id = payload[6]
        function_code = payload[7]

        function_names = {
            1: "Read Coils",
            2: "Read Discrete Inputs",
            3: "Read Holding Registers",
            4: "Read Input Registers",
            5: "Write Single Coil",
            6: "Write Single Register",
            15: "Write Multiple Coils",
            16: "Write Multiple Registers",
            23: "Read/Write Multiple Registers"
        }

        return {
            'transaction_id': transaction_id,
            'protocol_id': protocol_id,
            'length': length,
            'unit_id': unit_id,
            'function_code': function_code,
            'function_name': function_names.get(function_code, f"Unknown (0x{function_code:02x})")
        }
    except Exception as e:
        logger.debug(f"Error parsing Modbus: {e}")
        return None

def parse_s7comm(payload):
    """Parse S7comm protocol"""
    try:
        if len(payload) < 10:
            return None

        # TPKT header
        tpkt_version = payload[0]
        tpkt_reserved = payload[1]
        tpkt_length = int.from_bytes(payload[2:4], 'big')

        # COTP header
        cotp_length = payload[4]
        cotp_pdu_type = payload[5]

        if len(payload) < 12:
            return {'protocol': 'S7comm', 'type': 'COTP'}

        # S7comm header
        protocol_id = payload[7]
        message_type = payload[8]

        message_types = {
            1: "Job Request",
            2: "Ack",
            3: "Ack-Data",
            7: "Userdata"
        }

        return {
            'tpkt_length': tpkt_length,
            'protocol_id': protocol_id,
            'message_type': message_type,
            'message_type_name': message_types.get(message_type, f"Unknown (0x{message_type:02x})")
        }
    except Exception as e:
        logger.debug(f"Error parsing S7comm: {e}")
        return None

def parse_opcua(payload):
    """Parse OPC-UA protocol"""
    try:
        if len(payload) < 8:
            return None

        # OPC-UA header
        message_type = payload[0:3].decode('ascii', errors='ignore')
        chunk_type = chr(payload[3]) if payload[3] < 128 else '?'
        message_size = int.from_bytes(payload[4:8], 'little')

        message_types_map = {
            'HEL': 'Hello',
            'ACK': 'Acknowledge',
            'ERR': 'Error',
            'RHE': 'Reverse Hello',
            'OPN': 'Open Secure Channel',
            'CLO': 'Close Secure Channel',
            'MSG': 'Message'
        }

        chunk_types = {
            'F': 'Final',
            'C': 'Continue',
            'A': 'Abort'
        }

        return {
            'message_type': message_type,
            'message_type_name': message_types_map.get(message_type, message_type),
            'chunk_type': chunk_type,
            'chunk_type_name': chunk_types.get(chunk_type, 'Unknown'),
            'message_size': message_size
        }
    except Exception as e:
        logger.debug(f"Error parsing OPC-UA: {e}")
        return None

def parse_enip(payload):
    """Parse EtherNet/IP protocol"""
    try:
        if len(payload) < 24:
            return None

        command = int.from_bytes(payload[0:2], 'little')
        length = int.from_bytes(payload[2:4], 'little')
        session_handle = int.from_bytes(payload[4:8], 'little')
        status = int.from_bytes(payload[8:12], 'little')

        commands = {
            0x0001: "NOP",
            0x0004: "ListServices",
            0x0063: "ListIdentity",
            0x0064: "ListInterfaces",
            0x0065: "RegisterSession",
            0x0066: "UnregisterSession",
            0x006F: "SendRRData",
            0x0070: "SendUnitData"
        }

        return {
            'command': command,
            'command_name': commands.get(command, f"Unknown (0x{command:04x})"),
            'length': length,
            'session_handle': session_handle,
            'status': status
        }
    except Exception as e:
        logger.debug(f"Error parsing EtherNet/IP: {e}")
        return None

def capture_packets(interface='all', filter_str=''):
    """Background thread to capture network packets"""
    global network_capture_active, network_capture_packets

    try:
        # Try to import scapy
        try:
            from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP, DNS, Raw
            has_scapy = True
        except ImportError:
            logger.warning("Scapy not available, using simulated packet capture")
            has_scapy = False

        packet_id = 1

        if has_scapy:
            def packet_handler(packet):
                global network_capture_active
                nonlocal packet_id

                if not network_capture_active:
                    return True  # Stop sniffing

                try:
                    packet_data = {
                        'id': packet_id,
                        'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                        'timestamp': datetime.now().isoformat(),
                        'length': len(packet),
                        'layers': {},
                        'raw_packet': bytes(packet)  # Store raw packet for PCAP export
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

                        # Determine protocol
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

                        elif packet.haslayer(ICMP):
                            packet_data['protocol'] = 'ICMP'
                            packet_data['info'] = f"Type {packet[ICMP].type}"
                        else:
                            packet_data['protocol'] = 'IP'
                            packet_data['info'] = f"Protocol {ip_layer.proto}"

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

                    with network_capture_lock:
                        network_capture_packets.append(packet_data)

                    packet_id += 1

                except Exception as e:
                    logger.error(f"Error processing packet: {e}")

            # Start sniffing
            iface = None if interface == 'all' else interface
            sniff(prn=packet_handler, store=False, iface=iface, stop_filter=lambda x: not network_capture_active)
        else:
            # Simulated packet capture for demonstration
            import random
            protocols = ['TCP', 'UDP', 'ICMP', 'DNS', 'HTTP', 'ARP']

            while network_capture_active:
                # Generate simulated packet
                protocol = random.choice(protocols)
                packet_data = {
                    'id': packet_id,
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

                with network_capture_lock:
                    network_capture_packets.append(packet_data)

                packet_id += 1
                time.sleep(random.uniform(0.1, 1.0))  # Random interval between packets

    except Exception as e:
        logger.error(f"Error in packet capture: {e}")

@app.route('/api/network/start', methods=['POST'])
def start_network_capture():
    """Start network packet capture"""
    global network_capture_active, network_capture_thread

    try:
        data = request.get_json() or {}
        interface = data.get('interface', 'all')
        filter_str = data.get('filter', '')

        if network_capture_active:
            return jsonify({'error': 'Capture already active'}), 400

        # Clear previous packets
        with network_capture_lock:
            network_capture_packets.clear()

        network_capture_active = True

        # Start capture thread
        network_capture_thread = threading.Thread(
            target=capture_packets,
            args=(interface, filter_str),
            daemon=True
        )
        network_capture_thread.start()

        logger.info(f"Started network capture on interface: {interface}")
        return jsonify({'success': True, 'message': 'Capture started'})

    except Exception as e:
        logger.error(f"Error starting network capture: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/stop', methods=['POST'])
def stop_network_capture():
    """Stop network packet capture"""
    global network_capture_active

    try:
        network_capture_active = False
        logger.info("Stopped network capture")
        return jsonify({'success': True, 'message': 'Capture stopped'})
    except Exception as e:
        logger.error(f"Error stopping network capture: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/packets')
def get_network_packets():
    """Get captured network packets"""
    try:
        with network_capture_lock:
            packets = list(network_capture_packets)

        # Remove raw_packet data for JSON serialization (it's binary)
        packets_json = []
        for packet in packets:
            packet_copy = packet.copy()
            if 'raw_packet' in packet_copy:
                del packet_copy['raw_packet']  # Remove binary data for JSON
            packets_json.append(packet_copy)

        return jsonify({'packets': packets_json})
    except Exception as e:
        logger.error(f"Error getting network packets: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/clear', methods=['POST'])
def clear_network_capture():
    """Clear captured packets"""
    try:
        with network_capture_lock:
            network_capture_packets.clear()
        logger.info("Cleared network capture packets")
        return jsonify({'success': True, 'message': 'Packets cleared'})
    except Exception as e:
        logger.error(f"Error clearing network packets: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/export')
def export_network_capture():
    """Export captured packets as PCAP file"""
    try:
        from flask import send_file
        import io
        import struct

        with network_capture_lock:
            packets = list(network_capture_packets)

        # Create PCAP file in memory
        pcap_buffer = io.BytesIO()

        # PCAP Global Header
        # Magic number (0xa1b2c3d4 for standard pcap)
        pcap_buffer.write(struct.pack('I', 0xa1b2c3d4))
        # Version major, minor
        pcap_buffer.write(struct.pack('HH', 2, 4))
        # Timezone offset (0)
        pcap_buffer.write(struct.pack('I', 0))
        # Timestamp accuracy (0)
        pcap_buffer.write(struct.pack('I', 0))
        # Snapshot length (65535)
        pcap_buffer.write(struct.pack('I', 65535))
        # Data link type (1 = Ethernet)
        pcap_buffer.write(struct.pack('I', 1))

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

            # Use raw packet data if available, otherwise reconstruct
            if 'raw_packet' in packet:
                packet_data = packet['raw_packet']
            else:
                packet_data = _reconstruct_packet_data(packet)

            packet_length = len(packet_data)

            # PCAP Packet Header
            pcap_buffer.write(struct.pack('I', ts_sec))  # Timestamp seconds
            pcap_buffer.write(struct.pack('I', ts_usec))  # Timestamp microseconds
            pcap_buffer.write(struct.pack('I', packet_length))  # Captured length
            pcap_buffer.write(struct.pack('I', packet_length))  # Original length

            # Packet data
            pcap_buffer.write(packet_data)

        pcap_buffer.seek(0)

        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap"

        return send_file(
            pcap_buffer,
            mimetype='application/vnd.tcpdump.pcap',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error exporting network capture: {e}")
        return jsonify({'error': str(e)}), 500

def _reconstruct_packet_data(packet):
    """Reconstruct packet data from parsed information"""
    import struct

    # Build a minimal Ethernet frame
    packet_bytes = bytearray()

    # Ethernet header (14 bytes)
    if 'layers' in packet and 'ethernet' in packet['layers']:
        eth = packet['layers']['ethernet']
        # Destination MAC (use dummy if not available)
        dst_mac = bytes.fromhex(eth.get('dst', 'ff:ff:ff:ff:ff:ff').replace(':', ''))
        src_mac = bytes.fromhex(eth.get('src', '00:00:00:00:00:00').replace(':', ''))
        packet_bytes.extend(dst_mac)
        packet_bytes.extend(src_mac)
        packet_bytes.extend(struct.pack('!H', 0x0800))  # IPv4
    else:
        # Dummy Ethernet header
        packet_bytes.extend(b'\xff\xff\xff\xff\xff\xff')  # Dst MAC
        packet_bytes.extend(b'\x00\x00\x00\x00\x00\x00')  # Src MAC
        packet_bytes.extend(struct.pack('!H', 0x0800))  # IPv4

    # IPv4 header (20 bytes minimum)
    if 'layers' in packet and 'ip' in packet['layers']:
        ip = packet['layers']['ip']
        src_ip = packet.get('source', '0.0.0.0')
        dst_ip = packet.get('destination', '0.0.0.0')

        # IP header
        packet_bytes.append(0x45)  # Version 4, IHL 5
        packet_bytes.append(0x00)  # DSCP/ECN
        total_length = max(packet.get('length', 60), 60)
        packet_bytes.extend(struct.pack('!H', total_length))  # Total length
        packet_bytes.extend(struct.pack('!H', packet.get('id', 0)))  # Identification
        packet_bytes.extend(struct.pack('!H', 0x4000))  # Flags + Fragment offset
        packet_bytes.append(ip.get('ttl', 64))  # TTL

        # Protocol
        proto = 6  # TCP default
        if packet.get('protocol') == 'UDP':
            proto = 17
        elif packet.get('protocol') == 'ICMP':
            proto = 1
        packet_bytes.append(proto)

        packet_bytes.extend(struct.pack('!H', 0x0000))  # Checksum (dummy)

        # Source and Destination IP
        for octet in src_ip.split('.'):
            packet_bytes.append(int(octet))
        for octet in dst_ip.split('.'):
            packet_bytes.append(int(octet))
    else:
        # Dummy IP header
        packet_bytes.extend(b'\x45\x00\x00\x3c\x00\x00\x40\x00\x40\x06\x00\x00')
        packet_bytes.extend(b'\x00\x00\x00\x00\x00\x00\x00\x00')

    # TCP/UDP header (simplified)
    if 'layers' in packet and 'tcp' in packet['layers']:
        tcp = packet['layers']['tcp']
        packet_bytes.extend(struct.pack('!H', tcp.get('sport', 0)))
        packet_bytes.extend(struct.pack('!H', tcp.get('dport', 0)))
        packet_bytes.extend(struct.pack('!I', tcp.get('seq', 0)))
        packet_bytes.extend(struct.pack('!I', 0))  # ACK
        packet_bytes.extend(struct.pack('!H', 0x5000))  # Data offset + flags
        packet_bytes.extend(struct.pack('!H', 8192))  # Window
        packet_bytes.extend(struct.pack('!H', 0))  # Checksum
        packet_bytes.extend(struct.pack('!H', 0))  # Urgent pointer
    elif 'layers' in packet and 'udp' in packet['layers']:
        udp = packet['layers']['udp']
        packet_bytes.extend(struct.pack('!H', udp.get('sport', 0)))
        packet_bytes.extend(struct.pack('!H', udp.get('dport', 0)))
        packet_bytes.extend(struct.pack('!H', udp.get('len', 8)))
        packet_bytes.extend(struct.pack('!H', 0))  # Checksum

    # Pad to minimum size
    while len(packet_bytes) < 60:
        packet_bytes.append(0)

    return bytes(packet_bytes)

@app.route('/api/stats')
def get_stats():
    """Get current system and Docker container statistics"""
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        # Get memory usage
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 ** 3)  # GB
        memory_used = memory.used / (1024 ** 3)  # GB
        memory_percent = memory.percent

        # Get swap usage
        swap = psutil.swap_memory()
        swap_total = swap.total / (1024 ** 3)  # GB
        swap_used = swap.used / (1024 ** 3)  # GB
        swap_percent = swap.percent

        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024 ** 3)  # GB
        disk_used = disk.used / (1024 ** 3)  # GB
        disk_percent = disk.percent

        # Get system uptime
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)

        # Get network usage from host (via psutil)
        net_stats = get_host_network_stats()

        # Get packet counts from psutil
        net_io = psutil.net_io_counters()

        # Get Docker container stats from cache (updated by background thread)
        with docker_cache_lock:
            containers_info = docker_container_cache.copy()

        return jsonify({
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
            'containers': containers_info
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info('Starting Flask application')
    app.run(
        host='0.0.0.0',
        port=80,
        debug=True
    ) 