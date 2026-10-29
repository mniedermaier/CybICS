"""
TCP reachability probes for the firewall verify checks.

A firewall rule is only as good as what it lets through, so the Modbus
Firewall and Network Segmentation checks do not read the rule text alone:
they try the connection the rule is meant to stop, from the host it is meant
to stop, and the connections the plant needs, from the hosts that need them.

A probe is one TCP connect with a timeout, made from this board or from
inside a container with `docker exec` (python3, or node in the FUXA image,
which has no python). No data is sent, so nothing is created or changed.
Probes run only while a student clicks Verify.
"""
import socket
import subprocess

from utils.logger import logger

PROBE_TIMEOUT = 3
DOCKER_TIMEOUT = 15

_PYTHON = ("import socket,sys\n"
           "s=socket.socket(); s.settimeout({t})\n"
           "sys.exit(0 if s.connect_ex(('{h}',{p}))==0 else 1)\n")
_NODE = ("const s=require('net').connect({{host:'{h}',port:{p}}});"
         "s.setTimeout({t}000,()=>process.exit(1));"
         "s.on('connect',()=>process.exit(0));s.on('error',()=>process.exit(1));")


def container(fragment):
    """Name of the running container whose name contains fragment, or None."""
    try:
        out = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                             capture_output=True, text=True, timeout=DOCKER_TIMEOUT).stdout
    except Exception as e:
        logger.error(f"reach: docker ps failed: {e}")
        return None
    names = [n for n in out.split() if fragment in n.lower()]
    return names[0] if names else None


def tcp_open_here(host, port):
    """True if a TCP connect from this board to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=PROBE_TIMEOUT):
            return True
    except OSError:
        return False


def tcp_open_from(name, host, port, runtime="python3"):
    """True/False: does host:port answer a TCP connect from inside container name?

    Raises RuntimeError when the probe itself could not run.
    """
    if runtime == "node":
        command = ["node", "-e", _NODE.format(t=PROBE_TIMEOUT, h=host, p=port)]
    else:
        command = ["python3", "-c", _PYTHON.format(t=PROBE_TIMEOUT, h=host, p=port)]
    result = subprocess.run(["docker", "exec", name, *command],
                            capture_output=True, text=True, timeout=DOCKER_TIMEOUT)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
    return result.returncode == 0
