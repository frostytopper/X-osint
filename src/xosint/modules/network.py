"""Network OSINT: IP GeoIP/WHOIS lookups and DNS resolution."""

from __future__ import annotations

import ipaddress
from typing import Any

import dns.exception
import dns.resolver
import requests

DEFAULT_TIMEOUT = 10


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


def dns_query(
    domain: str,
    *,
    record_type: str = "A",
    nameserver: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Resolve DNS records for a domain, optionally against a specific nameserver."""
    resolver = dns.resolver.Resolver(configure=nameserver is None)
    resolver.lifetime = timeout
    if nameserver:
        resolver.nameservers = [validate_ip(nameserver)]

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
