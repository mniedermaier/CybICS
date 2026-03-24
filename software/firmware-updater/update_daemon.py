#!/usr/bin/env python3
"""
CybICS Firmware Update Daemon

Polls an HTTP endpoint for STM32 firmware updates, verifies integrity
using a MAC, saves the firmware, and triggers flashing via OpenOCD telnet.

MAC scheme: MD5(secret_key || firmware_binary)
Intentionally vulnerable to Length Extension Attack for the CTF scenario.
"""

import hashlib
import logging
import os
import subprocess
import time

import requests
import yaml


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

CONFIG_PATH = os.environ.get(
    "CONFIG_PATH", "/opt/cybics/update-service/config.yaml"
)

_FLASH_SCRIPT = os.path.join(os.path.dirname(__file__), "flash_firmware.sh")
_FLASH_TIMEOUT = 120        # FLASH_TIMEOUT passed to the shell script (seconds)
_SCRIPT_TIMEOUT_BUFFER = 10  # extra seconds for subprocess overhead beyond the flash timeout


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_secret_key(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def verify_mac(firmware: bytes, mac_hex: str, secret: bytes) -> bool:
    """Verify MAC = MD5(secret || firmware).

    Intentionally vulnerable to Length Extension Attack because MD5 uses
    the Merkle-Damgård construction.
    """
    expected = hashlib.md5(secret + firmware).hexdigest()
    return expected == mac_hex


def save_firmware(firmware: bytes, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(firmware)
    logger.info("Saved firmware to %s (%d bytes)", path, len(firmware))


def flash_via_openocd(firmware_path: str, host: str, port: int) -> bool:
    """Flash firmware by delegating to flash_firmware.sh.

    Calls flash_firmware.sh (the firmware-updater counterpart to
    flash_if_needed.sh in the stm32 container) which pipes the OpenOCD
    ``program`` command to the running OpenOCD telnet server via ``nc``.
    """
    env = os.environ.copy()
    env["OPENOCD_HOST"] = host
    env["OPENOCD_TELNET_PORT"] = str(port)
    env["FLASH_TIMEOUT"] = str(_FLASH_TIMEOUT)
    logger.info("Flashing %s via OpenOCD at %s:%d", firmware_path, host, port)
    script_timeout = _FLASH_TIMEOUT + _SCRIPT_TIMEOUT_BUFFER
    try:
        result = subprocess.run(
            [_FLASH_SCRIPT, firmware_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=script_timeout,
        )
        output = (result.stdout + result.stderr).strip()
        logger.debug("flash_firmware.sh output:\n%s", output)
        if result.returncode == 0:
            logger.info("Flashing completed successfully")
            return True
        logger.error(
            "Flashing failed (exit %d):\n%s", result.returncode, output
        )
        return False
    except subprocess.TimeoutExpired:
        logger.error(
            "Flash script timed out after %d seconds", script_timeout
        )
        return False
    except OSError as exc:
        logger.error("Could not run flash script %s: %s", _FLASH_SCRIPT, exc)
        return False


def poll_for_update(config: dict, secret: bytes) -> bool:
    """Poll the update server for new firmware.

    Returns True if a firmware update was downloaded and flashed.
    """
    base_url = os.environ.get(
        "UPDATE_SERVER_URL", config["update_server"]["url"]
    )
    endpoint = config["update_server"]["endpoint"]
    url = f"{base_url}{endpoint}"
    logger.info("Polling: %s", url)

    try:
        resp = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as exc:
        logger.debug("Poll failed (no server): %s", exc)
        return False

    if resp.status_code == 404:
        logger.debug("No update available (404)")
        return False

    if resp.status_code != 200:
        logger.warning("Unexpected HTTP status: %d", resp.status_code)
        return False

    data = resp.json()
    version = data.get("version")
    meta_mac = data.get("mac")
    download_path = data.get("url")

    if not version or not download_path:
        logger.error("Malformed update metadata: %s", data)
        return False

    logger.info("Update available: version=%s", version)

    # Download firmware binary
    download_url = f"{base_url}{download_path}"
    try:
        fw_resp = requests.get(download_url, timeout=30)
    except requests.exceptions.RequestException as exc:
        logger.error("Failed to download firmware: %s", exc)
        return False

    if fw_resp.status_code != 200:
        logger.error("Firmware download failed with status %d", fw_resp.status_code)
        return False

    firmware = fw_resp.content
    # Header takes precedence over metadata MAC
    mac = fw_resp.headers.get("X-Firmware-MAC", meta_mac)

    if not mac:
        logger.error("No MAC provided for firmware – discarding")
        return False

    logger.info("Downloaded %d bytes, MAC: %s", len(firmware), mac)

    # Verify MAC
    if not verify_mac(firmware, mac, secret):
        logger.error("MAC verification FAILED – discarding firmware")
        return False

    logger.info("MAC verification passed")

    pending_path = config["firmware"]["pending"]
    save_firmware(firmware, pending_path)

    # Flash via OpenOCD
    openocd_host = os.environ.get(
        "OPENOCD_HOST", config["openocd"]["host"]
    )
    openocd_port = int(
        os.environ.get("OPENOCD_TELNET_PORT", config["openocd"]["telnet_port"])
    )

    if not flash_via_openocd(pending_path, openocd_host, openocd_port):
        logger.error("Flashing failed – keeping pending firmware for retry")
        return False

    # Promote pending → current
    current_path = config["firmware"]["current"]
    os.makedirs(os.path.dirname(current_path), exist_ok=True)
    os.replace(pending_path, current_path)
    logger.info("Firmware successfully updated to version %s", version)
    return True


def main() -> None:
    config = load_config(CONFIG_PATH)

    key_path = config["security"]["key_path"]
    try:
        secret = load_secret_key(key_path)
    except FileNotFoundError:
        logger.error("MAC secret key not found at %s", key_path)
        raise

    poll_interval = int(config["update_server"].get("poll_interval", 30))

    logger.info("CybICS Firmware Update Daemon started")
    logger.info(
        "Polling %s every %ds",
        config["update_server"]["url"],
        poll_interval,
    )

    while True:
        try:
            poll_for_update(config, secret)
        except (OSError, requests.RequestException, ValueError, yaml.YAMLError) as exc:
            logger.error("Unexpected error in poll cycle: %s", exc)
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
