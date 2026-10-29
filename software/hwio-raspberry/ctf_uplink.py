"""Manage the board's uplink to a CybICS-mgmt server.

A USB Wi-Fi dongle joins the event network that the organiser's CybICS-mgmt
server sits on. The onboard radio stays what it always was: wlan0, the
training access point (or station). The image pins the dongle's name with a
udev rule (70-cybics-wifi.rules), installs the NetworkManager profile
cybics-ctf-uplink for the default network cybics-mgmt with autoconnect on, and
isolates the interface with nftables (cybics-ctf-uplink.nft): no forwarding to
or from it, and no new inbound connections.

The landing page asks for changes by writing request.json into a directory
shared with this container; this module applies it with nmcli and answers in
status.json. That keeps nmcli access in one service: landing already runs
with host networking and the Docker socket and does not need D-Bus as well.

nmcli is passed in rather than imported, so this runs in tests without a
NetworkManager.
"""
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

UPLINK_CONNECTION = 'cybics-ctf-uplink'
# Everything named like this belongs to the uplink, never to wlan0.
UPLINK_PREFIX = 'cybics-ctf-'
UPLINK_INTERFACE = os.environ.get('CYBICS_UPLINK_IFACE', 'ctfwlan0')
UPLINK_DIR = os.environ.get('CYBICS_UPLINK_DIR', '/var/lib/cybics-uplink')
REQUEST = 'request.json'
STATUS = 'status.json'
# Seconds between status refreshes while no request is pending (see Uplink.run).
STATUS_REFRESH = 15

# Kept in step with the keyfile the image ships
# (software/rpi-image/stage-cybics/01-configure-system/files/), autoconnect
# included. Used when the profile is missing, e.g. on a device set up with
# installRPI.sh before this existed.
PROFILE_AUTOCONNECT = True
PROFILE_OPTIONS = {
    # Keep trying for good. NetworkManager's default gives up after four
    # failed attempts, and a board that lost cybics-mgmt (the access point
    # full, out of range for a while) then stayed off the server.
    'connection.autoconnect-retries': '0',
    'wifi.mode': 'infrastructure',
    # The default network of the CybICS-mgmt Raspberry Pi image.
    'wifi.ssid': 'cybics-mgmt',
    'wifi-sec.key-mgmt': 'wpa-psk',
    'wifi-sec.psk': 'cybics-mgmt',
    'ipv4.method': 'auto',
    # Reach the CTF server's subnet only. Without this the uplink would become
    # the default route, and the training AP's NAT (ipv4.method=shared) would
    # carry participants' traffic into the event network.
    'ipv4.never-default': 'yes',
    'ipv4.route-metric': '600',
    'ipv6.method': 'disabled',
}


def is_uplink_connection(conn):
    """True for a profile that belongs to the uplink rather than to wlan0."""
    return conn.name.startswith(UPLINK_PREFIX) or conn.device == UPLINK_INTERFACE


def validate(request):
    """Return an error message, or None if the request is usable."""
    if not isinstance(request, dict) or not isinstance(request.get('enabled'), bool):
        return 'malformed request'
    if not request['enabled']:
        return None
    ssid, psk = request.get('ssid'), request.get('psk')
    if not isinstance(ssid, str) or not 1 <= len(ssid.encode('utf-8')) <= 32:
        return 'the network name must be 1 to 32 bytes long'
    if not isinstance(psk, str) or not 8 <= len(psk) <= 63 or not psk.isascii():
        return 'the Wi-Fi password must be 8 to 63 ASCII characters'
    return None


def _write_status(directory, status):
    tmp = os.path.join(directory, '.' + STATUS)
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(status, fh)
    os.replace(tmp, os.path.join(directory, STATUS))


