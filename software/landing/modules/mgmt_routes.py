"""
Settings -> CybICS-mgmt: connect this installation to the optional central server.

Everything here is optional. Until the user connects (or a board's uplink is
on the default network cybics-mgmt, see utils/mgmt.py) the client makes no
network calls, and local flag validation never depends on the server.
"""
from flask import jsonify, request

from modules.cybics_mgmt import MgmtClientError
from utils.config import CYBICS_PLATFORM, MGMT_DEFAULT_SSID, UPLINK_INTERFACE
from utils.logger import logger
from utils.mgmt import (device_info, opted_out, request_uplink, set_opted_out,
                        uplink_status, validate_uplink)


def _error(exc, status=400):
    # The server writes its messages for end users; show them as they are.
    return jsonify({'success': False, 'code': exc.code, 'message': exc.message}), status


def _invalid(message):
    return jsonify({'success': False, 'code': 'invalid_input', 'message': message}), 400


def _field(data, name, limit=200):
    value = data.get(name, '')
    return value.strip()[:limit] if isinstance(value, str) else ''


def register_mgmt_routes(app, client, banners):
    """Register the /api/settings/mgmt routes for one MgmtClient, and the banner poll."""

    def snapshot():
        view = client.snapshot()   # never contains the token, the key or the baseline
        view['platform'] = CYBICS_PLATFORM
        view['opted_out'] = opted_out()
        if CYBICS_PLATFORM == 'physical':
            view['uplink'] = uplink_status()
            view['uplink']['interface'] = UPLINK_INTERFACE
            view['uplink']['default_ssid'] = MGMT_DEFAULT_SSID
        return view

    @app.route('/api/mgmt/banners', methods=['GET'])
    def mgmt_banners():
        """Banners from identify and message jobs, polled by the dashboard."""
        return jsonify({'banners': banners.active()})

    @app.route('/api/settings/mgmt', methods=['GET'])
    def mgmt_snapshot():
        return jsonify(snapshot())

    @app.route('/api/settings/mgmt/test', methods=['POST'])
    def mgmt_test():
        data = request.get_json(silent=True) or {}
        try:
            info = client.test_connection(_field(data, 'server_url', 500))
        except MgmtClientError as exc:
            return _error(exc)
        return jsonify({'success': True, 'info': info})

    @app.route('/api/settings/mgmt/connect', methods=['POST'])
    def mgmt_connect():
        data = request.get_json(silent=True) or {}
        server_url = _field(data, 'server_url', 500)
        code = _field(data, 'code', 64)
        label = _field(data, 'label', 40) or None
        if not (server_url and code):
            return _invalid('Fill in the server address and the code from the organiser.')
        info = device_info()
        if info['kind'] == 'physical' and not info.get('device_uid'):
            return jsonify({'success': False, 'code': 'no_device_uid',
                            'message': 'The board ID is not known yet. Wait until the display shows '
                                       'the cybics-<id> network name, then try again.'}), 409
        try:
            resp = client.enroll(server_url, code, label=label)
        except MgmtClientError as exc:
            return _error(exc)
        # Connecting by hand ends an earlier opt-out from the default network.
        set_opted_out(False)
        logger.info('CybICS-mgmt: connected to %s as %r', client.snapshot().get('server_url'),
                    (resp.get('device') or {}).get('label'))
        return jsonify({'success': True, 'snapshot': snapshot()})

    @app.route('/api/settings/mgmt/join', methods=['POST'])
    def mgmt_join():
        data = request.get_json(silent=True) or {}
        join_code = _field(data, 'join_code', 64)
        team_name = _field(data, 'team_name', 64)
        # Passwords are not stripped: a trailing space is a character too.
        team_password = data.get('team_password')
        if not isinstance(team_password, str):
            team_password = ''
        if not (join_code and team_name and team_password):
            return _invalid('Fill in the join code, team name and team password.')
        try:
            resp = client.join_event(join_code, team_name, team_password)
        except MgmtClientError as exc:
            return _error(exc)
        logger.info('CybICS-mgmt: joined event %r as team %r',
                    (resp.get('event') or {}).get('slug'), (resp.get('team') or {}).get('name'))
        return jsonify({'success': True, 'snapshot': snapshot()})

    @app.route('/api/settings/mgmt/leave-event', methods=['POST'])
    def mgmt_leave_event():
        try:
            client.leave_event()
        except MgmtClientError as exc:
            return _error(exc, 500)
        logger.info('CybICS-mgmt: left the event')
        return jsonify({'success': True, 'snapshot': snapshot()})

    @app.route('/api/settings/mgmt/allowed', methods=['POST'])
    def mgmt_allowed():
        data = request.get_json(silent=True) or {}
        actions = data.get('actions')
        if not isinstance(actions, list) or not all(isinstance(a, str) for a in actions):
            return _invalid('Send the allowed actions as a list.')
        try:
            allowed = client.set_allowed(actions)
        except MgmtClientError as exc:
            return _error(exc, 500)
        logger.info('CybICS-mgmt: allowed actions: %s', ', '.join(allowed) or 'none')
        return jsonify({'success': True, 'allowed': allowed, 'snapshot': snapshot()})

    @app.route('/api/settings/mgmt/disconnect', methods=['POST'])
    def mgmt_disconnect():
        # On purpose: a board no longer enrols on its own on the default network.
        set_opted_out(True)
        try:
            client.leave()
        except MgmtClientError as exc:
            return _error(exc, 500)
        logger.info('CybICS-mgmt: disconnected')
        return jsonify({'success': True, 'snapshot': snapshot()})

    @app.route('/api/settings/mgmt/uplink', methods=['POST'])
    def mgmt_uplink():
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
                return _invalid(problem)
        try:
            request_uplink(enabled, ssid, psk)
        except OSError as exc:
            logger.error('CybICS-mgmt: cannot hand the uplink settings to hwio: %s', exc)
            return jsonify({'success': False, 'code': 'uplink_unavailable',
                            'message': 'The uplink cannot be configured: the hwio service does not '
                                       'share its settings volume with the landing page.'}), 503
        logger.info('CybICS-mgmt: uplink %s requested', f'to {ssid!r}' if enabled else 'off')
        return jsonify({'success': True, 'uplink': uplink_status()})
