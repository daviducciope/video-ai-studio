#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/.venv/bin/activate"
export PYTHONPATH="$ROOT_DIR/services/worker:$ROOT_DIR/packages/shared"
export DATA_ROOT="${DATA_ROOT:-$ROOT_DIR/data}"
cd "$ROOT_DIR"
python -m app.main serve
