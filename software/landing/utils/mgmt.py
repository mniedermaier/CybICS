"""Helpers that connect the landing page to CybICS-mgmt, the optional central server.

The client itself is modules/cybics_mgmt.py, vendored unchanged from the
CybICS-mgmt repository. This module supplies what the client needs from
CybICS -- the local progress, the device description, the heartbeat status,
the job handlers -- plus the banners those jobs show, the enrolment on the
default network cybics-mgmt, and the file exchange with hwio-raspberry for
the uplink Wi-Fi on a board.

Kept free of Flask so it can be tested without standing up the app.
"""
import json
import logging
import os
import re
import socket
import tempfile
import threading
import time

from modules.cybics_mgmt import MgmtClientError
from utils.config import (CYBICS_PLATFORM, DEVICE_STATE_FILE, MGMT_DEFAULT_CODE,
                          MGMT_DEFAULT_SSID, MGMT_DEFAULT_URL, MGMT_OPTOUT_FILE,
                          PROGRESS_FILE, UPLINK_DIR, VERSION_HEADER)
from utils.hardware import read_hardware_version
from utils.restart import RestartError

# The client's logger; app.py hands it landing's handlers.
logger = logging.getLogger('cybics_mgmt')

UPLINK_REQUEST = 'request.json'
UPLINK_STATUS = 'status.json'

# hwio publishes the UID as lower-case hex; the server accepts 6 to 32 of them.
DEVICE_UID_RE = re.compile(r'^[0-9a-f]{6,32}$')

THERMAL_ZONE = '/sys/class/thermal/thermal_zone0/temp'
# The server keeps at most 16 KB of a status; stay well below that.
STATUS_MAX = 12 * 1024
SERVICES_MAX = 64
SOLVED_MAX = 200


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


def device_info():
    """The `device` object sent with an enrolment."""
    info = {
        'kind': 'physical' if CYBICS_PLATFORM == 'physical' else 'virtual',
        'hostname': socket.gethostname(),
        'cybics_version': read_version(),
        'mode': os.environ.get('CYBICS_MODE') or None,
    }
    if info['kind'] == 'physical':
        info['device_uid'] = read_device_uid()
    return {k: v for k, v in info.items() if v is not None}


# ---------- heartbeat status ----------

def read_cpu_temp(path=THERMAL_ZONE):
    """The CPU temperature in degrees Celsius, or None where there is no sensor."""
    try:
        with open(path, encoding='ascii') as f:
            millidegrees = int(f.read().strip())
    except (OSError, ValueError):
        return None
    return round(millidegrees / 1000, 1) if -50000 < millidegrees < 150000 else None


def host_status(cpu_percent=None):
    """CPU, memory, disk, uptime and temperature of the host, as far as cheaply known.

    `cpu_percent` is StatsCollector's last sample: measuring here would block.
    """
    host = {}
    if isinstance(cpu_percent, (int, float)) and not isinstance(cpu_percent, bool):
        host['cpu_percent'] = round(float(cpu_percent), 1)
    try:
        import psutil   # in the landing image; the plain test environment may lack it
        memory = psutil.virtual_memory()
        host['memory_percent'] = memory.percent
        host['memory_total_mb'] = round(memory.total / 2 ** 20)
        disk = psutil.disk_usage('/')
        host['disk_percent'] = disk.percent
        host['disk_total_gb'] = round(disk.total / 2 ** 30, 1)
        host['uptime_s'] = int(time.time() - psutil.boot_time())
    except Exception:
        pass
    temperature = read_cpu_temp()
    if temperature is not None:
        host['cpu_temp_c'] = temperature
    return host


def board_status():
    """Revision, STM32 UID and uplink state of a board (from files landing already reads)."""
    board = {'revision': read_hardware_version().get('revision'), 'device_uid': read_device_uid()}
    uplink = uplink_status().get('status') or {}
    board['uplink'] = {k: uplink[k] for k in ('present', 'state', 'ssid', 'ip') if k in uplink}
    return {k: v for k, v in board.items() if v not in (None, {})}


