#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/.venv/bin/activate"
export PYTHONPATH="$ROOT_DIR/services/api:$ROOT_DIR/packages/shared"
export DATA_ROOT="${DATA_ROOT:-$ROOT_DIR/data}"
cd "$ROOT_DIR"
uvicorn app.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}" --reload
