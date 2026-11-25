"""Network OSINT: IP GeoIP/WHOIS lookups and DNS resolution."""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
from typing import Any

import dns.exception
import dns.resolver
import requests

DEFAULT_TIMEOUT = 10
FALLBACK_NAMESERVERS = ["1.1.1.1", "8.8.8.8"]


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "x-osint/3.0"})
    return session


def validate_ip(address: str) -> str:
    """Validate and normalize an IPv4/IPv6 address."""
    return str(ipaddress.ip_address(address.strip()))


def get_geoip_info(
    ip: str,
    *,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Fetch GeoIP metadata for an IP address from ipinfo.io."""
    normalized = validate_ip(ip)
    client = session or _build_session()
    resp = client.get(f"https://ipinfo.io/{normalized}/json", timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_whois_info(
    ip: str,
    *,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Fetch ARIN RDAP/WHOIS metadata for an IP address."""
    normalized = validate_ip(ip)
    client = session or _build_session()
    resp = client.get(
        f"https://whois.arin.net/rest/ip/{normalized}.json",
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def _create_resolver(nameserver: str | None, timeout: float) -> dns.resolver.Resolver:
    """Create a DNS resolver, falling back gracefully when /etc/resolv.conf is absent (Termux)."""
    if nameserver:
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = [validate_ip(nameserver)]
        resolver.lifetime = timeout
        return resolver

    try:
        resolver = dns.resolver.Resolver(configure=True)
    except dns.resolver.NoResolverConfiguration:
        resolver = dns.resolver.Resolver(configure=False)
        prefix = os.environ.get("PREFIX")
        termux_resolv = Path(prefix) / "etc" / "resolv.conf" if prefix else None
        if termux_resolv and termux_resolv.is_file():
            resolver.read_resolv_conf(str(termux_resolv))
        else:
            resolver.nameservers = list(FALLBACK_NAMESERVERS)

    resolver.lifetime = timeout
    return resolver


def dns_query(
    domain: str,
    *,
    record_type: str = "A",
    nameserver: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Resolve DNS records for a domain, optionally against a specific nameserver."""
    resolver = _create_resolver(nameserver, timeout)

    qtype = record_type.upper()
    try:
        answers = resolver.resolve(domain.strip(), qtype)
        records = [rdata.to_text() for rdata in answers]
        return {
            "domain": domain.strip(),
            "type": qtype,
            "nameserver": resolver.nameservers[0] if resolver.nameservers else None,
            "records": records,
        }
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException) as exc:
        return {
            "domain": domain.strip(),
            "type": qtype,
            "nameserver": resolver.nameservers[0] if resolver.nameservers else None,
            "records": [],
            "error": str(exc),
        }
