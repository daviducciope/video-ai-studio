#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/scripts/common.sh"

load_env_defaults "$ROOT_DIR/.env"
export WEB_PORT="$(ensure_port_available "${WEB_PORT:-3000}" "$ROOT_DIR" "WEB")"
cd "$ROOT_DIR/apps/web"
export NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://localhost:${API_PORT:-8000}}"
export PORT="${PORT:-$WEB_PORT}"
npm run dev
