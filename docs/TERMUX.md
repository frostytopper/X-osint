# Installing X-osint on Termux

## One-shot install

```bash
pkg install -y git
git clone --depth 1 -b dev https://github.com/frostytopper/X-osint.git
bash X-osint/install.sh
```

The shallow clone (`--depth 1`) skips the full upstream history, which includes large demo media.

The installer:

- installs `python`, `git` and `exiftool` with `pkg` (no `sudo`, no `pkg upgrade`)
- creates a virtual environment at `~/.local/share/xosint/venv`
- installs X-osint into that venv (pure-Python dependencies only)
- links `$PREFIX/bin/xosint` so `xosint` works from any directory
- runs `xosint doctor` as a self-check

The clone is not needed after installing and is never deleted for you.

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

This removes the launcher and the venv. Your config in `~/.config/xosint` is left in place.

## Developing

Use a separate checkout venv so development never touches the installed copy:

```bash
cd X-osint
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
pytest
```

`ruff` is in the `[dev]` extra, but pip cannot build it on Termux. Use `pkg install ruff` instead.

## API keys

Secrets are read from environment variables first, then `~/.config/xosint/config.toml`:

```bash
export XOSINT_IPQUALITYSCORE_KEY=...
```

```toml
[secrets]
ipqualityscore_key = "..."
```
