# Handoff: X-osint fork (read this first)

Last updated: 2026-11-25. Branch: `dev`. `master` is the untouched upstream baseline.

## Roles and workflow

- The assistant develops. It has no shell and no way to run code. It only writes files to GitHub through the connector (`push_files`, `delete_file`).
- The user (Brian) is the tester. He runs everything by hand in Termux on a Pixel 9 Pro XL (Android 17, aarch64, Python 3.14.10) and pastes output back.
- Always confirm before each push, with the full file list. `push_files` needs the full content of every file, so a changed file is resent whole.
- Keep steps small. Do not claim Termux behaviour is confirmed unless he has run it. Say what is verified and what is not.
- Commit style: `feat(module): ...`, `fix(module): ...`, `refactor(module): ...`, `chore: ...`, `docs: ...`.
- Scope is fixed: proper program design and a working build/install process for current stable Termux (F-Droid or GitHub build, v0.118.3). Do not add features. The assistant makes the design calls, and edits `src/` whenever the design needs it. There is no rule against touching `src/`.
- Run `bash scripts/check.sh` in the dev venv and paste the output. It is the assistant's main source of context about the code.

## Source project

- Upstream: `TermuxHackz/X-osint` (single 116 KB `xosint` script, `setup.sh`, Flask/Tkinter/Stripe baggage).
- Fork: `frostytopper/X-osint`. Rewrite lives in `src/xosint/` as a modular package. The legacy `xosint` script and `setup.sh` were deleted from `dev` and remain on `master`.
- Still in the `dev` root from upstream, unused: `templates/`, `static/`, `Demo/`, `Icons/`, `images/`, `bugs_report/`, `google_Dorks.txt`, `subdomains.txt`, `vins.txt`, `disclaimer.html`, `requirements.txt`, `.deepsource.toml`, `.github/`. Not yet reviewed for removal. `requirements.txt` is the one that matters (it lists stale dependencies).

## Current state of `dev`

