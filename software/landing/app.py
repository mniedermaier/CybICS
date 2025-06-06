from flask import Flask, render_template, jsonify
import logging
import sys
import json

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

# Service configurations
services = {
    'openplc': {
        'name': 'OpenPLC',
        'url': 'http://localhost:8080',
        'port': 8080
    },
    'fuxa': {
        'name': 'FUXA',
        'url': 'http://localhost:1881',
        'port': 1881
    },
    'vhardware': {
        'name': 'Virtual Hardware IO',
        'url': 'http://localhost:8090',
        'port': 8090
    }
}

logger.info('Starting application with services: %s', list(services.keys()))

app = Flask(__name__)

@app.route('/')
def main_page():
    logger.info('Rendering main page')
    return render_template('index.html', services=services)

@app.route('/api/services')
def get_services():
    return jsonify(services)

if __name__ == '__main__':
    logger.info('Starting Flask application')
    app.run(
        host='0.0.0.0',
        port=8081,
        debug=True
    ) 