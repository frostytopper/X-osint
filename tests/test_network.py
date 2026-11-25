"""Offline unit tests for the network OSINT module and CLI commands."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from xosint.cli import main
from xosint.modules import network


def test_validate_ip_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        network.validate_ip("not-an-ip")


def test_cli_ip_json(monkeypatch, capsys) -> None:
    fake_geo = {
        "ip": "1.1.1.1",
        "org": "AS13335 Cloudflare, Inc.",
        "country": "AU",
    }
    monkeypatch.setattr(network, "get_geoip_info", lambda ip: fake_geo)

    rc = main(["ip", "1.1.1.1", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["geoip"]["ip"] == "1.1.1.1"


def test_cli_ip_invalid_returns_2(capsys) -> None:
    rc = main(["ip", "999.999.999.999"])
    assert rc == 2
    assert "Invalid IP address" in capsys.readouterr().err


def test_dns_query_uses_custom_nameserver(monkeypatch) -> None:
    fake_rdata = MagicMock()
    fake_rdata.to_text.return_value = "93.184.216.34"

    fake_resolver = MagicMock()
    fake_resolver.nameservers = []
    fake_resolver.resolve.return_value = [fake_rdata]

    monkeypatch.setattr(network.dns.resolver, "Resolver", lambda configure=True: fake_resolver)

    result = network.dns_query("example.com", record_type="a", nameserver="1.1.1.1")
    assert fake_resolver.nameservers == ["1.1.1.1"]
    assert result["type"] == "A"
    assert result["records"] == ["93.184.216.34"]
    assert "error" not in result


def test_cli_dns_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        network,
        "dns_query",
        lambda domain, record_type="A", nameserver=None: {
            "domain": domain,
            "type": record_type.upper(),
            "nameserver": nameserver or "1.1.1.1",
            "records": ["93.184.216.34"],
        },
    )

    rc = main(["dns", "example.com", "--type", "A", "--server", "1.1.1.1", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["records"] == ["93.184.216.34"]
