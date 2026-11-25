"""xosint ip: GeoIP and optional ARIN WHOIS lookup."""

from __future__ import annotations

import argparse
import sys

from xosint.output import add_json_flag, emit_json

NAME = "ip"


def run(args: argparse.Namespace) -> int:
    import requests

    from xosint.modules.network import get_geoip_info, get_whois_info

    try:
        result: dict[str, object] = {"geoip": get_geoip_info(args.address)}
        if args.include_whois:
            result["whois"] = get_whois_info(args.address)
    except ValueError as exc:
        print(f"Invalid IP address: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        emit_json(result)
    else:
        geo = result["geoip"]
        assert isinstance(geo, dict)
        for key in ("ip", "hostname", "city", "region", "country", "loc", "org", "timezone"):
            if key in geo:
                print(f"{key:>10}: {geo[key]}")
        if args.include_whois:
            net = result.get("whois", {})
            if isinstance(net, dict) and "net" in net:
                name = net["net"].get("name", {}).get("$", "N/A")
                print(f"{'whois_net':>10}: {name}")
    return 0


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        NAME,
        help="Look up GeoIP (and optionally ARIN WHOIS) information for an IP address.",
    )
    parser.add_argument("address", help="IPv4 or IPv6 address to query.")
    parser.add_argument(
        "--whois",
        action="store_true",
        dest="include_whois",
        help="Also fetch ARIN WHOIS JSON.",
    )
    add_json_flag(parser)
    parser.set_defaults(handler=run)