| Area | Status |
| --- | --- |
| Packaging | `pyproject.toml`, setuptools, `src/` layout, `requires-python >= 3.11`, core deps pure Python: requests, beautifulsoup4, phonenumbers, dnspython. Extras: image, web, nlp, dev |
| Config | `src/xosint/config.py`. `XOSINT_<NAME>` env var first, then `~/.config/xosint/config.toml` `[secrets]`. Uses `tomllib` directly (3.11+) |
| CLI design | `cli.py` is a thin parser loop. Each command is a module in `src/xosint/commands/` with `NAME`, `register(subparsers)`, `run(args)`, listed in `COMMANDS` in `commands/__init__.py`. Shared `--json` helpers in `src/xosint/output.py`. Heavy imports are lazy, inside each `run()` |
| Commands | `doctor`, `config path`, `ip`, `dns`, `phone`, `metadata`, `news`. All except `config path` support `--json` |
| Logic modules | `src/xosint/modules/`: `network.py`, `phone.py`, `metadata.py`, `news.py`. No argparse or printing in these |
| ip / dns | dns uses dnspython and falls back to `$PREFIX/etc/resolv.conf`, then 1.1.1.1 and 8.8.8.8, because Termux has no `/etc/resolv.conf` |
| phone | Offline via phonenumbers. `--enrich` calls IPQualityScore with `XOSINT_IPQUALITYSCORE_KEY` |
| metadata | Runs `exiftool -j -n -G`. Never auto-installs. Prints an OpenStreetMap link, never opens a browser |
| news | NewsAPI `/v2/everything`, key from `XOSINT_NEWSAPI_KEY`, sent in a header. Fails clearly if absent. Live behaviour untested (needs the user's own key) |
| Installer | `install.sh`: Termux only, no sudo, checks Python >= 3.11, venv at `~/.local/share/xosint/venv`, launcher symlink at `$PREFIX/bin/xosint`, `--uninstall`. Docs in `docs/TERMUX.md`, `README.md` |
| Dev tooling | `scripts/check.sh` runs `ruff`, `ty`, `pytest --cov`, `vulture`. `ruff` and `ty` come from `pkg`. `[dev]` extra is pytest, pytest-cov, vulture |
| Tests | `tests/`, offline and mocked. 35 expected (34 verified plus one config-file test) |

## Verified on the Pixel

- `pytest`: 34 passed after the registry refactor.
- `scripts/check.sh`: `ruff` passed after two fixes. `pytest` with coverage ran: 75% total. `vulture` reported nothing. `ty` 0.0.110 installed with `pkg install ty` and ran.
- `xosint --help` and `xosint doctor` work. `xosint news "x" --limit 0` exits 2.
- `install.sh --uninstall` removes the launcher and venv. `command -v xosint` inside the dev venv prints the dev copy, as expected.
- `ip`, `dns` (with `--server`) and the resolver fallback passed.
- `xosint metadata` works on `PXL_20261125_172749268.RAW-01.jpg` (ExifTool 13.64 via `pkg install exiftool`): camera fields correct, `location: None`.
- `install.sh` (previous version): fresh install, re-run update, and `--uninstall` all passed.

## Findings from check.sh baseline

- `ty` found that on Python 3.10, `config.py` skipped `tomllib` and silently ignored `config.toml`, so secrets in the file never worked there. Fixed by raising the minimum to Python 3.11 and importing `tomllib` directly. Termux ships 3.14, so this never showed on the Pixel.
- Coverage gaps (percent of statements): `commands/ip.py` 51, `commands/metadata.py` 54, `commands/dns.py` 61, `commands/news.py` 61, `commands/doctor.py` 67, `modules/network.py` 72. The command wrappers have little direct test coverage. Adding tests for them is the next safety-net step.
- A malformed `config.toml` raises an uncaught `tomllib.TOMLDecodeError`. Not yet handled.

## Not yet verified

- `pytest` count after this commit (expect 35), and `ty` result on Python 3.11 floor (expect the `tomllib` error gone).
- The updated `install.sh` (Python 3.11 check and new error messages): re-run install.
- GPS extraction on a photo that has GPS. The no-location result has not been checked with `--json --all` to confirm the tags are absent.
- `xosint dns example.com --type MX` without `--server`, after the fallback fix.
- `xosint news` against the live API.

## Termux gotchas learned

- Current stable Termux is v0.118.3 from F-Droid or GitHub. The Google Play build is deprecated.
- Anything that needs Rust fails to build with pip on Termux: `ruff` (via maturin) and recent `mypy` (via `ast-serialize`). Use `pkg install ruff ty`. Do not install `mypy`.
- No `which` command. Use `command -v`.
- No `/etc/resolv.conf` (handled).
- Two separate venvs: the dev checkout `~/X-osint/.venv` and the installed copy under `~/.local/share/xosint/venv`. `pytest` is only on PATH inside the dev venv. `command -v xosint` inside the dev venv shows the dev copy.
- `~/storage/downloads` maps to the shared Download folder after `termux-setup-storage`.
- Leftover clones may exist at `~/xosint-test` and `~/xosint-upstream`. Safe to delete.

## Decisions made

- `master` stays as the untouched upstream mirror. `dev` is the working line. Do not merge the rewrite into `master`.
- The installer never runs `pkg upgrade` or `pkg update`. It points to `pkg update` only when `pkg install` fails.
- Minimum Python is 3.11. Python 3.10 reaches end of life in 2026, and the 3.10 fallback hid a real bug.
- Do not copy the NewsAPI key hardcoded in upstream `newsOsint()`. It is a shared key, and its quota exhaustion is upstream issue #98.
- Dropped on purpose: self-update via `git reset --hard`, `stripe`, Tkinter GUI, sudo auto-installs.

## Next steps

1. User: `git pull`, run `bash scripts/check.sh`, paste the output (expect 35 tests and a clean `ty`).
2. Add tests for the command wrappers and `modules/network.py` (mocked), starting with the lowest-coverage files.
3. Decide what to do with the remaining upstream files in the `dev` root, starting with `requirements.txt`.
4. Upstream features not yet ported are out of scope for this phase: reverse image search, network and Wi-Fi mapper plus Flask templates, code analysis, speed test, ping, VIN, email, GitHub email, Google dorks. The upstream file was only readable up to the phone module (connector truncation).
5. Performance, only if wanted: measure import time first with `python -X importtime`. Then a shared `requests.Session`, a threadpool for batch lookups, and a small TTL cache.

## Upstream issues worth remembering

- #98: shared NewsAPI quota exhausted.
- #100: spaCy build hangs on install. We avoid it by keeping `spacy` in the optional `nlp` extra.
- #103: no uninstall path. Solved by `install.sh --uninstall`.
