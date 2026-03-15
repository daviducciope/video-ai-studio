#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

load_env_file() {
  local env_file="$1"
  [[ -f "$env_file" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    local key="${line%%=*}"
    local value="${line#*=}"
    if [[ -z "${!key+x}" ]]; then
      export "$key=$value"
    fi
  done < "$env_file"
}

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI non trovata nel PATH." >&2
  exit 1
fi

load_env_file "$ROOT_DIR/.env"

REGION="${AWS_REGION:-}"
BUCKET="${S3_BUCKET_NAME:-}"
PREFIX="${S3_PREFIX:-}"

echo "AWS caller identity:"
aws sts get-caller-identity

echo
echo "AWS config:"
aws configure list

if [[ -n "$REGION" ]]; then
  echo
  echo "Resolved region: $REGION"
else
  echo
  echo "AWS_REGION non impostata. Il backend locale continua a funzionare, ma S3 non e' attivabile." >&2
fi

if [[ -n "$BUCKET" ]]; then
  echo
  echo "Checking bucket: $BUCKET"
  if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
    echo "Bucket raggiungibile."
    aws s3api get-public-access-block --bucket "$BUCKET" || true
    aws s3api get-bucket-versioning --bucket "$BUCKET" || true
    aws s3api get-bucket-encryption --bucket "$BUCKET" || true
    if [[ -n "$PREFIX" ]]; then
      echo "Configured prefix: $PREFIX/"
    fi
  else
    echo "Bucket non trovato o non accessibile con le credenziali correnti."
  fi
else
  echo
  echo "S3_BUCKET_NAME non impostato. Nessun bucket verificato."
fi
