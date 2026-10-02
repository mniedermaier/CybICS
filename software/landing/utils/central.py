"""Helpers that connect the landing page to the optional central CTF server.

The client itself is modules/central_ctf.py, vendored unchanged from the
CybICS-CTF repository. This module supplies what the client needs from
CybICS -- the local progress, the instance description, the heartbeat status --
and the file exchange with hwio-raspberry for the uplink Wi-Fi on a board.

Kept free of Flask so it can be tested without standing up the app.
"""
import json
import os
import re
import socket
import tempfile
import time

from utils.config import (CYBICS_PLATFORM, DEVICE_STATE_FILE, PROGRESS_FILE,
                          UPLINK_DIR, VERSION_HEADER)

UPLINK_REQUEST = 'request.json'
UPLINK_STATUS = 'status.json'

# hwio publishes the UID as lower-case hex; the server accepts 6 to 32 of them.
DEVICE_UID_RE = re.compile(r'^[0-9a-f]{6,32}$')


def read_progress_strict(path=None):
    """Solved challenge ids, raising when the progress file cannot be read.

    CTFManager.load_progress turns a half-written file into empty progress,
    which is right for the CTF page but wrong here: the client stores the
    local solves as a never-reported baseline at enrolment, and an empty
    baseline on a reused board would report every old solve as new. Raising
    makes the enrolment fail with progress_unreadable instead.
    """
    path = path or PROGRESS_FILE
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return list(json.load(f)['solved_challenges'])


def read_version(path=None):
    """The CybICS release, e.g. '1.2.3', or None if it cannot be determined."""
    env = os.environ.get('CYBICS_RELEASE')
    if env:
        return env
    try:
        with open(path or VERSION_HEADER, encoding='utf-8') as f:
            header = f.read()
    except OSError:
        return None
    parts = [re.search(rf'#define\s+FIRMWARE_VERSION_{name}\s+(\d+)', header)
             for name in ('MAJOR', 'MINOR', 'PATCH')]
    if not all(parts):
        return None
    return '.'.join(m.group(1) for m in parts)


def read_device_uid(path=None):
    """The STM32 UID hwio-raspberry published, or None on a virtual stack."""
    try:
        with open(path or DEVICE_STATE_FILE, encoding='utf-8') as f:
            uid = json.load(f).get('device_uid')
    except (OSError, ValueError, AttributeError):
        return None
    return uid if isinstance(uid, str) and DEVICE_UID_RE.match(uid) else None


def instance_info():
    """The `instance` object sent with an enrolment."""
    info = {
        'kind': 'physical' if CYBICS_PLATFORM == 'physical' else 'virtual',
        'hostname': socket.gethostname(),
        'cybics_version': read_version(),
        'mode': os.environ.get('CYBICS_MODE') or None,
    }
    if info['kind'] == 'physical':
        info['device_uid'] = read_device_uid()
    return {k: v for k, v in info.items() if v is not None}


def collect_status(containers, local_solved):
    """Heartbeat status: small and cheap, it is sent every 30 seconds.

    `containers` is StatsCollector's cached list (no Docker call). Nothing in
    here describes the participant's network.
    """
    return {
        'cybics_version': read_version(),
        'mode': os.environ.get('CYBICS_MODE') or None,
        'services': {c.get('name'): c.get('status') == 'running'
                     for c in containers if c.get('name')},
        'local_solved': local_solved,
    }


# ---------- uplink Wi-Fi (physical board only) ----------

def validate_uplink(ssid, psk):
    """Return an error message for the user, or None if the values are usable."""
    if not isinstance(ssid, str) or not 1 <= len(ssid.encode('utf-8')) <= 32:
        return 'The network name must be 1 to 32 bytes long.'
    if not isinstance(psk, str) or not 8 <= len(psk) <= 63 or not psk.isascii():
        return 'The Wi-Fi password must be 8 to 63 ASCII characters (WPA2-PSK).'
    return None


def _write_private(path, payload):
    """Write JSON atomically and readable only by its owner (it may hold a PSK)."""
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix='.uplink.')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def request_uplink(enabled, ssid=None, psk=None, directory=None):
    """Ask hwio-raspberry to configure the uplink profile.

    Raises OSError when the shared volume is missing, which means this is not
    a board (or the compose file predates this feature).
    """
    directory = directory or UPLINK_DIR
    if not os.path.isdir(directory):
        raise OSError(f'{directory} is not mounted')
    request = {'enabled': bool(enabled), 'id': time.time()}
    if enabled:
        request.update({'ssid': ssid, 'psk': psk})
    _write_private(os.path.join(directory, UPLINK_REQUEST), request)
    return request['id']


def uplink_status(directory=None):
    """What hwio-raspberry last reported about the uplink, or None if nothing."""
    directory = directory or UPLINK_DIR
    try:
        with open(os.path.join(directory, UPLINK_STATUS), encoding='utf-8') as f:
            status = json.load(f)
    except (OSError, ValueError):
        status = None
    if not isinstance(status, dict):
        status = None
    pending = os.path.exists(os.path.join(directory, UPLINK_REQUEST))
    return {'available': os.path.isdir(directory), 'pending': pending, 'status': status}
