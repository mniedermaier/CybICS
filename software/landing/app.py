"""
CybICS - Industrial Control Systems Training Platform
Main Flask Application (Refactored)
"""
from flask import Flask, render_template, jsonify, request, session, send_from_directory
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import configuration and utilities
from utils.config import *
from utils.logger import logger

# Import modules
from modules.stats_collector import StatsCollector
from modules.network_capture import NetworkCapture
from modules.ctf_manager import CTFManager
from modules.network_routes import register_network_routes

# Initialize Flask application
app = Flask(__name__)
app.secret_key = SECRET_KEY

logger.info('='*60)
logger.info('CybICS Application Starting')
logger.info(f'Services configured: {list(SERVICES.keys())}')
logger.info('='*60)

# Initialize modules
stats_collector = StatsCollector()
network_capture = NetworkCapture()
ctf_manager = CTFManager()

# Start background collection
stats_collector.start()

# ========== UTILITY FUNCTIONS ==========

def initialize_session():
    """Initialize session with persistent CTF data"""
    progress = ctf_manager.load_progress()
    session['solved_challenges'] = progress['solved_challenges']
    session['total_points'] = progress['total_points']
    logger.debug(f"Session initialized: {len(progress['solved_challenges'])} challenges solved")

def get_current_progress():
    """Get current progress from session or load from file"""
    if 'solved_challenges' not in session:
        initialize_session()

    return {
        'solved_challenges': session['solved_challenges'],
        'total_points': session['total_points']
    }

# ========== MAIN ROUTES ==========

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(
        os.path.join(app.root_path, 'pics'),
        'favicon.ico',
        mimetype='image/x-icon'
    )

@app.route('/')
def main_page():
    """Main dashboard page"""
    logger.info('Rendering main dashboard')
    return render_template('index.html', services=SERVICES)

@app.route('/api/services')
def get_services():
    """Get service configuration"""
    return jsonify(SERVICES)

# ========== STATS ROUTES ==========

@app.route('/stats')
def stats_page():
    """System statistics page"""
    logger.info('Rendering stats page')
    return render_template('stats.html')

@app.route('/api/stats')
def get_stats():
    """Get current system and Docker container statistics"""
    try:
        stats = stats_collector.get_current_stats()
        logger.debug("Stats retrieved successfully")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/history')
def get_stats_history():
    """Get historical stats data"""
    try:
        history = stats_collector.get_history()
        logger.debug(f"Retrieved {len(history['timestamps'])} historical data points")
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error getting stats history: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ========== NETWORK ANALYZER ROUTES ==========

@app.route('/network')
def network_page():
    """Network analyzer (Sharky) page"""
    logger.info('Rendering network analyzer page')
    return render_template('sharky.html')

# Register network-specific routes
register_network_routes(app, network_capture)

# ========== WEBSHELL ROUTES ==========

@app.route('/webshell')
def webshell_page():
    """Webshell page for running attack tools"""
    logger.info('Rendering webshell page')
    return render_template('webshell.html')

@app.route('/api/webshell/execute', methods=['POST'])
def execute_command():
    """Execute a shell command and return the output"""
    import subprocess
    data = request.get_json()
    command = data.get('command', '').strip()

    if not command:
        return jsonify({'success': False, 'output': 'No command provided'}), 400

    logger.info(f'Executing webshell command: {command}')

    try:
        # Execute the command without timeout
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.path.expanduser('~')
        )

        output = result.stdout
        if result.stderr:
            output += '\n' + result.stderr

        return jsonify({
            'success': True,
            'output': output,
            'exit_code': result.returncode
        })
    except Exception as e:
        logger.error(f'Error executing command: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'output': f'Error: {str(e)}'
        }), 500

# ========== CTF ROUTES ==========

@app.route('/ctf')
def ctf_page():
    """CTF main page"""
    initialize_session()
    logger.info('Rendering CTF page')
    return render_template('ctf.html',
                         config=ctf_manager.config,
                         challenges=ctf_manager.challenges,
                         solved=session['solved_challenges'],
                         total_points=session['total_points'])

