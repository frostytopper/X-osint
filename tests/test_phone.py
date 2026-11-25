"""Offline unit tests for the phone OSINT module and CLI command."""

from __future__ import annotations

import json

from xosint.cli import main
from xosint.modules import phone


def test_parse_phone_number_us() -> None:
    info = phone.parse_phone_number("+12065550100")
    assert info["e164"] == "+12065550100"
    assert info["country_code"] == 1
    assert info["region_code"] == "US"
    assert info["possible"] is True


def test_cli_phone_json(capsys) -> None:
    rc = main(["phone", "+12065550100", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["e164"] == "+12065550100"
    assert payload["region_code"] == "US"


def test_cli_phone_invalid_returns_2(capsys) -> None:
    rc = main(["phone", "not-a-phone"])
    assert rc == 2
    assert "Invalid phone number" in capsys.readouterr().err


def test_cli_phone_enrich_missing_key_returns_1(monkeypatch, capsys) -> None:
    monkeypatch.delenv("XOSINT_IPQUALITYSCORE_KEY", raising=False)
    monkeypatch.setattr(phone, "get_secret", lambda name: None)
    rc = main(["phone", "+12065550100", "--enrich"])
    assert rc == 1
    assert "IPQualityScore API key not configured" in capsys.readouterr().err
