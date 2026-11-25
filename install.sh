#!/usr/bin/env bash
# X-osint installer for Termux (F-Droid or GitHub build).
#   bash install.sh              install or update
#   bash install.sh --uninstall  remove launcher and venv
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/xosint"
VENV_DIR="$DATA_DIR/venv"

info() { printf '[*] %s\n' "$*"; }
warn() { printf '[!] %s\n' "$*" >&2; }
die() { printf '[x] %s\n' "$*" >&2; exit 1; }

if [ -z "${PREFIX:-}" ] || [ ! -d "$PREFIX/bin" ] || [ ! -d /data/data/com.termux ]; then
    die "This installer targets Termux. Elsewhere: python -m venv .venv && . .venv/bin/activate && pip install -e . pytest"
fi

LAUNCHER="$PREFIX/bin/xosint"

if [ "${1:-}" = "--uninstall" ]; then
    info "Removing launcher and venv"
    rm -f "$LAUNCHER"
    rm -rf "$DATA_DIR"
    info "Removed. Config in ~/.config/xosint was left untouched."
    exit 0
fi

info "Installing system packages (python, git)"
pkg install -y python git || die "pkg failed. Use Termux from F-Droid or GitHub (the Google Play build is deprecated), run 'pkg update', then retry."

PYTHON="$PREFIX/bin/python3"
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
    || die "Python 3.11 or newer is required (found $("$PYTHON" -V 2>&1))."

if ! command -v exiftool >/dev/null 2>&1; then
    info "Installing exiftool (needed for 'xosint metadata')"
    pkg install -y exiftool || warn "exiftool install failed; 'xosint metadata' will not work until it is installed"
fi

info "Creating virtual environment at $VENV_DIR"
mkdir -p "$DATA_DIR"
"$PYTHON" -m venv --clear "$VENV_DIR" || die "Could not create the virtual environment."

info "Installing X-osint from $REPO_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade --force-reinstall "$REPO_DIR"

info "Linking launcher at $LAUNCHER"
ln -sf "$VENV_DIR/bin/xosint" "$LAUNCHER"

info "Checking install"
"$LAUNCHER" doctor

info "Done. Run 'xosint --help' from any directory."
