"""Find and restart the CybICS containers for the settings page.

The scope of "Restart All Containers", of restarting a single service (a
CybICS-mgmt job) and of the log download comes from the compose project the
landing container belongs to.
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
from datetime import datetime

logger = logging.getLogger(__name__)

MOUNTINFO = "/proc/self/mountinfo"
PROJECT_LABEL = "com.docker.compose.project"
CONTAINER_ID_RE = re.compile(r"/containers/([0-9a-f]{64})/")

# One restart at a time; a second click while one runs is refused.
_running = threading.Lock()

# Identifies this landing process; changes when the container restarts.
BOOT_ID = uuid.uuid4().hex


class RestartError(Exception):
    """The restart was refused.

    The message is for the log (and a CybICS-mgmt job result, which only the
    organiser sees): it may name the compose project or carry docker's
    error output. `reason` picks the fixed text a browser gets, see
    public_message().
    """

    def __init__(self, message, reason="docker_failed"):
        super().__init__(message)
        self.reason = reason


# What a browser is told for each reason. Fixed strings only: nothing of the
# exception (project names, docker output) reaches an HTTP response.
PUBLIC_MESSAGES = {
    "busy": "A restart is already in progress.",
    "no_container": "Cannot identify the landing container, so nothing was restarted.",
    "no_project": "The landing container is not part of a compose project, so nothing was restarted.",
    "unknown_service": "That is not a running container of this CybICS installation.",
    "docker_failed": "Docker refused the request; the landing log has the details.",
}


def public_message(error):
    """The fixed text for a RestartError that may be shown in the browser."""
    return PUBLIC_MESSAGES.get(getattr(error, "reason", None), PUBLIC_MESSAGES["docker_failed"])


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
        raise RestartError("Cannot identify the landing container; not restarting anything", "no_container")
    project = _docker(run, "inspect", "--format",
                      '{{index .Config.Labels "%s"}}' % PROJECT_LABEL, own_id)
    if not project:
        raise RestartError("The landing container is not part of a compose project; "
                           "not restarting anything", "no_project")
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
                           "not restarting anything", "no_container")
    return project, others, own


def project_containers(run=subprocess.run, mountinfo=MOUNTINFO):
    """The running containers of landing's compose project, landing last.

    Returns (project, names). Raises RestartError like plan_restart().
    """
    project, others, own = plan_restart(run, mountinfo)
    return project, others + [own]


def _netns_followers(names, run):
    """Map each container to the containers that share its network namespace.

    A container started with network_mode "service:x" joins x's namespace by
    container ID.  When x restarts, it gets a new namespace and the follower
    is left with loopback only until it restarts too; in the virtual stack
    that is the Kali desktop, which shares the attack shell's 172.18.0.100.
    Best effort: if docker inspect fails, nothing has followers.
    """
    if not names:
        return {}
    try:
        rows = _docker(run, "inspect", "--format",
                       "{{.Name}} {{.Id}} {{.HostConfig.NetworkMode}}", *names)
    except (RestartError, subprocess.TimeoutExpired) as error:
        logger.warning("Cannot read the containers' network modes: %s", error)
        return {}
    by_id, modes = {}, {}
    for row in rows.splitlines():
        parts = row.split()
        if len(parts) == 3:
            name = parts[0].lstrip("/")
            by_id[parts[1]] = name
            modes[name] = parts[2]
    followers = {}
    for name, mode in modes.items():
        owner = by_id.get(mode.removeprefix("container:")) if mode.startswith("container:") else None
        if owner:
            followers.setdefault(owner, []).append(name)
    return followers


def _owners_first(names, run):
    """`names` with every container after the one whose namespace it shares."""
    followers = _netns_followers(names, run)
    later = {f for fs in followers.values() for f in fs}
    ordered = []
    for name in names:
        if name not in later:
            ordered.append(name)
            ordered.extend(f for f in followers.get(name, []) if f in names)
    return ordered + [name for name in names if name not in ordered]


def _restart_all(others, own, run):
    try:
        for name in _owners_first(others, run):
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
        raise RestartError("A restart is already in progress", "busy")
    try:
        project, others, own = plan_restart(run, mountinfo)
    except Exception:
        _running.release()
        raise
    logger.info("Restarting compose project %s: %s, then %s", project, others, own)
    threading.Thread(target=_restart_all, args=(others, own, run),
                     name="restart-containers", daemon=True).start()
    return project, others, own


def resolve_service(service, project, names):
    """The container of `names` that `service` means, or None.

    `service` is either a container's full name, as the landing page reports
    it to CybICS-mgmt, or a compose service name: compose names containers
    <project>-<service>-<n>. Anything else, including a container of another
    project, matches nothing.
    """
    if not isinstance(service, str) or not service:
        return None
    if service in names:
        return service
    pattern = re.compile(re.escape(f"{project}-{service}-") + r"\d+")
    matches = [name for name in names if pattern.fullmatch(name)]
    return matches[0] if len(matches) == 1 else None


def restart_service(service, run=subprocess.run, mountinfo=MOUNTINFO):
    """Restart one container of landing's compose project.

    Returns a short result text. Raises RestartError if `service` is not a
    running container of the project, or while a full restart runs. landing
    itself restarts from a background thread, like in start_restart().
    """
    project, others, own = plan_restart(run, mountinfo)
    name = resolve_service(service, project, others + [own])
    if name is None:
        raise RestartError(f"{service!r} is not a running container of {project}", "unknown_service")
    if not _running.acquire(blocking=False):
        raise RestartError("A restart is already in progress", "busy")
    if name == own:
        logger.info("Restarting %s (this container)", own)
        threading.Thread(target=_restart_all, args=([], own, run),
                         name="restart-containers", daemon=True).start()
        return f"restarting {own}"
    try:
        _docker(run, "restart", name, timeout=90)
        logger.info("Restarted %s", name)
        # Without this the containers sharing its namespace lose the network.
        followers = _netns_followers(others, run).get(name, [])
        for follower in followers:
            _docker(run, "restart", follower, timeout=90)
            logger.info("Restarted %s, which shares %s's network", follower, name)
    finally:
        _running.release()
    return " and ".join([f"restarted {name}"] + followers)


# Lines of each container's log in the bundle. The bundle is built in
# landing's memory, 64 MB on a board, and one container's full log once was
# 225 MB: hwio's, while OpenPLC was down. Landing was OOM-killed building it.
LOG_TAIL_LINES = 2000


def logs_bundle(run=subprocess.run, mountinfo=MOUNTINFO):
    """The text of Settings -> Download logs: the end of every project
    container's log.

    Raises RestartError if the project cannot be determined, and
    subprocess.TimeoutExpired if docker hangs.
    """
    project, containers = project_containers(run, mountinfo)
    versions = {}
    for container in containers:
        result = run(["docker", "inspect", "--format", "{{.Config.Image}}", container],
                     capture_output=True, text=True, timeout=5)
        versions[container] = result.stdout.strip() if result.returncode == 0 else "unknown"
    parts = []
    for container in containers:
        # errors="replace": a log file damaged by a power cut holds bytes
        # that are not UTF-8, and one such line must not fail the download.
        result = run(["docker", "logs", "--timestamps", "--tail", str(LOG_TAIL_LINES), container],
                     capture_output=True, text=True, errors="replace", timeout=30)
        parts.append(f"{'=' * 80}\nContainer: {container}\n{'=' * 80}\n{result.stdout}")
        if result.stderr:
            parts.append(f"\nSTDERR:\n{result.stderr}")
        parts.append("\n\n")
    head = [
        "CybICS Docker Logs",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Containers: {len(containers)}",
        f"Last {LOG_TAIL_LINES} lines of each container's log",
        "=" * 80, "",
        "CONTAINER VERSIONS",
        "=" * 80,
        *(f"{name}: {image}" for name, image in sorted(versions.items())),
        "=" * 80, "", "",
    ]
    return "\n".join(head) + "\n".join(parts)
