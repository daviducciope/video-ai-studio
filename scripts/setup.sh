#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "python3.11 non trovato. Installa Python 3.11 e riesegui 'make setup'." >&2
  exit 1
fi

python3.11 -m venv --clear "$ROOT_DIR/.venv"
source "$ROOT_DIR/.venv/bin/activate"
pip install -r "$ROOT_DIR/services/api/requirements.txt" -r "$ROOT_DIR/services/worker/requirements.txt"

cd "$ROOT_DIR/apps/web"
npm install
