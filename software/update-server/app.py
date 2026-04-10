import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field


class LatestFirmwareResponse(BaseModel):
    version: str
    mac: str = Field(
        description="Hex-encoded MD5(secret || firmware) value for the firmware binary."
    )
    url: str = Field(description="Relative download URL for the latest firmware binary.")


def _get_firmware_version() -> str:
    return os.environ.get("FIRMWARE_VERSION", "1.2.1")


def _get_firmware_mac() -> str:
    mac = os.environ.get("FIRMWARE_MAC", "").strip()
    if not mac:
        raise HTTPException(status_code=500, detail="FIRMWARE_MAC is not configured")
    return mac


def _get_firmware_path() -> Path:
    return Path(
        os.environ.get(
            "FIRMWARE_PATH", "/opt/cybics/update-server/firmware/firmware.bin"
        )
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="CybICS Firmware Update Server",
        version="1.0.0",
        description=(
            "Minimal firmware update server for the CybICS CTF scenario. "
            "Firmware authenticity is represented as a hex-encoded "
            "MD5(secret || firmware) MAC."
        ),
    )

    @app.get(
        "/api/v1/firmware/latest",
        response_model=LatestFirmwareResponse,
        tags=["firmware"],
    )
    def get_latest_firmware() -> LatestFirmwareResponse:
        version = _get_firmware_version()
        return LatestFirmwareResponse(
            version=version,
            mac=_get_firmware_mac(),
            url=f"/api/v1/firmware/download/{version}",
        )

    @app.get(
        "/api/v1/firmware/download/{version}",
        response_class=Response,
        tags=["firmware"],
        responses={
            200: {
                "description": "Firmware binary",
                "content": {
                    "application/octet-stream": {
                        "schema": {"type": "string", "format": "binary"}
                    }
                },
                "headers": {
                    "X-Firmware-MAC": {
                        "description": (
                            "Hex-encoded MD5(secret || firmware) value for the "
                            "returned firmware binary."
                        ),
                        "schema": {"type": "string"},
                    }
                },
            },
            404: {"description": "Firmware version not found"},
            500: {"description": "Firmware file or MAC is not configured"},
        },
    )
    def download_firmware(version: str) -> Response:
        expected_version = _get_firmware_version()
        if version != expected_version:
            raise HTTPException(status_code=404, detail="Firmware version not found")

        firmware_path = _get_firmware_path()
        if not firmware_path.is_file():
            raise HTTPException(status_code=500, detail="Firmware file is not available")

        return Response(
            content=firmware_path.read_bytes(),
            media_type="application/octet-stream",
            headers={"X-Firmware-MAC": _get_firmware_mac()},
        )

    return app


app = create_app()
