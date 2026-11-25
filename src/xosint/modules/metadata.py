"""File metadata OSINT via ExifTool (no auto-install, no network access)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

INSTALL_HINT = (
    "exiftool not found on PATH. Termux: pkg install exiftool | "
    "Debian/Ubuntu: sudo apt install libimage-exiftool-perl"
)

_SUMMARY_FIELDS: dict[str, tuple[str, ...]] = {
    "title": ("PDF:Title", "ID3:Title", "XMP:Title", "QuickTime:Title"),
    "author": ("PDF:Author", "ID3:Artist", "XMP:Creator", "EXIF:Artist"),
    "created": (
        "EXIF:DateTimeOriginal",
        "EXIF:CreateDate",
        "QuickTime:CreateDate",
        "PDF:CreateDate",
        "XMP:CreateDate",
        "ID3:Year",
    ),
    "camera_make": ("EXIF:Make",),
    "camera_model": ("EXIF:Model",),
    "software": ("EXIF:Software", "PDF:Producer"),
}

_LAT_KEYS = ("Composite:GPSLatitude", "QuickTime:GPSLatitude")
_LON_KEYS = ("Composite:GPSLongitude", "QuickTime:GPSLongitude")


class ExifToolError(RuntimeError):
    """Raised when ExifTool is missing or fails."""


def find_exiftool() -> str | None:
    return shutil.which("exiftool")


def extract_metadata(
    file_path: str | Path,
    *,
    exiftool: str | None = None,
    timeout: float = 30,
) -> dict[str, Any]:
    """Run ExifTool on a file and return its raw metadata dict.

    Uses -n (numeric values, so GPS is signed decimal degrees) and -G
    (group-prefixed keys such as EXIF:Make).
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {file_path}")

    binary = exiftool or find_exiftool()
    if not binary:
        raise ExifToolError(INSTALL_HINT)

    try:
        proc = subprocess.run(
            [binary, "-j", "-n", "-G", str(path.resolve())],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExifToolError(f"exiftool timed out after {timeout}s") from exc

    if proc.returncode != 0:
        raise ExifToolError(proc.stderr.strip() or f"exiftool exited with {proc.returncode}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ExifToolError(f"Could not parse exiftool output: {exc}") from exc

    if not data:
        raise ExifToolError("exiftool returned no metadata")
    return data[0]


def _first(metadata: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return value
    return None


def _first_number(metadata: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def summarize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Pick out the commonly useful fields, including GPS location if present."""
    summary: dict[str, Any] = {
        name: _first(metadata, keys) for name, keys in _SUMMARY_FIELDS.items()
    }
    lat = _first_number(metadata, _LAT_KEYS)
    lon = _first_number(metadata, _LON_KEYS)
    if lat is not None and lon is not None:
        summary["location"] = {
            "latitude": lat,
            "longitude": lon,
            "map_url": (
                f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}"
                f"#map=16/{lat}/{lon}"
            ),
        }
    else:
        summary["location"] = None
    return summary
