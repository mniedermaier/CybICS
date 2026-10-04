"""Unit tests for the settings page's "Restart All Containers" scope.

software/landing/utils/restart.py decides which containers the button
restarts. The landing container runs with host networking, so the old code's
hostname lookup never found it, fell back to `docker ps` without a filter and
restarted every container on the host. These tests pin the scope: only the
landing container's own compose project, landing itself last, and nothing at
all when the project cannot be determined.

docker is replaced by a fake, so no container is touched and no stack is needed.
"""
import os
import sys
import threading
from types import SimpleNamespace

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")

if not os.path.exists(os.path.join(LANDING, "utils", "restart.py")):
    pytest.skip("landing restart module not present", allow_module_level=True)

sys.path.insert(0, LANDING)
from utils import restart  # noqa: E402

OWN_ID = "8ebb7fd658db" + "f" * 52
OTHER_ID = "a1b2c3d4e5f6" + "0" * 52


def mountinfo(tmp_path, *ids):
    lines = [f"{n} 1 0:1 /var/lib/docker/containers/{cid}/hostname /etc/hostname rw - ext4 /dev/sda1 rw"
             for n, cid in enumerate(ids)]
    lines.append("30 1 0:2 / /proc rw - proc proc rw")
    path = tmp_path / "mountinfo"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


class FakeDocker:
    """Answers docker inspect/ps/restart like a host running two projects."""

    def __init__(self, project="virtual", fail_restart=()):
        self.project = project
        self.fail_restart = set(fail_restart)
        self.restarted = []
        self.done = threading.Event()

    def __call__(self, cmd, **_kwargs):
        assert cmd[0] == "docker"
        verb = cmd[1]
        if verb == "inspect":
            assert cmd[-1] == OWN_ID
            return SimpleNamespace(returncode=0, stdout=self.project + "\n", stderr="")
        if verb == "ps":
            # The filter is what keeps other projects out; a missing one
            # would list cybics-ctf and everything else on the host.
            assert f"label=com.docker.compose.project={self.project}" in cmd
            rows = [f"{OWN_ID[:12]} virtual-landing-1",
                    "111111111111 virtual-openplc-1",
                    "222222222222 virtual-hwio-1"]
            return SimpleNamespace(returncode=0, stdout="\n".join(rows) + "\n", stderr="")
        if verb == "restart":
            name = cmd[2]
            self.restarted.append(name)
            if name == "virtual-landing-1":
                self.done.set()
            if name in self.fail_restart:
                return SimpleNamespace(returncode=1, stdout="", stderr="boom")
            return SimpleNamespace(returncode=0, stdout=name, stderr="")
        raise AssertionError(f"unexpected docker call {cmd}")


def test_own_container_id_from_mountinfo(tmp_path):
    assert restart.own_container_id(mountinfo(tmp_path, OWN_ID, OWN_ID)) == OWN_ID


def test_own_container_id_outside_a_container(tmp_path):
    assert restart.own_container_id(mountinfo(tmp_path)) is None
    assert restart.own_container_id(str(tmp_path / "missing")) is None


def test_own_container_id_refuses_to_guess(tmp_path):
    assert restart.own_container_id(mountinfo(tmp_path, OWN_ID, OTHER_ID)) is None


def test_plan_is_limited_to_the_own_project_with_landing_last(tmp_path):
    project, others, own = restart.plan_restart(FakeDocker(), mountinfo(tmp_path, OWN_ID))
    assert project == "virtual"
    assert others == ["virtual-openplc-1", "virtual-hwio-1"]
    assert own == "virtual-landing-1"


def test_no_container_id_restarts_nothing(tmp_path):
    docker = FakeDocker()
    with pytest.raises(restart.RestartError):
        restart.plan_restart(docker, mountinfo(tmp_path))
    assert docker.restarted == []


def test_no_compose_project_restarts_nothing(tmp_path):
    docker = FakeDocker(project="")
    with pytest.raises(restart.RestartError):
        restart.plan_restart(docker, mountinfo(tmp_path, OWN_ID))
    assert docker.restarted == []


def test_restart_runs_landing_last_and_survives_a_failure(tmp_path):
    docker = FakeDocker(fail_restart={"virtual-openplc-1"})
    restart.start_restart(docker, mountinfo(tmp_path, OWN_ID))
    assert docker.done.wait(5)
    assert docker.restarted == ["virtual-openplc-1", "virtual-hwio-1", "virtual-landing-1"]


def test_second_restart_is_refused_while_one_runs(tmp_path):
    gate = threading.Event()
    docker = FakeDocker()
    original = docker.__call__

    def slow(cmd, **kwargs):
        if cmd[1] == "restart":
            gate.wait(5)
        return original(cmd, **kwargs)

    path = mountinfo(tmp_path, OWN_ID)
    restart.start_restart(slow, path)
    try:
        with pytest.raises(restart.RestartError, match="already in progress"):
            restart.start_restart(slow, path)
    finally:
        gate.set()
    assert docker.done.wait(5)
    # The lock is released once the first restart is through.
    for _ in range(50):
        if not restart._running.locked():
            break
        threading.Event().wait(0.05)
    assert not restart._running.locked()


def test_status_reports_this_process_and_whether_a_restart_runs():
    status = restart.restart_status()
    assert status == {"boot_id": restart.BOOT_ID, "running": False}
    assert len(restart.BOOT_ID) == 32


def test_log_download_covers_the_same_containers(tmp_path):
    project, names = restart.project_containers(FakeDocker(), mountinfo(tmp_path, OWN_ID))
    assert project == "virtual"
    assert names == ["virtual-openplc-1", "virtual-hwio-1", "virtual-landing-1"]


