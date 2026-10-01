"""Restart the CybICS containers from the settings page.

The scope comes from the compose project the landing container belongs to.
landing runs with host networking, so its hostname is the host's and cannot
be used to look the container up: the old code tried that, never found the
project, and fell back to restarting every container on the host. The
container ID is read from /proc/self/mountinfo instead, where Docker's bind
mounts of /etc/hostname, /etc/hosts and /etc/resolv.conf carry it. If the
project still cannot be determined, nothing is restarted.

landing restarts itself last, from a background thread, so the request that
asked for the restart is answered before its own container goes away. The
page cannot tell it is back by waiting for it to drop out first: Docker
starts the new process within the same second it kills the old one, faster
than the page polls. Each process gets a BOOT_ID instead, and the page
reloads when the ID changes.

Kept free of Flask so it can be tested without standing up the app.
"""
import logging
import re
import subprocess
import threading
import uuid

logger = logging.getLogger(__name__)

MOUNTINFO = "/proc/self/mountinfo"
PROJECT_LABEL = "com.docker.compose.project"
CONTAINER_ID_RE = re.compile(r"/containers/([0-9a-f]{64})/")

# One restart at a time; a second click while one runs is refused.
_running = threading.Lock()

# Identifies this landing process; changes when the container restarts.
BOOT_ID = uuid.uuid4().hex


class RestartError(Exception):
    """The restart was refused; the message is safe to show to the user."""


def own_container_id(mountinfo=MOUNTINFO):
    """Return this container's full ID, or None outside a container."""
    try:
        with open(mountinfo, encoding="utf-8") as fh:
            ids = set(CONTAINER_ID_RE.findall(fh.read()))
    except OSError:
        return None
    # More than one ID would mean another container's directory is mounted
    # in; guessing between them could pick the wrong project.
    return ids.pop() if len(ids) == 1 else None


def _docker(run, *args, timeout=10):
    result = run(["docker", *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RestartError(f"docker {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def plan_restart(run=subprocess.run, mountinfo=MOUNTINFO):
    """Work out what to restart.

    Returns (project, others, own): the compose project, the names of its
    running containers other than landing, and landing's own name, which
    restarts last. Raises RestartError if the project cannot be determined.
    """
    own_id = own_container_id(mountinfo)
    if not own_id:
        raise RestartError("Cannot identify the landing container; not restarting anything")
    project = _docker(run, "inspect", "--format",
                      '{{index .Config.Labels "%s"}}' % PROJECT_LABEL, own_id)
    if not project:
        raise RestartError("The landing container is not part of a compose project; "
                           "not restarting anything")
    listing = _docker(run, "ps", "--filter", f"label={PROJECT_LABEL}={project}",
                      "--format", "{{.ID}} {{.Names}}")
    others, own = [], None
    for line in listing.splitlines():
        short_id, _, name = line.partition(" ")
        # docker ps prints the 12-character short ID.
        if short_id and own_id.startswith(short_id):
            own = name
        elif name:
            others.append(name)
    if own is None:
        raise RestartError("The landing container is not in its own project listing; "
                           "not restarting anything")
    return project, others, own


def _restart_all(others, own, run):
    try:
        for name in others:
            try:
                _docker(run, "restart", name, timeout=90)
                logger.info("Restarted %s", name)
            except (RestartError, subprocess.TimeoutExpired) as error:
                logger.error("Failed to restart %s: %s", name, error)
        logger.info("Restarting %s (this container) last", own)
        # Docker carries out the restart even though this process is stopped
        # by it before the command returns.
        _docker(run, "restart", own, timeout=90)
    except Exception:
        logger.exception("Restart of %s did not complete", own)
    finally:
        _running.release()


def restart_status():
    """What the page polls while it waits for landing to come back."""
    return {"boot_id": BOOT_ID, "running": _running.locked()}


def start_restart(run=subprocess.run, mountinfo=MOUNTINFO):
    """Plan the restart and run it in the background.

    Returns the plan (project, others, own). Raises RestartError if it was
    refused, including while another restart is still running.
    """
    if not _running.acquire(blocking=False):
        raise RestartError("A restart is already in progress")
    try:
        project, others, own = plan_restart(run, mountinfo)
    except Exception:
        _running.release()
        raise
    logger.info("Restarting compose project %s: %s, then %s", project, others, own)
    threading.Thread(target=_restart_all, args=(others, own, run),
                     name="restart-containers", daemon=True).start()
    return project, others, own
