"""xosint metadata: file metadata via ExifTool."""

from __future__ import annotations

import argparse
import sys

from xosint.output import add_json_flag, emit_json

NAME = "metadata"


def run(args: argparse.Namespace) -> int:
    from xosint.modules.metadata import (
        ExifToolError,
        extract_metadata,
        summarize_metadata,
    )

    try:
        raw = extract_metadata(args.file)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ExifToolError as exc:
        print(f"ExifTool error: {exc}", file=sys.stderr)
        return 1

    summary = summarize_metadata(raw)

    if args.as_json:
        payload: dict[str, object] = {"file": args.file, "summary": summary}
        if args.show_all:
            payload["all"] = raw
        emit_json(payload)
        return 0

    for key, value in summary.items():
        if key == "location":
            continue
        print(f"{key:>13}: {value}")
    loc = summary.get("location")
    if loc:
        print(f"{'location':>13}: {loc['latitude']}, {loc['longitude']}")
        print(f"{'map':>13}: {loc['map_url']}")
    else:
        print(f"{'location':>13}: None")
    if args.show_all:
        print("\n--- all metadata ---")
        for key, value in raw.items():
            print(f"{key}: {value}")
    return 0


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        NAME,
        help="Extract file metadata (EXIF, PDF, ID3, ...) using ExifTool.",
    )
    parser.add_argument("file", help="Path to the file to inspect.")
    parser.add_argument(
        "--all",
        action="store_true",
        dest="show_all",
        help="Include every raw ExifTool field, not just the summary.",
    )
    add_json_flag(parser)
    parser.set_defaults(handler=run)
