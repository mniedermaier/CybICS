"""The board's uplink to a central CTF server, as hwio-raspberry manages it.

The landing page writes request.json into a directory shared with hwio;
software/hwio-raspberry/ctf_uplink.py applies it with nmcli and answers in
status.json. nmcli is passed in, so a fake stands in for NetworkManager here
and nothing needs a Pi or a running stack.
"""
import json
import os
from types import SimpleNamespace

import pytest

import ctf_uplink  # software/hwio-raspberry, on sys.path via conftest.py


class FakeNmcli:
    """Just enough of the nmcli package, recording every call."""

    def __init__(self, profile=True, dongle=True, active=False):
        self.calls = []
        self.profile = {'802-11-wireless.ssid': 'cybics-ctf', 'connection.autoconnect': 'no'} if profile else None
        self.dongle = dongle
        self.active = active
        self.fail = None
        outer = self

        class Connection:
            def __call__(self):
                conns = [SimpleNamespace(name='cybics', conn_type='wifi', device='wlan0')]
                if outer.profile is not None:
                    conns.append(SimpleNamespace(name=ctf_uplink.UPLINK_CONNECTION, conn_type='wifi',
                                                 device='ctfwlan0' if outer.active else '--'))
                return conns

            def add(self, conn_type, options, ifname, name, autoconnect):
                outer.calls.append(('add', conn_type, dict(options), ifname, name, autoconnect))
                outer.profile = {'802-11-wireless.ssid': options['wifi.ssid'],
                                 'connection.autoconnect': 'yes' if autoconnect else 'no'}

            def modify(self, name, options):
                if outer.fail:
                    raise RuntimeError(outer.fail)
                outer.calls.append(('modify', name, dict(options)))
                if 'wifi.ssid' in options:
                    outer.profile['802-11-wireless.ssid'] = options['wifi.ssid']
                if 'connection.autoconnect' in options:
                    outer.profile['connection.autoconnect'] = options['connection.autoconnect']

            def up(self, name, wait=None):
                outer.calls.append(('up', name))
                outer.active = True

            def down(self, name, wait=None):
                outer.calls.append(('down', name))
                outer.active = False

            def show(self, name, show_secrets=False):
                return dict(outer.profile)

        class Device:
            def __call__(self):
                devs = [SimpleNamespace(device='wlan0', device_type='wifi', state='connected', connection='cybics')]
                if outer.dongle:
                    devs.append(SimpleNamespace(device='ctfwlan0', device_type='wifi',
                                                state='connected' if outer.active else 'disconnected',
                                                connection=None))
                return devs

            def show(self, ifname, fields=None):
                return {'IP4.ADDRESS[1]': '10.42.0.17/24'} if outer.active else {}

        self.connection = Connection()
        self.device = Device()


@pytest.fixture
def shared(tmp_path):
    return tmp_path


def request(directory, payload):
    (directory / ctf_uplink.REQUEST).write_text(json.dumps(payload))


def status(directory):
    return json.loads((directory / ctf_uplink.STATUS).read_text())


def test_enabling_sets_the_network_and_connects(shared):
    nm = FakeNmcli()
    request(shared, {'enabled': True, 'ssid': 'event-wifi', 'psk': 'secret-pass', 'id': 1})
    ctf_uplink.Uplink(nm, str(shared)).poll()

    modify = next(c for c in nm.calls if c[0] == 'modify')
    assert modify[2]['wifi.ssid'] == 'event-wifi'
    assert modify[2]['wifi-sec.psk'] == 'secret-pass'
    assert modify[2]['connection.autoconnect'] == 'yes'
    # Pinned to the dongle, so NetworkManager never tries it on wlan0.
    assert modify[2]['connection.interface-name'] == 'ctfwlan0'
    assert ('up', ctf_uplink.UPLINK_CONNECTION) in nm.calls

    answer = status(shared)
    assert answer['present'] is True
    assert answer['ssid'] == 'event-wifi'
    assert answer['enabled'] is True
    assert answer['ip'] == '10.42.0.17'
    assert answer['error'] is None


def test_the_request_is_consumed_and_the_password_not_echoed(shared):
    """request.json holds the Wi-Fi password: it must not stay on the volume,
    and status.json must not repeat it."""
    request(shared, {'enabled': True, 'ssid': 'event-wifi', 'psk': 'secret-pass', 'id': 1})
    ctf_uplink.Uplink(FakeNmcli(), str(shared)).poll()
    assert not (shared / ctf_uplink.REQUEST).exists()
    assert 'secret-pass' not in (shared / ctf_uplink.STATUS).read_text()


def test_without_a_dongle_the_profile_is_armed_but_not_brought_up(shared):
    """autoconnect takes over once the adapter is plugged in."""
    nm = FakeNmcli(dongle=False)
    request(shared, {'enabled': True, 'ssid': 'event-wifi', 'psk': 'secret-pass'})
    ctf_uplink.Uplink(nm, str(shared)).poll()
    assert not any(c[0] == 'up' for c in nm.calls)
    assert nm.profile['connection.autoconnect'] == 'yes'
    assert status(shared)['present'] is False


