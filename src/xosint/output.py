"""Shared output helpers for CLI commands."""

from __future__ import annotations

import argparse
import json
from typing import Any


def add_json_flag(parser: argparse.ArgumentParser) -> None:
    """Add the standard --json flag (stored as args.as_json)."""
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON.",
    )


def emit_json(data: Any) -> None:
    print(json.dumps(data, indent=2))
