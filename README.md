# X-osint

A modular open-source intelligence (OSINT) command-line tool, built for Termux on Android and also usable on Linux.

This is a rewrite of [TermuxHackz/X-osint](https://github.com/TermuxHackz/X-osint) as a Python package. The upstream project remains on the `master` branch of this fork. Work happens on `dev`.

## Install on Termux

Use Termux from F-Droid or the GitHub releases. The Google Play build is deprecated.

```bash
pkg install -y git
git clone --depth 1 -b dev https://github.com/frostytopper/X-osint.git
bash X-osint/install.sh
```

Then run `xosint --help` from any directory. Update, uninstall and troubleshooting steps are in [docs/TERMUX.md](docs/TERMUX.md).

## Commands

| Command | What it does | Needs |
| --- | --- | --- |
| `xosint doctor` | Checks Python, config path and optional tools | nothing |
| `xosint config path` | Prints the config file path | nothing |
| `xosint ip ADDRESS [--whois]` | GeoIP and optional ARIN WHOIS lookup | network |
| `xosint dns DOMAIN [--type T] [--server IP]` | DNS record lookup | network |
| `xosint phone NUMBER [--region R] [--enrich]` | Parses a phone number offline. `--enrich` adds IPQualityScore data | key for `--enrich` |
| `xosint metadata FILE [--all]` | File metadata through ExifTool | `exiftool` |
| `xosint news QUERY [--limit N]` | Recent news articles through NewsAPI | NewsAPI key |

Every command except `config path` accepts `--json`.

## API keys

Keys come from environment variables first, then `~/.config/xosint/config.toml`.

```bash
export XOSINT_IPQUALITYSCORE_KEY=...
export XOSINT_NEWSAPI_KEY=...
```

```toml
[secrets]
ipqualityscore_key = "..."
newsapi_key = "..."
```

A command that needs a key and does not find one exits with a clear message.

## Development

```bash
git clone -b dev https://github.com/frostytopper/X-osint.git
cd X-osint
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
pytest
```

Each command is a module in `src/xosint/commands/` with `NAME`, `register(subparsers)` and `run(args)`. Add it to `COMMANDS` in `src/xosint/commands/__init__.py`. Lookup logic lives in `src/xosint/modules/` and does no printing. Tests are offline and mocked.

Project status and test notes are in [docs/HANDOFF.md](docs/HANDOFF.md).

## Responsible use

Use this tool only on data you are allowed to look up, and follow the terms of every service it queries. You are responsible for how you use it.

## License

See [LICENSE](LICENSE). Upstream project by TermuxHackz.