def test_disabling_takes_the_uplink_down(shared):
    nm = FakeNmcli(active=True)
    request(shared, {'enabled': False})
    ctf_uplink.Uplink(nm, str(shared)).poll()
    assert ('modify', ctf_uplink.UPLINK_CONNECTION, {'connection.autoconnect': 'no'}) in nm.calls
    assert ('down', ctf_uplink.UPLINK_CONNECTION) in nm.calls
    assert status(shared)['enabled'] is False


def test_a_missing_profile_is_created_isolated(shared):
    """A device set up before the image shipped the profile still works, and
    the profile it gets never becomes the default route."""
    nm = FakeNmcli(profile=False)
    request(shared, {'enabled': True, 'ssid': 'event-wifi', 'psk': 'secret-pass'})
    ctf_uplink.Uplink(nm, str(shared)).poll()
    add = next(c for c in nm.calls if c[0] == 'add')
    assert add[3] == 'ctfwlan0' and add[4] == ctf_uplink.UPLINK_CONNECTION
    assert add[2]['ipv4.never-default'] == 'yes'
    assert add[5] is False


@pytest.mark.parametrize('payload, message', [
    ({'enabled': True, 'ssid': '', 'psk': 'secret-pass'}, 'network name'),
    ({'enabled': True, 'ssid': 'x' * 33, 'psk': 'secret-pass'}, 'network name'),
    ({'enabled': True, 'ssid': 'event-wifi', 'psk': 'short'}, 'password'),
    ({'enabled': True, 'ssid': 'event-wifi', 'psk': 'p' * 64}, 'password'),
    ({'enabled': 'yes'}, 'malformed'),
    (['not', 'a', 'dict'], 'malformed'),
])
def test_bad_requests_are_rejected_once(shared, payload, message):
    nm = FakeNmcli()
    request(shared, payload)
    uplink = ctf_uplink.Uplink(nm, str(shared))
    uplink.poll()
    assert nm.calls == []
    assert message in status(shared)['error']
    assert not (shared / ctf_uplink.REQUEST).exists()


def test_an_unparsable_request_is_dropped(shared):
    (shared / ctf_uplink.REQUEST).write_text('{half')
    ctf_uplink.Uplink(FakeNmcli(), str(shared)).poll()
    assert not (shared / ctf_uplink.REQUEST).exists()
    assert 'malformed' in status(shared)['error']


def test_an_nmcli_failure_is_reported_not_raised(shared):
    nm = FakeNmcli()
    nm.fail = 'Error: Connection activation failed'
    request(shared, {'enabled': True, 'ssid': 'event-wifi', 'psk': 'secret-pass'})
    ctf_uplink.Uplink(nm, str(shared)).poll()
    assert 'activation failed' in status(shared)['error']


def test_status_is_refreshed_without_a_request(shared):
    nm = FakeNmcli()
    ctf_uplink.Uplink(nm, str(shared)).poll()
    assert nm.calls == []
    assert status(shared)['present'] is True


def test_run_does_nothing_without_the_shared_volume(tmp_path):
    """On a stack whose compose file predates the uplink, the thread just ends."""
    nm = FakeNmcli()
    ctf_uplink.Uplink(nm, str(tmp_path / 'missing')).run(interval=0)
    assert nm.calls == []


@pytest.mark.parametrize('name, device, expected', [
    ('cybics-ctf-uplink', '--', True),
    ('cybics-ctf-something-else', '--', True),
    ('EventWifi', 'ctfwlan0', True),
    ('cybics-station', '--', False),
    ('MyHomeNetwork', 'wlan0', False),
])
def test_uplink_profiles_are_recognised(name, device, expected):
    conn = SimpleNamespace(name=name, conn_type='wifi', device=device)
    assert ctf_uplink.is_uplink_connection(conn) is expected


def test_the_shipped_keyfile_matches_the_fallback_profile():
    """ctf_uplink.PROFILE_OPTIONS recreates the image's keyfile when it is
    missing; the two must describe the same isolated profile."""
    keyfile = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'software', 'rpi-image', 'stage-cybics', '01-configure-system',
                           'files', 'cybics-ctf-uplink.nmconnection')
    sections, current = {}, None
    with open(keyfile, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('['):
                current = line.strip('[]')
                continue
            key, value = line.split('=', 1)
            sections.setdefault(current, {})[key] = value

    assert sections['connection']['id'] == ctf_uplink.UPLINK_CONNECTION
    assert sections['connection']['interface-name'] == ctf_uplink.UPLINK_INTERFACE
    assert sections['connection']['autoconnect'] == 'false'
    assert sections['ipv4']['never-default'] == 'true'
    assert sections['ipv6']['method'] == ctf_uplink.PROFILE_OPTIONS['ipv6.method']
    assert sections['wifi']['ssid'] == ctf_uplink.PROFILE_OPTIONS['wifi.ssid']
    assert sections['wifi-security']['psk'] == ctf_uplink.PROFILE_OPTIONS['wifi-sec.psk']