class Uplink:
    def __init__(self, nmcli, directory=UPLINK_DIR, interface=UPLINK_INTERFACE):
        self.nmcli = nmcli
        self.directory = directory
        self.interface = interface
        self.last_error = None
        self.last_request = None

    def _profile_exists(self):
        return any(c.name == UPLINK_CONNECTION for c in self.nmcli.connection())

    def ensure_profile(self):
        if self._profile_exists():
            return
        logger.info('Uplink  : creating the %s profile', UPLINK_CONNECTION)
        self.nmcli.connection.add('wifi', PROFILE_OPTIONS, self.interface,
                                  UPLINK_CONNECTION, PROFILE_AUTOCONNECT)

    def keep_retrying(self):
        """Give a profile from an older image the retries of PROFILE_OPTIONS. Never raises."""
        key = 'connection.autoconnect-retries'
        try:
            if not self._profile_exists():
                return   # ensure_profile() creates it with them
            # nmcli adds a gloss to the value, e.g. '-1 (default)' or '0 (forever)'.
            current = (self.nmcli.connection.show(UPLINK_CONNECTION).get(key) or '').split()
            if current[:1] != ['0']:
                self.nmcli.connection.modify(UPLINK_CONNECTION, {key: PROFILE_OPTIONS[key]})
                logger.info('Uplink  : %s retries for good now', UPLINK_CONNECTION)
        except Exception as error:
            logger.error('Uplink  : cannot set the retries: %s', error)

    def apply(self, request):
        """Configure the profile as asked. Raises on an nmcli failure."""
        self.ensure_profile()
        if request['enabled']:
            self.nmcli.connection.modify(UPLINK_CONNECTION, {
                'wifi.ssid': request['ssid'],
                'wifi-sec.key-mgmt': 'wpa-psk',
                'wifi-sec.psk': request['psk'],
                'connection.interface-name': self.interface,
                'connection.autoconnect': 'yes',
            })
            if self.device_present():
                # Do not wait: a wrong password or an out-of-range network
                # shows up as the device state in the next status.
                self.nmcli.connection.up(UPLINK_CONNECTION, 0)
            logger.info('Uplink  : enabled for network %r', request['ssid'])
        else:
            self.nmcli.connection.modify(UPLINK_CONNECTION, {'connection.autoconnect': 'no'})
            if any(c.name == UPLINK_CONNECTION and c.device not in (None, '', '--')
                   for c in self.nmcli.connection()):
                self.nmcli.connection.down(UPLINK_CONNECTION, 0)
            logger.info('Uplink  : disabled')

    def device_present(self):
        return any(d.device == self.interface for d in self.nmcli.device())

    def status(self):
        status = {'interface': self.interface, 'present': False, 'updated': time.time(),
                  'error': self.last_error, 'request': self.last_request}
        try:
            for dev in self.nmcli.device():
                if dev.device == self.interface:
                    status['present'] = True
                    status['state'] = dev.state
            if self._profile_exists():
                profile = self.nmcli.connection.show(UPLINK_CONNECTION)
                status['ssid'] = profile.get('802-11-wireless.ssid')
                status['enabled'] = profile.get('connection.autoconnect') == 'yes'
            if status['present']:
                details = self.nmcli.device.show(self.interface)
                address = details.get('IP4.ADDRESS[1]')
                status['ip'] = address.split('/')[0] if address else None
        except Exception as error:
            status['error'] = f'cannot read the uplink state: {error}'
        return status

    def poll(self):
        """Apply a pending request, if any, and refresh status.json."""
        path = os.path.join(self.directory, REQUEST)
        try:
            with open(path, encoding='utf-8') as fh:
                request = json.load(fh)
        except FileNotFoundError:
            request = None
        except (OSError, ValueError) as error:
            request = {'malformed': str(error)}

        if request is not None:
            # Remove it first: it may hold a Wi-Fi password, and a request that
            # fails must not be retried every second.
            try:
                os.unlink(path)
            except OSError:
                pass
            problem = validate(request)
            self.last_request = request.get('id') if isinstance(request, dict) else None
            if problem:
                self.last_error = problem
                logger.warning('Uplink  : rejected request: %s', problem)
            else:
                try:
                    self.apply(request)
                    self.last_error = None
                except Exception as error:
                    self.last_error = f'nmcli failed: {error}'
                    logger.error('Uplink  : %s', self.last_error)

        _write_status(self.directory, self.status())

    def run(self, interval=3, refresh=STATUS_REFRESH):
        """Thread body. Does nothing on a stack without the shared volume.

        A request is picked up within `interval` seconds and answered at once.
        Without one, the status is only rebuilt every `refresh` seconds: it
        takes four nmcli processes, which is real CPU on a Pi Zero 2 W.
        """
        if not os.path.isdir(self.directory):
            logger.info('Uplink  : %s is not mounted, CTF uplink support is off', self.directory)
            return
        logger.info('Uplink  : watching %s for the CTF uplink on %s', self.directory, self.interface)
        self.keep_retrying()
        last_status = None
        while True:
            try:
                pending = os.path.exists(os.path.join(self.directory, REQUEST))
                if pending or last_status is None or time.monotonic() - last_status >= refresh:
                    self.poll()
                    last_status = time.monotonic()
            except Exception as error:
                logger.error('Uplink  : %s', error)
            time.sleep(interval)
