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
