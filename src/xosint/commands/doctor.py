"""xosint doctor: environment diagnostics."""

from __future__ import annotations

import argparse
import platform
import shutil

from xosint import __version__
from xosint.config import get_config_file
from xosint.output import add_json_flag, emit_json

NAME = "doctor"


def run(args: argparse.Namespace) -> int:
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
    if args.as_json:
        emit_json(report)
    else:
        print(f"x-osint {report['version']} (Python {report['python']})")
        print(f"Platform: {report['platform']}")
        print(f"Config:   {report['config_file']}")
        for tool, available in report["tools"].items():
            status = "ok" if available else "missing"
            print(f"  {tool}: {status}")
    return 0


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        NAME,
        help="Check Python environment, config path, and optional external binaries.",
    )
    add_json_flag(parser)
    parser.set_defaults(handler=run)
