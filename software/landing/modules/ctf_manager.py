"""
CTF (Capture The Flag) management module
"""
import json
import os
import importlib
import markdown
import re
import threading
import time
from collections import deque

from utils.logger import logger
from utils.config import PROGRESS_FILE, CTF_CONFIG_FILE, TRAINING_DIR

# Answer-graded challenges: a "verify" or "defense" challenge may declare
#   "answers": [{"name": "port", "label": "...", "placeholder": "...", "max_length": 16}]
# The student's text goes to the verify module as verify(answers); the
# expected values live only in that module, never in ctf_config.json or the
# page. Everything below bounds what a client can send before any module runs.
ANSWER_BODY_LIMIT = 4096       # bytes of JSON accepted on /ctf/verify/<id>
ANSWER_MAX_FIELDS = 8
ANSWER_MAX_LENGTH = 200        # hard cap per field; a field may set a lower one
ANSWER_NAME_RE = re.compile(r'^[a-z][a-z0-9_]{0,31}$')
# Graded attempts per challenge, client address and window: enough to correct
# a typo, too few to walk a small answer space by script.
ANSWER_ATTEMPTS = 10
ANSWER_WINDOW = 60.0
ANSWER_MAX_BUCKETS = 256       # stale throttle buckets are dropped beyond this
_CONTROL_RE = re.compile(r'[\x00-\x1f\x7f]')