# ---------- one service, for a CybICS-mgmt restart job ----------

def _wait_until_idle():
    for _ in range(100):
        if not restart._running.locked():
            return
        threading.Event().wait(0.05)
    raise AssertionError("the restart lock was never released")


@pytest.mark.parametrize("service, expected", [
    ("virtual-openplc-1", "virtual-openplc-1"),     # the name landing reports to CybICS-mgmt
    ("openplc", "virtual-openplc-1"),               # the compose service
    ("hwio", "virtual-hwio-1"),
    ("landing", "virtual-landing-1"),
    ("sshd", None),
    ("virtual", None),
    ("open", None),
    ("cybics-ctf-server-1", None),                  # another project's container
    ("", None),
    (None, None),
])
def test_resolve_service(service, expected):
    names = ["virtual-openplc-1", "virtual-hwio-1", "virtual-landing-1"]
    assert restart.resolve_service(service, "virtual", names) == expected


def test_restart_one_service(tmp_path):
    docker = FakeDocker()
    assert restart.restart_service("openplc", docker, mountinfo(tmp_path, OWN_ID)) == \
        "restarted virtual-openplc-1"
    assert docker.restarted == ["virtual-openplc-1"]
    assert not restart._running.locked()


def test_restart_of_an_unknown_service_is_refused(tmp_path):
    docker = FakeDocker()
    with pytest.raises(restart.RestartError, match="not a running container"):
        restart.restart_service("sshd", docker, mountinfo(tmp_path, OWN_ID))
    assert docker.restarted == []
    assert not restart._running.locked()


def test_a_failed_service_restart_releases_the_lock(tmp_path):
    docker = FakeDocker(fail_restart={"virtual-openplc-1"})
    with pytest.raises(restart.RestartError):
        restart.restart_service("openplc", docker, mountinfo(tmp_path, OWN_ID))
    assert not restart._running.locked()


def test_restarting_landing_alone_runs_in_the_background(tmp_path):
    docker = FakeDocker()
    assert restart.restart_service("landing", docker, mountinfo(tmp_path, OWN_ID)) == \
        "restarting virtual-landing-1"
    assert docker.done.wait(5)
    assert docker.restarted == ["virtual-landing-1"]
    _wait_until_idle()


def test_no_project_restarts_no_service(tmp_path):
    docker = FakeDocker()
    with pytest.raises(restart.RestartError):
        restart.restart_service("openplc", docker, mountinfo(tmp_path))
    assert docker.restarted == []


class LoggingDocker(FakeDocker):
    """Also answers the image lookup and the logs of the log bundle."""

    def __call__(self, cmd, **kwargs):
        if cmd[1] == "inspect" and cmd[-1] != OWN_ID:
            return SimpleNamespace(returncode=0, stdout=f"mniedermaier1337/{cmd[-1]}:1.2.4\n", stderr="")
        if cmd[1] == "logs":
            return SimpleNamespace(returncode=0, stdout=f"log of {cmd[-1]}\n",
                                   stderr="warning\n" if cmd[-1] == "virtual-hwio-1" else "")
        return super().__call__(cmd, **kwargs)


def test_logs_bundle_is_the_text_of_the_download(tmp_path):
    text = restart.logs_bundle(LoggingDocker(), mountinfo(tmp_path, OWN_ID))
    assert text.startswith("CybICS Docker Logs\n")
    assert "Containers: 3\n" in text
    assert "virtual-openplc-1: mniedermaier1337/virtual-openplc-1:1.2.4" in text
    for name in ("virtual-openplc-1", "virtual-hwio-1", "virtual-landing-1"):
        assert f"Container: {name}\n" in text and f"log of {name}" in text
    assert "STDERR:\nwarning" in text


def test_logs_bundle_needs_the_project(tmp_path):
    with pytest.raises(restart.RestartError):
        restart.logs_bundle(LoggingDocker(), mountinfo(tmp_path))


# ---------- what a browser is told ----------

def test_refusals_carry_a_reason_with_a_fixed_public_message(tmp_path):
    def failing(cmd, **_kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="permission denied on /var/run/docker.sock")

    cases = [
        (lambda: restart.plan_restart(failing, mountinfo(tmp_path, OWN_ID)), "docker_failed"),
        (lambda: restart.plan_restart(FakeDocker(), str(tmp_path / "missing")), "no_container"),
        (lambda: restart.plan_restart(FakeDocker(project=""), mountinfo(tmp_path, OWN_ID)), "no_project"),
        (lambda: restart.restart_service("nope", FakeDocker(), mountinfo(tmp_path, OWN_ID)), "unknown_service"),
    ]
    for call, reason in cases:
        with pytest.raises(restart.RestartError) as err:
            call()
        assert err.value.reason == reason
        assert restart.public_message(err.value) == restart.PUBLIC_MESSAGES[reason]
    assert "docker.sock" not in restart.public_message(restart.RestartError("x: docker.sock", "docker_failed"))


def test_public_messages_never_carry_the_detail():
    error = restart.RestartError("'x' is not a running container of my-secret-project", "unknown_service")
    assert "my-secret-project" not in restart.public_message(error)
    assert "my-secret-project" in str(error)        # still in the log
    assert restart.public_message(ValueError("boom")) == restart.PUBLIC_MESSAGES["docker_failed"]
    assert restart.public_message(restart.RestartError("x", "made-up")) == restart.PUBLIC_MESSAGES["docker_failed"]
