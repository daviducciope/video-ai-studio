#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/scripts/common.sh"

load_env_defaults "$ROOT_DIR/.env"
load_local_runtime_secrets "$ROOT_DIR"
export API_PORT="$(ensure_port_available "${API_PORT:-8000}" "$ROOT_DIR" "API")"
export WEB_PORT="$(ensure_port_available "${WEB_PORT:-3000}" "$ROOT_DIR" "WEB")"
export NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://localhost:$API_PORT}"

"$ROOT_DIR/scripts/run_api.sh" &
API_PID=$!

"$ROOT_DIR/scripts/run_worker.sh" &
WORKER_PID=$!

trap 'kill $API_PID $WORKER_PID 2>/dev/null || true' EXIT

echo "[DEV] API su http://localhost:$API_PORT" >&2
echo "[DEV] Web su http://localhost:$WEB_PORT" >&2
"$ROOT_DIR/scripts/run_web.sh"
