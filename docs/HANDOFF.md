# Handoff: X-osint fork (read this first)

Last updated: 2026-11-25. Branch: `dev`. `master` is the untouched upstream baseline.

## Roles and workflow

- The assistant develops. It has no shell and no way to run code. It only writes files to GitHub through the connector (`push_files`).
- The user (Brian) is the tester. He runs everything by hand in Termux on a Pixel 9 Pro XL (Android 17, aarch64, Python 3.14.10) and pastes output back.
- Always confirm before each push, with the full file list. `push_files` needs the full content of every file, so a changed `cli.py` is resent whole.
- Keep steps small. Do not write sprawling scripts or claim Termux behaviour is confirmed unless he has run it. Say what is verified and what is not.
- Commit style: `feat(module): ...`, `fix(module): ...`, `docs: ...`.

## Source project

- Upstream: `TermuxHackz/X-osint` (single 116 KB `xosint` script, `setup.sh`, Flask/Tkinter/Stripe baggage).
- Fork: `frostytopper/X-osint`. Rewrite lives in `src/xosint/` as a modular package. The legacy `xosint` script and `setup.sh` are still in the tree, unmodified and unused.

## Current state of `dev`

| Area | Status |
| --- | --- |
| Packaging | `pyproject.toml`, setuptools, `src/` layout, core deps pure Python: requests, beautifulsoup4, phonenumbers, dnspython. Extras: image, web, nlp, dev |
| Config | `src/xosint/config.py`. `XOSINT_<NAME>` env var first, then `~/.config/xosint/config.toml` `[secrets]` |
| CLI | `xosint doctor`, `config path`, `ip`, `dns`, `phone`, `metadata`. All support `--json`. Heavy imports are lazy, inside each `_cmd_*` |
| ip / dns | `modules/network.py`. dns uses dnspython and falls back to `$PREFIX/etc/resolv.conf`, then 1.1.1.1 and 8.8.8.8, because Termux has no `/etc/resolv.conf` |
| phone | `modules/phone.py`. Offline via phonenumbers. `--enrich` calls IPQualityScore with `XOSINT_IPQUALITYSCORE_KEY` |
| metadata | `modules/metadata.py`. Runs `exiftool -j -n -G`. Never auto-installs. Prints an OpenStreetMap link, never opens a browser |
| Installer | `install.sh`: Termux only, no sudo, venv at `~/.local/share/xosint/venv`, launcher symlink at `$PREFIX/bin/xosint`, `--uninstall`. Docs in `docs/TERMUX.md` |
| Tests | `tests/`, offline and mocked. 22 tests expected. The user last confirmed 13 passing (before metadata). Re-run `pytest` and confirm the count |

## Verified on the Pixel

- `pytest` passed through the phone module. `ip`, `dns` (with `--server`) and the resolver fallback passed.
- `xosint metadata` works on `PXL_20261125_172749268.RAW-01.jpg` (ExifTool 13.64 via `pkg install exiftool`): camera fields correct, `location: None`.
- `install.sh`: fresh install, re-run update, and `--uninstall` all passed.

## Not yet verified

- `pytest` after the metadata commit (expect 22).
- GPS extraction on a photo that has GPS. The no-location result has not been checked with `--json --all` to confirm the tags are absent.
- `xosint dns example.com --type MX` without `--server`, after the fallback fix.

## Termux gotchas learned

- `ruff` in `[dev]` fails with `maturin` metadata errors. Use `pkg install ruff`. `pip install -e .` then `pip install pytest` instead of `.[dev]`.
- No `which` command. Use `command -v`.
- No `/etc/resolv.conf` (handled).
- Two separate venvs: the dev checkout `~/X-osint/.venv` and the installed copy under `~/.local/share/xosint/venv`.
- `~/storage/downloads` maps to the shared Download folder after `termux-setup-storage`.
- A leftover test clone may exist at `~/xosint-test`. Safe to delete.

## Next steps

1. `news` module: `xosint news "<query>" [--limit N] [--json]`. Key from `XOSINT_NEWSAPI_KEY` or `[secrets] newsapi_key`. Fail clearly if absent. Use `params=`, not an f-string URL. Add timeout and `raise_for_status()`. The user needs his own NewsAPI key to test live.
2. Do not copy the NewsAPI key hardcoded in upstream `newsOsint()`. It is a shared key, and its quota exhaustion is upstream issue #98.
3. Port or drop the remaining upstream features. The upstream `xosint` was only partly read (truncated around the phone module), so review the rest before deciding. Known candidates: reverse image search (upstream stub is broken, it never uses the image), network and Wi-Fi mapper plus Flask templates (upstream imports the wrong template function), code analysis (`shell=True` with unquoted paths, so use argument lists), VIN, email, GitHub email, Google dorks.
4. Drop on purpose: self-update via `git reset --hard`, `stripe`, Tkinter GUI, sudo auto-installs.
5. Deferred until after install work (now done): performance. Measure import time first with `python -X importtime`. Then a shared `requests.Session`, a threadpool for batch lookups, and a small TTL cache. `aria2` and `xh` were judged not useful here (no large downloads, and spawning a process per request is slower than `requests`).
6. Eventually: merge `dev` into `master`, or keep `master` as an upstream mirror. Ask the user.

## Upstream issues worth remembering

- #98: shared NewsAPI quota exhausted.
- #100: spaCy build hangs on install. We avoid it by keeping `spacy` in the optional `nlp` extra.
- #103: no uninstall path. Solved by `install.sh --uninstall`.
