#!/usr/bin/env bash
set -euo pipefail

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI non trovata nel PATH." >&2
  exit 1
fi

echo "AWS identity:"
aws sts get-caller-identity
