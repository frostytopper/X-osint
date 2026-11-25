"""xosint config: inspect configuration."""

from __future__ import annotations

import argparse

from xosint.config import get_config_file

NAME = "config"


def run_path(args: argparse.Namespace) -> int:
    print(get_config_file())
    return 0


def register(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="Inspect X-osint configuration.")
    sub = parser.add_subparsers(dest="config_command")
    path_parser = sub.add_parser("path", help="Print the config.toml path.")
    path_parser.set_defaults(handler=run_path)
