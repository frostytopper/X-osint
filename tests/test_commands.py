"""Offline tests for the command wrappers in xosint.commands.

The lookup functions in xosint.modules are replaced with fakes, so these tests
check argument handling, output and exit codes only.
"""

from __future__ import annotations

import json

import pytest
import requests

from xosint.cli import main
from xosint.config import ConfigError, get_secret
from xosint.modules.metadata import ExifToolError
from xosint.modules.news import NewsAPIError


@pytest.fixture(autouse=True)
def _isolated_config(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    for name in ("XOSINT_NEWSAPI_KEY", "XOSINT_IPQUALITYSCORE_KEY"):
        monkeypatch.delenv(name, raising=False)


def _write_config(tmp_path, text):
    cfg = tmp_path / "cfg" / "xosint" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(text)
    return cfg


# ip


def test_ip_text(monkeypatch, capsys):
    monkeypatch.setattr(
        "xosint.modules.network.get_geoip_info",
        lambda ip: {"ip": ip, "city": "Seattle", "country": "US"},
    )
    assert main(["ip", "1.2.3.4"]) == 0
    out = capsys.readouterr().out
    assert "city: Seattle" in out
    assert "whois_net" not in out


def test_ip_whois_text(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.network.get_geoip_info", lambda ip: {"ip": ip})
    monkeypatch.setattr(
        "xosint.modules.network.get_whois_info",
        lambda ip: {"net": {"name": {"$": "EXAMPLE-NET"}}},
    )
    assert main(["ip", "1.2.3.4", "--whois"]) == 0
    assert "whois_net: EXAMPLE-NET" in capsys.readouterr().out


def test_ip_json(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.network.get_geoip_info", lambda ip: {"ip": ip})
    assert main(["ip", "1.2.3.4", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"geoip": {"ip": "1.2.3.4"}}


def test_ip_invalid_address_exits_2(capsys):
    assert main(["ip", "not-an-ip"]) == 2
    assert "Invalid IP address" in capsys.readouterr().err


def test_ip_network_error_exits_1(monkeypatch, capsys):
    def boom(ip):
        raise requests.ConnectionError("down")

    monkeypatch.setattr("xosint.modules.network.get_geoip_info", boom)
    assert main(["ip", "1.2.3.4"]) == 1
    assert "Network error" in capsys.readouterr().err


# dns

_DNS_OK = {
    "domain": "example.com",
    "type": "A",
    "nameserver": "1.1.1.1",
    "records": ["93.184.216.34"],
}
_DNS_ERR = {**_DNS_OK, "records": [], "error": "boom"}


def _fake_dns(result):
    return lambda domain, record_type, nameserver: result


def test_dns_text(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.network.dns_query", _fake_dns(_DNS_OK))
    assert main(["dns", "example.com"]) == 0
    assert "93.184.216.34" in capsys.readouterr().out


def test_dns_json(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.network.dns_query", _fake_dns(_DNS_OK))
    assert main(["dns", "example.com", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == _DNS_OK


def test_dns_error_text_exits_1(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.network.dns_query", _fake_dns(_DNS_ERR))
    assert main(["dns", "example.com"]) == 1
    assert "DNS lookup failed" in capsys.readouterr().err


def test_dns_error_json_still_prints_and_exits_1(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.network.dns_query", _fake_dns(_DNS_ERR))
    assert main(["dns", "example.com", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "boom"


def test_dns_invalid_server_exits_2(capsys):
    assert main(["dns", "example.com", "--server", "bogus"]) == 2
    assert "Invalid nameserver IP" in capsys.readouterr().err


# metadata

_RAW_GPS = {
    "EXIF:Make": "Google",
    "EXIF:Model": "Pixel",
    "Composite:GPSLatitude": 47.6,
    "Composite:GPSLongitude": -122.3,
}
_RAW_NO_GPS = {"EXIF:Make": "Google"}


def _fake_extract(raw):
    return lambda path: raw


def test_metadata_text_with_location(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.metadata.extract_metadata", _fake_extract(_RAW_GPS))
    assert main(["metadata", "photo.jpg"]) == 0
    out = capsys.readouterr().out
    assert "location: 47.6, -122.3" in out
    assert "openstreetmap.org" in out


def test_metadata_text_without_location(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.metadata.extract_metadata", _fake_extract(_RAW_NO_GPS))
    assert main(["metadata", "photo.jpg"]) == 0
    out = capsys.readouterr().out
    assert "camera_make: Google" in out
    assert "location: None" in out


def test_metadata_all_text(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.metadata.extract_metadata", _fake_extract(_RAW_NO_GPS))
    assert main(["metadata", "photo.jpg", "--all"]) == 0
    out = capsys.readouterr().out
    assert "--- all metadata ---" in out
    assert "EXIF:Make: Google" in out


def test_metadata_json_all(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.metadata.extract_metadata", _fake_extract(_RAW_NO_GPS))
    assert main(["metadata", "photo.jpg", "--json", "--all"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["all"] == _RAW_NO_GPS
    assert data["summary"]["camera_make"] == "Google"


def test_metadata_json_without_all(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.metadata.extract_metadata", _fake_extract(_RAW_NO_GPS))
    assert main(["metadata", "photo.jpg", "--json"]) == 0
    assert "all" not in json.loads(capsys.readouterr().out)


def test_metadata_missing_file_exits_2(tmp_path, capsys):
    assert main(["metadata", str(tmp_path / "missing.jpg")]) == 2
    assert "No such file" in capsys.readouterr().err


def test_metadata_exiftool_error_exits_1(monkeypatch, capsys):
    def boom(path):
        raise ExifToolError("exiftool not found")

    monkeypatch.setattr("xosint.modules.metadata.extract_metadata", boom)
    assert main(["metadata", "photo.jpg"]) == 1
    assert "ExifTool error" in capsys.readouterr().err


# news

_NEWS = {
    "query": "seattle",
    "total_results": 1,
    "articles": [
        {
            "title": "Headline",
            "source": "Example",
            "published_at": "2026-11-25T10:00:00Z",
            "url": "https://example.com/a",
            "description": "Desc",
        }
    ],
}


def test_news_text(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.news.search_news", lambda query, limit: _NEWS)
    assert main(["news", "seattle"]) == 0
    out = capsys.readouterr().out
    assert "1 of 1 results for 'seattle'" in out
    assert "Headline" in out
    assert "https://example.com/a" in out


def test_news_json(monkeypatch, capsys):
    monkeypatch.setattr("xosint.modules.news.search_news", lambda query, limit: _NEWS)
    assert main(["news", "seattle", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == _NEWS


def test_news_api_error_exits_1(monkeypatch, capsys):
    def boom(query, limit):
        raise NewsAPIError("rate limited")

    monkeypatch.setattr("xosint.modules.news.search_news", boom)
    assert main(["news", "seattle"]) == 1
    assert "News error: rate limited" in capsys.readouterr().err


def test_news_malformed_config_exits_1(tmp_path, capsys):
    _write_config(tmp_path, "[secrets\n")
    assert main(["news", "seattle"]) == 1
    assert "Invalid config file" in capsys.readouterr().err


# doctor, phone, config


def test_doctor_text(capsys):
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "x-osint" in out
    assert "exiftool:" in out


def test_phone_text(capsys):
    assert main(["phone", "+12065550100"]) == 0
    out = capsys.readouterr().out
    assert "e164" in out
    assert "+12065550100" in out


def test_phone_invalid_number_exits_2(capsys):
    assert main(["phone", "abc"]) == 2
    assert "Invalid phone number" in capsys.readouterr().err


def test_phone_enrich_without_key_exits_1(capsys):
    assert main(["phone", "+12065550100", "--enrich"]) == 1
    assert "XOSINT_IPQUALITYSCORE_KEY" in capsys.readouterr().err


def test_phone_enrich_json(monkeypatch, capsys):
    monkeypatch.setattr(
        "xosint.modules.phone.enrich_ipqualityscore", lambda e164: {"fraud_score": 5}
    )
    assert main(["phone", "+12065550100", "--enrich", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["ipqualityscore"] == {"fraud_score": 5}


def test_get_secret_malformed_config_raises(tmp_path):
    _write_config(tmp_path, "[secrets\n")
    with pytest.raises(ConfigError, match="Invalid config file"):
        get_secret("newsapi_key")
