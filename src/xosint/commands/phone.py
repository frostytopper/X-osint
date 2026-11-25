"""xosint phone: parse and inspect a phone number."""

from __future__ import annotations

import argparse
import sys

from xosint.output import add_json_flag, emit_json

NAME = "phone"


def run(args: argparse.Namespace) -> int:
    import phonenumbers
    import requests

    from xosint.modules.phone import enrich_ipqualityscore, parse_phone_number

    try:
        result = parse_phone_number(args.number, default_region=args.region)
        if args.enrich:
            result["ipqualityscore"] = enrich_ipqualityscore(result["e164"])
    except phonenumbers.NumberParseException as exc:
        print(f"Invalid phone number: {exc}", file=sys.stderr)
        return 2
    except (RuntimeError, requests.RequestException) as exc:
        print(f"Enrichment error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        emit_json(result)
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


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        NAME,
        help="Parse and inspect a phone number (offline by default, optional --enrich).",
    )
    parser.add_argument("number", help="Phone number (e.g. +12065550100).")
    parser.add_argument(
        "--region",
        default=None,
        help="Optional default ISO region code if no country code is supplied (e.g. US).",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Query IPQualityScore using XOSINT_IPQUALITYSCORE_KEY.",
    )
    add_json_flag(parser)
    parser.set_defaults(handler=run)