@app.route('/ctf/challenge/<challenge_id>')
def challenge_detail(challenge_id):
    """CTF challenge detail page"""
    initialize_session()
    logger.info(f'Rendering challenge detail: {challenge_id}')

    challenge, category = ctf_manager.get_challenge(challenge_id)

    if not challenge:
        logger.warning(f'Challenge not found: {challenge_id}')
        return "Challenge not found", 404

    # Load training content if available
    training_content = ""
    if 'training_content' in challenge:
        training_content = ctf_manager.load_markdown_content(challenge['training_content'])

    return render_template('challenge.html',
                         challenge=challenge,
                         category=category,
                         training_content=training_content,
                         solved=challenge_id in session['solved_challenges'])

@app.route('/ctf/submit', methods=['POST'])
def submit_flag():
    """Submit a CTF flag for validation"""
    initialize_session()
    data = request.get_json()
    challenge_id = data.get('challenge_id')
    submitted_flag = data.get('flag', '').strip()

    logger.info(f'Flag submission for challenge: {challenge_id}')

    current_progress = get_current_progress()
    result = ctf_manager.submit_flag(challenge_id, submitted_flag, current_progress)

    if result['success']:
        session['solved_challenges'].append(challenge_id)
        session['total_points'] += result['points']
        session.modified = True

        # Save progress to file
        progress = {
            'solved_challenges': session['solved_challenges'],
            'total_points': session['total_points']
        }
        ctf_manager.save_progress(progress)

    return jsonify(result)

@app.route('/ctf/progress')
def ctf_progress():
    """Get CTF progress statistics"""
    initialize_session()
    current_progress = get_current_progress()
    stats = ctf_manager.get_progress_stats(current_progress)
    return jsonify(stats)

@app.route('/ctf/reset', methods=['POST'])
def reset_progress():
    """Reset CTF progress"""
    try:
        progress = ctf_manager.reset_progress()

        # Clear session
        session['solved_challenges'] = []
        session['total_points'] = 0
        session.modified = True

        logger.info("CTF progress reset")
        return jsonify({'success': True, 'message': 'Progress has been reset successfully!'})
    except Exception as e:
        logger.error(f"Failed to reset progress: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to reset progress'}), 500

# ========== TRAINING FILE ROUTES ==========

@app.route('/training/<path:filename>')
def serve_training_file(filename):
    """Serve training files including images"""
    return send_from_directory(TRAINING_DIR, filename)

@app.route('/ctf/challenge/<challenge_id>/<path:filename>')
def serve_challenge_asset(challenge_id, filename):
    """Serve challenge assets like images"""
    training_dir = os.path.join(TRAINING_DIR, challenge_id)
    return send_from_directory(training_dir, filename)

@app.route('/ctf/challenge/doc/<path:filename>')
def serve_challenge_doc_asset(filename):
    """Serve challenge doc assets like images from doc/ folder"""
    # Check the referer header to determine which challenge we're in
    referer = request.headers.get('Referer', '')
    if '/ctf/challenge/' in referer:
        challenge_id = referer.split('/ctf/challenge/')[-1].split('/')[0].split('?')[0]
        doc_path = os.path.join(TRAINING_DIR, challenge_id, 'doc')
        try:
            return send_from_directory(doc_path, filename)
        except:
            pass

    # Fallback: try to find the file in any training directory's doc folder
    for challenge_dir in os.listdir(TRAINING_DIR):
        doc_path = os.path.join(TRAINING_DIR, challenge_dir, 'doc')
        if os.path.isdir(doc_path):
            try:
                return send_from_directory(doc_path, filename)
            except:
                continue

    logger.warning(f'Doc asset not found: {filename}')
    return "File not found", 404

# ========== APPLICATION ENTRY POINT ==========

if __name__ == '__main__':
    logger.info('='*60)
    logger.info(f'Starting Flask application on {HOST}:{PORT}')
    logger.info(f'Debug mode: {DEBUG}')
    logger.info('='*60)

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )
