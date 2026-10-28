"""
Defense check: close the PLC's side doors (defense_unused_protocols).

OpenPLC listens on six TCP ports. The plant uses two of them: Modbus on 502
(hwio, FUXA and the OPC-UA gateway) and the web interface on 8080 (the
engineers). The other four are side doors that earlier challenges walk
through:

* 102   S7comm (Snap7)        -- S7 Side Door, Stop Means Stop?
* 20000 DNP3 outstation       -- DNP3 Side Door
* 44818 EtherNet/IP           -- found by Service Scanning
* 8443  the REST API          -- The Forgotten API

The first three have a switch in OpenPLC's Settings page. Saving the page
writes the Settings table and stops the server at once (configure_runtime in
webserver.py), and the table keeps it off across a restart. The REST API has
no switch: webserver.py starts it unconditionally, so a firewall rule is the
only way to close it.

The check passes when

* the Settings table (read-only, sqlite mode=ro inside the PLC container) has
  snap7=false, Dnp3_port=disabled and Enip_port=disabled, and the PLC no
  longer LISTENs on 102, 20000 or 44818 (its own /proc/net/tcp{,6}). A
  firewall rule in front of a running server does not count: it hides the
  service, it does not remove it;
* port 8443 refuses or drops a TCP connection from this board (172.18.0.1,
  the landing page's host network) and from the attack shell (172.18.0.100).
  Only a connect is made, no TLS and no HTTP, so nothing is created;
* Modbus 502 and the web interface 8080 still LISTEN, and the plant still
  runs: the PLC's heartbeat output toggles as seen by hwio (its /api/state is
  filled from the PLC over Modbus, so this also proves the plant's own
  Modbus link works) or, where there is no hwio API (the board), read over
  Modbus from here.

Everything it does is a read or a TCP connect; it changes nothing.
"""
import socket
import subprocess
import time

import requests

from utils.config import PLC_HOST, PLC_MODBUS_PORT
from utils.logger import logger

SETTINGS_DB = "file:/CybICS/OpenPLC_v3/webserver/openplc.db?mode=ro"

# port -> (name, Settings key, value meaning "off")
SIDE_DOORS = {
    102: ("S7comm", "snap7", "false"),
    20000: ("DNP3", "Dnp3_port", "disabled"),
    44818: ("EtherNet/IP", "Enip_port", "disabled"),
}
REST_PORT = 8443
KEEP = {PLC_MODBUS_PORT: "Modbus", 8080: "web interface"}

HWIO_STATE = "http://172.18.0.2:8090/api/state"
HEARTBEAT_COIL = 0          # %QX0.0
HEARTBEAT_SAMPLE = 3.0      # the heartbeat toggles about once a second
PROBE_TIMEOUT = 3
DOCKER_TIMEOUT = 15


def _container(fragment):
    """Name of the running container whose name contains fragment, or None."""
    try:
        out = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                             capture_output=True, text=True, timeout=DOCKER_TIMEOUT).stdout
    except Exception as e:
        logger.error(f"unused_protocols: docker ps failed: {e}")
        return None
    names = [n for n in out.split() if fragment in n.lower()]
    return names[0] if names else None


