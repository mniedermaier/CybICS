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
DATA_DIR = os.path.join(BASE_DIR, 'data')
TRAINING_DIR = os.path.join(BASE_DIR, 'training')
PROGRESS_FILE = os.path.join(DATA_DIR, 'ctf_progress.json')
CTF_CONFIG_FILE = os.path.join(BASE_DIR, 'ctf_config.json')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

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

# Systems Access Information (for the home page "Systems access" info box)
# Intentionally-insecure default lab credentials - not for production use.
ACCESS_INFO = [
    {
        'system': 'Landing Page',
        'url': 'http://localhost:80',
        'ip': 'host network',
        'ports': '80',
        'username': None,
        'password': None,
        'note': 'This dashboard',
        'virtual_only': False,
    },
    {
        'system': 'OpenPLC',
        'url': 'http://localhost:8080',
        'ip': '172.18.0.3',
        'ports': '8080 (web), 502 (Modbus), 102 (S7)',
        'username': 'openplc',
        'password': 'openplc',
        'note': 'PLC runtime & programming',
        'virtual_only': False,
    },
    {
        'system': 'FUXA (viewer)',
        'url': 'http://localhost:1881',
        'ip': '172.18.0.4',
        'ports': '1881',
        'username': 'viewer',
        'password': 'viewer',
        'note': 'HMI - read-only role',
        'virtual_only': False,
    },
    {
        'system': 'FUXA (operator)',
        'url': 'http://localhost:1881',
        'ip': '172.18.0.4',
        'ports': '1881',
        'username': 'operator',
        'password': 'operator',
        'note': 'HMI - IEC 62443 operator role',
        'virtual_only': False,
    },
    {
        'system': 'FUXA (admin)',
        'url': 'http://localhost:1881',
        'ip': '172.18.0.4',
        'ports': '1881',
        'username': 'admin',
        'password': '123456',
        'note': 'HMI - full configuration access',
        'virtual_only': False,
    },
    {
        'system': 'OPC-UA Server',
        'url': 'opc.tcp://localhost:4840',
        'ip': '172.18.0.5',
        'ports': '4840',
        'username': 'user1',
        'password': 'test',
        'note': 'Industrial protocol endpoint',
        'virtual_only': False,
    },
    {
        'system': 'IDS',
        'url': 'https://localhost:8443',
        'ip': 'host network',
        'ports': '8443',
        'username': None,
        'password': None,
        'note': 'Intrusion detection dashboard',
        'virtual_only': False,
    },
    {
        'system': 'Virtual Hardware',
        'url': 'http://localhost:8090',
        'ip': '172.18.0.2',
        'ports': '8090',
        'username': None,
        'password': None,
        'note': '3D process visualization',
        'virtual_only': True,
    },
    {
        'system': 'Engineering Workstation',
        'url': 'http://localhost:6080/vnc.html',
        'ip': '172.18.0.10',
        'ports': '6080 (noVNC), 5901 (VNC)',
        'username': None,
        'password': None,
        'note': 'PLC development desktop',
        'virtual_only': True,
    },
    {
        'system': 'Attack Box',
        'url': 'http://localhost:6081/vnc.html',
        'ip': '172.18.0.100',
        'ports': '6081 (noVNC), 5902 (VNC)',
        'username': None,
        'password': 'cybics',
        'note': 'Kali-based security testing box',
        'virtual_only': True,
    },
    {
        'system': 'Physical Device (hardware mode)',
        'url': None,
        'ip': '10.0.0.1',
        'ports': '3333 (SWD), Wi-Fi AP: cybics-XXXXXX',
        'username': None,
        'password': '1234567890 (Wi-Fi)',
        'note': 'Raspberry Pi + STM32 lab hardware',
        'virtual_only': False,
    },
]

# Network Topology - ISA-95 / Purdue Model mapping (for the home page topology diagram)
PURDUE_LEVELS = [
    {
        'level': 'Level 0/1 - Process & Control',
        'zone': 'ot',
        'systems': [
            {'name': 'Physical Process / HWIO', 'ip': '172.18.0.2'},
            {'name': 'STM32 Hardware', 'ip': '172.18.0.7'},
            {'name': 'OpenPLC', 'ip': '172.18.0.3'},
        ],
    },
    {
        'level': 'Level 2 - Supervisory (HMI/SCADA)',
        'zone': 'ot',
        'systems': [
            {'name': 'FUXA HMI', 'ip': '172.18.0.4'},
            {'name': 'OPC-UA Server', 'ip': '172.18.0.5'},
            {'name': 'S7 Communication', 'ip': '172.18.0.6'},
        ],
    },
    {
        'level': 'Level 3 / DMZ - Operations & Monitoring',
        'zone': 'dmz',
        'systems': [
            {'name': 'Landing Page', 'ip': 'host'},
            {'name': 'IDS', 'ip': 'host'},
            {'name': 'Engineering Workstation', 'ip': '172.18.0.10'},
        ],
    },
    {
        'level': 'External - Enterprise / Attacker',
        'zone': 'external',
        'systems': [
            {'name': 'Attack Box', 'ip': '172.18.0.100'},
        ],
    },
]

# Statistics Configuration
HISTORY_MAX_LENGTH = 720  # 1 hour of data at 5-second intervals
STATS_COLLECTION_INTERVAL = 15  # seconds
DOCKER_STATS_INTERVAL = 30  # seconds

# Network Capture Configuration (optimized for Raspberry Pi)
MAX_PACKETS_IN_MEMORY = 1000  # Maximum number of packets to keep in memory (~2MB with full raw bytes)