def _bounded(status):
    """Cut the status down until it is safely below what the server keeps."""
    if len(json.dumps(status)) <= STATUS_MAX:
        return status
    status.pop('services', None)
    status.pop('board', None)
    if len(json.dumps(status)) <= STATUS_MAX:
        return status
    return {k: status[k] for k in ('cybics_version', 'mode', 'hostname') if k in status}


def collect_status(containers, local_solved, cpu_percent=None, platform=None):
    """Heartbeat status: small and cheap, it is sent every 30 seconds. Never raises.

    `containers` is StatsCollector's cached list (no Docker call). Nothing in
    here describes the participant's network; the uplink it reports is the
    organiser's event network.
    """
    try:
        status = {
            'cybics_version': read_version(),
            'mode': os.environ.get('CYBICS_MODE') or None,
            'hostname': socket.gethostname()[:64],
            'services': {str(c.get('name'))[:64]: c.get('status') == 'running'
                         for c in (containers or [])[:SERVICES_MAX]
                         if isinstance(c, dict) and c.get('name')},
            'local_solved': [str(cid)[:64] for cid in list(local_solved or [])[:SOLVED_MAX]],
            'host': host_status(cpu_percent),
        }
        if (platform or CYBICS_PLATFORM) == 'physical':
            status['board'] = board_status()
        return _bounded({k: v for k, v in status.items() if v is not None})
    except Exception:
        logger.exception('cybics-mgmt: cannot collect the status')
        return {}


# ---------- banners (identify and message jobs) ----------

class Banners:
    """Short texts the dashboard shows on top until they expire or are dismissed."""

    def __init__(self, clock=time.time):
        self._clock = clock
        self._lock = threading.Lock()
        self._items = []
        self._next_id = 1

    def show(self, text, seconds, kind='message'):
        seconds = min(3600, max(1, int(seconds)))
        with self._lock:
            banner = {'id': self._next_id, 'kind': kind, 'text': str(text)[:500],
                      'until': self._clock() + seconds}
            self._next_id += 1
            self._items = [b for b in self._items if b['until'] > self._clock()][-9:] + [banner]
        return banner['id']

    def active(self):
        """The banners still to show, with the seconds each has left (the browser's clock may differ)."""
        now = self._clock()
        with self._lock:
            self._items = [b for b in self._items if b['until'] > now]
            return [{'id': b['id'], 'kind': b['kind'], 'text': b['text'],
                     'remaining': max(1, round(b['until'] - now))} for b in self._items]


# ---------- job handlers ----------

MESSAGE_SECONDS = 300


def device_label(client):
    """What the identify banner calls this installation: its label on the server, or the hostname."""
    try:
        label = (client.snapshot().get('device') or {}).get('label')
    except Exception:
        label = None
    return label if isinstance(label, str) and label.strip() else socket.gethostname()


def make_handlers(label, banners, reset_progress, restart_all, restart_service, logs_text):
    """The five actions landing offers. The client runs one only if the user allowed it.

    The callables are injected so the handlers can be tested without Docker:
    label() names this installation (see device_label), restart_all() returns
    (project, others, own) like utils.restart.start_restart, restart_service(name)
    a result text, and logs_text() the log bundle.
    """
    def identify(params):
        try:
            seconds = min(600, max(5, int(params.get('seconds', 60))))
        except (TypeError, ValueError):
            seconds = 60
        banners.show(f'This is {label()}', seconds, kind='identify')
        return f'banner shown for {seconds} s'

    def message(params):
        text = params.get('text')
        if not isinstance(text, str) or not text.strip():
            raise MgmtClientError('invalid_params', 'The message is empty.')
        banners.show(text.strip(), MESSAGE_SECONDS)
        return 'message shown'

    def restart(params):
        service = params.get('service') or 'all'
        try:
            if service == 'all':
                project, others, own = restart_all()
                return f'restarting {len(others) + 1} containers of {project}'
            return restart_service(service)
        except RestartError as exc:
            raise MgmtClientError('restart_refused', str(exc)) from None

    def reset(_params):
        reset_progress()
        return 'local CTF progress reset'

    def collect_logs(_params):
        try:
            return logs_text()
        except RestartError as exc:
            raise MgmtClientError('logs_unavailable', str(exc)) from None

    return {'identify': identify, 'message': message, 'restart': restart,
            'reset_progress': reset, 'collect_logs': collect_logs}


