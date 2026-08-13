#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
OUT="${1:-$ROOT/dist/runtime_probe}"
python3 -m unittest discover -s "$ROOT/runtime_probe/tests" -p 'test_*.py' -v
python3 "$ROOT/runtime_probe/tools/build_probe_packs.py" --repo-root "$ROOT" --output "$OUT"
