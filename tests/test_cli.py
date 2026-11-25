"""Smoke tests for the X-osint CLI and config layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from xosint import __version__
from xosint.cli import main
from xosint.commands import COMMANDS
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


def test_get_secret_from_config_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("XOSINT_NEWSAPI_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / "xosint" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('[secrets]\nnewsapi_key = "from-file"\n')
    assert get_secret("newsapi_key") == "from-file"


def test_every_registered_command_in_help(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for module in COMMANDS:
        assert module.NAME in out


def test_no_command_prints_help(capsys) -> None:
    assert main([]) == 0
    assert "usage: xosint" in capsys.readouterr().out


def test_news_without_key_exits_1(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.delenv("XOSINT_NEWSAPI_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert main(["news", "seattle"]) == 1
    assert "XOSINT_NEWSAPI_KEY" in capsys.readouterr().err


def test_news_bad_limit_exits_2(capsys) -> None:
    assert main(["news", "seattle", "--limit", "0"]) == 2
    assert "limit" in capsys.readouterr().err
