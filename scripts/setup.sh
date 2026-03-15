#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3.11 -m venv --clear "$ROOT_DIR/.venv"
source "$ROOT_DIR/.venv/bin/activate"
pip install -r "$ROOT_DIR/services/api/requirements.txt" -r "$ROOT_DIR/services/worker/requirements.txt"

cd "$ROOT_DIR/apps/web"
npm install
