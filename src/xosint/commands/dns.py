"""xosint dns: resolve DNS records."""

from __future__ import annotations

import argparse
import sys

from xosint.output import add_json_flag, emit_json

NAME = "dns"


def run(args: argparse.Namespace) -> int:
    from xosint.modules.network import dns_query

    try:
        result = dns_query(
            args.domain, record_type=args.record_type, nameserver=args.nameserver
        )
    except ValueError as exc:
        print(f"Invalid nameserver IP: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        emit_json(result)
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


def register(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="Resolve DNS records for a domain.")
    parser.add_argument("domain", help="Domain name to resolve.")
    parser.add_argument(
        "--type",
        default="A",
        dest="record_type",
        help="DNS record type (default: A).",
    )
    parser.add_argument(
        "--server",
        default=None,
        dest="nameserver",
        help="Optional nameserver IP (e.g. 1.1.1.1).",
    )
    add_json_flag(parser)
    parser.set_defaults(handler=run)
