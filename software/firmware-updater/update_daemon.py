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
import socket
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

# OpenOCD telnet interaction constants
_OPENOCD_BANNER_DELAY = 0.3   # seconds to wait for the welcome banner
_SOCKET_RECV_TIMEOUT = 5      # per-recv timeout in seconds
_FLASH_TIMEOUT = 60           # maximum seconds to wait for flash to complete


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
    """Flash firmware via OpenOCD telnet interface (port 4444).

    Sends the ``program`` command to the running OpenOCD server so that
    the firmware file (accessible inside the stm32 container via the
    shared volume) is written to flash.
    """
    cmd = f"program {firmware_path} verify reset 0x08000000\n"
    logger.info("Connecting to OpenOCD at %s:%d", host, port)
    try:
        with socket.create_connection((host, port), timeout=30) as sock:
            # Use a short per-recv timeout so the loop stays responsive
            sock.settimeout(_SOCKET_RECV_TIMEOUT)

            # Discard OpenOCD welcome banner
            time.sleep(_OPENOCD_BANNER_DELAY)
            try:
                sock.recv(4096)
            except socket.timeout:
                pass

            sock.sendall(cmd.encode())
            logger.info("Sent flash command, waiting for OpenOCD...")

            output = b""
            deadline = time.monotonic() + _FLASH_TIMEOUT
            while time.monotonic() < deadline:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    output += chunk
                    if (
                        b"** Programming Finished **" in output
                        or b"verified" in output.lower()
                        or b"Error" in output
                    ):
                        break
                except socket.timeout:
                    # No data within 5 s – check overall deadline and retry
                    continue

            sock.sendall(b"exit\n")
            logger.debug("OpenOCD output: %s", output.decode(errors="replace"))

            if b"** Programming Finished **" in output or b"verified" in output.lower():
                logger.info("Flashing completed successfully")
                return True

            logger.error(
                "Flashing may have failed. OpenOCD output: %s",
                output.decode(errors="replace"),
            )
            return False

    except OSError as exc:
        logger.error("Could not connect to OpenOCD at %s:%d: %s", host, port, exc)
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
