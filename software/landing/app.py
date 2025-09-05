from flask import Flask, render_template, jsonify, request, session
import logging
import sys
import json
import os
import markdown

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
app.secret_key = 'cybics_ctf_secret_key_change_in_production'

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
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up to /CybICS
    full_path = os.path.join(base_path, relative_path)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            # Convert markdown to HTML with extensions for better formatting
            html = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables', 'nl2br'])
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

def initialize_session():
    if 'solved_challenges' not in session:
        session['solved_challenges'] = []
    if 'total_points' not in session:
        session['total_points'] = 0

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

if __name__ == '__main__':
    logger.info('Starting Flask application')
    app.run(
        host='0.0.0.0',
        port=8081,
        debug=True
    ) 