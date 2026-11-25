#!/usr/bin/env bash
# Project health check: lint, types, tests with coverage, dead code.
# Run inside the dev venv. Missing tools are skipped, not fatal.
#   bash scripts/check.sh
# Termux: pkg install ruff ty   (pip cannot build them)
set -u

cd "$(dirname "${BASH_SOURCE[0]}")/.."

fail=0

step() {
    local name="$1"
    shift
    local tool="$1"
    printf '\n=== %s ===\n' "$name"
    if ! command -v "$tool" >/dev/null 2>&1; then
        printf '[skip] %s is not installed\n' "$tool"
        return
    fi
    "$@" || {
        printf '[fail] %s\n' "$name"
        fail=1
    }
}

step "ruff (lint)" ruff check src tests
step "ty (types)" ty check src
step "pytest + coverage" pytest -q --cov --cov-report=term-missing
step "vulture (dead code)" vulture src --min-confidence 80

printf '\n'
if [ "$fail" -eq 0 ]; then
    printf '[*] All checks passed\n'
else
    printf '[!] Some checks failed (see above)\n'
fi
exit "$fail"
