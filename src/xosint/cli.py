"""Command-line entry point for X-osint.

Commands live in xosint.commands and are listed in COMMANDS there.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from xosint import __version__
from xosint.commands import COMMANDS


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
    for module in COMMANDS:
        module.register(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
