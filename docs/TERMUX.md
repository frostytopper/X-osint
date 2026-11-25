# Installing X-osint on Termux

## Requirements

- Termux from F-Droid or the GitHub releases of `termux/termux-app` (current stable: v0.118.3). The Google Play build is deprecated and no longer updated, so its package mirrors can fail.
- Python 3.11 or newer (the `python` package from `pkg`). Tested on Python 3.14.10, aarch64, Android 17.
- About 100 MB of free storage for the venv and dependencies.

Termux:API is not required.

## One-shot install

```bash
pkg install -y git
git clone --depth 1 -b dev https://github.com/frostytopper/X-osint.git
bash X-osint/install.sh
```

The shallow clone (`--depth 1`) skips the full upstream history, which includes large demo media.

The installer:

- installs `python`, `git` and `exiftool` with `pkg` (no `sudo`, no `pkg upgrade`)
- checks that Python is 3.11 or newer
- creates a virtual environment at `~/.local/share/xosint/venv`
- installs X-osint into that venv (pure-Python dependencies only)
- links `$PREFIX/bin/xosint` so `xosint` works from any directory
- runs `xosint doctor` as a self-check

The clone is not needed after installing and is never deleted for you.

If `pkg` reports a mirror or repository error, run `termux-change-repo`, then `pkg update`, and run the installer again.

## Update

```bash
cd X-osint
git pull --ff-only origin dev
bash install.sh
```

## Uninstall

```bash
bash X-osint/install.sh --uninstall
command -v xosint   # should print nothing
```

This removes the launcher and the venv. Your config in `~/.config/xosint` is left in place. If you run `command -v xosint` inside the dev checkout venv, it prints that venv's copy instead. Run `deactivate` first.

## Commands

`xosint --help` lists every command. Current commands: `doctor`, `config path`, `ip`, `dns`, `phone`, `metadata`, `news`. All except `config path` accept `--json`.

## Developing

Use a separate checkout venv so development never touches the installed copy:

```bash
cd X-osint
python -m venv .venv
source .venv/bin/activate
pkg install -y ruff ty
pip install -e '.[dev]'
bash scripts/check.sh
```

`scripts/check.sh` runs `ruff` (lint), `ty` (types), `pytest` with coverage, and `vulture` (dead code). Missing tools are skipped.

`ruff` and `ty` come from `pkg`, not pip. pip cannot build them on Termux because they need Rust. For the same reason, do not install `mypy`: recent releases depend on `ast-serialize`, which fails to build here.

To add a command, create `src/xosint/commands/<name>.py` with `NAME`, `register(subparsers)` and `run(args)`, then add it to `COMMANDS` in `src/xosint/commands/__init__.py`.

## API keys

Secrets are read from environment variables first, then `~/.config/xosint/config.toml`:

```bash
export XOSINT_IPQUALITYSCORE_KEY=...
export XOSINT_NEWSAPI_KEY=...
```

```toml
[secrets]
ipqualityscore_key = "..."
newsapi_key = "..."
```

Commands that need a key fail with a clear message when it is missing.
