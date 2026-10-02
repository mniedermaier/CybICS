"""
Settings -> Central CTF server: enrol this instance with an event's server.

Everything here is optional. Until the user joins an event the client makes
no network calls, and local flag validation never depends on the server.
"""
from flask import jsonify, request

from modules.central_ctf import CTFClientError
from utils.central import (instance_info, request_uplink, uplink_status,
                           validate_uplink)
from utils.config import CYBICS_PLATFORM, UPLINK_INTERFACE
from utils.logger import logger


def _error(exc, status=400):
    # The server writes its messages for end users; show them as they are.
    return jsonify({'success': False, 'code': exc.code, 'message': exc.message}), status


def _field(data, name, limit=200):
    value = data.get(name, '')
    return value.strip()[:limit] if isinstance(value, str) else ''


def register_central_routes(app, central):
    """Register the /api/settings/central routes for one CTFClient."""

    @app.route('/api/settings/central', methods=['GET'])
    def central_snapshot():
        view = central.snapshot()   # never contains the token
        view['platform'] = CYBICS_PLATFORM
        if CYBICS_PLATFORM == 'physical':
            view['uplink'] = uplink_status()
            view['uplink']['interface'] = UPLINK_INTERFACE
        return jsonify(view)

    @app.route('/api/settings/central/test', methods=['POST'])
    def central_test():
        data = request.get_json(silent=True) or {}
        try:
            info = central.test_connection(_field(data, 'server_url', 500))
        except CTFClientError as exc:
            return _error(exc)
        return jsonify({'success': True, 'info': info})

    @app.route('/api/settings/central/enroll', methods=['POST'])
    def central_enroll():
        data = request.get_json(silent=True) or {}
        server_url = _field(data, 'server_url', 500)
        join_code = _field(data, 'join_code', 64)
        team_name = _field(data, 'team_name', 64)
        # Passwords are not stripped: a trailing space is a character too.
        team_password = data.get('team_password')
        if not isinstance(team_password, str):
            team_password = ''
        if not (server_url and join_code and team_name and team_password):
            return jsonify({'success': False, 'code': 'invalid_input',
                            'message': 'Fill in the server address, join code, team name and team password.'}), 400
        instance = instance_info()
        if instance['kind'] == 'physical' and not instance.get('device_uid'):
            return jsonify({'success': False, 'code': 'no_device_uid',
                            'message': 'The board ID is not known yet. Wait until the display shows '
                                       'the cybics-<id> network name, then try again.'}), 409
        try:
            resp = central.enroll(server_url, join_code, team_name, team_password, instance)
        except CTFClientError as exc:
            return _error(exc)
        logger.info('Central CTF: joined event %r as team %r',
                    (resp.get('event') or {}).get('slug'), (resp.get('team') or {}).get('name'))
        return jsonify({'success': True, 'snapshot': central.snapshot()})

    @app.route('/api/settings/central/leave', methods=['POST'])
    def central_leave():
        central.leave()
        logger.info('Central CTF: left the event')
        return jsonify({'success': True, 'snapshot': central.snapshot()})

    @app.route('/api/settings/central/uplink', methods=['POST'])
    def central_uplink():
        """Configure the board's USB Wi-Fi uplink; hwio-raspberry applies it."""
        if CYBICS_PLATFORM != 'physical':
            return jsonify({'success': False, 'code': 'not_physical',
                            'message': 'The Wi-Fi uplink only exists on a CybICS board.'}), 404
        data = request.get_json(silent=True) or {}
        enabled = data.get('enabled') is True
        ssid = data.get('ssid') if isinstance(data.get('ssid'), str) else ''
        psk = data.get('psk') if isinstance(data.get('psk'), str) else ''
        if enabled:
            problem = validate_uplink(ssid, psk)
            if problem:
                return jsonify({'success': False, 'code': 'invalid_input', 'message': problem}), 400
        try:
            request_uplink(enabled, ssid, psk)
        except OSError as exc:
            logger.error('Central CTF: cannot hand the uplink settings to hwio: %s', exc)
            return jsonify({'success': False, 'code': 'uplink_unavailable',
                            'message': 'The uplink cannot be configured: the hwio service does not '
                                       'share its settings volume with the landing page.'}), 503
        logger.info('Central CTF: uplink %s requested', f'to {ssid!r}' if enabled else 'off')
        return jsonify({'success': True, 'uplink': uplink_status()})
