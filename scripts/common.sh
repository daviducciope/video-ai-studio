#!/usr/bin/env bash

load_env_defaults() {
  local env_file="$1"
  [[ -f "$env_file" ]] || return 0

  local -a keys=()
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)= ]]; then
      keys+=("${BASH_REMATCH[1]}")
    fi
  done < "$env_file"

  local key
  local -A original_values=()
  local -A was_set=()
  for key in "${keys[@]}"; do
    if [[ -n "${!key+x}" ]]; then
      was_set["$key"]=1
      original_values["$key"]="${!key}"
    fi
  done

  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a

  for key in "${keys[@]}"; do
    if [[ -n "${was_set[$key]+x}" ]]; then
      export "$key=${original_values[$key]}"
    fi
  done
}

load_local_runtime_secrets() {
  local root_dir="$1"
  local credential_file="${AWS_CREDENTIAL_FILE:-$root_dir/aws_credential}"
  [[ -f "$credential_file" ]] || return 0
  [[ -n "${XAI_API_KEY:-}" ]] && return 0

  local key
  key="$(
    python3 - "$credential_file" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    match = re.match(r'^(?:export\s+)?XAI_API_KEY\s*=\s*(.+)$', line)
    if not match:
        continue
    value = match.group(1).strip()
    if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
        value = value[1:-1]
    print(value)
    break
PY
  )"
  if [[ -n "$key" ]]; then
    export XAI_API_KEY="$key"
  fi
}

port_pids() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u
}

describe_pid() {
  local pid="$1"
  local command cwd
  command="$(ps -p "$pid" -o command= 2>/dev/null | sed 's/^ *//')"
  cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
  printf 'pid=%s cwd=%s cmd=%s\n' "$pid" "${cwd:-unknown}" "${command:-unknown}"
}

is_safe_project_pid() {
  local pid="$1"
  local root_dir="$2"
  local command cwd
  command="$(ps -p "$pid" -o command= 2>/dev/null | sed 's/^ *//')"
  cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"

  [[ -n "$command" ]] || return 1
  [[ "$command" =~ (node|next|npm|uvicorn|python) ]] || return 1
  [[ "$command" == *"$root_dir"* || "$cwd" == "$root_dir"* ]] || return 1
  return 0
}

find_available_port() {
  local start_port="$1"
  local port="$start_port"
  while [[ "$port" -lt $((start_port + 50)) ]]; do
    if [[ -z "$(port_pids "$port")" ]]; then
      echo "$port"
      return 0
    fi
    port=$((port + 1))
  done
  echo "$start_port"
  return 1
}

ensure_port_available() {
  local desired_port="$1"
  local root_dir="$2"
  local label="$3"
  local allow_force_kill=0
  case "$desired_port" in
    3000|8000|3010|8010) allow_force_kill=1 ;;
  esac

  if ! command -v lsof >/dev/null 2>&1; then
    echo "[$label] lsof non disponibile, uso la porta richiesta $desired_port." >&2
    echo "$desired_port"
    return 0
  fi

  local pids
  pids="$(port_pids "$desired_port")"
  if [[ -z "$pids" ]]; then
    echo "$desired_port"
    return 0
  fi

  echo "[$label] porta $desired_port occupata." >&2
  local pid
  while IFS= read -r pid; do
    [[ -n "$pid" ]] || continue
    echo "[$label] trovato $(describe_pid "$pid")" >&2
    if is_safe_project_pid "$pid" "$root_dir"; then
      echo "[$label] termino il processo locale precedente $pid per liberare la porta $desired_port." >&2
      kill "$pid" 2>/dev/null || true
      sleep 1
      if kill -0 "$pid" 2>/dev/null; then
        echo "[$label] il processo $pid non si e' fermato subito; invio SIGTERM finale." >&2
        kill -TERM "$pid" 2>/dev/null || true
        sleep 1
      fi
      if [[ "$allow_force_kill" -eq 1 ]] && kill -0 "$pid" 2>/dev/null; then
        echo "[$label] il processo $pid e' ancora attivo; invio kill -9 sulla porta di dev locale $desired_port." >&2
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
      fi
    fi
  done <<< "$pids"

  if [[ -z "$(port_pids "$desired_port")" ]]; then
    echo "$desired_port"
    return 0
  fi

  local alternative
  alternative="$(find_available_port "$((desired_port + 1))")"
  if [[ "$alternative" != "$desired_port" ]]; then
    echo "[$label] porta $desired_port non liberata in sicurezza; uso la porta alternativa $alternative." >&2
    echo "$alternative"
    return 0
  fi

  echo "[$label] impossibile trovare una porta libera a partire da $desired_port." >&2
  return 1
}
