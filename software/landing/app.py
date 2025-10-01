from flask import Flask, render_template, jsonify, request, session, send_from_directory
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

if __name__ == '__main__':
    logger.info('Starting Flask application')
    app.run(
        host='0.0.0.0',
        port=8081,
        debug=True
    ) 