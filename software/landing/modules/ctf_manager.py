"""
CTF (Capture The Flag) management module
"""
import json
import os
import markdown
import re

from utils.logger import logger
from utils.config import PROGRESS_FILE, CTF_CONFIG_FILE, TRAINING_DIR

class CTFManager:
    """Manage CTF challenges and user progress"""

    def __init__(self):
        self.config = self._load_config()
        self.challenges = self.config.get('categories', {})
        logger.info(f"CTFManager initialized with {self._count_challenges()} challenges")

    def _load_config(self):
        """Load CTF configuration from file"""
        try:
            with open(CTF_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Loaded CTF config from {CTF_CONFIG_FILE}")
                return config
        except FileNotFoundError:
            logger.error(f"CTF config file not found: {CTF_CONFIG_FILE}")
            return {"categories": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing CTF config: {e}")
            return {"categories": {}}

    def _count_challenges(self):
        """Count total number of challenges"""
        return sum(len(cat['challenges']) for cat in self.challenges.values())

    def load_progress(self):
        """Load CTF progress from file"""
        try:
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    logger.info(f"Loaded progress: {len(progress.get('solved_challenges', []))} challenges solved")
                    return progress
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load progress file: {e}")

        return {'solved_challenges': [], 'total_points': 0}

    def save_progress(self, progress):
        """Save CTF progress to file"""
        try:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
            logger.info(f"Progress saved: {len(progress['solved_challenges'])} challenges, {progress['total_points']} points")
            return True
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
            return False

    def get_challenge(self, challenge_id):
        """Get a specific challenge by ID"""
        for cat_data in self.challenges.values():
            for chall in cat_data['challenges']:
                if chall['id'] == challenge_id:
                    return chall, cat_data
        return None, None

    def submit_flag(self, challenge_id, submitted_flag, current_progress):
        """
        Submit a flag for validation

        Returns:
            dict: Result with success status and message
        """
        if challenge_id in current_progress.get('solved_challenges', []):
            logger.info(f"Challenge {challenge_id} already solved")
            return {'success': False, 'message': 'Challenge already solved!'}

        challenge, _ = self.get_challenge(challenge_id)

        if not challenge:
            logger.warning(f"Challenge not found: {challenge_id}")
            return {'success': False, 'message': 'Challenge not found'}

        if submitted_flag.strip() == challenge['flag']:
            points = challenge['points']
            logger.info(f"Correct flag submitted for {challenge_id}, earned {points} points")
            return {
                'success': True,
                'message': f'Correct! You earned {points} points!',
                'points': points
            }
        else:
            logger.info(f"Incorrect flag submitted for {challenge_id}")
            return {'success': False, 'message': 'Incorrect flag. Try again!'}

    def reset_progress(self):
        """Reset all progress"""
        progress = {'solved_challenges': [], 'total_points': 0}
        self.save_progress(progress)
        logger.info("CTF progress has been reset")
        return progress

    def get_progress_stats(self, current_progress):
        """Get progress statistics"""
        total_challenges = self._count_challenges()
        solved_count = len(current_progress.get('solved_challenges', []))
        max_points = sum(chall['points'] for cat in self.challenges.values() for chall in cat['challenges'])

        return {
            'solved_challenges': solved_count,
            'total_challenges': total_challenges,
            'total_points': current_progress.get('total_points', 0),
            'max_points': max_points,
            'progress_percentage': (solved_count / total_challenges * 100) if total_challenges > 0 else 0
        }

    def load_markdown_content(self, relative_path):
        """Load and convert markdown content to HTML"""
        if not relative_path:
            return ""

        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

                # Preprocess to add markdown="1" attribute to HTML tags
                markdown_content = re.sub(r'<details>', '<details markdown="1">', markdown_content)
                markdown_content = re.sub(r'<summary>', '<summary markdown="1">', markdown_content)
                markdown_content = re.sub(r'<div([^>]*)>', r'<div\1 markdown="1">', markdown_content)

                # Convert markdown to HTML with extensions
                html = markdown.markdown(markdown_content, extensions=[
                    'fenced_code',
                    'codehilite',
                    'tables',
                    'nl2br',
                    'extra',
                    'md_in_html'
                ])

                logger.debug(f"Loaded markdown content from {relative_path}")
                return html
        except FileNotFoundError:
            logger.warning(f"Training content file not found: {full_path}")
            return f"<p><em>Training content not available at: {relative_path}</em></p>"
        except Exception as e:
            logger.error(f"Error loading markdown content from {full_path}: {e}")
            return f"<p><em>Error loading training content: {str(e)}</em></p>"
