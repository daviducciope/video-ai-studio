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

if [[ -z "$REGION" ]]; then
  echo "AWS_REGION obbligatoria per il bootstrap S3." >&2
  exit 1
fi

if [[ -z "$BUCKET" ]]; then
  echo "S3_BUCKET_NAME obbligatorio per il bootstrap S3." >&2
  exit 1
fi

echo "Bootstrap bucket S3 privato: $BUCKET (region $REGION)"

if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "Bucket gia' esistente o accessibile. Nessuna creazione eseguita."
else
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET"
  else
    aws s3api create-bucket \
      --bucket "$BUCKET" \
      --region "$REGION" \
      --create-bucket-configuration "LocationConstraint=$REGION"
  fi
  echo "Bucket creato."
fi

aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws s3api put-bucket-versioning \
  --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket "$BUCKET" \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

if [[ -n "$PREFIX" ]]; then
  aws s3api put-object --bucket "$BUCKET" --key "$PREFIX/"
  echo "Prefix placeholder creato: $PREFIX/"
fi

echo "Bootstrap completato."
