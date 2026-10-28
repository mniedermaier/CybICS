"""
POST /ctf/verify/<challenge_id>: run a challenge's verify module, submit its flag on success.

An answer-graded challenge (one that declares "answers" in ctf_config.json)
sends {"answers": {field: text}}. The body is bounded and validated here,
before any verify module runs, and the module grades it server-side. Other
challenges send no body and get verify() with no arguments, as they always
did. Kept out of app.py so the route can be tested with a Flask test client
without starting the landing page's background threads.
"""
from flask import jsonify, request, session

from modules.ctf_manager import ANSWER_BODY_LIMIT, AnswerError
from modules.ctf_manager import parse_answers


def _refused(message, status, **headers):
    return jsonify({'success': False, 'message': message, 'checks': []}), status, headers


def register_verify_route(app, ctf_manager, report_solve):
    """Register /ctf/verify/<id> for one CTFManager.

    report_solve(challenge_id, flag) is called after a solve is saved; it must
    not raise or block (MgmtClient.report_solve in production).
    """

    @app.route('/ctf/verify/<challenge_id>', methods=['POST'])
    def verify_defense(challenge_id):
        """Verify a challenge and auto-submit its flag on success."""
        challenge, _ = ctf_manager.get_challenge(challenge_id)
        if not challenge:
            return _refused('Challenge not found', 404)

        # Bounded read: never pull more than the limit into memory.
        if (request.content_length or 0) > ANSWER_BODY_LIMIT:
            return _refused('Request too large', 413)
        raw_body = request.stream.read(ANSWER_BODY_LIMIT + 1)
        try:
            answers = parse_answers(challenge, raw_body)
        except AnswerError as e:
            return _refused(e.message, e.status)

        # The progress file is the source of truth, as on every CTF route.
        progress = ctf_manager.load_progress()
        session['solved_challenges'] = progress['solved_challenges']
        session['total_points'] = progress['total_points']

        if challenge_id in progress['solved_challenges']:
            return jsonify({'success': True, 'message': 'Challenge already solved!', 'checks': []})

        result = ctf_manager.verify_defense(challenge_id, answers, client=request.remote_addr)
        if result.get('retry_after'):
            return _refused(result['message'], 429, **{'Retry-After': str(result['retry_after'])})

        if result.get('success') and result.get('flag'):
            submit_result = ctf_manager.submit_flag(challenge_id, result['flag'], progress)
            if submit_result['success']:
                session['solved_challenges'].append(challenge_id)
                session['total_points'] += submit_result['points']
                session.modified = True
                ctf_manager.save_progress({
                    'solved_challenges': session['solved_challenges'],
                    'total_points': session['total_points'],
                })
                result['points'] = submit_result['points']
                report_solve(challenge_id, result['flag'])
                result['message'] = f"{result['message']} You earned {submit_result['points']} points!"

        return jsonify(result)

    return verify_defense
