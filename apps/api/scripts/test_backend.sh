#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python scripts/prepare_test_db.py
ruff check app
PYTHONPATH=. pytest -q
