# Handoff: X-osint fork (read this first)

Last updated: 2026-11-25. Branch: `dev`. `master` is the untouched upstream baseline.

## Roles and workflow

- The assistant develops. It has no shell and no way to run code. It only writes files to GitHub through the connector (`push_files`).
- The user (Brian) is the tester. He runs everything by hand in Termux on a Pixel 9 Pro XL (Android 17, aarch64, Python 3.14.10) and pastes output back.
- Always confirm before each push, with the full file list. `push_files` needs the full content of every file, so a changed file is resent whole.
- Keep steps small. Do not write sprawling scripts or claim Termux behaviour is confirmed unless he has run it. Say what is verified and what is not.
- Commit style: `feat(module): ...`, `fix(module): ...`, `refactor(module): ...`, `docs: ...`.
- Scope is fixed: proper program design and a working build/install process for current stable Termux (F-Droid or GitHub build, v0.118.3). Do not add features. The assistant makes the design calls.

## Source project

- Upstream: `TermuxHackz/X-osint` (single 116 KB `xosint` script, `setup.sh`, Flask/Tkinter/Stripe baggage).
- Fork: `frostytopper/X-osint`. Rewrite lives in `src/xosint/` as a modular package. The legacy `xosint` script and `setup.sh` are still in the tree, unmodified and unused, unless a later commit removed them.

## Current state of `dev`

| Area | Status |
| --- | --- |
| Packaging | `pyproject.toml`, setuptools, `src/` layout, core deps pure Python: requests, beautifulsoup4, phonenumbers, dnspython. Extras: image, web, nlp, dev |
| Config | `src/xosint/config.py`. `XOSINT_<NAME>` env var first, then `~/.config/xosint/config.toml` `[secrets]` |
| CLI design | `cli.py` is a thin parser loop. Each command is a module in `src/xosint/commands/` with `NAME`, `register(subparsers)`, `run(args)`, listed in `COMMANDS` in `commands/__init__.py`. Shared `--json` helpers in `src/xosint/output.py`. Heavy imports are lazy, inside each `run()` |
| Commands | `doctor`, `config path`, `ip`, `dns`, `phone`, `metadata`, `news`. All except `config path` support `--json` |
| Logic modules | `src/xosint/modules/`: `network.py`, `phone.py`, `metadata.py`, `news.py`. No argparse or printing in these |
| ip / dns | dns uses dnspython and falls back to `$PREFIX/etc/resolv.conf`, then 1.1.1.1 and 8.8.8.8, because Termux has no `/etc/resolv.conf` |
| phone | Offline via phonenumbers. `--enrich` calls IPQualityScore with `XOSINT_IPQUALITYSCORE_KEY` |
| metadata | Runs `exiftool -j -n -G`. Never auto-installs. Prints an OpenStreetMap link, never opens a browser |
| news | NewsAPI `/v2/everything`, key from `XOSINT_NEWSAPI_KEY`, sent in a header. Fails clearly if absent. Live behaviour untested (needs the user's own key) |
| Installer | `install.sh`: Termux only, no sudo, checks Python >= 3.10, venv at `~/.local/share/xosint/venv`, launcher symlink at `$PREFIX/bin/xosint`, `--uninstall`. Docs in `docs/TERMUX.md` |
| Tests | `tests/`, offline and mocked. 34 tests |

## Verified on the Pixel

- `pytest`: 34 passed after the registry refactor.
- `xosint news "x" --limit 0` printed the limit error with exit 2, and `xosint doctor` ran correctly.
- `xosint --help` displays correctly, from the updated installer.
- `ip`, `dns` (with `--server`) and the resolver fallback passed.
- `xosint metadata` works on `PXL_20261125_172749268.RAW-01.jpg` (ExifTool 13.64 via `pkg install exiftool`): camera fields correct, `location: None`.
- `install.sh` (previous version): fresh install, re-run update, and `--uninstall` all passed.

## Not yet verified

- `--uninstall` and `command -v xosint` printing nothing, with the updated `install.sh`. The new Python version check and error messages have only been exercised on the success path.
- GPS extraction on a photo that has GPS. The no-location result has not been checked with `--json --all` to confirm the tags are absent.
- `xosint dns example.com --type MX` without `--server`, after the fallback fix.
- `xosint news` against the live API.

## Termux gotchas learned

- Current stable Termux is v0.118.3 from F-Droid or GitHub. The Google Play build is deprecated.
- `ruff` in `[dev]` fails with `maturin` metadata errors. Use `pkg install ruff`. `pip install -e .` then `pip install pytest` instead of `.[dev]`.
- No `which` command. Use `command -v`.
- No `/etc/resolv.conf` (handled).
- Two separate venvs: the dev checkout `~/X-osint/.venv` and the installed copy under `~/.local/share/xosint/venv`. `pytest` is only on PATH inside the dev venv.
- `~/storage/downloads` maps to the shared Download folder after `termux-setup-storage`.
- Leftover clones may exist at `~/xosint-test` and `~/xosint-upstream`. Safe to delete.

## Decisions made

- `master` stays as the untouched upstream mirror. `dev` is the working line. Do not merge the rewrite into `master`.
- The legacy `xosint` script and `setup.sh` are removed from `dev` only. They remain on `master`.
- The installer never runs `pkg upgrade` or `pkg update`. It points to `pkg update` only when `pkg install` fails.
- Do not copy the NewsAPI key hardcoded in upstream `newsOsint()`. It is a shared key, and its quota exhaustion is upstream issue #98.
- Dropped on purpose: self-update via `git reset --hard`, `stripe`, Tkinter GUI, sudo auto-installs.

## Next steps

1. User: run `bash install.sh --uninstall` then `command -v xosint` (expect no output).
2. Upstream features not yet ported are out of scope for this phase: reverse image search, network and Wi-Fi mapper plus Flask templates, code analysis, speed test, ping, VIN, email, GitHub email, Google dorks. The upstream file was only readable up to the phone module (connector truncation), so VIN, email, GitHub email and Google dorks were never reviewed.
3. Performance, only if wanted: measure import time first with `python -X importtime`. Then a shared `requests.Session`, a threadpool for batch lookups, and a small TTL cache.

## Upstream issues worth remembering

- #98: shared NewsAPI quota exhausted.
- #100: spaCy build hangs on install. We avoid it by keeping `spacy` in the optional `nlp` extra.
- #103: no uninstall path. Solved by `install.sh --uninstall`.
