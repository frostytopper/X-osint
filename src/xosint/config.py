"""XDG-compliant configuration and secrets management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 fallback
    tomllib = None  # type: ignore[assignment]


def get_config_dir() -> Path:
    """Return the XDG config directory for xosint."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "xosint"


def get_config_file() -> Path:
    """Return the path to config.toml."""
    return get_config_dir() / "config.toml"


def load_config() -> dict[str, Any]:
    """Load config.toml if present, returning an empty dict otherwise."""
    cfg_path = get_config_file()
    if not cfg_path.is_file() or tomllib is None:
        return {}
    with cfg_path.open("rb") as fh:
        return tomllib.load(fh)


def get_secret(name: str) -> str | None:
    """Look up a secret from XOSINT_<NAME> env var, then config.toml [secrets]."""
    env_key = f"XOSINT_{name.upper()}"
    if val := os.environ.get(env_key):
        return val.strip()
    cfg = load_config()
    secrets = cfg.get("secrets", {})
    val = secrets.get(name.lower())
    return str(val).strip() if val else None
