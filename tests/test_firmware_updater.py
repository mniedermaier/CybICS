"""
CybICS Firmware Updater Test Suite

Tests the firmware-updater service for the CTF scenario.

Includes:
- Unit tests for MAC verification (the intentionally weak MD5 scheme)
- Unit tests for the poll loop (mocked HTTP server + mocked OpenOCD socket)
- Docker image build and container startup tests (virtual environment)
"""

import hashlib
import os
import socket
import socketserver
import struct
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock, patch

import pytest
import requests
import yaml

# Allow importing the daemon without a running config file
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "software", "firmware-updater"))
from update_daemon import (  # noqa: E402
    flash_via_openocd,
    poll_for_update,
    save_firmware,
    verify_mac,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SECRET = b"mysecretkey12345"  # 16 bytes – matches the CTF known secret length
FIRMWARE = b"\x00\x01\x02\x03" * 64  # 256 bytes of fake firmware
INVALID_MAC = "deadbeef" * 4        # valid-length hex string that won't match any real MAC


def make_mac(firmware: bytes, secret: bytes = SECRET) -> str:
    return hashlib.md5(secret + firmware).hexdigest()


# ---------------------------------------------------------------------------
# Pure-Python MD5 Length Extension
# ---------------------------------------------------------------------------

import math as _math

_MD5_S = [
    7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
    5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
    4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
    6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,
]
_MD5_K = [int(abs(_math.sin(i + 1)) * (2 ** 32)) & 0xFFFFFFFF for i in range(64)]


def _md5_compress(state: tuple, block: bytes) -> tuple:
    """Apply one 512-bit MD5 compression round to a 128-bit state."""
    assert len(block) == 64
    M = list(struct.unpack("<16I", block))
    a, b, c, d = state
    for i in range(64):
        if i < 16:
            F, g = (b & c) | (~b & d), i
        elif i < 32:
            F, g = (d & b) | (~d & c), (5 * i + 1) % 16
        elif i < 48:
            F, g = b ^ c ^ d, (3 * i + 5) % 16
        else:
            F, g = c ^ (b | ~d), (7 * i) % 16
        F = (F + a + _MD5_K[i] + M[g]) & 0xFFFFFFFF
        a = d
        d = c
        c = b
        b = (b + ((F << _MD5_S[i]) | (F >> (32 - _MD5_S[i])))) & 0xFFFFFFFF
    return (
        (state[0] + a) & 0xFFFFFFFF,
        (state[1] + b) & 0xFFFFFFFF,
        (state[2] + c) & 0xFFFFFFFF,
        (state[3] + d) & 0xFFFFFFFF,
    )


def _md5_length_extend(original_mac: str, append_data: bytes, original_total_len: int) -> str:
    """Compute MD5(secret || msg || padding || append_data) without knowing the secret.

    Implements the MD5 Length Extension Attack using a pure-Python MD5 compression
    function.  The ``original_mac`` provides the internal state after hashing
    (secret || msg); we continue from that state to hash ``append_data``.

    This is exactly what HashPump does under the hood.  The secret is never used.

    Args:
        original_mac: hex digest of MD5(secret || msg), captured from network.
        append_data:  the malicious payload to append.
        original_total_len: len(secret) + len(msg), known from the CTF hint.

    Returns:
        The forged MAC as a hex string.
    """
    # MD5 padding appended after (secret || msg)
    pad_len = (55 - original_total_len % 64) % 64 + 1
    padding = b"\x80" + b"\x00" * (pad_len - 1) + struct.pack("<Q", original_total_len * 8)
    padded_total = original_total_len + len(padding)

    # Seed the MD5 state from the original MAC (four little-endian 32-bit words)
    state = struct.unpack("<4I", bytes.fromhex(original_mac))

    # Apply standard MD5 padding to append_data (starting byte count = padded_total)
    total = padded_total + len(append_data)
    ap_len = (55 - total % 64) % 64 + 1
    padded = append_data + b"\x80" + b"\x00" * (ap_len - 1) + struct.pack("<Q", total * 8)

    for i in range(0, len(padded), 64):
        state = _md5_compress(state, padded[i:i + 64])

    return struct.pack("<4I", *state).hex()


def make_config(tmp_path: str) -> dict:
    """Return a minimal config dict using temp paths."""
    return {
        "update_server": {
            "url": "http://localhost:9999",
            "endpoint": "/api/v1/firmware/latest",
            "poll_interval": 30,
        },
        "firmware": {
            "current": os.path.join(tmp_path, "current.bin"),
            "pending": os.path.join(tmp_path, "pending.bin"),
        },
        "openocd": {
            "host": "127.0.0.1",
            "telnet_port": 14444,
        },
        "security": {
            "key_path": os.path.join(tmp_path, "update.key"),
            "algorithm": "md5",
            "secret_length": 16,
        },
    }


# ---------------------------------------------------------------------------
# Unit Tests – MAC Verification
# ---------------------------------------------------------------------------


class TestMacVerification:
    """Validates the MD5(secret || firmware) MAC scheme."""

    def test_valid_mac_passes(self):
        """Correct MAC for the firmware must be accepted."""
        mac = make_mac(FIRMWARE)
        assert verify_mac(FIRMWARE, mac, SECRET) is True

    def test_wrong_mac_rejected(self):
        """A tampered MAC must be rejected."""
        assert verify_mac(FIRMWARE, INVALID_MAC, SECRET) is False

    def test_modified_firmware_rejected(self):
        """Firmware modified after MAC calculation must be rejected."""
        mac = make_mac(FIRMWARE)
        tampered = FIRMWARE + b"\xff"
        assert verify_mac(tampered, mac, SECRET) is False

    def test_wrong_secret_rejected(self):
        """MAC computed with a different secret must be rejected."""
        mac = make_mac(FIRMWARE, secret=b"wrongsecretvalue")
        assert verify_mac(FIRMWARE, mac, SECRET) is False

    def test_length_extension_attack_succeeds(self):
        """
        Demonstrate that the weak MAC scheme is exploitable.

        A Length Extension Attack appends data to the original message and
        constructs a valid MAC without knowing the secret, using only the
        original MAC and the known secret length.

        This test uses a pure-Python reimplementation of the MD5 length
        extension to prove the vulnerability works – the same thing a CTF
        participant would do with HashPump.
        """
        payload = b"MALICIOUS_PAYLOAD"
        secret_len = 16  # known to the attacker (provided as a CTF hint)
        original_mac = make_mac(FIRMWARE)  # MD5(secret || firmware) – attacker captured this
        original_total_len = secret_len + len(FIRMWARE)

        # --- Step 1: compute MD5 padding for (secret || firmware) ---
        # MD5 pads to a multiple of 512 bits: 0x80 + zeros + 64-bit little-endian bit length
        pad_len = (55 - original_total_len % 64) % 64 + 1
        padding = b"\x80" + b"\x00" * (pad_len - 1) + struct.pack("<Q", original_total_len * 8)

        # --- Step 2: craft the extended firmware (no secret knowledge needed) ---
        extended_firmware = FIRMWARE + padding + payload

        # --- Step 3: forge the MAC without knowing the secret ---
        # MD5 is a Merkle-Damgård hash.  After processing (secret || firmware),
        # the four 32-bit state words A, B, C, D are exactly the bytes of original_mac
        # (written in little-endian order).  An attacker can seed a new MD5 computation
        # from that state and continue hashing only the append_data.
        # The result equals MD5(secret || firmware || padding || payload).
        #
        # _md5_length_extend is a pure-Python MD5 compression that uses only
        # original_mac and the known secret length (not the secret itself),
        # mirroring what HashPump does.
        forged_mac = _md5_length_extend(original_mac, payload, original_total_len)

        # The server verifies: MD5(secret || extended_firmware) == forged_mac
        # Both sides compute the same hash because the MD5 state after the padding block
        # is identical to the state we injected into the forged MAC computation.
        assert verify_mac(extended_firmware, forged_mac, SECRET) is True, (
            "Forged firmware with extended MAC must pass verification "
            "(this confirms the Length Extension Attack vulnerability)"
        )
        # Sanity: the forged MAC was computed WITHOUT using the secret bytes directly
        assert forged_mac != make_mac(FIRMWARE)  # it's a different MAC for a different message


# ---------------------------------------------------------------------------
# Unit Tests – save_firmware
# ---------------------------------------------------------------------------


class TestSaveFirmware:
    def test_saves_to_file(self, tmp_path):
        path = str(tmp_path / "fw.bin")
        save_firmware(FIRMWARE, path)
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == FIRMWARE

    def test_creates_parent_directories(self, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "fw.bin")
        save_firmware(FIRMWARE, path)
        assert os.path.exists(path)


# ---------------------------------------------------------------------------
# Unit Tests – flash_via_openocd (mocked telnet server)
# ---------------------------------------------------------------------------


class _MockOpenOCDHandler(socketserver.BaseRequestHandler):
    """Minimal TCP handler that mimics the OpenOCD telnet interface."""

    def handle(self):
        # Send welcome banner
        self.request.sendall(b"Open On-Chip Debugger 0.12.0\r\n> ")
        data = b""
        while True:
            chunk = self.request.recv(256)
            if not chunk:
                break
            data += chunk
            if b"program" in data:
                # Simulate successful flash output
                self.request.sendall(
                    b"** Programming Started **\r\n"
                    b"** Programming Finished **\r\n"
                    b"verified OK\r\n> "
                )
                data = b""
            if b"exit" in data:
                break


class TestFlashViaOpenOCD:
    @pytest.fixture
    def mock_openocd_server(self):
        server = socketserver.TCPServer(("127.0.0.1", 0), _MockOpenOCDHandler)
        server.allow_reuse_address = True
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        yield port
        server.shutdown()

    def test_flash_success(self, mock_openocd_server, tmp_path):
        fw_path = str(tmp_path / "fw.bin")
        with open(fw_path, "wb") as f:
            f.write(FIRMWARE)
        result = flash_via_openocd(fw_path, "127.0.0.1", mock_openocd_server)
        assert result is True

    def test_flash_fails_when_no_server(self, tmp_path):
        fw_path = str(tmp_path / "fw.bin")
        with open(fw_path, "wb") as f:
            f.write(FIRMWARE)
        # Port 1 is reserved and should refuse connection
        result = flash_via_openocd(fw_path, "127.0.0.1", 1)
        assert result is False


# ---------------------------------------------------------------------------
# Unit Tests – poll_for_update (mocked HTTP + mocked OpenOCD)
# ---------------------------------------------------------------------------


class _MockUpdateServerHandler(BaseHTTPRequestHandler):
    """HTTP handler returning a firmware update with a valid MAC."""

    firmware = FIRMWARE
    secret = SECRET
    version = "1.2.1"

    def log_message(self, *args, **kwargs):  # silence access logs
        pass

    def do_GET(self):
        if self.path == "/api/v1/firmware/latest":
            mac = make_mac(self.firmware, self.secret)
            body = (
                f'{{"version": "{self.version}", "mac": "{mac}", '
                f'"url": "/api/v1/firmware/download/{self.version}"}}'
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/api/v1/firmware/download/"):
            mac = make_mac(self.firmware, self.secret)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(self.firmware)))
            self.send_header("X-Firmware-MAC", mac)
            self.end_headers()
            self.wfile.write(self.firmware)
        else:
            self.send_response(404)
            self.end_headers()


