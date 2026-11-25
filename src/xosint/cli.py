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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _cmd_doctor(as_json=args.as_json)
    if args.command == "config" and args.config_command == "path":
        return _cmd_config_path()

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