# ---------- enrolment on the default network (board only) ----------

def opted_out(path=None):
    """True while the user has disconnected on purpose."""
    return os.path.exists(path or MGMT_OPTOUT_FILE)


def set_opted_out(value, path=None):
    """Remember (or forget) that the user disconnected on purpose. Never raises."""
    path = path or MGMT_OPTOUT_FILE
    try:
        if value:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'{time.time()}\n')
        elif os.path.exists(path):
            os.unlink(path)
    except OSError as exc:
        logger.warning('cybics-mgmt: cannot update %s: %s', path, exc)


class AutoEnrol:
    """Enrol a board on its own while its uplink is on the default network.

    Being connected to the network named MGMT_DEFAULT_SSID is the opt-in: on
    any other network, on a virtual instance, after the user disconnected on
    purpose, or after the organiser retired the device, nothing is sent. A
    refused enrolment is not retried until the uplink reconnects or landing
    restarts, so a disabled code does not cause a stream of attempts.
    """

    def __init__(self, client, platform=None, uplink=None, device_uid=None, optout_path=None,
                 ssid=MGMT_DEFAULT_SSID, url=MGMT_DEFAULT_URL, code=MGMT_DEFAULT_CODE):
        self.client = client
        self.platform = platform or CYBICS_PLATFORM
        self.uplink = uplink or uplink_status
        self.device_uid = device_uid or read_device_uid
        self.optout_path = optout_path or MGMT_OPTOUT_FILE
        self.ssid, self.url, self.code = ssid, url, code
        self._refused_on = None     # the uplink connection (its address) a refusal happened on
        self._stop = threading.Event()

    def connection(self):
        """The uplink's address while it is connected to the default network, else None."""
        status = (self.uplink() or {}).get('status') or {}
        state, ssid, address = status.get('state'), status.get('ssid'), status.get('ip')
        if (isinstance(state, str) and state.startswith('connected') and ssid == self.ssid
                and isinstance(address, str) and address):
            return address
        return None

    def check(self):
        """One decision. Returns what happened, for the log and the tests. Never raises."""
        try:
            return self._check()
        except Exception:
            logger.exception('cybics-mgmt: the default-network check failed')
            return 'error'

    def _check(self):
        if self.platform != 'physical':
            return 'virtual'
        connection = self.connection()
        if connection is None:
            self._refused_on = None     # off the network: a reconnect may try again
            return 'not_on_default_network'
        if opted_out(self.optout_path):
            return 'opted_out'
        snap = self.client.snapshot()
        if snap.get('enabled'):
            return 'enrolled'
        if snap.get('revoked'):
            return 'revoked'
        if self._refused_on == connection:
            return 'refused_before'
        uid = self.device_uid()
        if not uid:
            return 'no_device_uid'      # hwio has not published it yet; next round
        try:
            self.client.enroll(self.url, self.code, label=f'cybics-{uid}')
        except MgmtClientError as exc:
            self._refused_on = connection
            logger.warning('cybics-mgmt: enrolling on %s was refused (%s): %s; not retrying until '
                           'the uplink reconnects', self.ssid, exc.code, exc.message)
            return 'refused'
        logger.info('cybics-mgmt: enrolled with %s on the default network %s', self.url, self.ssid)
        return 'enrolled_now'

    def run(self, interval=15):
        """Thread body: one check every `interval` seconds, until stop()."""
        while not self._stop.is_set():
            self.check()
            self._stop.wait(interval)

    def stop(self):
        self._stop.set()


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
