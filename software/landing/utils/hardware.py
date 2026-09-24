"""Report which CybICS board the platform is running on.

hwio-raspberry reads the board revision straps at startup and writes them to a
JSON file on a volume this container mounts read-only; see
software/hwio-raspberry/hw_version.py for the encoding and
hardware/README.md#version-coding for the authoritative table.

Kept free of Flask so it can be tested without standing up the app.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

HARDWARE_STATE = os.environ.get(
    "CYBICS_HARDWARE_STATE", "/var/lib/cybics/hardware.json"
)

# The Docker-only stack has no board, so a missing file is the normal case
# there and must not surface as an error.
NO_BOARD = "no CybICS board detected (virtual stack)"
UNREADABLE = "board revision unavailable"


def read_hardware_version(path=None):
    """Return the board revision for the settings panel.

    Always returns a dict with at least `revision`, `detected` and
    `description`, so the caller never has to guard against a missing key.
    """
    path = path or HARDWARE_STATE
    try:
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
    except FileNotFoundError:
        return {"revision": None, "detected": False, "description": NO_BOARD}
    except (OSError, ValueError) as error:
        logger.warning("Could not read %s: %s", path, error)
        return {"revision": None, "detected": False, "description": UNREADABLE}

    if not isinstance(state, dict) or not state.get("revision"):
        logger.warning("%s has no revision in it", path)
        return {"revision": None, "detected": False, "description": UNREADABLE}

    return {
        "revision": state.get("revision"),
        "detected": True,
        "straps_present": state.get("straps_present"),
        "strap_code": state.get("strap_code"),
        "description": state.get("description"),
    }
