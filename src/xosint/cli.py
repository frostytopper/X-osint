"""Command-line entry point for X-osint."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from typing import Sequence

from xosint import __version__
from xosint.config import get_config_file


def _cmd_doctor(as_json: bool) -> int:
    report = {
        "version": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "config_file": str(get_config_file()),
        "tools": {
            "exiftool": shutil.which("exiftool") is not None,
            "tor": shutil.which("tor") is not None,
            "git": shutil.which("git") is not None,
        },
    }
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"x-osint {report['version']} (Python {report['python']})")
        print(f"Platform: {report['platform']}")
        print(f"Config:   {report['config_file']}")
        for tool, available in report["tools"].items():
            status = "ok" if available else "missing"
            print(f"  {tool}: {status}")
    return 0


def _cmd_config_path() -> int:
    print(get_config_file())
    return 0


def _cmd_ip(address: str, include_whois: bool, as_json: bool) -> int:
    import requests

    from xosint.modules.network import get_geoip_info, get_whois_info

    try:
        result: dict[str, object] = {"geoip": get_geoip_info(address)}
        if include_whois:
            result["whois"] = get_whois_info(address)
    except ValueError as exc:
        print(f"Invalid IP address: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        geo = result["geoip"]
        assert isinstance(geo, dict)
        for key in ("ip", "hostname", "city", "region", "country", "loc", "org", "timezone"):
            if key in geo:
                print(f"{key:>10}: {geo[key]}")
        if include_whois:
            net = result.get("whois", {})
            if isinstance(net, dict) and "net" in net:
                name = net["net"].get("name", {}).get("$", "N/A")
                print(f"{'whois_net':>10}: {name}")
    return 0


def _cmd_dns(
    domain: str,
    record_type: str,
    nameserver: str | None,
    as_json: bool,
) -> int:
    from xosint.modules.network import dns_query

    try:
        result = dns_query(domain, record_type=record_type, nameserver=nameserver)
    except ValueError as exc:
        print(f"Invalid nameserver IP: {exc}", file=sys.stderr)
        return 2

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("error"):
            print(
                f"DNS lookup failed ({result['type']} {result['domain']}): {result['error']}",
                file=sys.stderr,
            )
            return 1
        for rec in result["records"]:
            print(rec)
    return 1 if result.get("error") else 0


def _cmd_phone(
    number: str,
    region: str | None,
    enrich: bool,
    as_json: bool,
) -> int:
    import phonenumbers
    import requests

    from xosint.modules.phone import enrich_ipqualityscore, parse_phone_number

    try:
        result = parse_phone_number(number, default_region=region)
        if enrich:
            result["ipqualityscore"] = enrich_ipqualityscore(result["e164"])
    except phonenumbers.NumberParseException as exc:
        print(f"Invalid phone number: {exc}", file=sys.stderr)
        return 2
    except (RuntimeError, requests.RequestException) as exc:
        print(f"Enrichment error: {exc}", file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        for key in (
            "e164",
            "international",
            "valid",
            "region_code",
            "location",
            "carrier",
            "line_type",
            "timezones",
        ):
            print(f"{key:>13}: {result.get(key)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xosint",
        description="Modular Open Source Intelligence CLI framework.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check Python environment, config path, and optional external binaries.",
    )
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output diagnostics as JSON.",
    )

    config_parser = subparsers.add_parser(
        "config",
        help="Inspect X-osint configuration.",
    )
    config_sub = config_parser.add_subparsers(dest="config_command")
    config_sub.add_parser("path", help="Print the config.toml path.")

    ip_parser = subparsers.add_parser(
        "ip",
        help="Look up GeoIP (and optionally ARIN WHOIS) information for an IP address.",
    )
    ip_parser.add_argument("address", help="IPv4 or IPv6 address to query.")
    ip_parser.add_argument(
        "--whois",
        action="store_true",
        dest="include_whois",
        help="Also fetch ARIN WHOIS JSON.",
    )
    ip_parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON.",
    )

    dns_parser = subparsers.add_parser(
        "dns",
        help="Resolve DNS records for a domain.",
    )
    dns_parser.add_argument("domain", help="Domain name to resolve.")
    dns_parser.add_argument(
        "--type",
        default="A",
        dest="record_type",
        help="DNS record type (default: A).",
    )
    dns_parser.add_argument(
        "--server",
        default=None,
        dest="nameserver",
        help="Optional nameserver IP (e.g. 1.1.1.1).",
    )
    dns_parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON.",
    )

    phone_parser = subparsers.add_parser(
        "phone",
        help="Parse and inspect a phone number (offline by default, optional --enrich).",
    )
    phone_parser.add_argument("number", help="Phone number (e.g. +12065550100).")
    phone_parser.add_argument(
        "--region",
        default=None,
        help="Optional default ISO region code if no country code is supplied (e.g. US).",
    )
    phone_parser.add_argument(
        "--enrich",
        action="store_true",
        help="Query IPQualityScore using XOSINT_IPQUALITYSCORE_KEY.",
    )
    phone_parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _cmd_doctor(as_json=args.as_json)
    if args.command == "config" and args.config_command == "path":
        return _cmd_config_path()
    if args.command == "ip":
        return _cmd_ip(args.address, args.include_whois, args.as_json)
    if args.command == "dns":
        return _cmd_dns(args.domain, args.record_type, args.nameserver, args.as_json)
    if args.command == "phone":
        return _cmd_phone(args.number, args.region, args.enrich, args.as_json)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