def _exec(container, *command):
    result = subprocess.run(["docker", "exec", container, *command],
                            capture_output=True, text=True, timeout=DOCKER_TIMEOUT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
    return result.stdout


def listening_ports(proc_net_tcp):
    """TCP ports in LISTEN state (st 0A) in /proc/net/tcp or tcp6 text."""
    ports = set()
    for line in proc_net_tcp.splitlines():
        fields = line.split()
        if len(fields) > 3 and fields[3] == "0A" and ":" in fields[1]:
            try:
                ports.add(int(fields[1].rsplit(":", 1)[1], 16))
            except ValueError:
                continue
    return ports


def parse_settings(text):
    """{Key: Value} from sqlite3's default 'Key|Value' output."""
    settings = {}
    for line in text.splitlines():
        if "|" in line:
            key, value = line.split("|", 1)
            settings[key.strip()] = value.strip()
    return settings


def _tcp_open_here(port):
    try:
        with socket.create_connection((PLC_HOST, port), timeout=PROBE_TIMEOUT):
            return True
    except OSError:
        return False


_PROBE = ("import socket,sys\n"
          "s=socket.socket(); s.settimeout({t})\n"
          "sys.exit(0 if s.connect_ex(('{h}',{p}))==0 else 1)\n")


def _tcp_open_from(container, port):
    """True/False: does port answer a TCP connect from inside container?"""
    code = _PROBE.format(t=PROBE_TIMEOUT, h=PLC_HOST, p=port)
    result = subprocess.run(["docker", "exec", container, "python3", "-c", code],
                            capture_output=True, text=True, timeout=DOCKER_TIMEOUT)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
    return result.returncode == 0


def _sample(read):
    seen = set()
    deadline = time.monotonic() + HEARTBEAT_SAMPLE
    while True:
        seen.add(read())
        if len(seen) > 1 or time.monotonic() >= deadline:
            return len(seen) > 1
        time.sleep(0.2)


def _heartbeat_hwio():
    def read():
        r = requests.get(HWIO_STATE, timeout=2)
        r.raise_for_status()
        return bool(r.json()["heartbeat"])
    return _sample(read)


def _heartbeat_modbus():
    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient(PLC_HOST, port=PLC_MODBUS_PORT, timeout=2, retries=0)
    try:
        if not client.connect():
            raise ConnectionError("Modbus connect failed")

        def read():
            result = client.read_coils(HEARTBEAT_COIL, count=1, slave=1)
            if result.isError():
                raise ConnectionError("Modbus error response")
            return bool(result.bits[0])
        return _sample(read)
    finally:
        client.close()


def plant_running():
    """(running, how it was seen)."""
    try:
        requests.get(HWIO_STATE, timeout=2).raise_for_status()
    except Exception:
        return _heartbeat_modbus(), "over Modbus from this board"
    return _heartbeat_hwio(), "by the plant simulation (hwio), which reads it over Modbus"


def _side_door_check(port, settings, listening):
    name, key, off = SIDE_DOORS[port]
    value = settings.get(key)
    switched_off = value == off
    listens = port in listening
    passed = switched_off and not listens
    if passed:
        detail = f"Switched off in Settings ({key} = {off}) and nothing listens on {port}"
    elif listens and switched_off:
        detail = (f"Settings say off, but the PLC still listens on {port}. Save the "
                  "Settings page so OpenPLC applies it")
    elif listens:
        detail = (f"{name} is still enabled ({key} = {value}) and listening on {port}. "
                  "A firewall rule would only hide it: switch it off in OpenPLC's Settings")
    else:
        detail = (f"Nothing listens on {port}, but the Settings table still enables it "
                  f"({key} = {value}): it comes back with the next PLC restart")
    return {"name": f"{name} (port {port}) switched off", "passed": passed, "detail": detail}


def verify():
    checks = []
    plc = _container("openplc")
    if not plc:
        return {"success": False, "message": "OpenPLC container not found",
                "checks": [{"name": "OpenPLC container found", "passed": False,
                            "detail": "No running container with 'openplc' in its name"}]}

    try:
        listening = listening_ports(_exec(plc, "cat", "/proc/net/tcp", "/proc/net/tcp6"))
        settings = parse_settings(_exec(plc, "sqlite3", SETTINGS_DB,
                                        "SELECT Key, Value FROM Settings"))
    except Exception as e:
        logger.error(f"unused_protocols: cannot read the PLC's state: {e}")
        return {"success": False, "message": "Cannot read OpenPLC's settings or listeners.",
                "checks": [{"name": "PLC state readable", "passed": False,
                            "detail": "docker exec into the OpenPLC container failed"}]}

    for port in SIDE_DOORS:
        checks.append(_side_door_check(port, settings, listening))

    # The REST API: no switch, so it must be unreachable from the network.
    try:
        from_board = _tcp_open_here(REST_PORT)
        attacker = _container("attack-shell")
        from_attacker = _tcp_open_from(attacker, REST_PORT) if attacker else None
        open_from = [w for w, is_open in (("this board (172.18.0.1)", from_board),
                                          ("the attack shell (172.18.0.100)", from_attacker))
                     if is_open]
        closed = not open_from
        if closed:
            detail = (f"Port {REST_PORT} refuses connections from this board"
                      + (" and from the attack shell" if attacker else "")
                      + (". The API itself still runs inside the PLC: the firewall rule is "
                         "what keeps it closed" if REST_PORT in listening else ""))
        else:
            detail = (f"Port {REST_PORT} still accepts connections from "
                      + " and ".join(open_from) + ". OpenPLC has no switch for its REST "
                      "API: block the port with a firewall rule on the PLC")
        checks.append({"name": f"REST API (port {REST_PORT}) unreachable",
                       "passed": closed, "detail": detail})
    except Exception as e:
        logger.error(f"unused_protocols: REST probe failed: {e}")
        checks.append({"name": f"REST API (port {REST_PORT}) unreachable", "passed": False,
                       "detail": "Could not probe the port, see the landing log"})

    missing = [f"{name} ({port})" for port, name in KEEP.items() if port not in listening]
    checks.append({
        "name": "Modbus and the web interface still on",
        "passed": not missing,
        "detail": "The PLC listens on 502 (Modbus) and 8080 (web interface)" if not missing
        else "Switched off too: " + ", ".join(missing) + ". hwio, FUXA and the OPC-UA "
             "gateway need Modbus, the engineers the web interface",
    })

    try:
        running, how = plant_running()
        checks.append({
            "name": "Plant still running",
            "passed": running,
            "detail": f"The PLC's heartbeat output toggles, seen {how}" if running
            else f"The PLC's heartbeat output did not change for {HEARTBEAT_SAMPLE:.0f} s, "
                 f"seen {how}. Is the PLC still running, and can hwio reach port 502?",
        })
    except Exception as e:
        logger.error(f"unused_protocols: cannot read the heartbeat: {e}")
        checks.append({"name": "Plant still running", "passed": False,
                       "detail": "Cannot read the PLC's heartbeat through hwio or over Modbus"})

    success = all(c["passed"] for c in checks)
    message = ("Only Modbus and the web interface are left: the S7, DNP3, EtherNet/IP and "
               "REST side doors are closed and the plant runs on. Undo it (README, "
               "'Undoing it') before you play the side-door challenges again."
               if success else
               "Not all side doors are closed yet, or the plant lost something it needs.")
    return {"success": success, "message": message, "checks": checks}
