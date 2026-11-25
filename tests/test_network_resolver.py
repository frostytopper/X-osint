"""Offline tests for the network module: session, lookups and resolver setup."""

from __future__ import annotations

from unittest.mock import MagicMock

import dns.resolver
import pytest

from xosint.modules import network


def _session(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    session = MagicMock()
    session.get.return_value = resp
    return session, resp


def test_build_session_sets_user_agent():
    assert network._build_session().headers["User-Agent"] == "x-osint/3.0"


def test_geoip_normalizes_address_and_checks_status():
    session, resp = _session({"ip": "1.2.3.4"})
    assert network.get_geoip_info(" 1.2.3.4 ", session=session) == {"ip": "1.2.3.4"}
    assert session.get.call_args.args[0] == "https://ipinfo.io/1.2.3.4/json"
    resp.raise_for_status.assert_called_once()


def test_whois_requests_json():
    session, resp = _session({"net": {}})
    network.get_whois_info("8.8.8.8", session=session)
    args, kwargs = session.get.call_args
    assert args[0] == "https://whois.arin.net/rest/ip/8.8.8.8.json"
    assert kwargs["headers"] == {"Accept": "application/json"}
    resp.raise_for_status.assert_called_once()


@pytest.mark.parametrize("func", [network.get_geoip_info, network.get_whois_info])
def test_lookup_rejects_invalid_ip_before_any_request(func):
    session, _ = _session({})
    with pytest.raises(ValueError):
        func("not-an-ip", session=session)
    session.get.assert_not_called()


class _Answer:
    def __init__(self, text):
        self._text = text

    def to_text(self):
        return self._text


class _FakeResolver:
    def __init__(self, answers=(), error=None):
        self.nameservers = ["1.1.1.1"]
        self.answers = list(answers)
        self.error = error
        self.queries = []

    def resolve(self, domain, qtype):
        self.queries.append((domain, qtype))
        if self.error is not None:
            raise self.error
        return self.answers


def test_dns_query_success_uppercases_type_and_strips_domain(monkeypatch):
    fake = _FakeResolver([_Answer("10 mail.example.com.")])
    monkeypatch.setattr(network, "_create_resolver", lambda nameserver, timeout: fake)
    result = network.dns_query(" example.com ", record_type="mx")
    assert result == {
        "domain": "example.com",
        "type": "MX",
        "nameserver": "1.1.1.1",
        "records": ["10 mail.example.com."],
    }
    assert fake.queries == [("example.com", "MX")]


def test_dns_query_failure_returns_error_entry(monkeypatch):
    fake = _FakeResolver(error=dns.resolver.NoAnswer())
    monkeypatch.setattr(network, "_create_resolver", lambda nameserver, timeout: fake)
    result = network.dns_query("example.com")
    assert result["records"] == []
    assert result["error"]
    assert result["type"] == "A"


class _NoSystemConfigResolver:
    """Stands in for dns.resolver.Resolver on a system without /etc/resolv.conf."""

    def __init__(self, configure=True):
        if configure:
            raise dns.resolver.NoResolverConfiguration()
        self.nameservers = []
        self.lifetime = None
        self.read_files = []

    def read_resolv_conf(self, path):
        self.read_files.append(path)
        self.nameservers = ["9.9.9.9"]


def test_termux_resolv_conf_used_when_system_config_missing(monkeypatch, tmp_path):
    conf = tmp_path / "etc" / "resolv.conf"
    conf.parent.mkdir()
    conf.write_text("nameserver 9.9.9.9\n")
    monkeypatch.setenv("PREFIX", str(tmp_path))
    monkeypatch.setattr(dns.resolver, "Resolver", _NoSystemConfigResolver)
    resolver = network._create_resolver(None, 5)
    assert resolver.read_files == [str(conf)]
    assert resolver.nameservers == ["9.9.9.9"]
    assert resolver.lifetime == 5
