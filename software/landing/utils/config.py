"""
Configuration module for CybICS application
"""
import os

# Application Configuration
SECRET_KEY = 'cybics_ctf_secret_key_change_in_production'
HOST = '0.0.0.0'
PORT = 80
DEBUG = True

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

# Statistics Configuration
HISTORY_MAX_LENGTH = 720  # 1 hour of data at 5-second intervals
STATS_COLLECTION_INTERVAL = 5  # seconds
DOCKER_STATS_INTERVAL = 10  # seconds

# Network Capture Configuration (optimized for Raspberry Pi)
MAX_PACKETS_IN_MEMORY = 1000  # Maximum number of packets to keep in memory (~2MB with full raw bytes)
