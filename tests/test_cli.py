"""Smoke tests for the X-osint CLI and config layer."""

from __future__ import annotations

import json
from pathlib import Path

from xosint import __version__
from xosint.cli import main
from xosint.config import get_config_file, get_secret


def test_doctor_json(capsys) -> None:
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["version"] == __version__
    assert "tools" in data
    assert set(data["tools"].keys()) == {"exiftool", "tor", "git"}


def test_config_path_respects_xdg(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    rc = main(["config", "path"])
    assert rc == 0
    assert Path(capsys.readouterr().out.strip()) == tmp_path / "xosint" / "config.toml"
    assert get_config_file() == tmp_path / "xosint" / "config.toml"


def test_get_secret_env_override(monkeypatch) -> None:
    monkeypatch.setenv("XOSINT_NEWSAPI_KEY", "test-key-123")
    assert get_secret("newsapi_key") == "test-key-123"