class AnswerError(ValueError):
    """A verify request whose answers cannot be graded; carries an HTTP status."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def answer_fields(challenge):
    """The answer fields a challenge declares, normalised.

    Raises AnswerError(500) on a malformed declaration rather than guessing,
    so a broken config entry fails closed instead of grading the wrong thing.
    """
    spec = (challenge or {}).get('answers')
    if not spec:
        return []
    if not isinstance(spec, list) or len(spec) > ANSWER_MAX_FIELDS:
        raise AnswerError('Challenge answer fields are misconfigured', 500)
    fields, seen = [], set()
    for item in spec:
        name = item.get('name') if isinstance(item, dict) else None
        if not isinstance(name, str) or not ANSWER_NAME_RE.match(name) or name in seen:
            raise AnswerError('Challenge answer fields are misconfigured', 500)
        seen.add(name)
        limit = item.get('max_length', ANSWER_MAX_LENGTH)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= ANSWER_MAX_LENGTH:
            raise AnswerError('Challenge answer fields are misconfigured', 500)
        fields.append({
            'name': name,
            'label': str(item.get('label') or name),
            'placeholder': str(item.get('placeholder') or ''),
            'max_length': limit,
        })
    return fields


def parse_answers(challenge, raw_body):
    """Validate the body of a verify request against the challenge's fields.

    raw_body is the request body as bytes (possibly empty). Returns None for a
    challenge without answer fields (the existing verify() call), otherwise a
    dict {field name: stripped text}. Raises AnswerError on anything else.
    """
    if raw_body and len(raw_body) > ANSWER_BODY_LIMIT:
        raise AnswerError('Request too large', 413)
    payload = {}
    if raw_body and raw_body.strip():
        try:
            payload = json.loads(raw_body)
        except (ValueError, UnicodeDecodeError):
            raise AnswerError('Request body is not valid JSON')
        if not isinstance(payload, dict):
            raise AnswerError('Request body must be a JSON object')
    submitted = payload.get('answers')

    fields = answer_fields(challenge)
    if not fields:
        if submitted not in (None, {}):
            raise AnswerError('This challenge does not take answers')
        return None

    if not isinstance(submitted, dict):
        raise AnswerError('Please fill in the answer fields')
    known = {f['name'] for f in fields}
    if set(submitted) - known:
        raise AnswerError('Unknown answer field')
    answers = {}
    for field in fields:
        value = submitted.get(field['name'])
        if value is None:
            value = ''
        if not isinstance(value, str):
            raise AnswerError(f"Answer for '{field['label']}' must be text")
        value = value.strip()
        if not value:
            raise AnswerError(f"Please fill in '{field['label']}'")
        if len(value) > field['max_length']:
            raise AnswerError(f"Answer for '{field['label']}' is too long "
                              f"(at most {field['max_length']} characters)")
        if _CONTROL_RE.search(value):
            raise AnswerError(f"Answer for '{field['label']}' contains control characters")
        answers[field['name']] = value
    return answers


def _clean_result(result):
    """Only the keys the page renders, typed; a module cannot add a flag."""
    if not isinstance(result, dict):
        return {'success': False, 'message': 'Verification failed due to an internal error', 'checks': []}
    checks = []
    for check in result.get('checks') or []:
        if isinstance(check, dict):
            checks.append({'name': str(check.get('name', '')),
                           'passed': bool(check.get('passed')),
                           'detail': str(check.get('detail', ''))})
    return {'success': bool(result.get('success')),
            'message': str(result.get('message', '')),
            'checks': checks}


class CTFManager:
    """Manage CTF challenges and user progress"""

    def __init__(self):
        self.config = self._load_config()
        self.challenges = self.config.get('categories', {})
        self._attempts = {}
        self._attempts_lock = threading.Lock()
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
            if not re.match(r'^CybICS\(.*\)$', submitted_flag.strip()):
                return {'success': False, 'message': 'Incorrect format. Flags look like CybICS(...)'}
            return {'success': False, 'message': 'Incorrect flag. The format is right, but the value is wrong.'}

    def _take_attempt(self, challenge_id, client=None, now=None):
        """Count one graded attempt; return seconds to wait, 0 when allowed.

        The bucket is per challenge and client address, so another host on
        the network cannot use up a student's attempts. Clients that reach
        landing through the same proxy share an address and so a bucket.
        """
        now = time.monotonic() if now is None else now
        key = (challenge_id, client or '')
        with self._attempts_lock:
            if len(self._attempts) > ANSWER_MAX_BUCKETS:
                for stale in [k for k, w in self._attempts.items()
                              if not w or now - w[-1] >= ANSWER_WINDOW]:
                    del self._attempts[stale]
            window = self._attempts.setdefault(key, deque())
            while window and now - window[0] >= ANSWER_WINDOW:
                window.popleft()
            if len(window) >= ANSWER_ATTEMPTS:
                return max(1, int(ANSWER_WINDOW - (now - window[0])) + 1)
            window.append(now)
            return 0

    def verify_defense(self, challenge_id, answers=None, client=None):
        """Run defense verification for a challenge.

        answers is None for a challenge without answer fields; the module is
        then called as verify(), exactly as before. For an answer-graded
        challenge it is the dict from parse_answers() and the module is called
        as verify(answers). client (the request's address) keys the attempt
        throttle for graded challenges.

        Returns:
            dict with keys: success, message, flag (if success), checks (list of check results)
        """
        challenge, _ = self.get_challenge(challenge_id)
        if not challenge:
            return {'success': False, 'message': 'Challenge not found', 'checks': []}

        verify_module = challenge.get('verify_module')
        if not verify_module:
            return {'success': False, 'message': 'No verification module configured', 'checks': []}

        try:
            graded = bool(answer_fields(challenge))
        except AnswerError as e:
            logger.error(f"Challenge {challenge_id}: {e.message}")
            return {'success': False, 'message': e.message, 'checks': []}
        if graded and not isinstance(answers, dict):
            return {'success': False, 'message': 'Please fill in the answer fields', 'checks': []}

        if graded:
            wait = self._take_attempt(challenge_id, client)
            if wait:
                return {'success': False, 'checks': [], 'retry_after': wait,
                        'message': f'Too many attempts. Try again in {wait} seconds.'}

        try:
            module = importlib.import_module(f'modules.defense_checks.{verify_module}')
            result = _clean_result(module.verify(answers) if graded else module.verify())

            if result['success']:
                result['flag'] = challenge['flag']
            if graded:
                logger.info(f"Answer attempt for {challenge_id}: "
                            f"{'correct' if result['success'] else 'incorrect'}")

            return result
        except ImportError as e:
            logger.error(f"Could not load defense check module: {verify_module}: {e}")
            return {'success': False, 'message': f'Verification module not found: {verify_module}', 'checks': []}
        except Exception as e:
            logger.error(f"Error running defense check {verify_module}: {e}", exc_info=True)
            # Detail is logged above with exc_info; the client gets a generic
            # message so an exception string never reaches the HTTP response.
            return {'success': False, 'message': 'Verification failed due to an internal error', 'checks': []}

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

    @staticmethod
    def extract_hint_from_html(html):
        """Extract the 💡 Hint <details> block from rendered HTML and return (hint_html, cleaned_html)."""
        pattern = r'<details[^>]*>\s*<summary[^>]*>[^<]*💡\s*Hint[^<]*</summary>(.*?)</details>'
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if match:
            hint_html = match.group(1).strip()
            cleaned = html[:match.start()] + html[match.end():]
            return hint_html, cleaned
        return None, html

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

                # Dedent fenced code blocks so they render inside list items
                def _dedent_fenced(m):
                    indent = m.group(1)
                    return '\n'.join(
                        line[len(indent):] if line.startswith(indent) else line
                        for line in m.group(0).split('\n')
                    )

                markdown_content = re.sub(
                    r'^([ \t]+)(```\w*\n.*?\n[ \t]*```)',
                    _dedent_fenced,
                    markdown_content,
                    flags=re.MULTILINE | re.DOTALL
                )

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
