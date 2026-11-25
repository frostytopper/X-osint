"""Offline unit tests for the metadata module and CLI command."""

from __future__ import annotations

import json
import subprocess

import pytest

from xosint.cli import main
from xosint.modules import metadata

FAKE_EXIF = {
    "SourceFile": "photo.jpg",
    "EXIF:Make": "Google",
    "EXIF:Model": "Pixel 8",
    "EXIF:DateTimeOriginal": "2026:11:25 09:00:00",
    "Composite:GPSLatitude": 47.6062,
    "Composite:GPSLongitude": -122.3321,
}


def _fake_run(payload, returncode=0, stderr=""):
    def runner(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd, returncode, stdout=json.dumps(payload), stderr=stderr
        )

    return runner


def test_summarize_extracts_signed_gps() -> None:
    summary = metadata.summarize_metadata(FAKE_EXIF)
    assert summary["camera_model"] == "Pixel 8"
    assert summary["created"] == "2026:11:25 09:00:00"
    assert summary["location"]["latitude"] == 47.6062
    assert summary["location"]["longitude"] == -122.3321
    assert "openstreetmap.org" in summary["location"]["map_url"]


def test_summarize_without_gps_has_no_location() -> None:
    assert metadata.summarize_metadata({"EXIF:Make": "Google"})["location"] is None


def test_summarize_ignores_non_numeric_gps() -> None:
    raw = {
        "Composite:GPSLatitude": "47 deg 36' 22.00\" N",
        "Composite:GPSLongitude": "122 deg 19' 55.00\" W",
    }
    assert metadata.summarize_metadata(raw)["location"] is None


def test_extract_missing_file_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        metadata.extract_metadata(tmp_path / "nope.jpg")


def test_extract_without_exiftool_raises(monkeypatch, tmp_path) -> None:
    f = tmp_path / "a.jpg"
    f.write_bytes(b"x")
    monkeypatch.setattr(metadata, "find_exiftool", lambda: None)
    with pytest.raises(metadata.ExifToolError, match="exiftool not found"):
        metadata.extract_metadata(f)


def test_extract_uses_numeric_group_flags(monkeypatch, tmp_path) -> None:
    f = tmp_path / "a.jpg"
    f.write_bytes(b"x")
    seen = {}

    def runner(cmd, **kwargs):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps([FAKE_EXIF]), stderr="")

    monkeypatch.setattr(metadata.subprocess, "run", runner)
    result = metadata.extract_metadata(f, exiftool="/usr/bin/exiftool")
    assert result["EXIF:Make"] == "Google"
    assert seen["cmd"][:4] == ["/usr/bin/exiftool", "-j", "-n", "-G"]
    assert seen["cmd"][4] == str(f.resolve())


def test_cli_metadata_json(monkeypatch, tmp_path, capsys) -> None:
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"x")
    monkeypatch.setattr(metadata, "find_exiftool", lambda: "/usr/bin/exiftool")
    monkeypatch.setattr(metadata.subprocess, "run", _fake_run([FAKE_EXIF]))

    rc = main(["metadata", str(f), "--json", "--all"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["location"]["latitude"] == 47.6062
    assert payload["all"]["EXIF:Make"] == "Google"


def test_cli_metadata_missing_file_returns_2(capsys) -> None:
    rc = main(["metadata", "/nonexistent/file.jpg"])
    assert rc == 2
    assert "No such file" in capsys.readouterr().err


def test_cli_metadata_missing_exiftool_returns_1(monkeypatch, tmp_path, capsys) -> None:
    f = tmp_path / "a.jpg"
    f.write_bytes(b"x")
    monkeypatch.setattr(metadata, "find_exiftool", lambda: None)
    rc = main(["metadata", str(f)])
    assert rc == 1
    assert "exiftool not found" in capsys.readouterr().err
