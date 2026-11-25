"""Command registry.

Each command module defines:
  NAME: str                      the subcommand name
  register(subparsers) -> None   add its parser and set_defaults(handler=run)
  run(args) -> int               the exit code

To add a command: create a module here, then append it to COMMANDS.
Heavy imports belong inside run(), not at module top level.
"""

from __future__ import annotations

from xosint.commands import (
    config_cmd,
    dns,
    doctor,
    ip,
    metadata,
    news,
    phone,
)

COMMANDS = (doctor, config_cmd, ip, dns, phone, metadata, news)
