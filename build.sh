#!/usr/bin/env bash
# One-shot build script: clean, test, then produce wheel + sdist into dist/.
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/3] Running test suite..."
python -m pytest tests/ -q

echo "[2/3] Cleaning previous builds..."
rm -rf build dist

echo "[3/3] Building wheel and sdist..."
python -m build .

echo
echo "Build artifacts:"
ls -lh dist/
