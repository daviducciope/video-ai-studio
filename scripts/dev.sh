#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/run_api.sh" &
API_PID=$!

"$ROOT_DIR/scripts/run_worker.sh" &
WORKER_PID=$!

trap 'kill $API_PID $WORKER_PID 2>/dev/null || true' EXIT

"$ROOT_DIR/scripts/run_web.sh"
