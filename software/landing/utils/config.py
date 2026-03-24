"""
Configuration module for CybICS application
"""
import os

# Application Configuration
SECRET_KEY = 'cybics_ctf_secret_key_change_in_production'
HOST = '0.0.0.0'
PORT = 80
DEBUG = False

# Data Directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if os.environ.get('CYBICS_REPO_ROOT'):
    REPO_ROOT = os.environ['CYBICS_REPO_ROOT']
elif os.path.basename(BASE_DIR) == 'landing' and os.path.basename(os.path.dirname(BASE_DIR)) == 'software':
    REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
else:
    REPO_ROOT = BASE_DIR
DATA_DIR = os.path.join(BASE_DIR, 'data')
TRAINING_DIR = os.path.join(BASE_DIR, 'training')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
CHALLENGE_SCRIPTS_DIR = os.path.join(SCRIPTS_DIR, 'challenges')
PROGRESS_FILE = os.path.join(DATA_DIR, 'ctf_progress.json')
CTF_CONFIG_FILE = os.path.join(BASE_DIR, 'ctf_config.json')
ACTIVE_CHALLENGE_FILE = os.path.join(DATA_DIR, 'active_challenge.json')
COMPOSE_DIR = os.environ.get('CYBICS_COMPOSE_DIR', os.path.join(REPO_ROOT, '.devcontainer', 'virtual'))
COMPOSE_FILE = os.environ.get('CYBICS_COMPOSE_FILE', os.path.join(COMPOSE_DIR, 'docker-compose.yml'))

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHALLENGE_SCRIPTS_DIR, exist_ok=True)

# Service Configurations
SERVICES = {
    'openplc': {
        'name': 'OpenPLC',
        'port': 8080,
        'virtual_only': False,
        'icon': '⚙️',
        'description': 'PLC runtime environment. Program and control industrial automation processes using IEC 61131-3 standards.'
    },
    'fuxa': {
        'name': 'FUXA',
        'port': 1881,
        'virtual_only': False,
        'icon': '📊',
        'description': 'Human-Machine Interface (HMI). Monitor and control your industrial processes with a visual dashboard.'
    },
    'vhardware': {
        'name': 'Virtual Hardware',
        'port': 8090,
        'virtual_only': True,
        'icon': '🔌',
        'description': 'Simulated hardware interface. Test PLC programs without physical hardware in the virtual environment.'
    },
    'engineeringws': {
        'name': 'EngWS',
        'port': 6080,
        'virtual_only': True,
        'path': '/vnc.html?autoconnect=true&resize=scale',
        'icon': '💻',
        'description': 'Engineering workstation - Full desktop environment with OpenPLC Editor. Develop and modify PLC programs using Beremiz.'
    },
    'attackmachine': {
        'name': 'Attack Box',
        'port': 6081,
        'virtual_only': True,
        'path': '/vnc.html?autoconnect=true&resize=scale',
        'icon': '🎯',
        'description': 'Kali Linux-based security testing environment. Perform penetration testing and vulnerability assessments on ICS/SCADA systems.'
    },
    'ids': {
        'name': 'IDS',
        'port': 8443,
        'virtual_only': False,
        'icon': '🛡️',
        'description': 'Intrusion Detection System. Monitor network traffic for attacks against industrial protocols.'
    }
}

# Statistics Configuration
HISTORY_MAX_LENGTH = 720  # 1 hour of data at 5-second intervals
STATS_COLLECTION_INTERVAL = 15  # seconds
DOCKER_STATS_INTERVAL = 30  # seconds

# Network Capture Configuration (optimized for Raspberry Pi)
MAX_PACKETS_IN_MEMORY = 1000  # Maximum number of packets to keep in memory (~2MB with full raw bytes)
