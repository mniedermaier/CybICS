"""
Challenge lifecycle orchestration for CTF environments.
"""
import json
import os
import re
import shlex
import subprocess
import time
import shutil
from datetime import datetime, timezone

from utils.config import (
    ACTIVE_CHALLENGE_FILE,
    COMPOSE_DIR,
    COMPOSE_FILE,
    REPO_ROOT,
    SCRIPTS_DIR,
)
from utils.logger import logger


class ChallengeLifecycleManager:
    """Start and stop challenge-specific environments."""

    def __init__(self, ctf_manager):
        self.ctf_manager = ctf_manager
        self.compose_dir = COMPOSE_DIR
        self.compose_file = COMPOSE_FILE
        self.scripts_dir = SCRIPTS_DIR
        self.state_file = ACTIVE_CHALLENGE_FILE
        self.compose_command = self._detect_compose_command()
        self.allowed_profiles = self._load_allowed_profiles()
        self._reconcile_state()

    def _utc_now(self):
        return datetime.now(timezone.utc).isoformat()

    def _load_allowed_profiles(self):
        """Parse compose profile names from the compose file."""
        profiles = set()
        if not os.path.exists(self.compose_file):
            logger.warning(f"Compose file not found for lifecycle manager: {self.compose_file}")
            return profiles

        in_services = False
        in_profiles = False
        current_service_indent = None
        profiles_indent = None
        service_pattern = re.compile(r"^(\s{2})([A-Za-z0-9][A-Za-z0-9._-]*):\s*$")
        profile_pattern = re.compile(r"^\s*-\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*$")

        with open(self.compose_file, "r", encoding="utf-8") as compose_file:
            for raw_line in compose_file:
                line = raw_line.rstrip("\n")
                stripped = line.strip()

                if not stripped or stripped.startswith("#"):
                    continue

                if not in_services:
                    if stripped == "services:":
                        in_services = True
                    continue

                if line and not line.startswith(" "):
                    break

                match = service_pattern.match(line)
                if match:
                    current_service_indent = len(match.group(1))
                    in_profiles = False
                    profiles_indent = None
                    continue

                current_indent = len(line) - len(line.lstrip(" "))
                if current_service_indent is not None and current_indent <= current_service_indent:
                    in_profiles = False
                    profiles_indent = None

                if stripped == "profiles:":
                    in_profiles = True
                    profiles_indent = current_indent
                    continue

                if not in_profiles:
                    continue

                if current_indent <= profiles_indent:
                    in_profiles = False
                    profiles_indent = None
                    continue

                profile_match = profile_pattern.match(line)
                if profile_match:
                    profiles.add(profile_match.group(1))

        logger.info(f"ChallengeLifecycleManager loaded {len(profiles)} allowed compose profiles")
        return profiles

    def _detect_compose_command(self):
        """Prefer `docker compose`, fall back to `docker-compose`."""
        docker_binary = shutil.which("docker")
        if docker_binary:
            try:
                result = subprocess.run(
                    [docker_binary, "compose", "version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if result.returncode == 0:
                    return [docker_binary, "compose"]
            except OSError:
                pass

        docker_compose_binary = shutil.which("docker-compose")
        if docker_compose_binary:
            return [docker_compose_binary]

        logger.warning("No docker compose command available inside landing container")
        return None

    def _default_state(self):
        return {
            "challenge_id": None,
            "status": "stopped",
            "last_error": None,
            "updated_at": self._utc_now(),
        }

    def _load_state(self):
        if not os.path.exists(self.state_file):
            return self._default_state()

        try:
            with open(self.state_file, "r", encoding="utf-8") as state_file:
                state = json.load(state_file)
                if not isinstance(state, dict):
                    return self._default_state()
                return {**self._default_state(), **state}
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(f"Could not load active challenge state: {exc}")
            return self._default_state()

    def _save_state(self, state):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        state["updated_at"] = self._utc_now()
        with open(self.state_file, "w", encoding="utf-8") as state_file:
            json.dump(state, state_file, indent=2)

    def _clear_state(self):
        self._save_state(self._default_state())

    def _reconcile_state(self):
        """Drop stale active state if the challenge or its lifecycle no longer exists."""
        state = self._load_state()
        challenge_id = state.get("challenge_id")
        if not challenge_id:
            return

        challenge, _ = self.ctf_manager.get_challenge(challenge_id)
        lifecycle = self._get_lifecycle(challenge)

        if not challenge or not lifecycle.get("enabled"):
            logger.warning(f"Removing stale lifecycle state for missing challenge: {challenge_id}")
            self._clear_state()

    def _get_lifecycle(self, challenge):
        if not challenge:
            return {}
        lifecycle = challenge.get("lifecycle") or {}
        return lifecycle if isinstance(lifecycle, dict) else {}

    def _get_challenge_lifecycle(self, challenge_id):
        challenge, _ = self.ctf_manager.get_challenge(challenge_id)
        if not challenge:
            return None, None
        return challenge, self._get_lifecycle(challenge)

    def _validate_profile(self, profile):
        if not profile:
            return
        if profile not in self.allowed_profiles:
            raise ValueError(f"Unknown compose profile: {profile}")

    def _get_compose_services(self, lifecycle):
        services = lifecycle.get("compose_services") or []
        if not isinstance(services, list):
            raise ValueError("compose_services must be a list")

        validated_services = []
        service_pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
        for service in services:
            if not isinstance(service, str) or not service_pattern.match(service):
                raise ValueError(f"Invalid compose service name: {service}")
            validated_services.append(service)

        if lifecycle.get("compose_profile") and not validated_services:
            raise ValueError("compose_services must be set when compose_profile is used")

        return validated_services

    def _resolve_script(self, script_command):
        if not script_command:
            return None

        script_parts = shlex.split(script_command)
        if not script_parts:
            return None

        script_name = script_parts[0]
        script_path = os.path.normpath(os.path.join(self.scripts_dir, script_name))
        if os.path.commonpath([self.scripts_dir, script_path]) != self.scripts_dir:
            raise ValueError("Script path must stay within the scripts directory")
        if not os.path.exists(script_path):
            raise ValueError(f"Lifecycle script does not exist: {script_name}")
        return script_path, script_parts[1:]

    def _get_script_runner(self, script_path):
        """Respect the script shebang instead of forcing /bin/sh for every script."""
        try:
            with open(script_path, "r", encoding="utf-8") as script_file:
                first_line = script_file.readline().strip()
        except OSError as exc:
            raise RuntimeError(f"Could not read lifecycle script: {exc}") from exc

        if not first_line.startswith("#!"):
            return ["/bin/sh"]

        runner = shlex.split(first_line[2:].strip())
        if not runner:
            return ["/bin/sh"]

        if os.path.basename(runner[0]) == "env" and len(runner) > 1:
            return runner

        if os.path.exists(runner[0]):
            return runner

        resolved_binary = shutil.which(runner[0])
        if resolved_binary:
            return [resolved_binary, *runner[1:]]

        raise RuntimeError(f"Lifecycle script interpreter not found: {' '.join(runner)}")

    def _run_compose(self, args):
        if not self.compose_command:
            raise RuntimeError("No docker compose command available inside landing container")

        command = [*self.compose_command, "-f", self.compose_file, *args]
        logger.info(f"Running compose command: {' '.join(command)}")
        result = subprocess.run(
            command,
            cwd=self.compose_dir,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            stderr = (result.stderr or result.stdout).strip()
            raise RuntimeError(stderr or "docker compose command failed")
        return result

    def _run_script(self, script_command, challenge_id, phase):
        resolved_script = self._resolve_script(script_command)
        if not resolved_script:
            return
        script_path, script_args = resolved_script
        script_runner = self._get_script_runner(script_path)

        env = os.environ.copy()
        env["CYBICS_CHALLENGE_ID"] = challenge_id
        env["CYBICS_LIFECYCLE_PHASE"] = phase

        logger.info(f"Running lifecycle script {script_path} for {challenge_id} ({phase})")
        result = subprocess.run(
            [*script_runner, script_path, *script_args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
            env=env,
        )
        if result.returncode != 0:
            stderr = (result.stderr or result.stdout).strip()
            raise RuntimeError(stderr or f"Lifecycle script failed: {os.path.basename(script_path)}")

    def _is_healthcheck_ready(self, healthcheck):
        if not healthcheck:
            return True

        check_type = healthcheck.get("type")
        target = self._expand_target(healthcheck.get("target", ""))

        if check_type == "command":
            command = healthcheck.get("command")
            if not command:
                raise ValueError("Command healthcheck requires a script command")

            env = os.environ.copy()
            env["CYBICS_LIFECYCLE_PHASE"] = "healthcheck"

            resolved_script = None
            try:
                resolved_script = self._resolve_script(command)
            except (AttributeError, ValueError):
                resolved_script = None

            if resolved_script:
                script_path, script_args = resolved_script
                script_runner = self._get_script_runner(script_path)
                run_args = {
                    "args": [*script_runner, script_path, *script_args],
                    "shell": False,
                }
            else:
                run_args = {
                    # Healthcheck commands are configured by trusted challenge config.
                    "args": command,
                    "shell": True,
                }

            result = subprocess.run(  # nosec B602
                run_args["args"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                env=env,
                shell=run_args["shell"],
            )
            if result.returncode != 0:
                error_output = (result.stderr or result.stdout).strip()
                raise RuntimeError(error_output or "Command healthcheck failed")
            return True

        raise ValueError(f"Unsupported healthcheck type: {check_type}")

    def _wait_for_healthcheck(self, healthcheck):
        if not healthcheck:
            return

        timeout_seconds = int(healthcheck.get("timeout_seconds", 30))
        deadline = time.time() + timeout_seconds
        last_error = None

        while time.time() < deadline:
            try:
                if self._is_healthcheck_ready(healthcheck):
                    return
            except Exception as exc:
                last_error = str(exc)

            time.sleep(1)

        raise RuntimeError(last_error or "Healthcheck timed out")

    def _expand_target(self, target):
        """Expand ${VAR} and ${VAR:-default} placeholders in config strings."""
        pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")

        def replace(match):
            env_name = match.group(1)
            default_value = match.group(2)
            return os.environ.get(env_name, default_value if default_value is not None else "")

        return pattern.sub(replace, target)

    def _build_state_payload(self, challenge_id, lifecycle, status, last_error=None):
        return {
            "challenge_id": challenge_id,
            "display_name": lifecycle.get("display_name"),
            "status": status,
            "last_error": last_error,
        }

    def get_status(self, challenge_id):
        challenge, lifecycle = self._get_challenge_lifecycle(challenge_id)
        if not challenge:
            return {"success": False, "message": "Challenge not found"}, 404

        if not lifecycle.get("enabled"):
            return {
                "success": True,
                "enabled": False,
                "challenge_id": challenge_id,
                "status": "unsupported",
                "message": "This challenge does not define a lifecycle.",
            }, 200

        state = self._load_state()
        if state.get("challenge_id") != challenge_id:
            return {
                "success": True,
                "enabled": True,
                "challenge_id": challenge_id,
                "status": "stopped",
                "message": "Challenge environment is stopped.",
                "display_name": lifecycle.get("display_name"),
            }, 200

        if state.get("status") == "starting" and lifecycle.get("healthcheck"):
            try:
                if self._is_healthcheck_ready(lifecycle.get("healthcheck")):
                    state = self._build_state_payload(challenge_id, lifecycle, "running")
                    self._save_state(state)
            except Exception:
                pass

        if state.get("status") == "running":
            try:
                self._wait_for_healthcheck(lifecycle.get("healthcheck"))
            except Exception as exc:
                state["status"] = "failed"
                state["last_error"] = str(exc)
                self._save_state(state)

        return {
            "success": True,
            "enabled": True,
            "challenge_id": challenge_id,
            "status": state.get("status", "stopped"),
            "message": state.get("last_error") or f"Challenge environment is {state.get('status', 'stopped')}.",
            "display_name": state.get("display_name") or lifecycle.get("display_name"),
            "last_error": state.get("last_error"),
        }, 200

    def start_challenge(self, challenge_id):
        challenge, lifecycle = self._get_challenge_lifecycle(challenge_id)
        if not challenge:
            return {"success": False, "message": "Challenge not found"}, 404
        if not lifecycle.get("enabled"):
            return {"success": False, "message": "Challenge lifecycle is not enabled"}, 400

        state = self._load_state()
        if state.get("challenge_id") == challenge_id and state.get("status") == "running":
            return {
                "success": True,
                "challenge_id": challenge_id,
                "enabled": True,
                "status": "running",
                "already_running": True,
                "message": "Challenge environment is already running.",
                "display_name": lifecycle.get("display_name"),
            }, 200

        try:
            if state.get("challenge_id") and state.get("challenge_id") != challenge_id:
                stop_result, stop_code = self.stop_challenge(state["challenge_id"], suppress_inactive_error=True)
                if stop_code >= 400 or not stop_result.get("success"):
                    raise RuntimeError(stop_result.get("message", "Failed to stop previously active challenge"))

            compose_profile = lifecycle.get("compose_profile")
            compose_services = self._get_compose_services(lifecycle)
            start_config = lifecycle.get("start") or {}
            self._validate_profile(compose_profile)
            self._resolve_script(start_config.get("script"))

            self._save_state(self._build_state_payload(challenge_id, lifecycle, "starting"))

            if compose_profile:
                self._run_compose(["--profile", compose_profile, "rm", "-f", "-s", *compose_services])
                self._run_compose(["--profile", compose_profile, "up", "-d", *compose_services])
            self._run_script(start_config.get("script"), challenge_id, "start")
            self._wait_for_healthcheck(lifecycle.get("healthcheck"))

            running_state = self._build_state_payload(challenge_id, lifecycle, "running")
            self._save_state(running_state)
            return {
                "success": True,
                "challenge_id": challenge_id,
                "enabled": True,
                "status": "running",
                "message": "Challenge environment started successfully.",
                "last_error": None,
                "display_name": lifecycle.get("display_name"),
            }, 200
        except Exception as exc:
            logger.error(f"Failed to start challenge lifecycle for {challenge_id}: {exc}", exc_info=True)
            failed_state = self._build_state_payload(challenge_id, lifecycle, "failed", str(exc))
            self._save_state(failed_state)
            return {
                "success": False,
                "challenge_id": challenge_id,
                "enabled": True,
                "status": "failed",
                "message": f"Failed to start challenge environment: {exc}",
                "last_error": str(exc),
                "display_name": lifecycle.get("display_name"),
            }, 500

    def stop_challenge(self, challenge_id, suppress_inactive_error=False):
        challenge, lifecycle = self._get_challenge_lifecycle(challenge_id)
        if not challenge:
            return {"success": False, "message": "Challenge not found"}, 404
        if not lifecycle.get("enabled"):
            return {"success": False, "message": "Challenge lifecycle is not enabled"}, 400

        state = self._load_state()
        if state.get("challenge_id") != challenge_id:
            if suppress_inactive_error:
                return {
                    "success": True,
                    "challenge_id": challenge_id,
                    "enabled": True,
                    "status": "stopped",
                    "already_stopped": True,
                    "environment_stopped": False,
                    "message": "Challenge environment is already stopped.",
                }, 200
            return {
                "success": True,
                "challenge_id": challenge_id,
                "enabled": True,
                "status": "stopped",
                "already_stopped": True,
                "environment_stopped": False,
                "message": "Challenge environment is already stopped.",
            }, 200

        try:
            compose_profile = lifecycle.get("compose_profile")
            compose_services = self._get_compose_services(lifecycle)
            stop_config = lifecycle.get("stop") or {}
            self._validate_profile(compose_profile)
            self._resolve_script(stop_config.get("script"))

            self._save_state(self._build_state_payload(challenge_id, lifecycle, "stopping"))

            self._run_script(stop_config.get("script"), challenge_id, "stop")
            if compose_profile:
                self._run_compose(["--profile", compose_profile, "stop", *compose_services])

            self._clear_state()
            return {
                "success": True,
                "challenge_id": challenge_id,
                "enabled": True,
                "status": "stopped",
                "environment_stopped": True,
                "message": "Challenge environment stopped successfully.",
                "last_error": None,
                "display_name": lifecycle.get("display_name"),
            }, 200
        except Exception as exc:
            logger.error(f"Failed to stop challenge lifecycle for {challenge_id}: {exc}", exc_info=True)
            failed_state = self._build_state_payload(challenge_id, lifecycle, "failed", str(exc))
            self._save_state(failed_state)
            return {
                "success": False,
                "challenge_id": challenge_id,
                "enabled": True,
                "status": "failed",
                "environment_stopped": False,
                "message": f"Failed to stop challenge environment: {exc}",
                "last_error": str(exc),
                "display_name": lifecycle.get("display_name"),
            }, 500