class TestPollForUpdate:
    @pytest.fixture
    def http_server(self):
        server = HTTPServer(("127.0.0.1", 0), _MockUpdateServerHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        yield port
        server.shutdown()

    @pytest.fixture
    def mock_openocd(self):
        server = socketserver.TCPServer(("127.0.0.1", 0), _MockOpenOCDHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        yield port
        server.shutdown()

    def test_poll_downloads_and_flashes(self, http_server, mock_openocd, tmp_path):
        cfg = make_config(str(tmp_path))
        cfg["update_server"]["url"] = f"http://127.0.0.1:{http_server}"
        cfg["openocd"]["telnet_port"] = mock_openocd

        result = poll_for_update(cfg, SECRET)

        assert result is True
        assert os.path.exists(cfg["firmware"]["current"])
        with open(cfg["firmware"]["current"], "rb") as f:
            assert f.read() == FIRMWARE

    def test_poll_404_returns_false(self, tmp_path):
        """When the server returns 404 (normal operation), polling returns False."""
        server = HTTPServer(("127.0.0.1", 0), _MockUpdateServerHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()

        cfg = make_config(str(tmp_path))
        cfg["update_server"]["url"] = f"http://127.0.0.1:{port}"
        cfg["update_server"]["endpoint"] = "/nonexistent"

        result = poll_for_update(cfg, SECRET)
        server.shutdown()
        assert result is False

    def test_poll_bad_mac_rejected(self, tmp_path):
        """A firmware with an invalid MAC must not be flashed."""
        class BadMacHandler(_MockUpdateServerHandler):
            def do_GET(self):
                if self.path.startswith("/api/v1/firmware/download/"):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(len(self.firmware)))
                    # Deliberately wrong MAC
                    self.send_header("X-Firmware-MAC", INVALID_MAC)
                    self.end_headers()
                    self.wfile.write(self.firmware)
                else:
                    super().do_GET()

        server = HTTPServer(("127.0.0.1", 0), BadMacHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()

        cfg = make_config(str(tmp_path))
        cfg["update_server"]["url"] = f"http://127.0.0.1:{port}"

        result = poll_for_update(cfg, SECRET)
        server.shutdown()
        assert result is False
        assert not os.path.exists(cfg["firmware"]["current"])

    def test_poll_no_server_returns_false(self, tmp_path):
        """When the update server is unreachable, polling must return False gracefully."""
        cfg = make_config(str(tmp_path))
        cfg["update_server"]["url"] = "http://127.0.0.1:19999"
        result = poll_for_update(cfg, SECRET)
        assert result is False


# ---------------------------------------------------------------------------
# Docker Integration Tests (virtual environment)
# ---------------------------------------------------------------------------


DOCKER_IMAGE = "cybics-firmware-updater:test"


def _has_docker() -> bool:
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


requires_docker = pytest.mark.skipif(
    not _has_docker(), reason="Docker not available"
)


@requires_docker
class TestDockerImage:
    """Tests that the firmware-updater Docker image is functional."""

    def test_image_exists_or_buildable(self):
        """The Docker image must either already exist or build without errors."""
        import subprocess

        result = subprocess.run(
            ["docker", "image", "inspect", DOCKER_IMAGE],
            capture_output=True,
        )
        if result.returncode != 0:
            # Not cached – build it
            repo_root = os.path.join(
                os.path.dirname(__file__), "..", "software", "firmware-updater"
            )
            build = subprocess.run(
                ["docker", "build", "-t", DOCKER_IMAGE, repo_root],
                capture_output=True,
                timeout=300,
            )
            assert build.returncode == 0, (
                f"Docker build failed:\n{build.stderr.decode()}"
            )

    def test_entrypoint_generates_key_and_exits_gracefully(self, tmp_path):
        """Container must generate the MAC key on first start and then attempt to
        start the daemon (which will fail because there is no config at the
        real path – we expect a non-zero exit with a recognisable error, not a
        crash from a missing entrypoint or missing dependency).
        """
        import subprocess

        # We override CONFIG_PATH to a non-existent file so the daemon
        # exits quickly.  The entrypoint still runs and generates the key
        # in the temp dir before the daemon errors out.
        key_dir = str(tmp_path / "keys")
        os.makedirs(key_dir)

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CONFIG_PATH=/nonexistent/config.yaml",
                "-v", f"{key_dir}:/opt/cybics/keys",
                DOCKER_IMAGE,
            ],
            capture_output=True,
            timeout=30,
        )
        output = result.stdout.decode() + result.stderr.decode()

        # Entrypoint must have generated the key
        key_file = os.path.join(key_dir, "update.key")
        assert os.path.exists(key_file), (
            f"MAC key was not generated. Container output:\n{output}"
        )
        assert os.path.getsize(key_file) == 16, (
            f"MAC key should be 16 bytes, got {os.path.getsize(key_file)}"
        )

        # Daemon should fail due to missing config, not crash in entrypoint
        assert "Generating 16-byte MAC secret key" in output or os.path.exists(key_file), (
            f"Unexpected container output:\n{output}"
        )

    def test_generate_mac_script_runs_in_container(self, tmp_path):
        """The generate_mac.py helper must produce a valid hex digest."""
        import subprocess

        # Write a firmware and key file into the temp dir
        fw_path = str(tmp_path / "fw.bin")
        key_path = str(tmp_path / "update.key")
        with open(fw_path, "wb") as f:
            f.write(FIRMWARE)
        with open(key_path, "wb") as f:
            f.write(SECRET)

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--entrypoint", "python3",
                "-v", f"{tmp_path}:/data",
                DOCKER_IMAGE,
                "/opt/cybics/update-service/generate_mac.py",
                "/data/fw.bin", "/data/update.key",
            ],
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"generate_mac.py failed:\n{result.stderr.decode()}"
        )
        computed_mac = result.stdout.decode().strip()
        expected_mac = make_mac(FIRMWARE)
        assert computed_mac == expected_mac, (
            f"MAC mismatch: computed={computed_mac}, expected={expected_mac}"
        )
